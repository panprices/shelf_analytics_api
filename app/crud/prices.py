from typing import List, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.crud import get_results_from_statement_with_filters
from app.models import (
    RetailerProductHistory,
    RetailerProduct,
    MockBrandProductWithMarketPrices,
    MSRP,
)
from app.schemas.filters import (
    GlobalFilter,
    PagedGlobalFilter,
    PagedPriceValuesFilter,
    PriceValuesFilter,
)


def get_historical_prices_by_retailer_for_brand_product(
    db: Session, prices_filter: PriceValuesFilter, brand_product_id: str, brand_id: str
) -> List[RetailerProductHistory]:
    statement = f"""
        with available_prices as (
            select *
            from (
                select rpts.product_id,
                    rp.retailer_id,
                    CASE 
                        WHEN c.name = :selected_currency THEN rpts.price
                        ELSE rpts.price * c.to_sek / dc.to_sek
                    END as price,
                    :selected_currency as currency,
                    rpts.availability,
                    date_trunc('day', time)::timestamp as time,
                    row_number() over (
                        partition by rp.retailer_id, date_trunc('day', time)
                    ) as "rank"
                from retailer_product_time_series rpts
                    join retailer_product rp on rp.id = rpts.product_id
                    join retailer r on r.id = rp.retailer_id
                    join product_matching pm on rp.id = pm.retailer_product_id
                    join brand_product bp on bp.id = pm.brand_product_id
                    JOIN brand b ON b.id = bp.brand_id 
                    join currency c on c.name = rpts.currency
                    join currency dc ON dc.name = :selected_currency 
                    LEFT JOIN product_group_assignation pga ON pga.product_id = bp.id
                where bp.id = :brand_product_id and rpts.price <> 0
                    AND bp.brand_id = :brand_id
                    AND rpts.availability <> 'out_of_stock'
                    AND pm.certainty >= 'auto_high_confidence'
                    AND rpts.time >= :start_date
                    {"AND bp.category_id IN :categories" if prices_filter.categories else ""}
                    {"AND rp.retailer_id IN :retailers" if prices_filter.retailers else ""}
                    {"AND r.country IN :countries" if prices_filter.countries else ""}
                    {"AND pga.product_group_id IN :groups" if prices_filter.groups else ""}
                order by time asc
            ) per_retailer_time_series
            where rank = 1
        )
        select ap.product_id,
            ap.price,
            ap.currency,
            ap.availability,
            ap.time
        from available_prices ap
        UNION
        select dates.product_id,
            ap.price,
            ap.currency,
            ap.availability,
            dates.time
        from (
            select retailer_id, product_id,
                date_trunc('week', generate_series(
                    (select min(time) from available_prices),
                    (select max(time) from available_prices),
                    '1w'
                )::timestamp) as time
            from available_prices
            group by retailer_id, product_id
        ) dates LEFT JOIN available_prices ap ON dates.retailer_id = ap.retailer_id 
                                                AND dates.time = date_trunc('week', ap.time)
        order by time asc
    """

    return (
        db.query(RetailerProductHistory)
        .from_statement(text(statement))
        .params(
            brand_product_id=brand_product_id,
            categories=tuple(prices_filter.categories),
            retailers=tuple(prices_filter.retailers),
            countries=tuple(prices_filter.countries),
            groups=tuple(prices_filter.groups),
            brand_id=brand_id,
            start_date=prices_filter.start_date,
            selected_currency=prices_filter.currency,
        )
        .options(
            selectinload(RetailerProductHistory.product).selectinload(
                RetailerProduct.retailer
            )
        )
        .all()
    )


