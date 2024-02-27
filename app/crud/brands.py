from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.models import (
    brand,
    BrandProduct,
    ProductMatching,
    BrandImage,
)
from app.models.groups import ProductGroup


def get_brands(db: Session) -> List[brand.Brand]:
    return db.query(brand.Brand).all()


def get_brand_categories(db: Session, brand_id: str) -> List[brand.BrandCategory]:
    return (
        db.query(brand.BrandCategory)
        .from_statement(
            text(
                """
                    WITH current_brand_category AS (
                        SELECT *
                        FROM brand_category
                        WHERE brand_id = :brand_id
                    ), brand_category_with_active_products AS (
                        SELECT bc.id, COUNT(*) FILTER (WHERE bp.active = TRUE) AS active_products_count
                        FROM brand_category bc
                            JOIN brand_product bp ON bc.id = bp.category_id
                        WHERE bc.id IN (SELECT DISTINCT id FROM current_brand_category)
                        GROUP BY bc.id
                    )
                    SELECT bc.*
                    FROM current_brand_category bc
                        JOIN brand_category_with_active_products ON bc.id = brand_category_with_active_products.id
                    WHERE active_products_count > 0            
        """
            )
        )
        .params(brand_id=brand_id)
        .all()
    )


def get_groups(db: Session, brand_id: str) -> List[ProductGroup]:
    return db.query(ProductGroup).filter(ProductGroup.brand_id == brand_id).all()


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


def get_brand_product_detailed_for_id(db: Session, product_id: str, brand_id: str):
    return (
        db.query(BrandProduct)
        .filter(BrandProduct.id == product_id)
        .filter(BrandProduct.brand_id == brand_id)
        .options(
            selectinload(BrandProduct.matched_retailer_products).selectinload(
                ProductMatching.retailer_product
            ),
            selectinload(BrandProduct.images),
            selectinload(BrandProduct.images).selectinload(BrandImage.type_predictions),
            selectinload(BrandProduct.keywords),
        )
        .first()
    )
