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
        SELECT time as time, 
            100 * SUM(CASE WHEN availability = 'out_of_stock' THEN 0 ELSE 1.0 END) / COUNT(*) as score
        FROM product_stock_time_series pmts
            {"LEFT JOIN product_group_assignation pga ON pga.product_id = pmts.id" if global_filter.groups else ""}
            JOIN retailer_to_brand_mapping rtbm ON rtbm.retailer_id = pmts.retailer_id AND rtbm.brand_id = pmts.brand_id
        WHERE pmts.brand_id = :brand_id 
            AND time >= :start_date
            AND NOT rtbm.shallow
            {"AND category_id IN :categories" if global_filter.categories else ""}
            {"AND rtbm.retailer_id in :retailers" if global_filter.retailers else ""}
            {"AND country in :countries" if global_filter.countries else ""}
            {"AND pga.product_group_id in :groups" if global_filter.groups else ""}
        group by time
        order by time asc
    """

    return get_results_from_statement_with_filters(
        db, brand_id, global_filter, statement
    )
