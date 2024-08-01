from typing import Optional

import pandas

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from structlog import get_logger

from app import crud
from app.crud.utils import export_dataframe_to_xlsx, export_rows_to_xlsx
from app.database import get_db
from app.schemas.auth import TokenData, AuthMetadata
from app.schemas.filters import (
    PagedGlobalFilter,
    PagedPriceValuesFilter,
    PriceValuesFilter,
)
from app.schemas.product import (
    RetailerOffersPage,
    MockRetailerProductGridItem,
)
from app.security import get_logged_in_user_data, get_auth_data
from app.service.currency import add_user_currency_to_retailer_offers
from app.service.screenshot import add_screenshots_to_retailer_offers
from app.tags import TAG_DATA, TAG_EXTERNAL

router = APIRouter(prefix="/products/retailers")
logger = get_logger()


@router.post("", tags=[TAG_DATA], response_model=RetailerOffersPage)
async def get_retailer_offers(
    page_global_filter: PagedGlobalFilter,
    user: TokenData = Depends(get_logged_in_user_data),
    db: Session = Depends(get_db),
):
    products = crud.get_retailer_offers(db, user.client, page_global_filter)
    products_with_screenshots = await add_screenshots_to_retailer_offers(
        products, output_model_class=MockRetailerProductGridItem
    )
    return {
        "rows": products_with_screenshots,
        "count": len(products),
        "offset": page_global_filter.get_products_offset(),
        "total_count": crud.count_retailer_offers(db, user.client, page_global_filter),
    }


@router.post("/export", tags=[TAG_DATA])
async def export_products_to_xlsx(
    global_filter: PagedPriceValuesFilter,
    user: TokenData = Depends(get_logged_in_user_data),
    db: Session = Depends(get_db),
):
    products = crud.export_full_retailer_offers_result(
        db,
        user.client,
        global_filter,
    )
    products_with_screenshots = await add_screenshots_to_retailer_offers(
        products, output_model_class=MockRetailerProductGridItem
    )
    products_with_currency = add_user_currency_to_retailer_offers(
        products_with_screenshots,
        global_filter.currency,
        db
    )
    products_df = pandas.DataFrame(
        [p.dict_exclude_deprecated_fields() for p in products_with_currency]
    )
    return export_dataframe_to_xlsx(products_df)
