from typing import List

from sqlalchemy.orm import Session

from app.models import brand


def get_brand_categories(db: Session, brand_id: str) -> List[brand.BrandCategory]:
    return db.query(brand.BrandCategory).filter(brand.BrandCategory.brand_id == brand_id).all()
