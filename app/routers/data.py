import io
from datetime import timedelta
from functools import reduce

import pandas
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import StreamingResponse

from app import crud
from app.crud.utils import (
    add_extra_date_value_to_historical_prices,
    extract_min_for_date,
    create_append_to_history_reducer,
)
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.filters import PagedGlobalFilter, GlobalFilter, DataPageFilter
from app.schemas.prices import HistoricalPerRetailerResponse, RetailerHistoricalItem
from app.schemas.product import (
    ProductPage,
    BrandProductScaffold,
    BrandProductMatchesScaffold,
    MockRetailerProductGridItem,
)
from app.security import get_user_data
from app.tags import TAG_DATA

router = APIRouter(prefix="/products")


@router.post("", tags=[TAG_DATA], response_model=ProductPage)
def get_products(
    page_global_filter: PagedGlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    products = crud.get_products(db, user.client, page_global_filter)

    return {
        "rows": products,
        "count": len(products),
        "offset": page_global_filter.get_products_offset(),
        "total_count": crud.count_products(db, user.client, page_global_filter),
    }


@router.post("/brand/count", tags=[TAG_DATA], response_model=int)
def get_brand_products_count(
    paged_global_filter: DataPageFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    return crud.count_brand_products(db, user.client, paged_global_filter)


@router.post("/export", tags=[TAG_DATA])
async def export_products_to_csv(
    page_global_filter: PagedGlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    products = crud.export_full_brand_products_result(
        db, user.client, page_global_filter
    )
    products = [MockRetailerProductGridItem.from_orm(p) for p in products]
    products_df = pandas.DataFrame([p.dict() for p in products])

    buffer = io.BytesIO()
    products_df.to_excel(buffer, index=False, engine="xlsxwriter")

    return Response(buffer.getvalue())


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

    result = crud.get_brand_product_detailed_for_id(db, brand_product_id)
    return result


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

    matches = crud.get_retailer_products_for_brand_product(
        db, global_filter, brand_product_id
    )
    return {"matches": matches}


@router.post(
    "/brand/{brand_product_id}/prices",
    tags=[TAG_DATA],
    response_model=HistoricalPerRetailerResponse,
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
        RetailerHistoricalItem(**v)
        for v in reduce(extract_min_for_date, history, {}).values()
    ]

    # Add an extra date to show the step if a change in price occurred on the last date we have data on
    extra_date = minimal_values[-1].x + timedelta(days=1) if minimal_values else None

    minimal_values = (
        add_extra_date_value_to_historical_prices(
            minimal_values, extra_date, minimal_values[-1].y
        )
        if minimal_values
        else []
    )
    retailers = [
        {
            **v,
            "data": add_extra_date_value_to_historical_prices(
                v["data"], extra_date, v["data"][-1]["y"]
            ),
        }
        for v in reduce(
            create_append_to_history_reducer(
                lambda history_item: f"{history_item.product.retailer.name} - {history_item.product.retailer.country}",
                lambda history_item: history_item.time_as_week,
                lambda history_item: history_item.price_standard,
            ),
            history,
            {},
        ).values()
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
