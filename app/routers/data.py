from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app import crud
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.filters import PagedGlobalFilter, GlobalFilter
from app.schemas.product import (
    ProductPage,
    RetailerProductScaffold,
    BrandProductScaffold,
    BrandProductMatchesScaffold,
)
from app.security import get_user_data
from app.tags import TAG_DATA

router = APIRouter(prefix="/products")


@router.post("", tags=[TAG_DATA], response_model=ProductPage)
def get_products(
    page_global_filter: PagedGlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    products = crud.get_products(db, user.client, page_global_filter)
    products = [RetailerProductScaffold.from_orm(p) for p in products]

    unmatched_products = [rp for rp in products if not rp.matched_brand_products]
    brand_products_ids = [rp.id for rp in unmatched_products]

    if unmatched_products:
        brand_products = crud.get_brand_products_for_ids(db, brand_products_ids)

        for p in unmatched_products:
            p.matched_brand_products = [
                {"brand_product": bp} for bp in brand_products if bp.id == p.id
            ]

    return {
        "products": products,
        "count": len(products),
        "offset": page_global_filter.get_products_offset(),
        "total_count": crud.count_products(db, user.client, page_global_filter),
    }


@router.get(
    "/brand/{brand_product_id}", tags=[TAG_DATA], response_model=BrandProductScaffold
)
def get_brand_product_details(
    bran_product_id: str,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Must be authenticated"
        )

    return crud.get_brand_product_detailed_for_id(db, bran_product_id)


@router.post(
    "/brand/{brand_product_id}/matches",
    tags=[TAG_DATA],
    response_model=BrandProductMatchesScaffold,
)
def get_matched_retailer_products_for_brand_product(
    brand_product_id: str,
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Must be authenticated"
        )

    return {
        "matches": crud.get_retailer_products_for_brand_product(
            db, global_filter, brand_product_id
        )
    }
