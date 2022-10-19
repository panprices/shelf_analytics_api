import uuid
from typing import List

from sqlalchemy.orm import Session

from app.models import retailer, brand


def get_retailers(db: Session, brand_id: str) -> List[retailer.Retailer]:
    return db.query(retailer.Retailer).filter(retailer.Retailer.brands.any(brand.Brand.id == brand_id)).all()


def get_countries(db: Session, brand_id: str) -> List[str]:
    return db.query(retailer.Retailer.country)\
        .filter(retailer.Retailer.brands.any(brand.Brand.id == brand_id))\
        .distinct()\
        .all()
