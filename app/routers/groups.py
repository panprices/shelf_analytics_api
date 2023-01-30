from fastapi import APIRouter, Depends, HTTPException
from requests import Session
from starlette import status

from app import crud
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.groups import BrandProductGroupScaffold
from app.security import get_user_data
from app.tags import TAG_GROUPS

router = APIRouter(prefix="/groups")


@router.post("/new", tags=[TAG_GROUPS])
def create_group(
    group: BrandProductGroupScaffold,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    if not group.products:
        if group.retailer_products:
            group.products = crud.get_unique_brand_product_ids_by_retailer_matches(
                db, group.retailer_products
            )
        elif group.filter:
            group.products = crud.get_unique_brand_product_ids(
                db, user.client, group.filter
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either products, retailer_products or filter must be provided",
            )

    # Create the group
    crud.create_brand_product_group(db, group, user)

    # Return the group
    return {"message": "Group created successfully."}
