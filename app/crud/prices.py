from typing import List

from sqlalchemy.orm import Session, selectinload

from app.models import (
    RetailerProductHistory,
    RetailerProduct,
    ProductMatching,
    BrandProduct,
    Retailer,
)
from app.schemas.filters import GlobalFilter


def get_historical_prices_by_retailer_for_brand_product(
    db: Session, global_filter: GlobalFilter, brand_product_id: str
) -> List[RetailerProductHistory]:
    query = (
        db.query(RetailerProductHistory)
        .join(RetailerProductHistory.product)
        .join(RetailerProduct.retailer)
        .join(RetailerProduct.matched_brand_products)
        .join(ProductMatching.brand_product)
        .filter(BrandProduct.id == brand_product_id)
    )

    if global_filter.retailers:
        query = query.filter(Retailer.id.in_(global_filter.retailers))

    if global_filter.countries:
        query = query.filter(Retailer.country.in_(global_filter.countries))

    return (
        query.options(
            selectinload(RetailerProductHistory.product).selectinload(
                RetailerProduct.retailer
            )
        )
        .order_by(RetailerProductHistory.time)
        .all()
    )
