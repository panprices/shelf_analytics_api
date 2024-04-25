import asyncio
import hashlib
from typing import List, TypeVar, Type, Union

import httpx
from pydantic import BaseModel
from structlog import get_logger

from app.database import Base

logger = get_logger(__name__)

# Define type variables with bounds to specific model classes if needed
TRetailerProductModel = TypeVar("TRetailerProductModel", bound=Base)
TRetailerProductSchema = TypeVar("TRetailerProductSchema", bound=BaseModel)


async def __retrieve_screenshot_url(
    client: httpx.AsyncClient, product_url: str
) -> Union[str, None]:
    try:
        url_hash = hashlib.md5(str(product_url).encode()).hexdigest()
        tentative_screenshot_url = f"https://storage.googleapis.com/b2b_shelf_analytics_images/screenshots/{url_hash}.jpg"

        logger.debug(f"Retrieving screenshot URL for {product_url}...")
        head_response = await client.head(tentative_screenshot_url)
        return tentative_screenshot_url if head_response.status_code == 200 else None
    except httpx.HTTPError as exc:
        logger.warn(
            f"HTTP exception while checking for the screenshot for {product_url} - {exc}"
        )
        return None


async def assign_screenshot_url(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    product: TRetailerProductModel,
    output_model_class: Type[TRetailerProductSchema],
) -> TRetailerProductSchema:
    async with semaphore:
        result = output_model_class.from_orm(product)
        result.screenshot_url = await __retrieve_screenshot_url(client, product.url)
        return result


async def preprocess_retailer_offers(
    products: List[TRetailerProductModel],
    output_model_class: Type[TRetailerProductSchema],
) -> List[TRetailerProductSchema]:
    # Check for the screenshots in parallel
    concurrency = 100
    semaphore = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(
        limits=httpx.Limits(max_connections=concurrency),
    ) as client:
        tasks = [
            assign_screenshot_url(client, semaphore, p, output_model_class)
            for p in products
        ]
        return list(await asyncio.gather(*tasks))