def _create_price_table_data_query(
    global_filter: PagedPriceValuesFilter, brand_id: str
) -> Tuple[str, dict]:
    well_defined_grid_filters = [
        i for i in global_filter.data_grid_filter.items if i.is_well_defined()
    ]
    query = f"""
        SELECT 
            "brand_product_id", brand_product_msrp_view."name", "gtin", "sku", "category_id", "brand_id", "msrp_standard", "msrp_currency", "msrp_country", "image_id", "image_url", "offers",
            CASE 
                WHEN c.name = :selected_currency THEN NULL -- no need to convert
                ELSE msrp_standard * c.to_sek / dc.to_sek
            END as msrp_client_currency,
            :selected_currency AS client_currency
        FROM brand_product_msrp_view
            JOIN LATERAL (
                SELECT * FROM currency WHERE currency.name = :selected_currency LIMIT 1
            ) dc ON TRUE
            JOIN LATERAL (
                SELECT * FROM currency WHERE currency.name = brand_product_msrp_view.msrp_currency LIMIT 1
            ) c ON TRUE
        WHERE brand_id = :brand_id
            AND array_length(offers, 1) > 0
            {"AND category_id IN :categories" if global_filter.categories else ""}
            {"AND msrp_country IN :countries" if global_filter.countries else ""}
            {"AND brand_product_id IN (SELECT product_id FROM product_group_assignation pga WHERE pga.product_group_id IN :groups)" 
                if global_filter.groups else ""}
            {"AND EXISTS (SELECT 1 FROM unnest(offers) AS offer WHERE offer->>'retailer_id' IN :retailers)" 
                if global_filter.retailers else ""}
            {
                (
                    "AND " + (" " + global_filter.data_grid_filter.operator + " ")
                        .join([
                            i.to_postgres_condition(index) 
                            for index, i in enumerate(well_defined_grid_filters)
                        ])
                )
                if well_defined_grid_filters else ""
            }
    """

    params = {
        "brand_id": brand_id,
        "categories": tuple(global_filter.categories),
        "countries": tuple(global_filter.countries),
        "groups": tuple(global_filter.groups),
        "retailers": tuple(global_filter.retailers),
        "selected_currency": global_filter.currency,
        **{
            f"fv_{index}": i.get_safe_postgres_value()
            for index, i in enumerate(global_filter.data_grid_filter.items)
            if i.is_well_defined()
        },
    }

    return query, params


def get_price_table_data(
    db: Session, global_filter: PagedPriceValuesFilter, brand_id: str
):
    price_data_query, price_data_params = _create_price_table_data_query(
        global_filter, brand_id
    )

    query = f"""
        SELECT * 
        FROM (
            {price_data_query}
        ) price_data
        {
            "ORDER BY " + global_filter.sorting.column + " " + global_filter.sorting.direction 
            if global_filter.sorting else "ORDER BY name, msrp_country ASC"
        }
        OFFSET :offset
        LIMIT :limit;
    """

    results = (
        db.query(MockBrandProductWithMarketPrices)
        .from_statement(statement=text(query))
        .params(
            offset=global_filter.get_products_offset(),
            limit=global_filter.page_size,
            sorting=global_filter.sorting,
            **price_data_params,
        )
        .all()
    )

    return results


def count_price_table_data(
    db: Session, global_filter: PagedPriceValuesFilter, brand_id: str
):
    price_data_query, price_data_params = _create_price_table_data_query(
        global_filter, brand_id
    )

    query = f"""
        SELECT COUNT(*)
        FROM (
            {price_data_query}
        ) price_data;
    """

    return db.execute(
        text(query),
        params=price_data_params,
    ).scalar()


def get_historical_msrp_deviation_per_retailer(
    db: Session, global_filter: GlobalFilter, brand_id: str
):
    query = f"""
        SELECT retailer, time,
            AVG(price_deviation) as average_price_deviation
        FROM msrp_deviation_matview
        WHERE brand_id = :brand_id
            AND time >= :start_date
            {"AND category_id IN :categories" if global_filter.categories else ""}
            {"AND country IN :countries" if global_filter.countries else ""}
            {"AND retailer_id IN :retailers" if global_filter.retailers else ""}
            {"AND brand_product_id IN " +
                "(SELECT product_id FROM product_group_assignation pga WHERE pga.product_group_id IN :groups)" 
                if global_filter.groups else ""
            }
        GROUP BY retailer_id, retailer, country, time
        ORDER BY time ASC;
    """

    return get_results_from_statement_with_filters(db, brand_id, global_filter, query)


def get_historical_wholesale_deviation_per_retailer(
    db: Session, global_filter: GlobalFilter, brand_id: str
):
    query = f"""
        SELECT retailer, time,
            AVG(price_deviation) as average_price_deviation
        FROM wholesale_deviation_matview
        WHERE brand_id = :brand_id
            AND time >= :start_date
            {"AND category_id IN :categories" if global_filter.categories else ""}
            {"AND country IN :countries" if global_filter.countries else ""}
            {"AND retailer_id IN :retailers" if global_filter.retailers else ""}
            {"AND brand_product_id IN " +
                "(SELECT product_id FROM product_group_assignation pga WHERE pga.product_group_id IN :groups)" 
                if global_filter.groups else ""
            }
        GROUP BY retailer, time
        ORDER BY time ASC;
    """

    return get_results_from_statement_with_filters(db, brand_id, global_filter, query)


