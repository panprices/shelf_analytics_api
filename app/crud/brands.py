from typing import List
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.models import (
    brand,
    BrandProduct,
    Brand,
    ProductMatching,
    RetailerProduct,
    Retailer,
)
from app.schemas.filters import GlobalFilter


def get_brand_categories(db: Session, brand_id: str) -> List[brand.BrandCategory]:
    return (
        db.query(brand.BrandCategory)
        .filter(brand.BrandCategory.brand_id == brand_id)
        .all()
    )


def get_brand_products_for_ids(
    db: Session, ids: List[UUID]
) -> List[brand.BrandProduct]:
    return (
        db.query(BrandProduct)
        .options(selectinload(BrandProduct.category))
        .filter(BrandProduct.id.in_(ids))
        .all()
    )


def get_brand_product_detailed_for_id(db: Session, product_id: str):
    return (
        db.query(BrandProduct)
        .filter(BrandProduct.id == product_id)
        .options(
            selectinload(BrandProduct.matched_retailer_products).selectinload(
                ProductMatching.retailer_product
            ),
            selectinload(BrandProduct.images),
        )
        .first()
    )
