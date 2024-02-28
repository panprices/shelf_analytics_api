from typing import List

from fastapi import APIRouter, Depends, HTTPException
from requests import Session
from starlette import status

from app import crud
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.groups import (
    BrandProductGroupCreationScaffold,
    BrandProductGroupAppendScaffold,
    BaseBrandProductGroupScaffold,
)
from app.security import get_user_data
from app.tags import TAG_GROUPS

router = APIRouter(prefix="/groups")


def _check_existing_products_in_filter(
    group: BaseBrandProductGroupScaffold, db: Session, user: TokenData
) -> List[str]:
    if group.products:
        return group.products
    if group.retailer_products:
        return crud.get_unique_brand_product_ids_by_retailer_matches(
            db, group.retailer_products
        )
    elif group.filter:
        return crud.get_unique_brand_product_ids(db, user.client, group.filter)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either products, retailer_products or filter must be provided",
        )


@router.post("", tags=[TAG_GROUPS])
def create_group(
    group: BrandProductGroupCreationScaffold,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    group.products = _check_existing_products_in_filter(group, db, user)

    # Create the group
    crud.create_brand_product_group(db, group, user)

    # Return the group
    return {"message": "Group created successfully."}


@router.put("", tags=[TAG_GROUPS])
def add_products_to_group(
    group: BrandProductGroupAppendScaffold,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    group.products = _check_existing_products_in_filter(group, db, user)

    # Add the products to the group
    crud.add_products_to_group(db, group)

    # Return the group
    return {"message": "Products added to group successfully."}


@router.delete("/{group_id}", tags=[TAG_GROUPS])
def delete_group(
    group_id: str,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    crud.delete_brand_products_group(db, group_id, user.client)

    return {"message": "Group deleted successfully."}
