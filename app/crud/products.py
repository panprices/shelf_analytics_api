from typing import List

from sqlalchemy.orm import Session

from app.models import retailer, brand, RetailerProduct
from app.schemas.filters import PagedGlobalFilter


def get_products(db: Session, brand_id: str, global_filter: PagedGlobalFilter) -> List[RetailerProduct]:
    return db.query(retailer.RetailerProduct)\
        .join(retailer.RetailerProduct.retailer)\
        .filter(retailer.Retailer.brands.any(brand.Brand.id == brand_id))\
        .filter(retailer.RetailerProduct.matched_brand_products.any(brand.BrandProduct.brand_id == brand_id))\
        .limit(global_filter.page_size)\
        .offset(global_filter.get_products_offset())\
        .all()
