from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.crud import get_results_from_statement_with_filters, convert_rows_to_dicts
from app.schemas.filters import GlobalFilter


def get_overview_stats(db: Session, brand_id: str, global_filter: GlobalFilter):
    query = f"""
        SELECT 
            (
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
            ) AS products_count,
            COUNT(DISTINCT retailer_id) AS retailers_count,
            COUNT(DISTINCT country) AS markets_count,
            COUNT(id) AS matches_count
        FROM retailer_product_including_unavailable_matview
        WHERE brand_id = :brand_id
            AND available_at_retailer = TRUE
            {"AND country IN :countries" if global_filter.countries else ""}
            {"AND retailer_id IN :retailers" if global_filter.retailers else ""}
            {"AND brand_category_id IN :categories" if global_filter.categories else ""}
            {
                "AND matched_brand_product_id IN (SELECT product_id FROM product_group_assignation WHERE product_group_id IN :groups)"
                if global_filter.groups
                else ""
            };
    """

    return get_results_from_statement_with_filters(db, brand_id, global_filter, query)[
        0
    ]


def get_currencies(db: Session) -> List[str]:
    return [
        "EUR",
        "SEK",
        "DKK",
        "NOK",
        "GBP",
        "CHF",
        "USD",
        "CAD",
        "AUD",
        "JPY",
        "CNY",
        "HKD",
    ]


def get_default_currency(db: Session, brand_id: str) -> str:
    query = """
        SELECT default_currency
        FROM brand
        WHERE id = :brand_id;
    """

    result = db.execute(text(query), {"brand_id": brand_id})
    return result.first()[0]
