from datetime import datetime
from typing import List, Dict, Optional, TypeVar, Callable

from sqlalchemy import text
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session

from app.models import RetailerProductHistory
from app.schemas.filters import GlobalFilter
from app.schemas.prices import RetailerHistoricalItem


def convert_rows_to_dicts(rows: List[Row]) -> List[Dict]:
    # As suggested here: https://stackoverflow.com/a/72126705/6760346
    return [dict(r._mapping) for r in rows]


def get_results_from_statement_with_filters(
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
            "groups": tuple(global_filter.groups),
        },
    ).all()

    return convert_rows_to_dicts(result)


def add_extra_date_value_to_historical_prices(
    historical_value: List[RetailerHistoricalItem],
    date: datetime.date,
    value: Optional[float],
) -> List[RetailerHistoricalItem]:
    if not date:
        return historical_value
    return [*historical_value, {"x": date, "y": value}]


T = TypeVar("T")


def create_append_to_history_reducer(
    retailer_extractor: Callable[[T], str],
    time_extractor: Callable[[T], datetime.date],
    value_extractor: Callable[[T], any],
):
    def append_to_history(result: Dict[str, Dict[str, any]], history_item: T):
        retailer_key = retailer_extractor(history_item)
        result[retailer_key] = result.get(
            retailer_key,
            {
                "id": retailer_key,
                "data": [],
            },
        )

        result[retailer_key]["data"].append(
            {"x": time_extractor(history_item), "y": value_extractor(history_item)}
        )

        return result

    return append_to_history


def extract_min_for_date(
    result: Dict[str, Dict[str, any]], history_item: RetailerProductHistory
):
    history_date = history_item.time_as_week
    result[history_date] = result.get(
        history_date, {"x": history_date, "y": history_item.price_standard}
    )

    if not history_item.price_standard:
        return result

    if (
        not result[history_date]["y"]
        or result[history_date]["y"] > history_item.price_standard
    ):
        result[history_date]["y"] = history_item.price_standard

    return result
