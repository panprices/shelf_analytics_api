from typing import List

from sqlalchemy.orm import Session, selectinload

from app.models import (
    brand,
    BrandProduct,
    ProductMatching,
)


def get_brand_categories(db: Session, brand_id: str) -> List[brand.BrandCategory]:
    return (
        db.query(brand.BrandCategory)
        .filter(brand.BrandCategory.brand_id == brand_id)
        .all()
    )


def get_brand_products_for_gtins(
    db: Session, gtins: List[str]
) -> List[brand.BrandProduct]:
    return (
        db.query(BrandProduct)
        .options(selectinload(BrandProduct.category))
        .filter(BrandProduct.gtin.in_(gtins))
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
