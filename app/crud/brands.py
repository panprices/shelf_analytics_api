from typing import List
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.models import brand, BrandProduct


def get_brand_categories(db: Session, brand_id: str) -> List[brand.BrandCategory]:
    return db.query(brand.BrandCategory).filter(brand.BrandCategory.brand_id == brand_id).all()


def get_brand_products_for_ids(db: Session, ids: List[UUID]) -> List[brand.BrandProduct]:
    return db.query(BrandProduct).options(selectinload(BrandProduct.category))\
        .filter(BrandProduct.id.in_(ids)).all()