def get_historical_average_price_deviation_per_retailer(
    db: Session, global_filter: GlobalFilter, brand_id: str
):
    query = f"""
        SELECT retailer, time,
            AVG(price_deviation) as average_price_deviation
        FROM average_price_deviation_matview
        WHERE brand_id = :brand_id
            AND time >= :start_date
            {"AND category_id IN :categories" if global_filter.categories else ""}
            {"AND country IN :countries" if global_filter.countries else ""}
            {"AND retailer_id IN :retailers" if global_filter.retailers else ""}
            {"AND brand_product_id IN " +
                "(SELECT product_id FROM product_group_assignation pga WHERE pga.product_group_id IN :groups)"
                if global_filter.groups else ""
            }
        GROUP BY retailer, time
        ORDER BY time ASC;
    """

    return get_results_from_statement_with_filters(db, brand_id, global_filter, query)


def get_price_changes(
    db: Session,
    global_filter: GlobalFilter,
    brand_id: str,
    sign: int,
):
    query = f"""
        SELECT retailer_name, product_name, price_diff, brand_product_id, sku, r.country as retailer_country
        FROM price_changes_matview pcm
            JOIN retailer r ON r.id = pcm.retailer_id
        WHERE brand_id = :brand_id AND r.status = 'success'
            {"AND brand_category_id IN :categories" if global_filter.categories else ""}
            {"AND r.country IN :countries" if global_filter.countries else ""}
            {"AND pcm.retailer_id IN :retailers" if global_filter.retailers else ""}
            {"AND brand_product_id IN " +
                "(SELECT product_id FROM product_group_assignation pga WHERE pga.product_group_id IN :groups)"
                if global_filter.groups else ""
            }
            AND price_diff * :sign >= 0
        ORDER BY ABS(price_diff) DESC
        LIMIT :limit
        OFFSET :offset;
    """

    return get_results_from_statement_with_filters(
        db, brand_id, global_filter, query, limit=200, extra_params={"sign": sign}
    )


