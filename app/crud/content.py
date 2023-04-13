from sqlalchemy import text
from sqlalchemy.orm import Session

from app.crud import convert_rows_to_dicts, get_results_from_statement_with_filters
from app.schemas.filters import GlobalFilter


def _get_scores_root_query(global_filter: GlobalFilter):
    return f"""
        FROM brand_product bp 
            JOIN product_matching pm ON bp.id = pm.brand_product_id 
            JOIN product_matching_time_series pmts ON pm.id = pmts.product_matching_id
            JOIN retailer_product rp ON rp.id = pm.retailer_product_id
            JOIN retailer r ON r.id = rp.retailer_id
            LEFT JOIN product_group_assignation pga ON pga.product_id = bp.id
            JOIN retailer_to_brand_mapping rtbm ON rtbm.retailer_id = r.id AND rtbm.brand_id = bp.brand_id
        where bp.brand_id = :brand_id 
            AND NOT rtbm.shallow
            AND pmts.time < date_trunc('week', now())::date
            AND pmts.image_score IS NOT NULL
            AND pmts.text_score IS NOT NULL
            AND pm.certainty NOT IN ('auto_low_confidence', 'not_match')
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
                SELECT date_trunc('week', pmts.time)::date as time, 
                    {score_field} as score
                {_get_scores_root_query(global_filter)}
                group by date_trunc('week', pmts.time)::date
                order by time asc
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
           SELECT r.name || ' ' || r.country as retailer, date_trunc('week', pmts.time)::date as time, 
               {score_field} as score
           {_get_scores_root_query(global_filter)}
           group by r.id, date_trunc('week', pmts.time)::date
           order by time asc, r.id
       """,
    )


def get_historical_image_score(db: Session, brand_id: str, global_filter: GlobalFilter):
    return _get_historical_score(db, brand_id, global_filter, "AVG(pmts.image_score)")


def get_historical_image_score_per_retailer(
    db: Session, brand_id: str, global_filter: GlobalFilter
):
    return _get_historical_score_per_retailer(
        db, brand_id, global_filter, "AVG(pmts.image_score)"
    )


def get_historical_text_score(db: Session, brand_id: str, global_filter: GlobalFilter):
    return _get_historical_score(db, brand_id, global_filter, "AVG(pmts.text_score)")


def get_historical_text_score_per_retailer(
    db: Session, brand_id: str, global_filter: GlobalFilter
):
    return _get_historical_score_per_retailer(
        db, brand_id, global_filter, "AVG(pmts.text_score)"
    )


def get_historical_content_score(
    db: Session, brand_id: str, global_filter: GlobalFilter
):
    return _get_historical_score(
        db,
        brand_id,
        global_filter,
        "(AVG(pmts.image_score) + AVG(pmts.text_score)) / 2",
    )


def get_current_score_per_retailer(
    db: Session, brand_id: str, global_filter: GlobalFilter
):
    statement = f"""
        SELECT r.name || ' ' || r.country as retailer,
            (AVG(COALESCE(pm.image_score, 0)) + AVG(COALESCE(pm.text_score, 0))) / 2 as score
        FROM brand_product bp
            JOIN product_matching pm ON bp.id = pm.brand_product_id
            JOIN retailer_product rp ON rp.id = pm.retailer_product_id
            JOIN retailer r ON r.id = rp.retailer_id
            LEFT JOIN product_group_assignation pga ON pga.product_id = bp.id
            JOIN retailer_to_brand_mapping rtbm ON rtbm.retailer_id = r.id AND rtbm.brand_id = bp.brand_id
        where bp.brand_id = :brand_id
            AND NOT rtbm.shallow
            AND pm.certainty NOT IN ('auto_low_confidence', 'not_match')
            {"AND bp.category_id IN :categories" if global_filter.categories else ""}
            {"AND r.id in :retailers" if global_filter.retailers else ""}
            {"AND r.country in :countries" if global_filter.countries else ""}
            {"AND pga.product_group_id in :groups" if global_filter.groups else ""}
        group by r.name, r.country
        order by score desc
    """
    return get_results_from_statement_with_filters(
        db, brand_id, global_filter, statement
    )
