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
    MatchingTaskDeterministicRequest,
    MatchingTaskIdentifierScaffold,
)
from app.security import get_user_data
from app.tags import TAG_MATCHING

router = APIRouter(prefix="/matching")


def fill_matching_task(
    db: Session,
    user: TokenData,
    brand_product_retailer_pair: dict,
    global_filter: GlobalFilter,
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

    tasks_count = crud.count_product_matching_tasks(
        db, user.client, global_filters=global_filter
    )

    return MatchingTaskScaffold(
        **{
            "brand_product": brand_product,
            "retailer_candidates": retailer_products,
            "brand_name": brand_name,
            "retailer_name": retailer_name,
            "retailer_id": brand_product_retailer_pair["retailer_id"],
            "tasks_count": tasks_count,
        }
    )


@router.post(
    "/next", tags=[TAG_MATCHING], response_model=MatchingTaskIdentifierScaffold
)
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

    result = crud.get_next_brand_product_to_match(db, user.client, global_filter, index)

    return result if result else {"finished": True}


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

    if matching.action == "skip":
        # On case of skip
        crud.invalidate_product_matching_selection(
            db,
            brand_product_id=matching.brand_product_id,
            retailer_id=matching.retailer_id,
            certainty="auto_low_confidence_skipped",
        )
        return {"status": "success"}

    # On case of submission
    if matching.retailer_product_id:
        crud.submit_product_matching_selection(
            db,
            brand_product_id=matching.brand_product_id,
            retailer_id=matching.retailer_id,
            retailer_product_id=matching.retailer_product_id,
        )
    elif matching.url:
        crud.submit_product_matching_url(
            db,
            user_id=user.uid,
            brand_product_id=matching.brand_product_id,
            retailer_id=matching.retailer_id,
            url=matching.url,
        )
    else:
        crud.invalidate_product_matching_selection(
            db,
            brand_product_id=matching.brand_product_id,
            retailer_id=matching.retailer_id,
        )

    return {"status": "success"}


@router.post("/task", tags=[TAG_MATCHING], response_model=MatchingTaskScaffold)
def get_task_deterministically(
    request: MatchingTaskDeterministicRequest,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    if not user:
        return HTTPException(
            status_code=401,
            detail="Must be authenticated",
        )
    identifier = request.identifier

    brand_product_retailer_pair = crud.get_brand_product_to_match_deterministically(
        db, identifier.brand_product_id, identifier.retailer_id
    )

    # By default we don't filter by global filters when getting a task deterministically
    return fill_matching_task(
        db, user, brand_product_retailer_pair, global_filter=request.global_filter
    )
