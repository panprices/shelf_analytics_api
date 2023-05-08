from typing import Dict, List, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.crud.utils import (
    convert_rows_to_dicts,
    get_results_from_statement_with_filters,
)
from app.models import (
    RetailerProduct,
)
from app.models.retailer import MockRetailerProductGridItem
from app.schemas.filters import PagedGlobalFilter, GlobalFilter, DataPageFilter


def _create_query_for_products_datapool(
    brand_id, global_filter: DataPageFilter
) -> Tuple[str, Dict]:
    well_defined_grid_filters = [
        i for i in global_filter.data_grid_filter.items if i.is_well_defined()
    ]
    filter_on_product_group_statement = """
        AND rp.matched_brand_product_id IN (
            SELECT product_id 
            FROM product_group_assignation pga 
            WHERE pga.product_group_id IN :groups
        )
    """

    statement = f"""
        SELECT * 
        FROM retailer_product_including_unavailable_matview rp
        WHERE created_at > :start_date 
            AND brand_id = :brand_id
            {"AND brand_category_id IN :categories" if global_filter.categories else ""}
            {"AND retailer_id IN :retailers" if global_filter.retailers else ""}
            {"AND country IN :countries" if global_filter.countries else ""}
            {filter_on_product_group_statement if global_filter.groups else ""}
            {"AND (sku LIKE :search_text OR gtin LIKE :search_text)" if global_filter.search_text else ""}
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
        ORDER BY id ASC
    """
    params = {
        "start_date": global_filter.start_date,
        "brand_id": brand_id,
        "categories": tuple(global_filter.categories),
        "retailers": tuple(global_filter.retailers),
        "countries": tuple(global_filter.countries),
        "groups": tuple(global_filter.groups),
        "search_text": f"%{global_filter.search_text}%",
        **{
            f"fv_{index}": i.get_safe_postgres_value()
            for index, i in enumerate(global_filter.data_grid_filter.items)
            if i.is_well_defined()
        },
    }
    return statement, params


def _get_full_product_list(
    db: Session, brand_id: str, statement: str, global_filter: PagedGlobalFilter
):
    return (
        db.query(MockRetailerProductGridItem)
        .from_statement(text(statement))
        .params(
            start_date=global_filter.start_date,
            brand_id=brand_id,
            categories=tuple(global_filter.categories),
            retailers=tuple(global_filter.retailers),
            countries=tuple(global_filter.countries),
            groups=tuple(global_filter.groups),
            offset=global_filter.get_products_offset(),
            limit=global_filter.page_size,
            search_text=f"%{global_filter.search_text}%",
            **{
                f"fv_{index}": i.get_safe_postgres_value()
                for index, i in enumerate(global_filter.data_grid_filter.items)
                if i.is_well_defined()
            },
        )
        .all()
    )


def get_products(
    db: Session, brand_id: str, global_filter: PagedGlobalFilter
) -> List[RetailerProduct]:
    """
    Returns the list of products from each retailer corresponding to the client currently using the application.

    A special request here was to also return unmatched items from the client (brand), so they can easily keep an eye
    on the products they need to push on. These lists of unmatched items should be added on a 'per retailer' basis
    meaning that if the item A is missing from retailers X and Y, then we need to add to rows corresponding to A at X,
    and A at Y respectively.

    To fulfill this requirement, we use plain SQL queries concatenated by 'UNION ALL' statements, then we apply the
    set LIMIT and OFFSET corresponding to paging on the result. A mock product will have a randomly generated id. We
    tried also using the id of the brand product, but that resulted in duplicated values for the primary key (the same
    brand product mocked for different retailers) which generated weird behaviour from SQLAlchemy.

    Note: the mock-up missing products are returned without the matching brand product. The connection between a
    retailer product and a brand product is done through the `product_matching` association table, which does not have
    any rows for the mock-up products. If you require the "match" as well, see :func:~`app.routers.data` for an example
    of how to do that. We chose to keep that logic out of this file to avoid creating a dependency between 2 crud
    solvers, which could evolve in a circular dependency in the future.

    :param db:
    :param brand_id:
    :param global_filter:
    :return:
    """
    query, params = _create_query_for_products_datapool(brand_id, global_filter)
    statement = f"""
        SELECT * FROM (
            {query}
        ) products_datapool
        {
            "ORDER BY " + global_filter.sorting.column + " " + global_filter.sorting.direction 
            if global_filter.sorting else "ORDER BY name ASC"
        }
        OFFSET :offset
        LIMIT :limit
    """

    return _get_full_product_list(db, brand_id, statement, global_filter)


def _count_products_datapool(
    db: Session,
    brand_id: str,
    global_filter: DataPageFilter,
    count_target: str = "*",
) -> int:
    query, params = _create_query_for_products_datapool(brand_id, global_filter)
    statement = f"""
        SELECT COUNT({count_target}) FROM (
            {query}
        ) brand_products
    """

    return db.execute(
        text(statement),
        params=params,
    ).scalar()


