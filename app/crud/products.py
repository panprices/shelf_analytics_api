from typing import List

from sqlalchemy.orm import Session, joinedload, contains_eager

from app.models import (
    retailer,
    RetailerProduct,
    brand,
    Retailer,
    BrandProduct,
    ProductMatching,
)
from app.schemas.filters import PagedGlobalFilter


def get_products(
    db: Session, brand_id: str, global_filter: PagedGlobalFilter
) -> List[RetailerProduct]:
    query = (
        db.query(
            RetailerProduct
        )
        .join(RetailerProduct.retailer)
        .filter(Retailer.brands.any(brand.Brand.id == brand_id))
        .filter(
            RetailerProduct.matched_brand_products.any(
                brand.BrandProduct.brand_id == brand_id
            )
        )
        .filter(RetailerProduct.created_at > global_filter.start_date)
    )

    if global_filter.countries:
        query = query.filter(Retailer.country.in_(global_filter.countries))

    if global_filter.retailers:
        query = query.filter(Retailer.id.in_(global_filter.retailers))

    if global_filter.categories:
        query = query\
            .join(RetailerProduct.matched_brand_products)\
            .join(ProductMatching.brand_product)\
            .filter(BrandProduct.category_id.in_(global_filter.categories))

    return (
        query
        .limit(global_filter.page_size)
        .offset(global_filter.get_products_offset())
        .options(
            joinedload(RetailerProduct.retailer),
            joinedload(RetailerProduct.images),
            joinedload(
                RetailerProduct.matched_brand_products
            ).joinedload(
                ProductMatching.brand_product
            ).joinedload(
                BrandProduct.images
            ),
            joinedload(
                RetailerProduct.matched_brand_products
            ).joinedload(
                ProductMatching.brand_product
            ).joinedload(
                BrandProduct.category
            )
        )
        .all()
    )
