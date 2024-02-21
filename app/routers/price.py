from datetime import timedelta

from fastapi import APIRouter, Depends
from requests import Session

from app import crud
from app.crud.utils import (
    process_historical_value_per_retailer,
    duplicate_unique_points,
)
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.filters import GlobalFilter, PagedGlobalFilter, PricingChangesFilter
from app.schemas.prices import (
    PriceTableData,
    HistoricalPerRetailerResponse,
    PriceChangeResponse,
    RetailerPricingOverviewResponse,
    ComparisonProductsResponse,
)
from app.security import get_user_data
from app.tags import TAG_DATA, TAG_PRICE

router = APIRouter(prefix="/price")


@router.post("/data", tags=[TAG_PRICE, TAG_DATA], response_model=PriceTableData)
def get_price_table_data(
    global_filter: PagedPriceValuesFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    result = crud.get_price_table_data(db, global_filter, user.client)

    return {
        "rows": result,
        "count": len(result),
        "offset": global_filter.get_products_offset(),
        "total_count": crud.count_price_table_data(db, global_filter, user.client),
    }


@router.post(
    "/msrp",
    tags=[TAG_PRICE],
    response_model=HistoricalPerRetailerResponse,
)
def get_historical_msrp_deviation_per_retailer(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    history = crud.get_historical_msrp_deviation_per_retailer(
        db, global_filter, user.client
    )
    grouped_history = process_historical_value_per_retailer(
        history, "average_price_deviation", False
    )

    return duplicate_unique_points(grouped_history)


@router.post(
    "/wholesale",
    tags=[TAG_PRICE],
    response_model=HistoricalPerRetailerResponse,
)
def get_historical_wholesale_deviation_per_retailer(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    history = crud.get_historical_wholesale_deviation_per_retailer(
        db, global_filter, user.client
    )

    grouped_history = process_historical_value_per_retailer(
        history, "average_price_deviation", False
    )
    return duplicate_unique_points(grouped_history)


@router.post(
    "/average_price_deviation",
    tags=[TAG_PRICE],
    response_model=HistoricalPerRetailerResponse,
)
def get_historical_average_price_deviation_per_retailer(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    history = crud.get_historical_average_price_deviation_per_retailer(
        db, global_filter, user.client
    )

    grouped_history = process_historical_value_per_retailer(
        history, "average_price_deviation", False
    )
    return duplicate_unique_points(grouped_history)


@router.post("/changes", tags=[TAG_PRICE], response_model=PriceChangeResponse)
def get_price_changes(
    global_filter: GlobalFilter,
    sign: int,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    changes = crud.get_price_changes(db, global_filter, user.client, sign)

    return {
        "changes": changes,
    }


@router.post(
    "/retailer_overview",
    tags=[TAG_PRICE],
    response_model=RetailerPricingOverviewResponse,
)
def get_retailer_pricing_overview(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    retailer_pricing = crud.get_retailer_pricing_overview(
        db,
        global_filter,
        user.client,
    )

    return {"rows": retailer_pricing}


@router.post(
    "/{brand_product_id}/comparison",
    tags=[TAG_PRICE, TAG_DATA],
    response_model=ComparisonProductsResponse,
)
def get_comparison_products(
    global_filter: PriceValuesFilter,
    brand_product_id: str,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    comparison_products = crud.get_comparison_products(
        db,
        global_filter,
        brand_product_id,
        user.client,
    )

    return {"products": comparison_products}
