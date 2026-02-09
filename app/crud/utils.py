import io
from datetime import datetime, timedelta
from functools import reduce
from typing import List, Dict, Optional, TypeVar, Callable, Type, Literal, Union
from cachetools import cached, TTLCache

import pandas
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.schemas.filters import GlobalFilter, PagedGlobalFilter, DataPageFilter
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
    extra_params: Optional[Dict] = None,
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
            **(extra_params or {}),
        },
    ).all()

    return convert_rows_to_dicts(result)


def get_result_entities_from_statement_with_paged_filters(
    db: Session,
    entity: Union[Type[BaseModel], Literal["count"]],
    brand_id: str,
    global_filter: Union[PagedGlobalFilter, DataPageFilter],
    statement: str,
    ignore_pagination: bool = False,
):
    params_dict = {
        "brand_id": brand_id,
        "start_date": global_filter.start_date,
        "countries": tuple(global_filter.countries),
        "retailers": tuple(global_filter.retailers),
        "categories": tuple(global_filter.categories),
        "groups": tuple(global_filter.groups),
        "offset": global_filter.get_products_offset() if not ignore_pagination else 0,
        "limit": global_filter.page_size if not ignore_pagination else None,
        "search_text": f"%{global_filter.search_text}%",
        **{
            f"fv_{index}": i.get_safe_postgres_value()
            for index, i in enumerate(global_filter.data_grid_filter.items)
            if i.is_well_defined()
        },
    }

    if entity == "count":
        statement = f"""
            SELECT COUNT(*)
            FROM (
                {statement}
            ) aux
        """
        query = db.execute(text(statement), params=params_dict)
    else:
        query = (
            db.query(entity)
            .from_statement(text(statement))
            .params(
                **params_dict,
            )
        )

    return query.all()


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
) -> dict:
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


def duplicate_unique_points(grouped_history: dict) -> dict:
    for r in grouped_history["retailers"]:
        if len(r["data"]) == 1:
            r["data"].insert(
                0, {**r["data"][0], "x": r["data"][0]["x"] - timedelta(days=7)}
            )

    return grouped_history


def export_dataframe_to_xlsx(df: pandas.DataFrame):
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="xlsxwriter")

    return Response(buffer.getvalue())


def export_rows_to_xlsx(products: List[BaseModel]):
    products_df = pandas.DataFrame([p.dict() for p in products])
    return export_dataframe_to_xlsx(products_df)

@cached(cache=TTLCache(maxsize=512, ttl=3600)) # Cache for 1 hour
def get_currency_exchange_rates(
        db: Session,
        user_currency: str,
    ):
    statement = text("""
        SELECT
            name,
            CASE
                WHEN name = :user_currency THEN 1
                ELSE (
                    SELECT to_eur
                    FROM currency
                    WHERE name = :user_currency
                    LIMIT 1
                ) / to_eur
            END AS conversion_rate
        FROM currency;
    """)
    # Execute the query with the parameter
    result = db.execute(statement, {'user_currency': user_currency})
    # Convert rows to a flat dictionary like this {'USD': 1.2, 'EUR': 0.8...}
    result_as_dict = {row['name']: row['conversion_rate'] for row in result}
    return result_as_dict
