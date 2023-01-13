from typing import List

from sqlalchemy.orm import Session, selectinload

from app.models import (
    brand,
    BrandProduct,
    ProductMatching,
    BrandImage,
)


def get_brand_categories(db: Session, brand_id: str) -> List[brand.BrandCategory]:
    return (
        db.query(brand.BrandCategory)
        .filter(brand.BrandCategory.brand_id == brand_id)
        .all()
    )


def get_brand_name(db: Session, brand_id: str) -> str:
    return db.query(brand.Brand.name).filter(brand.Brand.id == brand_id).first()[0]


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
            selectinload(BrandProduct.candidate_retailer_products).selectinload(
                ProductMatching.retailer_product
            ),
            selectinload(BrandProduct.images),
            selectinload(BrandProduct.images).selectinload(BrandImage.type_predictions),
            selectinload(BrandProduct.keywords),
        )
        .first()
    )
