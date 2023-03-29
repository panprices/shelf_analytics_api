from typing import List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from firebase_admin import firestore
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.routers.auth import (
    SHELF_ANALYTICS_USER_METADATA_COLLECTION,
    authenticate_verified_user,
)
from app.schemas.auth import TokenData, AuthenticationResponse
from app.schemas.filters import GlobalFilter
from app.schemas.general import (
    TrackedRetailerPool,
    ProductCategorisation,
    ActiveMarket,
    ProductGrouping,
    NamedBrand,
)
from app.schemas.scores import HistoricalScore, AvailableProductsPerRetailer
from app.security import get_user_data
from app.tags import TAG_OVERVIEW, TAG_FILTERING

router = APIRouter(prefix="")


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
    countries: Optional[List[str]] = Query(None),
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    retailers = crud.get_retailers(db, user.client, countries)
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


@router.get("/brands", tags=[TAG_OVERVIEW], response_model=List[NamedBrand])
def get_brands(user: TokenData = Depends(get_user_data), db: Session = Depends(get_db)):
    if "developer" not in user.roles:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this resource",
        )

    return crud.get_brands(db)


@router.post("/brand", tags=[TAG_OVERVIEW], response_model=AuthenticationResponse)
def switch_brand(
    brand_change_request: Dict[str, str],
    user: TokenData = Depends(get_user_data),
):
    if "developer" not in user.roles:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this resource",
        )

    db = firestore.client()
    db.collection(SHELF_ANALYTICS_USER_METADATA_COLLECTION).document(user.uid).update(
        {"client": brand_change_request["brand_id"]}
    )

    return authenticate_verified_user(user.uid)
