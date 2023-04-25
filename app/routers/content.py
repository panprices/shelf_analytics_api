from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.crud.utils import (
    process_historical_value_per_retailer,
)
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.filters import GlobalFilter
from app.schemas.prices import HistoricalPerRetailerResponse
from app.schemas.scores import ContentScorePerRetailer
from app.schemas.scores import HistoricalScore
from app.security import get_user_data
from app.tags import TAG_CONTENT

router = APIRouter(prefix="/content")


@router.post("/score/image", tags=[TAG_CONTENT], response_model=HistoricalScore)
def get_image_score(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    history = crud.get_historical_image_score(db, user.client, global_filter)
    if len(history) == 1:
        history.insert(
            0, {**history[0], "time": history[0]["time"] - timedelta(days=7)}
        )
    return {"history": history}


@router.post("/score/text", tags=[TAG_CONTENT], response_model=HistoricalScore)
def get_text_score(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    history = crud.get_historical_text_score(db, user.client, global_filter)
    if len(history) == 1:
        history.insert(
            0, {**history[0], "time": history[0]["time"] - timedelta(days=7)}
        )
    return {"history": history}


@router.post("/score", tags=[TAG_CONTENT], response_model=HistoricalScore)
def get_content_score(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    history = crud.get_historical_content_score(db, user.client, global_filter)
    if len(history) == 1:
        history.insert(
            0, {**history[0], "time": history[0]["time"] - timedelta(days=7)}
        )
    return {"history": history}


@router.post(
    "/score/image/per_retailer",
    tags=[TAG_CONTENT],
    response_model=HistoricalPerRetailerResponse,
)
def get_image_score_per_retailer(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    history = crud.get_historical_image_score_per_retailer(
        db, user.client, global_filter
    )
    return process_historical_value_per_retailer(history, "score")


@router.post(
    "/score/text/per_retailer",
    tags=[TAG_CONTENT],
    response_model=HistoricalPerRetailerResponse,
)
def get_text_score_per_retailer(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    history = crud.get_historical_text_score_per_retailer(
        db, user.client, global_filter
    )
    return process_historical_value_per_retailer(history, "score")


@router.post(
    "/per_retailer",
    tags=[TAG_CONTENT],
    response_model=ContentScorePerRetailer,
)
def get_content_score_per_retailer(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    history = crud.get_historical_content_score_per_retailer(
        db, user.client, global_filter
    )
    historical_result = process_historical_value_per_retailer(history, "score")
    max_date = max([p["x"] for r in historical_result["retailers"] for p in r["data"]])
    result = [
        {
            "retailer": r["id"],
            "score": r["data"][-1]["y"],
        }
        for r in historical_result["retailers"]
        if r["data"][-1]["x"] == max_date and r["data"][-1]["y"] is not None
    ]

    return {"data": result}