def get_retailer_pricing_overview(
    db: Session,
    global_filter: GlobalFilter,
    brand_id: str,
):
    query = f"""
        -- Nr of products found last 1 day per retailer
        WITH products_per_retailer AS (
            SELECT 
                r.id, 
                r.name,
                r.country,
                count(*) AS nr_products
            FROM retailer_product rp
                JOIN product_matching pm ON rp.id = pm.retailer_product_id
                JOIN brand_product bp ON bp.id = pm.brand_product_id
                JOIN retailer r ON r.id = rp.retailer_id
                JOIN brand b ON b.id = bp.brand_id
                JOIN retailer_to_brand_mapping rtbm ON rtbm.retailer_id = r.id 
                                                AND rtbm.brand_id = b.id
            WHERE b.id = :brand_id
                AND bp.active = TRUE
                AND pm.certainty >= 'auto_high_confidence'
                AND fetched_at >= now()::date - interval '1 day'
                {"AND r.country IN :countries" if global_filter.countries else ""}
                {"AND r.id IN :retailers" if global_filter.retailers else ""}
                {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                {"AND bp.id IN " +
                    "(SELECT product_id FROM product_group_assignation pga WHERE pga.product_group_id IN :groups)"
                    if global_filter.groups else ""
                }
            GROUP BY r.id
        -- Nr of products with price changed last 7 days
        ), product_price_changed AS (
            SELECT 
                rp.id,
                rp.retailer_id
            FROM retailer_product rp
                JOIN product_matching pm ON rp.id = pm.retailer_product_id
                JOIN brand_product bp ON bp.id = pm.brand_product_id
                JOIN brand b ON b.id = bp.brand_id
                JOIN retailer_product_time_series rpts ON rpts.product_id = rp.id
                JOIN retailer r ON r.id = rp.retailer_id
            WHERE b.id = :brand_id
                AND bp.active = TRUE
                AND pm.certainty >= 'auto_high_confidence'
                AND time >= now()::date - interval '7 days'
                {"AND r.country IN :countries" if global_filter.countries else ""}
                {"AND r.id IN :retailers" if global_filter.retailers else ""}
                {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                {"AND bp.id IN " +
                    "(SELECT product_id FROM product_group_assignation pga WHERE pga.product_group_id IN :groups)"
                    if global_filter.groups else ""
                }
            GROUP BY rp.id
            HAVING count(DISTINCT rpts.price) > 1
        ), retailer_with_nr_products_price_changed AS (
            SELECT 
                r.id AS retailer_id,
                count(*) AS nr_products_with_price_changed
            FROM product_price_changed
                JOIN retailer r ON product_price_changed.retailer_id = r.id
            GROUP BY r.id
        ),
        -- Nr products with cheapest price per market (country)
        market_price AS (
            SELECT 
                bp.id AS brand_product_id,
                country,
                currency,
                min(rp.price) AS min_price,
                avg(rp.price) AS average_price
            FROM retailer_product rp
                JOIN product_matching pm ON rp.id = pm.retailer_product_id
                JOIN brand_product bp ON bp.id = pm.brand_product_id
                JOIN retailer r ON r.id = rp.retailer_id
                JOIN brand b ON b.id = bp.brand_id
                JOIN retailer_to_brand_mapping rtbm ON rtbm.retailer_id = r.id AND rtbm.brand_id = b.id
            WHERE b.id = :brand_id
                AND fetched_at >= now()::date - interval '1 day'
            GROUP BY bp.id, r.country, rp.currency
        ), 
        retailer_with_nr_cheapest_price AS (
            SELECT 
                r.id,
                COUNT(*) AS nr_products_with_cheapest_price
            FROM retailer_product rp
                JOIN product_matching pm ON rp.id = pm.retailer_product_id
                JOIN brand_product bp ON bp.id = pm.brand_product_id
                JOIN retailer r ON r.id = rp.retailer_id
                JOIN brand b ON b.id = bp.brand_id
                JOIN retailer_to_brand_mapping rtbm ON rtbm.retailer_id = r.id AND rtbm.brand_id = b.id
                JOIN market_price ON market_price.brand_product_id = bp.id
                                 AND market_price.country = r.country
                                 AND market_price.currency = rp.currency
            WHERE b.id = :brand_id
                AND bp.active = TRUE
                AND pm.certainty >= 'auto_high_confidence'
                AND fetched_at >= now()::date - interval '1 day'
                AND rp.price = market_price.min_price
                {"AND r.country IN :countries" if global_filter.countries else ""}
                {"AND r.id IN :retailers" if global_filter.retailers else ""}
                {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                {"AND bp.id IN " +
                    "(SELECT product_id FROM product_group_assignation pga WHERE pga.product_group_id IN :groups)"
                    if global_filter.groups else ""
                }
            GROUP BY r.id
        ), retailer_with_market_price_deviation AS (
            SELECT 
                r.id, 
                r.name,
                r.country,
                count(*) AS nr_products,
                100.0 * avg((rp.price - average_price) / average_price::double precision) AS average_market_price_deviation
            FROM retailer_product rp
                JOIN product_matching pm ON rp.id = pm.retailer_product_id
                JOIN brand_product bp ON bp.id = pm.brand_product_id
                JOIN retailer r ON r.id = rp.retailer_id
                JOIN brand b ON b.id = bp.brand_id
                JOIN retailer_to_brand_mapping rtbm ON rtbm.retailer_id = r.id 
                                                AND rtbm.brand_id = b.id
                JOIN market_price mp ON mp.brand_product_id = bp.id
                                 AND mp.country = r.country
                                 AND mp.currency = rp.currency
            WHERE b.id = :brand_id
                AND bp.active = TRUE
                AND pm.certainty >= 'auto_high_confidence'
                AND fetched_at >= now()::date - interval '1 day'
                -- AND market_price.time = (SELECT max(time) FROM market_price)
                AND average_price > 0 -- to make sure, even though average_price should not be 0
                {"AND r.country IN :countries" if global_filter.countries else ""}
                {"AND r.id IN :retailers" if global_filter.retailers else ""}
                {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                {"AND bp.id IN " +
                    "(SELECT product_id FROM product_group_assignation pga WHERE pga.product_group_id IN :groups)"
                    if global_filter.groups else ""
                }
            GROUP BY r.id
        )
        SELECT 
            r.id AS retailer_id,
            r.name AS retailer_name,
            r.country AS retailer_country,
            r.nr_products AS products_count,
            COALESCE(nr_products_with_cheapest_price, 0) AS cheapest_price_count,
            COALESCE(nr_products_with_price_changed, 0) AS price_changed_count,
            average_market_price_deviation::decimal(10, 2)
        FROM products_per_retailer r
            LEFT JOIN retailer_with_nr_products_price_changed
                ON retailer_with_nr_products_price_changed.retailer_id = r.id
            LEFT JOIN retailer_with_nr_cheapest_price
                ON retailer_with_nr_cheapest_price.id = r.id
            LEFT JOIN retailer_with_market_price_deviation
                ON retailer_with_market_price_deviation.id = r.id
        WHERE average_market_price_deviation IS NOT NULL
        ORDER BY products_count DESC;
    """

    return get_results_from_statement_with_filters(db, brand_id, global_filter, query)


