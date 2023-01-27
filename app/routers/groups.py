from fastapi import APIRouter, Depends
from requests import Session

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
    # Create the group
    crud.create_brand_product_group(db, group, user)

    # Return the group
    return {"message": "Group created successfully."}
