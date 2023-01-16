from typing import Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.filters import GlobalFilter
from app.schemas.matching import (
    MatchingTaskScaffold,
    MatchingSolutionScaffold,
    MatchingTaskIdentifierScaffold,
)
from app.security import get_user_data
from app.tags import TAG_MATCHING

router = APIRouter(prefix="/matching")


def fill_matching_task(
    db: Session, user: TokenData, brand_product_retailer_pair: dict
) -> MatchingTaskScaffold:
    brand_product = crud.get_brand_product_detailed_for_id(
        db, brand_product_retailer_pair["id"]
    )

    retailer_products = crud.get_matched_retailer_products_by_brand_product_id(
        db,
        brand_product_retailer_pair["id"],
        brand_product_retailer_pair["retailer_id"],
    )

    brand_name = crud.get_brand_name(db, user.client)
    retailer_name = crud.get_retailer_name_and_country(
        db, brand_product_retailer_pair["retailer_id"]
    )
    return MatchingTaskScaffold(
        **{
            "brand_product": brand_product,
            "retailer_candidates": retailer_products,
            "brand_name": brand_name,
            "retailer_name": retailer_name,
        }
    )


@router.post("/", tags=[TAG_MATCHING], response_model=MatchingTaskScaffold)
def get_next(
    global_filter: GlobalFilter,
    index: Union[int, None] = None,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    if not user:
        return HTTPException(
            status_code=401,
            detail="Must be authenticated",
        )

    if not index:
        index = 0

    brand_product_retailer_pair = crud.get_next_brand_product_to_match(
        db, user.client, global_filter, index
    )

    return fill_matching_task(db, user, brand_product_retailer_pair)


@router.post("/submit", tags=[TAG_MATCHING])
def submit_matching(
    matching: MatchingSolutionScaffold,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    if not user:
        return HTTPException(
            status_code=401,
            detail="Must be authenticated",
        )

    crud.submit_product_matching_selection(
        db, matching.brand_product_id, matching.retailer_product_id
    )

    return {"status": "success"}


@router.post("/task", tags=[TAG_MATCHING], response_model=MatchingTaskScaffold)
def get_task_deterministically(
    identifier: MatchingTaskIdentifierScaffold,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    if not user:
        return HTTPException(
            status_code=401,
            detail="Must be authenticated",
        )

    brand_product_retailer_pair = crud.get_brand_product_to_match_deterministically(
        db, identifier.brand_product_id, identifier.retailer_id
    )

    return fill_matching_task(db, user, brand_product_retailer_pair)
