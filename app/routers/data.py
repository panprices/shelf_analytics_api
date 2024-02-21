import io
from functools import reduce

import pandas
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from starlette import status

from app import crud
from app.crud.utils import (
    create_append_to_history_reducer,
    extract_minimal_values,
)
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.filters import (
    PagedGlobalFilter,
    GlobalFilter,
    DataPageFilter,
    PriceValuesFilter,
)
from app.schemas.prices import HistoricalPerRetailerResponse, MSRPValueItem
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

    result = crud.get_brand_product_detailed_for_id(db, brand_product_id, user.client)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Brand product not found"
        )
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
    """
    Get all the retailer products that match the brand product

    Returns only products matched on deep indexed retailers
    :param brand_product_id:
    :param global_filter:
    :param user:
    :param db:
    :return:
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Must be authenticated"
        )

    matches = crud.get_retailer_products_for_brand_product(
        db, global_filter, brand_product_id, user.client
    )
    return {"matches": matches}


@router.post(
    "/brand/{brand_product_id}/prices",
    tags=[TAG_DATA],
    response_model=HistoricalPerRetailerResponse,
)
def get_historical_prices_for_brand_product(
    brand_product_id: str,
    global_filter: PriceValuesFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Must be authenticated"
        )

    history = crud.get_historical_prices_by_retailer_for_brand_product(
        db, global_filter, brand_product_id, user.client
    )

    retailers = [
        v
        for v in reduce(
            create_append_to_history_reducer(
                lambda history_item: f"{history_item.product.retailer.name} - {history_item.product.retailer.country}",
                lambda history_item: history_item.time_as_date,
                lambda history_item: history_item.price_standard,
            ),
            history,
            {},
        ).values()
    ]
    if not retailers:
        return {"retailers": [], "max_value": 0, "minimal_values": []}

    minimal_values = extract_minimal_values(retailers)

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


@router.post(
    "/brand/{brand_product_id}/msrp",
    tags=[TAG_DATA],
    response_model=MSRPValueItem,
)
def get_product_msrp(
    brand_product_id: str,
    global_filter: PriceValuesFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Must be authenticated"
        )

    result = crud.get_product_msrp(db, global_filter, brand_product_id)

    return (
        {
            "price_standard": result[0],
            "currency": result[1],
            "country": result[2],
        }
        if result
        else {"price_standard": None, "currency": None, "country": None}
    )
