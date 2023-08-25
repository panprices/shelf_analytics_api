from sqlalchemy.orm import Session

from app.crud import get_results_from_statement_with_filters
from app.schemas.filters import GlobalFilter


def get_overview_stats(db: Session, brand_id: str, global_filter: GlobalFilter):
    query = f"""
        WITH matches AS (
            SELECT rp.id, rp.retailer_id, r.country
            FROM retailer_product rp
                JOIN retailer r ON r.id = rp.retailer_id
                JOIN product_matching pm ON rp.id = pm.retailer_product_id
                JOIN brand_product bp ON bp.id = pm.brand_product_id
                JOIN retailer_to_brand_mapping rtbm USING (retailer_id, brand_id)
            WHERE bp.brand_id = :brand_id
                AND bp.active = TRUE
                AND (
                    (rp.fetched_at >= date_trunc('day', now() - '1 day'::interval) AND rtbm.shallow = TRUE)
                    OR 
                    (rp.fetched_at >= date_trunc('week', now() - '1 week'::interval) AND rtbm.shallow = FALSE)
                )
                {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                {
                    "AND bp.id IN (SELECT product_id FROM product_group_assignation WHERE product_group_id IN :groups)"
                    if global_filter.groups
                    else ""
                }
                {"AND r.country IN :countries" if global_filter.countries else ""}
                {"AND r.id IN :retailers" if global_filter.retailers else ""}
        )
        SELECT (
            SELECT COUNT(id)
            FROM brand_product bp
            WHERE bp.brand_id = :brand_id
                AND bp.active = TRUE
                {"AND bp.category_id IN :categories" if global_filter.categories else ""}
                {
                    "AND bp.id IN (SELECT product_id FROM product_group_assignation WHERE product_group_id IN :groups)" 
                    if global_filter.groups
                    else ""
                }
        ) as products_count,
        (
            SELECT COUNT(DISTINCT retailer_id)
            FROM matches
        ) as retailers_count,
        (
            SELECT COUNT(DISTINCT country)
            FROM matches
        ) as markets_count,
        (
            SELECT COUNT(DISTINCT id)
            FROM matches
        ) as matches_count
    """

    return get_results_from_statement_with_filters(db, brand_id, global_filter, query)[
        0
    ]
