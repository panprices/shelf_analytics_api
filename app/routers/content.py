from datetime import timedelta
from functools import reduce

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.crud.utils import create_append_to_history_reducer
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.availability import HistoricalScore
from app.schemas.filters import GlobalFilter
from app.schemas.prices import HistoricalPerRetailerResponse
from app.schemas.scores import ContentScorePerRetailer
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


def _process_score_per_retailer(history):
    retailers = [
        v
        for v in reduce(
            create_append_to_history_reducer(
                lambda history_item: history_item["retailer"],
                lambda history_item: history_item["time"],
                lambda history_item: history_item["score"],
            ),
            history,
            {},
        ).values()
    ]

    for retailer in retailers:
        if len(retailer["data"]) == 1:
            retailer["data"].insert(
                0,
                {
                    **retailer["data"][0],
                    "x": retailer["data"][0]["x"] - timedelta(days=7),
                },
            )

    max_value = max([i["score"] for i in history]) if history else 0
    min_value = min([i["score"] for i in history]) if history else 0

    return {"retailers": retailers, "max_value": max_value, "min_value": min_value}


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
    return _process_score_per_retailer(history)


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
    return _process_score_per_retailer(history)


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
    history = crud.get_current_score_per_retailer(db, user.client, global_filter)
    return {"data": history}
