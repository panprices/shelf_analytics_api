import io
from datetime import timedelta
from functools import reduce
from typing import Dict, List

import pandas
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import StreamingResponse

from app import crud
from app.database import get_db
from app.models import RetailerProductHistory, RetailerProduct
from app.schemas.auth import TokenData
from app.schemas.filters import PagedGlobalFilter, GlobalFilter
from app.schemas.prices import HistoricalPriceResponse
from app.schemas.product import (
    ProductPage,
    RetailerProductScaffold,
    BrandProductScaffold,
    BrandProductMatchesScaffold,
)
from app.security import get_user_data
from app.tags import TAG_DATA

router = APIRouter(prefix="/products")


def _preprocess_products(
    db: Session,
    products: List[RetailerProduct],
) -> List[RetailerProductScaffold]:
    products = [RetailerProductScaffold.from_orm(p) for p in products]

    unmatched_products = [rp for rp in products if not rp.matched_brand_products]
    brand_products_gtins = [rp.gtin for rp in unmatched_products]

    if unmatched_products:
        brand_products = crud.get_brand_products_for_gtins(db, brand_products_gtins)

        for p in unmatched_products:
            p.url = None
            p.matched_brand_products = [
                {"brand_product": bp} for bp in brand_products if bp.gtin == p.gtin
            ]
    return products


@router.post("", tags=[TAG_DATA], response_model=ProductPage)
def get_products(
    page_global_filter: PagedGlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    products = crud.get_products(db, user.client, page_global_filter)
    products = _preprocess_products(db, products)

    return {
        "products": products,
        "count": len(products),
        "offset": page_global_filter.get_products_offset(),
        "total_count": crud.count_products(db, user.client, page_global_filter),
    }


@router.post("/export", tags=[TAG_DATA])
async def export_products_to_csv(
    page_global_filter: PagedGlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    products = crud.export_full_brand_products_result(
        db, user.client, page_global_filter
    )
    products = [RetailerProductScaffold.from_orm(p) for p in products]

    products_df = pandas.DataFrame([p.dict() for p in products])
    response = StreamingResponse(io.StringIO(products_df.to_csv(index=False)))
    response.headers["Content-Disposition"] = "attachment; filename=export.csv"
    return response


@router.get(
    "/brand/{brand_product_id}", tags=[TAG_DATA], response_model=BrandProductScaffold
)
def get_brand_product_details(
    brand_product_id: str,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Must be authenticated"
        )

    return crud.get_brand_product_detailed_for_id(db, brand_product_id)


@router.post(
    "/brand/{brand_product_id}/matches",
    tags=[TAG_DATA],
    response_model=BrandProductMatchesScaffold,
)
def get_matched_retailer_products_for_brand_product(
    brand_product_id: str,
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Must be authenticated"
        )

    return {
        "matches": crud.get_retailer_products_for_brand_product(
            db, global_filter, brand_product_id
        )
    }


@router.post(
    "/brand/{brand_product_id}/prices",
    tags=[TAG_DATA],
    response_model=HistoricalPriceResponse,
)
def get_historical_prices_for_brand_product(
    brand_product_id: str,
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Must be authenticated"
        )

    history = crud.get_historical_prices_by_retailer_for_brand_product(
        db, global_filter, brand_product_id
    )

    # Keep a list of the sorted dates to insert None when values are missing
    sorted_dates = sorted(list(set([h.time_as_week for h in history])))
    beginning_of_time = sorted_dates[0] - timedelta(days=7) if sorted_dates else None
    sorted_dates.insert(0, beginning_of_time)

    def append_to_history(
        result: Dict[str, Dict[str, any]], history_item: RetailerProductHistory
    ):
        retailer_key = f"{history_item.product.retailer.name} - {history_item.product.retailer.country}"
        result[retailer_key] = result.get(
            retailer_key,
            {
                "id": retailer_key,
                "data": [],
            },
        )

        # Check if we skipped any date (relies on the fact that the data coming from postgres is sorted by date
        # If we skipped some dates, we add them with `None` values to display gaps in the price chart
        current_date_index = sorted_dates.index(history_item.time_as_week)
        last_known_date = (
            result[retailer_key]["data"][-1]["x"]
            if result[retailer_key]["data"]
            else beginning_of_time
        )
        last_known_date_index = sorted_dates.index(last_known_date)

        if current_date_index - last_known_date_index > 1:
            for i in range(last_known_date_index + 1, current_date_index):
                result[retailer_key]["data"].append({"x": sorted_dates[i], "y": None})

        result[retailer_key]["data"].append(
            {"x": history_item.time_as_week, "y": history_item.price_standard}
        )

        return result

    def extract_min_for_date(
        result: Dict[str, Dict[str, any]], history_item: RetailerProductHistory
    ):
        history_date = history_item.time_as_week
        result[history_date] = result.get(
            history_date, {"x": history_date, "y": history_item.price_standard}
        )

        if result[history_date]["y"] > history_item.price_standard:
            result[history_date]["y"] = history_item.price_standard

        return result

    max_value = max([i.price_standard for i in history]) if history else 0
    retailers = [v for v in reduce(append_to_history, history, {}).values()]
    minimal_values = [v for v in reduce(extract_min_for_date, history, {}).values()]
    minimal_values = (
        [
            *minimal_values,
            {
                "x": minimal_values[-1]["x"] + timedelta(days=1),
                "y": minimal_values[-1]["y"],
            },
        ]
        if minimal_values
        else []
    )

    return {
        "retailers": retailers,
        "max_value": max_value,
        "minimal_values": minimal_values,
    }
