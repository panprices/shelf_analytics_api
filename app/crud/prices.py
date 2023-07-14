from typing import List, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.crud import get_results_from_statement_with_filters
from app.models import (
    RetailerProductHistory,
    RetailerProduct,
    MockBrandProductWithMarketPrices,
)
from app.schemas.filters import GlobalFilter, PagedGlobalFilter


def get_historical_prices_by_retailer_for_brand_product(
    db: Session, global_filter: GlobalFilter, brand_product_id: str, brand_id: str
) -> List[RetailerProductHistory]:
    statement = f"""
        with available_prices as (
            select *
            from (
                select rpts.product_id,
                    rp.retailer_id,
                    rpts.price * c.to_sek as price,
                    'SEK' as currency,
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
                    join currency c on c.name = rpts.currency
                    LEFT JOIN product_group_assignation pga ON pga.product_id = bp.id
                where bp.id = :brand_product_id and rpts.price <> 0
                    AND bp.brand_id = :brand_id
                    AND rpts.availability <> 'out_of_stock'
                    AND pm.certainty >= 'auto_high_confidence'
                    {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                    {"AND rp.retailer_id IN :retailers" if global_filter.retailers else ""}
                    {"AND r.country IN :countries" if global_filter.countries else ""}
                    {"AND pga.product_group_id IN :groups" if global_filter.groups else ""}
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
            categories=tuple(global_filter.categories),
            retailers=tuple(global_filter.retailers),
            countries=tuple(global_filter.countries),
            groups=tuple(global_filter.groups),
            brand_id=brand_id,
        )
        .options(
            selectinload(RetailerProductHistory.product).selectinload(
                RetailerProduct.retailer
            )
        )
        .all()
    )


def _create_price_table_data_query(
    global_filter: PagedGlobalFilter, brand_id: str
) -> Tuple[str, dict]:
    well_defined_grid_filters = [
        i for i in global_filter.data_grid_filter.items if i.is_well_defined()
    ]
    query = f"""
        SELECT * FROM brand_product_msrp_view
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
        **{
            f"fv_{index}": i.get_safe_postgres_value()
            for index, i in enumerate(global_filter.data_grid_filter.items)
            if i.is_well_defined()
        },
    }

    return query, params


def get_price_table_data(db: Session, global_filter: PagedGlobalFilter, brand_id: str):
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
    db: Session, global_filter: PagedGlobalFilter, brand_id: str
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
