from sqlalchemy.orm import Session

from app.crud import get_result_entities_from_statement_with_paged_filters
from app.models import MockBrandProductGridItem
from app.schemas.filters import PagedGlobalFilter, DataPageFilter


def _get_full_product_list(
    db: Session,
    brand_id: str,
    statement: str,
    global_filter: PagedGlobalFilter,
    ignore_pagination=False,
):
    return get_result_entities_from_statement_with_paged_filters(
        db,
        MockBrandProductGridItem,
        brand_id,
        global_filter,
        statement,
        ignore_pagination,
    )


def _create_query_for_retailer_offers_datapool(global_filter: DataPageFilter) -> str:
    well_defined_grid_filters = [
        i for i in global_filter.data_grid_filter.items if i.is_well_defined()
    ]

    return f"""
            WITH retailers_count_for_client AS (
                SELECT COUNT(*)
                FROM retailer_to_brand_mapping
                    JOIN retailer ON retailer.id = retailer_to_brand_mapping.retailer_id
                WHERE brand_id = :brand_id
                    {"AND country IN :countries" if global_filter.countries else ""}
                    {"AND id IN :retailers" if global_filter.retailers else ""} 
            ), table_data AS (
                SELECT bp.id, bp.name, bp.description, bp.sku, bp.gtin, 
                    COALESCE(bp.availability = 'in_stock', TRUE) as brand_in_stock, -- Assume in stock if not specified
                    COUNT(DISTINCT r.id) FILTER (WHERE rp.fetched_at > DATE_TRUNC('week', NOW()) - INTERVAL '1 week') as retailers_count,
                    COUNT(DISTINCT r.country) FILTER (WHERE rp.fetched_at > DATE_TRUNC('week', NOW()) - INTERVAL '1 week') as markets_count,
                    COUNT(DISTINCT r.id) FILTER (WHERE rp.fetched_at > DATE_TRUNC('week', NOW()) - INTERVAL '1 week') 
                        / (SELECT * FROM retailers_count_for_client LIMIT 1)::float as retailer_coverage_rate
                FROM brand_product bp
                    LEFT JOIN product_matching pm ON pm.brand_product_id = bp.id
                    LEFT JOIN retailer_product rp ON rp.id = pm.retailer_product_id
                    LEFT JOIN retailer r ON r.id = rp.retailer_id
                WHERE bp.brand_id = :brand_id
                    AND bp.active = TRUE
                    {"AND category_id IN :categories" if global_filter.categories else ""}
                    {"AND retailer_id IN :retailers" if global_filter.retailers else ""}
                    {"AND country IN :countries" if global_filter.countries else ""}
                    {'''
                        AND brand_product_id IN (
                            SELECT product_id 
                            FROM product_group_assignation pga 
                            WHERE pga.product_group_id IN :groups
                        )
                    ''' if global_filter.groups else ""}    
                GROUP BY bp.id, bp.name, bp.sku, bp.gtin, brand_in_stock
            )
            SELECT * FROM table_data
            WHERE 1=1
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


def get_brand_products_data_grid(
    db: Session, brand_id: str, global_filter: PagedGlobalFilter
):
    statement = _create_query_for_retailer_offers_datapool(global_filter)

    paged_statement = f"""
        {statement}
        {
            "ORDER BY " + global_filter.sorting.column + " " + global_filter.sorting.direction
            if global_filter.sorting else "ORDER BY name ASC"
        }
        LIMIT :limit OFFSET :offset
    """

    return _get_full_product_list(
        db,
        brand_id,
        paged_statement,
        global_filter,
    )


def export_full_brand_products_result(
    db: Session, brand_id: str, global_filter: PagedGlobalFilter
):
    statement = _create_query_for_retailer_offers_datapool(global_filter)
    return _get_full_product_list(
        db,
        brand_id,
        statement=statement,
        global_filter=global_filter,
        ignore_pagination=True,
    )


def count_brand_products(
    db: Session, brand_id: str, global_filter: DataPageFilter
) -> int:
    query = _create_query_for_retailer_offers_datapool(global_filter)

    result = get_result_entities_from_statement_with_paged_filters(
        db, "count", brand_id, global_filter, query, ignore_pagination=True
    )

    return result[0][0]
