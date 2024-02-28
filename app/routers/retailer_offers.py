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
from app.security import get_user_data
from app.tags import TAG_DATA

router = APIRouter(prefix="/products/retailers")


@router.post("", tags=[TAG_DATA], response_model=RetailerOffersPage)
def get_retailer_offers(
    page_global_filter: PagedGlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    products = crud.get_retailer_offers(db, user.client, page_global_filter)

    return {
        "rows": products,
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
    products = [MockRetailerProductGridItem.from_orm(p) for p in products]
    return export_rows_to_xlsx(products)
