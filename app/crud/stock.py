from typing import List, Dict, Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.crud import convert_rows_to_dicts, get_results_from_statement_with_filters
from app.schemas.filters import GlobalFilter


def get_historical_in_stock(
    db: Session,
    brand_id: str,
    global_filter: GlobalFilter,
) -> List[Dict[str, Any]]:
    statement = f"""
        WITH product_matching_time_series as (
            SELECT DISTINCT product_matching_id,
                            brand_product_id,
                            retailer_product_id,
                            image_score,
                            text_score,
                            date_trunc('week', time) as time
            FROM product_matching_time_series
        ), brand_product_time_series as (
            SELECT DISTINCT product_id, availability, date_trunc('week', time) as time
            FROM brand_product_time_series
        ), retailer_product_time_series as (
            SELECT DISTINCT product_id, availability, date_trunc('week', time) as time
            FROM retailer_product_time_series
        )
        SELECT date_trunc('week', pmts.time)::date as time, 
            100 * SUM(CASE WHEN rpts.availability = 'out_of_stock' THEN 0 ELSE 1.0 END) / COUNT(*) as score
        FROM brand_product bp 
            JOIN product_matching_time_series pmts ON pmts.brand_product_id = bp.id
            JOIN retailer_product rp ON rp.id = pmts.retailer_product_id
            JOIN retailer r ON r.id = rp.retailer_id
            JOIN brand_product_time_series bpts ON bpts.product_id = bp.id AND bpts.time = pmts.time
            JOIN retailer_product_time_series rpts ON rpts.product_id = rp.id AND rpts.time = pmts.time
            {"LEFT JOIN product_group_assignation pga ON pga.product_id = bp.id" if global_filter.groups else ""}
        where bp.brand_id = :brand_id 
            AND pmts.time < date_trunc('week', now())::date
            AND bpts.availability = 'in_stock'
            {"AND bp.category_id IN :categories" if global_filter.categories else ""}
            {"AND r.id in :retailers" if global_filter.retailers else ""}
            {"AND r.country in :countries" if global_filter.countries else ""}
            {"AND pga.product_group_id in :groups" if global_filter.groups else ""}
        group by date_trunc('week', pmts.time)::date
        order by time asc
    """

    return get_results_from_statement_with_filters(
        db, brand_id, global_filter, statement
    )