def count_brand_products(
    db: Session, brand_id: str, global_filter: DataPageFilter
) -> int:
    return _count_products_datapool(
        db, brand_id, global_filter, count_target="DISTINCT matched_brand_product_id"
    )


def count_products(db: Session, brand_id: str, global_filter: PagedGlobalFilter) -> int:
    return _count_products_datapool(db, brand_id, global_filter, count_target="*")


def get_unique_brand_product_ids(
    db: Session, brand_id: str, global_filter: DataPageFilter
) -> List[str]:
    query, params = _create_query_for_products_datapool(brand_id, global_filter)
    statement = f"""
        SELECT DISTINCT matched_brand_product_id FROM (
            {query}
        ) products_datapool
    """
    return [
        r["matched_brand_product_id"]
        for r in convert_rows_to_dicts(db.execute(statement, params).fetchall())
    ]


def get_unique_brand_product_ids_by_retailer_matches(
    db: Session, retailer_product_ids: List[str]
) -> List[str]:
    statement = """
        SELECT DISTINCT matched_brand_product_id 
        FROM retailer_product_including_unavailable_matview
        WHERE id IN :retailer_product_ids
    """
    result = db.execute(
        text(statement),
        params={
            "retailer_product_ids": tuple(retailer_product_ids),
        },
    ).fetchall()
    return [r["matched_brand_product_id"] for r in convert_rows_to_dicts(result)]


def get_historical_visibility(db: Session, brand_id: str, global_filter: GlobalFilter):
    result = db.execute(
        text(
            f"""
            WITH visible_product AS (
                SELECT DISTINCT brand_product_in_stock.id, brand_product_in_stock.date
                FROM brand_product_in_stock 
                    INNER JOIN scraped_brand_product USING (id, date)
                    LEFT JOIN product_group_assignation pga ON pga.product_id = scraped_brand_product.id
                    JOIN retailer_to_brand_mapping rtbm ON rtbm.retailer_id = scraped_brand_product.retailer_id
                        AND rtbm.brand_id = scraped_brand_product.brand_id
                WHERE brand_product_in_stock.brand_id = :brand_id
                    AND NOT rtbm.shallow
                    {"AND scraped_brand_product.category_id IN :categories" if global_filter.categories else ""}
                    {"AND scraped_brand_product.retailer_id in :retailers" if global_filter.retailers else ""}
                    {"AND scraped_brand_product.country in :countries" if global_filter.countries else ""}
                    {"AND pga.product_group_id IN :groups" if global_filter.groups else ""}
            )
            SELECT
                date AS time,
                full_count - visible_count AS not_visible_count,
                visible_count
            FROM (
                SELECT date, COUNT(DISTINCT id) AS visible_count
                FROM visible_product
                GROUP BY date
            ) visible_product_grouped
            JOIN (
                SELECT date, COUNT(DISTINCT id) AS full_count
                FROM brand_product_in_stock
                WHERE brand_product_in_stock.brand_id = :brand_id
                GROUP BY date
            ) brand_product_in_stock_grouped  USING (date) 
            -- Only present data up to last week:
            WHERE date < date_trunc('week', now())::date
            ORDER BY date ASC
            """
        ),
        params={
            "brand_id": brand_id,
            "start_date": global_filter.start_date,
            "countries": tuple(global_filter.countries),
            "retailers": tuple(global_filter.retailers),
            "categories": tuple(global_filter.categories),
            "groups": tuple(global_filter.groups),
        },
    ).all()

    return convert_rows_to_dicts(result)


def get_historical_visibility_average(
    db: Session, brand_id: str, global_filter: GlobalFilter
):
    statement = f"""
        -- Note: When filter on a retailer that has no data for a few weeks, those week 
        -- will be missing from the result instead of being 0.
        -- This might be the desired behavior when filter on individual retailer, 
        -- but can be semi-weird for the "availability over time line chart" on all retailers.
        
        WITH scraped_brand_product_in_stock_per_retailer_count AS (
            SELECT
                date,
                full_count - visible_count AS not_visible_count,
                visible_count,
                retailer_id
            FROM (
                SELECT date, COUNT(DISTINCT id) AS visible_count, rtbm.retailer_id
                FROM scraped_brand_product_in_stock_per_retailer
                    LEFT JOIN product_group_assignation pga ON pga.product_id 
                        = scraped_brand_product_in_stock_per_retailer.id
                    JOIN retailer_to_brand_mapping rtbm 
                        ON rtbm.retailer_id = scraped_brand_product_in_stock_per_retailer.retailer_id 
                            AND rtbm.brand_id = scraped_brand_product_in_stock_per_retailer.brand_id
                WHERE rtbm.brand_id = :brand_id
                    AND NOT rtbm.shallow
                    {"AND category_id IN :categories" if global_filter.categories else ""}
                    {"AND rtbm.retailer_id in :retailers" if global_filter.retailers else ""}
                    {"AND country in :countries" if global_filter.countries else ""}
                    {"AND pga.product_group_id IN :groups" if global_filter.groups else ""}
                GROUP BY date, rtbm.retailer_id
            ) scraped_brand_product_in_stock_per_retailer_grouped
            JOIN (
                SELECT date, COUNT(DISTINCT id) AS full_count
                FROM brand_product_in_stock
                    LEFT JOIN product_group_assignation pga ON pga.product_id = brand_product_in_stock.id
                WHERE brand_id = :brand_id
                    {"AND category_id IN :categories" if global_filter.categories else ""}
                    {"AND pga.product_group_id in :groups" if global_filter.groups else ""}   
                GROUP BY date
            ) brand_product_in_stock_grouped USING (date)
            -- Only present data up to last week:
            WHERE date < date_trunc('week', now())::date
            ORDER BY date ASC
        )
        SELECT
            ROUND(AVG(visible_count)) AS visible_count,
            ROUND(AVG(not_visible_count)) AS not_visible_count,
            date AS time
        FROM scraped_brand_product_in_stock_per_retailer_count
        GROUP BY time
        ORDER BY time ASC;
    """
    return get_results_from_statement_with_filters(
        db, brand_id, global_filter, statement
    )


