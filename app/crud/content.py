from sqlalchemy.orm import Session

from app.crud import get_results_from_statement_with_filters
from app.schemas.filters import GlobalFilter

CONTENT_SCORE_FIELD = """
    CASE
        WHEN AVG(text_score) IS NULL
            THEN COALESCE(AVG(image_score), 0)
        ELSE COALESCE(AVG(image_score) + AVG(text_score)) / 2
    END
"""

TEXT_SCORE_FIELD = "COALESCE(AVG(text_score), 0)"
IMAGE_SCORE_FIELD = "COALESCE(AVG(image_score), 0)"


def _get_scores_root_query(global_filter: GlobalFilter):
    return f"""
        SELECT pmts.time as time, pmts.image_score, pmts.text_score, pmts.specs_score,
            r.name || ' ' || r.country as retailer
        FROM brand_product bp 
            JOIN product_matching pm ON bp.id = pm.brand_product_id 
            JOIN product_matching_time_series pmts ON pm.id = pmts.product_matching_id
            JOIN retailer_product rp ON rp.id = pm.retailer_product_id
            JOIN retailer r ON r.id = rp.retailer_id
            JOIN retailer_to_brand_mapping rtbm ON rtbm.retailer_id = r.id AND rtbm.brand_id = bp.brand_id
            {"LEFT JOIN product_group_assignation pga ON pga.product_id = bp.id" if global_filter.groups else ""}
        where bp.brand_id = :brand_id
            AND pmts.time < date_trunc('week', now())::date
            AND pm.certainty NOT IN ('auto_low_confidence', 'not_match')
            AND NOT rtbm.shallow
            {"AND bp.category_id IN :categories" if global_filter.categories else ""}
            {"AND r.id in :retailers" if global_filter.retailers else ""}
            {"AND r.country in :countries" if global_filter.countries else ""}
            {"AND pga.product_group_id in :groups" if global_filter.groups else ""}
    """


def _get_historical_score(
    db: Session, brand_id: str, global_filter: GlobalFilter, score_field: str
):
    return get_results_from_statement_with_filters(
        db,
        brand_id,
        global_filter,
        f"""
            SELECT 
                time, 
                {score_field} as score
            FROM retailer_product_per_week_matview
            WHERE brand_id = :brand_id
                AND time < date_trunc('week', now())
                {"AND brand_category_id IN :categories" if global_filter.categories else ""}
                {"AND retailer_id in :retailers" if global_filter.retailers else ""}
                {"AND retailer_country in :countries" if global_filter.countries else ""}
                {'''AND brand_product_id IN 
                    (SELECT product_id FROM product_group_assignation pga WHERE pga.product_group_id IN :groups)''' 
                    if global_filter.groups else ""
                }
            GROUP BY time
            ORDER BY time ASC
        """,
    )


def _get_historical_score_per_retailer(
    db: Session, brand_id: str, global_filter: GlobalFilter, score_field: str
):
    return get_results_from_statement_with_filters(
        db,
        brand_id,
        global_filter,
        f"""
            SELECT 
                retailer_name || ' ' || retailer_country as retailer,
                time, 
                {score_field} as score
            FROM retailer_product_per_week_matview
            WHERE brand_id = :brand_id
                AND time < date_trunc('week', now())
                {"AND brand_category_id IN :categories" if global_filter.categories else ""}
                {"AND retailer_id in :retailers" if global_filter.retailers else ""}
                {"AND retailer_country in :countries" if global_filter.countries else ""}
                {'''AND brand_product_id IN 
                    (SELECT product_id FROM product_group_assignation pga WHERE pga.product_group_id IN :groups)''' 
                    if global_filter.groups else ""
                }
            GROUP BY time, retailer
            ORDER BY time ASC, retailer ASC
       """,
    )


def get_historical_image_score(db: Session, brand_id: str, global_filter: GlobalFilter):
    return _get_historical_score(
        db,
        brand_id,
        global_filter,
        IMAGE_SCORE_FIELD,
    )


def get_historical_image_score_per_retailer(
    db: Session, brand_id: str, global_filter: GlobalFilter
):
    return _get_historical_score_per_retailer(
        db,
        brand_id,
        global_filter,
        IMAGE_SCORE_FIELD,
    )


def get_historical_text_score(db: Session, brand_id: str, global_filter: GlobalFilter):
    return _get_historical_score(
        db,
        brand_id,
        global_filter,
        TEXT_SCORE_FIELD,
    )


def get_historical_text_score_per_retailer(
    db: Session, brand_id: str, global_filter: GlobalFilter
):
    return _get_historical_score_per_retailer(
        db,
        brand_id,
        global_filter,
        TEXT_SCORE_FIELD,
    )


def get_historical_content_score(
    db: Session, brand_id: str, global_filter: GlobalFilter
):
    return _get_historical_score(
        db,
        brand_id,
        global_filter,
        CONTENT_SCORE_FIELD,
    )


def get_historical_content_score_per_retailer(
    db: Session, brand_id: str, global_filter: GlobalFilter
):
    return _get_historical_score_per_retailer(
        db,
        brand_id,
        global_filter,
        CONTENT_SCORE_FIELD,
    )
