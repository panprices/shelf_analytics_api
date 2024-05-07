from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas.auth import TokenData, AuthMetadata
from app.schemas.filters import GlobalFilter
from app.schemas.scores import HistoricalScore
from app.security import get_auth_data
from app.tags import TAG_OVERVIEW

router = APIRouter(prefix="/stock")


@router.post("", tags=[TAG_OVERVIEW], response_model=HistoricalScore)
def get_historical_in_stock(
    global_filter: GlobalFilter,
    user: AuthMetadata = Depends(get_auth_data),
    db: Session = Depends(get_db),
):
    """
    Returns the historical "in stock" data for the given filters.
    """
    history = crud.get_historical_in_stock(db, user.client, global_filter)
    if len(history) == 1:
        history.insert(
            0, {**history[0], "time": history[0]["time"] - timedelta(days=7)}
        )

    return {"history": history}
