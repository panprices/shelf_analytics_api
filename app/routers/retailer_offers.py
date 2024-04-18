import asyncio
import hashlib
from typing import List

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.crud.utils import export_rows_to_xlsx
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.filters import (
    PagedGlobalFilter,
)
from app.schemas.product import (
    RetailerOffersPage,
    MockRetailerProductGridItem,
)
from app.models.retailer import MockRetailerProductGridItem as MockRetailerProductModel
from app.security import get_user_data
from app.tags import TAG_DATA
from structlog import get_logger

router = APIRouter(prefix="/products/retailers")
logger = get_logger()


async def __assign_screenshot_url(
    client: httpx.AsyncClient, product: MockRetailerProductModel
) -> MockRetailerProductModel:
    result = MockRetailerProductGridItem.from_orm(product)
    try:
        url_hash = hashlib.md5(str(product.url).encode()).hexdigest()
        tentative_screenshot_url = f"https://storage.googleapis.com/b2b_shelf_analytics_images/screenshots/{url_hash}.jpg"

        head_response = await client.head(tentative_screenshot_url)

        result.screenshot_url = (
            tentative_screenshot_url if head_response.status_code == 200 else None
        )
        return result
    except httpx.HTTPError as exc:
        logger.warn(
            f"HTTP exception while checking for the screenshot for {product.url} - {exc}"
        )
        result.screenshot_url = None
        return result


async def __preprocess_retailer_offers(
    products: List[MockRetailerProductModel],
) -> List[MockRetailerProductGridItem]:
    # Check for the screenshots in parallel
    async with httpx.AsyncClient() as client:
        tasks = [__assign_screenshot_url(client, p) for p in products]
        return list(await asyncio.gather(*tasks))


@router.post("", tags=[TAG_DATA], response_model=RetailerOffersPage)
async def get_retailer_offers(
    page_global_filter: PagedGlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    products = crud.get_retailer_offers(db, user.client, page_global_filter)
    processed_products = await __preprocess_retailer_offers(products)
    return {
        "rows": processed_products,
        "count": len(products),
        "offset": page_global_filter.get_products_offset(),
        "total_count": crud.count_retailer_offers(db, user.client, page_global_filter),
    }


@router.post("/export", tags=[TAG_DATA])
async def export_products_to_csv(
    page_global_filter: PagedGlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    products = crud.export_full_retailer_offers_result(
        db, user.client, page_global_filter
    )
    processed_products = await __preprocess_retailer_offers(products)
    return export_rows_to_xlsx(processed_products)
