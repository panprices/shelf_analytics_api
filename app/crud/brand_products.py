from sqlalchemy.orm import Session

from app.crud import get_result_entities_from_statement_with_paged_filters
from app.models import MockBrandProductGridItem
from app.schemas.filters import PagedGlobalFilter


def _get_full_product_list(
    db: Session, brand_id: str, statement: str, global_filter: PagedGlobalFilter
):
    return get_result_entities_from_statement_with_paged_filters(
        db,
        MockBrandProductGridItem,
        brand_id,
        global_filter,
        statement,
    )


def get_brand_products_data_grid(
    db: Session, brand_id: str, global_filter: PagedGlobalFilter
):
    """
    Get brand products data grid

    :param db:
    :param brand_id:
    :param global_filter:
    :return:
    """

    statement = """
        WITH retailers_count_for_client AS (
            SELECT COUNT(*)
            FROM retailer_to_brand_mapping
            WHERE brand_id = :brand_id
        )
        SELECT bp.id, bp.name, bp.description, bp.sku, bp.gtin, 
            COALESCE(bp.availability = 'in_stock', TRUE) as brand_in_stock, -- Assume in stock if not specified
            COUNT(DISTINCT r.id) as retailers_count,
            COUNT(DISTINCT r.country) as markets_count,
            COUNT(DISTINCT r.id) / (SELECT * FROM retailers_count_for_client LIMIT 1) as retailer_coverage_rate
        FROM brand_product bp
            LEFT JOIN product_matching pm ON pm.brand_product_id = bp.id
            LEFT JOIN retailer_product rp ON rp.id = pm.retailer_product_id
            LEFT JOIN retailer r ON r.id = rp.retailer_id
        WHERE rp.fetched_at > DATE_TRUNC('week', NOW()) - INTERVAL '1 week'
            AND bp.brand_id = :brand_id
        GROUP BY bp.id, bp.name, bp.sku, bp.gtin, brand_in_stock
    """

    return _get_full_product_list(
        db,
        brand_id,
        statement,
        global_filter,
    )