def get_product_msrp(
    db: Session,
    brand_product_id: str,
):
    return db.query(MSRP).filter(MSRP.brand_product_id == brand_product_id).all()


def get_comparison_products(
    db, prices_filter: PriceValuesFilter, brand_product_id, brand_id
):
    query = """
        SELECT AVG(
                CASE
                    WHEN rp.currency = :selected_currency THEN rp.price
                    ELSE rp.price * rc.to_sek / dc.to_sek
                END / 100
           ) as market_average, bi.url as image_url, bp.name, true as is_client
        FROM brand_product bp
            JOIN product_matching pm ON pm.brand_product_id = bp.id
            JOIN retailer_product rp ON rp.id = pm.retailer_product_id
            JOIN retailer r ON rp.retailer_id = r.id
            JOIN brand b ON bp.brand_id = b.id
            JOIN LATERAL (
                SELECT * FROM currency WHERE currency.name = :selected_currency LIMIT 1
            ) dc ON true
            JOIN LATERAL (
                SELECT * FROM currency WHERE currency.name = rp.currency LIMIT 1
            ) rc ON true
            LEFT JOIN LATERAL (
                SELECT *
                FROM brand_image
                WHERE brand_product_id = bp.id
                ORDER BY processed DESC
                LIMIT 1
            ) bi ON true
        WHERE bp.id = :brand_product_id
            AND bp.brand_id = :brand_id
            AND pm.certainty >= 'auto_high_confidence'
            AND rp.fetched_at >= date_trunc('week', now()) - '1 week'::interval
        GROUP BY bi.url, bp.name
        UNION ALL
        SELECT  AVG(
                CASE
                    WHEN rp.currency = :selected_currency THEN rp.price
                    ELSE rp.price * rc.to_sek / dc.to_sek
                END / 100
           ) as market_average, 
           CASE WHEN cp.image_processed THEN 'https://storage.googleapis.com/b2b_shelf_analytics_images/' || cp.id::text || '.png' ELSE image_url END as image_url, 
           cp.brand_name || ' - ' || cp.name, false as is_client
        FROM brand_product bp
            JOIN comparison_to_brand_product ctbp ON bp.id = ctbp.brand_product_id
            JOIN comparison_product cp ON cp.id = ctbp.comparison_product_id
            JOIN comparison_product_matching cpm ON cpm.comparison_product_id = cp.id
            JOIN retailer_product rp ON rp.id = cpm.retailer_product_id
            JOIN retailer r ON rp.retailer_id = r.id
            JOIN brand b ON bp.brand_id = b.id
            JOIN LATERAL (
                SELECT * FROM currency WHERE currency.name = :selected_currency LIMIT 1
            ) dc ON true
            JOIN LATERAL (
                SELECT * FROM currency WHERE currency.name = rp.currency LIMIT 1
            ) rc ON true
        WHERE bp.id = :brand_product_id
            AND bp.brand_id = :brand_id
            AND cpm.certainty >= 'auto_high_confidence'
            AND rp.fetched_at >= date_trunc('week', now()) - '1 week'::interval
        GROUP BY cp.image_url, cp.name, cp.image_processed, cp.id;
    """

    return get_results_from_statement_with_filters(
        db,
        brand_id,
        prices_filter,
        query,
        extra_params={
            "brand_product_id": brand_product_id,
            "selected_currency": prices_filter.currency,
        },
    )
