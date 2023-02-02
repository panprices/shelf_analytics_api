from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.filters import GlobalFilter
from app.schemas.scores import HistoricalScore
from app.security import get_user_data
from app.tags import TAG_OVERVIEW

router = APIRouter(prefix="/stock")


@router.post("", tags=[TAG_OVERVIEW], response_model=HistoricalScore)
def get_historical_out_of_stock(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    """
    Returns the historical out of stock data for the given filters.
    """
    history = crud.get_historical_out_of_stock(db, user.client, global_filter)

    return {"history": history}
