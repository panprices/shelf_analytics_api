from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.availability import HistoricalVisibility
from app.schemas.filters import GlobalFilter
from app.schemas.scores import AvailableProductsPerRetailer
from app.security import get_logged_in_user_data
from app.tags import TAG_AVAILABILITY, TAG_OVERVIEW

router = APIRouter(prefix="/availability")


@router.post("/visible", tags=[TAG_AVAILABILITY], response_model=HistoricalVisibility)
def get_visible_history(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_logged_in_user_data),
    db: Session = Depends(get_db),
):
    history = crud.get_historical_visibility(db, user.client, global_filter)
    if len(history) == 1:
        history.insert(
            0, {**history[0], "time": history[0]["time"] - timedelta(days=7)}
        )
    return {"history": history}


@router.post(
    "/visible/average", tags=[TAG_AVAILABILITY], response_model=HistoricalVisibility
)
def get_visible_history_average(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_logged_in_user_data),
    db: Session = Depends(get_db),
):
    history = crud.get_historical_visibility_average(db, user.client, global_filter)
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
    user: TokenData = Depends(get_logged_in_user_data),
    db: Session = Depends(get_db),
):
    brand_id = user.client
    available_products_by_retailers = crud.count_available_products_by_retailers(
        db, brand_id, global_filter
    )

    return {
        "data": available_products_by_retailers,
        "available_status": "available",
        "not_available_status": "not_available",
    }
