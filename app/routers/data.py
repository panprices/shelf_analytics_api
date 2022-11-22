import datetime
import io
from datetime import timedelta
from functools import reduce
from typing import Dict, List, Optional

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
from app.schemas.prices import HistoricalPriceResponse, RetailerPriceHistoricalItem
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


def _add_extra_date_value_to_historical_prices(
    historical_value: List[RetailerPriceHistoricalItem],
    date: datetime.date,
    value: Optional[float],
) -> List[RetailerPriceHistoricalItem]:
    if not date:
        return historical_value
    return [*historical_value, {"x": date, "y": value}]


def _append_to_history(
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

    result[retailer_key]["data"].append(
        {"x": history_item.time_as_week, "y": history_item.price_standard}
    )

    return result


def _extract_min_for_date(
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

    minimal_values = [
        RetailerPriceHistoricalItem(**v)
        for v in reduce(_extract_min_for_date, history, {}).values()
    ]

    # Add an extra date to show the step if a change in price occurred on the last date we have data on
    extra_date = minimal_values[-1].x + timedelta(days=1) if minimal_values else None

    minimal_values = (
        _add_extra_date_value_to_historical_prices(
            minimal_values, extra_date, minimal_values[-1].y
        )
        if minimal_values
        else []
    )
    retailers = [
        {
            **v,
            "data": _add_extra_date_value_to_historical_prices(
                v["data"], extra_date, None
            ),
        }
        for v in reduce(_append_to_history, history, {}).values()
    ]

    max_value = (
        max([i.price_standard for i in history if i.price_standard is not None])
        if history
        else 0
    )

    return {
        "retailers": retailers,
        "max_value": max_value,
        "minimal_values": minimal_values,
    }
