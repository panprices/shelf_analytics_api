from datetime import datetime, timedelta
from functools import reduce
from typing import List, Dict, Optional, TypeVar, Callable

from sqlalchemy import text
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session

from app.schemas.filters import GlobalFilter
from app.schemas.prices import RetailerHistoricalItem


def convert_rows_to_dicts(rows: List[Row]) -> List[Dict]:
    # As suggested here: https://stackoverflow.com/a/72126705/6760346
    return [dict(r._mapping) for r in rows]


def get_results_from_statement_with_filters(
    db: Session,
    brand_id: str,
    global_filter: GlobalFilter,
    statement: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
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
            "limit": limit,
            "offset": offset,
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
    return [*historical_value, RetailerHistoricalItem(x=date, y=value)]


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


def extract_minimal_values(retailers: List[Dict[str, any]]):
    """
    Extract the minimal values for the area shown on the individual product price chart

    The idea of the algorithm is to iterate over all the dates available for all the retailers. For each date,
    we take into account the value at the respective data, plus all the date prior to that if no null value was
    encountered.

    This is meant to work similarly to nivo. A missing date means that the lines continues without any point at that
    date, but an existing date with a null value signifies an interruption of the line.

    :param retailers:
    :return:
    """
    indexes_for_retailers = [0] * len(retailers)
    minimal_values = []

    next_max_date = min([r["data"][0]["x"] for r in retailers])
    while not all(
        [i == len(r["data"]) - 1 for i, r in zip(indexes_for_retailers, retailers)]
    ):
        next_value_by_retailer = [
            r["data"][indexes_for_retailers[i]]["y"]
            for i, r in enumerate(retailers)
            if (
                indexes_for_retailers[i] < len(r["data"])
                and r["data"][indexes_for_retailers[i]]["x"] <= next_max_date
                and r["data"][indexes_for_retailers[i]]["y"] is not None
            )
        ]

        # If no value is found for any of the retailers it means we have a gap in the data
        # for all the retailers at that date. To keep the continuity of the area under the curve
        # with minimal prices, we duplicate the last datapoint and continue iterating
        min_value = (
            min(next_value_by_retailer)
            if next_value_by_retailer
            else minimal_values[-1]["y"]
        )

        # Update min if different than the previous, we are only interested in steps
        if (
            not minimal_values
            or minimal_values[len(minimal_values) - 1]["y"] != min_value
        ):
            minimal_values.append(
                {
                    "x": next_max_date,
                    "y": min_value,
                }
            )

        next_max_date = min(
            [
                r["data"][indexes_for_retailers[i] + 1]["x"]
                for i, r in enumerate(retailers)
                if indexes_for_retailers[i] + 1 < len(r["data"])
            ]
        )

        # Increase indexes for retailers that do not go over next max date
        for i, r in enumerate(retailers):
            if (
                indexes_for_retailers[i] + 1 < len(r["data"])
                and r["data"][indexes_for_retailers[i] + 1]["x"] == next_max_date
            ):
                indexes_for_retailers[i] += 1

    # Add last date with the last known value
    minimal_values.append(
        {
            "x": next_max_date,
            "y": minimal_values[len(minimal_values) - 1]["y"],
        }
    )

    return minimal_values


def process_historical_value_per_retailer(
    history, value_label: str = "score", force_two_points: bool = True
):
    """
    Process the historical value per retailer

    :param history:
    :param value_label:
    :param force_two_points: if we only have one data point, we add a second one with the same value but a week before
    to make sure the line is visible
    :return:
    """
    retailers = [
        v
        for v in reduce(
            create_append_to_history_reducer(
                lambda history_item: history_item["retailer"],
                lambda history_item: history_item["time"],
                lambda history_item: history_item[value_label],
            ),
            history,
            {},
        ).values()
    ]

    if force_two_points:
        for retailer in retailers:
            if len(retailer["data"]) == 1:
                retailer["data"].insert(
                    0,
                    {
                        **retailer["data"][0],
                        "x": retailer["data"][0]["x"] - timedelta(days=7),
                    },
                )

    max_value = (
        max([i[value_label] for i in history if i[value_label] is not None])
        if history
        else 0
    )
    min_value = (
        min([i[value_label] for i in history if i[value_label] is not None])
        if history
        else 0
    )

    return {"retailers": retailers, "max_value": max_value, "min_value": min_value}
