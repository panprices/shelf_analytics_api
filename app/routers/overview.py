from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.filters import GlobalFilter
from app.schemas.general import (
    TrackedRetailerPool,
    ProductCategorisation,
    ActiveMarket,
    ProductGrouping,
)
from app.schemas.scores import HistoricalScore, AvailableProductsPerRetailer
from app.security import get_user_data
from app.tags import TAG_OVERVIEW, TAG_FILTERING

router = APIRouter(prefix="")


@router.post("/score", tags=[TAG_OVERVIEW], response_model=HistoricalScore)
def get_overall_scores(client_id: str, global_filter: GlobalFilter):
    """
    Returns the overall score corresponding to the applied filters.

    This same method can be used for showing the breakdown values at the bottom of the overview page. The idea is that
    method would be called with filters corresponding to the displayed value, for example a filter that only selects
    Sweden as a country, or only selects Trademax as a retailer, etc.
    """
    pass


@router.get(
    "/countries", tags=[TAG_OVERVIEW, TAG_FILTERING], response_model=ActiveMarket
)
def get_countries(
    user: TokenData = Depends(get_user_data), db: Session = Depends(get_db)
):
    countries = crud.get_countries(db, user.client)
    return {"countries": [c[0] for c in countries]}


@router.get(
    "/retailers", tags=[TAG_OVERVIEW, TAG_FILTERING], response_model=TrackedRetailerPool
)
def get_retailers(
    user: TokenData = Depends(get_user_data), db: Session = Depends(get_db)
):
    retailers = crud.get_retailers(db, user.client)
    return {"retailers": retailers}


@router.get(
    "/groups", tags=[TAG_OVERVIEW, TAG_FILTERING], response_model=ProductGrouping
)
def get_groups(user: TokenData = Depends(get_user_data), db: Session = Depends(get_db)):
    groups = crud.get_groups(db, user.client)
    return {"groups": groups}


@router.get(
    "/categories",
    tags=[TAG_OVERVIEW, TAG_FILTERING],
    response_model=ProductCategorisation,
)
def get_categories(
    user: TokenData = Depends(get_user_data), db: Session = Depends(get_db)
):
    categories = crud.get_brand_categories(db, user.client)
    return {"categories": [{"id": c.id, "name": c.full_name} for c in categories]}
