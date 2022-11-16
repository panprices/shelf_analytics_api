from datetime import timedelta

from fastapi import APIRouter, Depends
from requests import Session

from app import crud
from app.database import get_db
from app.preprocess import preprocess_global_filters
from app.schemas.auth import TokenData
from app.schemas.availability import HistoricalStockStatus, HistoricalVisibility
from app.schemas.filters import GlobalFilter
from app.schemas.scores import AvailableProductsPerRetailer, HistoricalScore
from app.security import get_user_data
from app.tags import TAG_AVAILABILITY, TAG_OVERVIEW

router = APIRouter(prefix="/availability")


@router.post(
    "/score", tags=[TAG_AVAILABILITY, TAG_OVERVIEW], response_model=HistoricalScore
)
def get_overall_availability_score(client_id: str, global_filter: GlobalFilter):
    """
    Returns the overall availability score corresponding to the applied filters. This is the same as the score that
    is visible when looking at the overview page in the FE.
    """
    pass


@router.post("/in_stock", tags=[TAG_AVAILABILITY], response_model=HistoricalStockStatus)
def get_in_stock_history(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    global_filter = preprocess_global_filters(db, user.client, global_filter)

    history = crud.get_historical_stock_status(db, user.client, global_filter)
    return {"history": history}


@router.post("/visible", tags=[TAG_AVAILABILITY], response_model=HistoricalVisibility)
def get_visible_history(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    history = crud.get_historical_visibility(db, user.client, global_filter)
    if len(history) == 1:
        history.insert(
            0, {**history[0], "time": history[0]["time"] - timedelta(days=7)}
        )
    return {"history": history}


@router.post(
    "/per_retailer",
    tags=[TAG_OVERVIEW],
    response_model=AvailableProductsPerRetailer,
)
def get_overview_availability_data(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    brand_id = user.client
    available_products_by_retailers = crud.count_available_products_by_retailers(
        db, brand_id, global_filter
    )

    return {"data": available_products_by_retailers}