def export_full_brand_products_result(
    db: Session, brand_id: str, global_filter: PagedGlobalFilter
):
    statement, params = _create_query_for_products_datapool(brand_id, global_filter)
    return _get_full_product_list(
        db,
        brand_id,
        statement=statement,
        global_filter=global_filter,
    )


def count_available_products_by_retailers(
    db: Session, brand_id: str, global_filter: GlobalFilter
) -> List[Dict]:
    statement = f"""
        WITH 
        scraped_brand_product_last_week AS (
            SELECT DISTINCT
                bp.id,
                rp.retailer_id
            FROM brand_product bp
                JOIN product_matching pm ON bp.id = pm.brand_product_id
                JOIN retailer_product_time_series rpts ON pm.retailer_product_id = rpts.product_id
                JOIN retailer_product rp ON rpts.product_id = rp.id
                JOIN retailer r ON rp.retailer_id = r.id
                LEFT JOIN product_group_assignation pga ON pga.product_id = bp.id
                JOIN retailer_to_brand_mapping rtbm ON rtbm.retailer_id = r.id AND rtbm.brand_id = bp.brand_id
            WHERE
                bp.brand_id = :brand_id
                AND NOT rtbm.shallow
                AND pm.certainty NOT IN('auto_low_confidence', 'not_match')
                AND rpts.time 
                    BETWEEN date_trunc('week', now() - '7 days'::interval)::date AND date_trunc('week', now())::date
                {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                {"AND r.id in :retailers" if global_filter.retailers else ""}
                {"AND r.country in :countries" if global_filter.countries else ""}
                {"AND pga.product_group_id IN :groups" if global_filter.groups else ""}
        ),
        brand_product_in_stock_last_week AS (
            SELECT DISTINCT
                bp.id
            FROM brand_product bp
                JOIN brand_product_time_series bpts ON bpts.product_id = bp.id
                LEFT JOIN product_group_assignation pga ON pga.product_id = bp.id
            WHERE
                bp.brand_id = :brand_id
                AND bpts.availability = 'in_stock'
                AND bpts.time BETWEEN 
                    date_trunc('week', now() - '7 days'::interval)::date AND date_trunc('week', now())::date
                {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                {"AND pga.product_group_id in :groups" if global_filter.groups else ""}  
                
        ),
        brand_product_count_per_retailer AS (
            SELECT 
                retailer_id,
                COUNT(DISTINCT scraped_brand_product_last_week.id) AS available_products_count
            FROM scraped_brand_product_last_week
                JOIN brand_product_in_stock_last_week USING (id)
            GROUP BY retailer_id

            UNION -- retailers that does not have any products last week

            SELECT 
                r.id AS retailer_id,
                0 AS available_products_count
            FROM retailer r
                JOIN retailer_to_brand_mapping ON r.id = retailer_to_brand_mapping.retailer_id
            WHERE retailer_to_brand_mapping.brand_id = :brand_id
                AND r.id NOT IN (SELECT retailer_id FROM scraped_brand_product_last_week)
                {"AND r.id in :retailers" if global_filter.retailers else ""}
                {"AND r.country in :countries" if global_filter.countries else ""}
        )

        SELECT
            r.name || ' ' || r.country AS retailer,
            available_products_count,
            (
                SELECT COUNT(DISTINCT id) FROM brand_product_in_stock_last_week
            ) - available_products_count AS not_available_products_count
        FROM brand_product_count_per_retailer
            JOIN retailer r ON brand_product_count_per_retailer.retailer_id = r.id
            JOIN retailer_to_brand_mapping rtbm on r.id = rtbm.retailer_id
        WHERE NOT rtbm.shallow
    """

    return get_results_from_statement_with_filters(
        db, brand_id, global_filter, statement
    )
