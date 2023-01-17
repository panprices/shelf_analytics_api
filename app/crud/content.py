from sqlalchemy import text
from sqlalchemy.orm import Session

from app.crud import convert_rows_to_dicts
from app.schemas.filters import GlobalFilter


def _get_scores_root_query(global_filter: GlobalFilter):
    return f"""
        FROM brand_product bp 
            JOIN product_matching pm ON bp.id = pm.brand_product_id 
            JOIN product_matching_time_series pmts ON pm.id = pmts.product_matching_id
            JOIN retailer_product rp ON rp.id = pm.retailer_product_id
            JOIN retailer r ON r.id = rp.retailer_id
        where bp.brand_id = :brand_id 
            AND pmts.time < date_trunc('week', now())::date
            AND pmts.image_score IS NOT NULL
            AND pmts.text_score IS NOT NULL
            AND pm.certainty NOT IN ('auto_low_confidence', 'not_match')
            {"AND bp.category_id IN :categories" if global_filter.categories else ""}
            {"AND r.id in :retailers" if global_filter.retailers else ""}
            {"AND r.country in :countries" if global_filter.countries else ""}
    """


def _get_historical_results(
    db: Session, brand_id: str, global_filter: GlobalFilter, statement: str
):
    result = db.execute(
        text(statement),
        params={
            "brand_id": brand_id,
            "start_date": global_filter.start_date,
            "countries": tuple(global_filter.countries),
            "retailers": tuple(global_filter.retailers),
            "categories": tuple(global_filter.categories),
        },
    ).all()

    return convert_rows_to_dicts(result)


def _get_historical_score(
    db: Session, brand_id: str, global_filter: GlobalFilter, score_field: str
):
    return _get_historical_results(
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
    return _get_historical_results(
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
            (AVG(pm.image_score) + AVG(pm.text_score)) / 2 as score
        FROM brand_product bp
            JOIN product_matching pm ON bp.id = pm.brand_product_id
            JOIN retailer_product rp ON rp.id = pm.retailer_product_id
            JOIN retailer r ON r.id = rp.retailer_id
        where bp.brand_id = :brand_id
            AND pm.certainty NOT IN ('auto_low_confidence', 'not_match')
            {"AND bp.category_id IN :categories" if global_filter.categories else ""}
            {"AND r.id in :retailers" if global_filter.retailers else ""}
            {"AND r.country in :countries" if global_filter.countries else ""}
        group by r.name, r.country
        order by score desc
    """

    result = db.execute(
        text(statement),
        params={
            "brand_id": brand_id,
            "countries": tuple(global_filter.countries),
            "retailers": tuple(global_filter.retailers),
            "categories": tuple(global_filter.categories),
        },
    ).all()

    return convert_rows_to_dicts(result)