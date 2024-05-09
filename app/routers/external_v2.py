from typing import Optional

from fastapi import APIRouter, Depends
from requests import Session

from app import crud
from app.database import get_db
from app.schemas.auth import AuthMetadata
from app.schemas.external_v2 import ExternalRetailerOffersPage
from app.schemas.filters import PagedGlobalFilter
from app.security import get_auth_data
from app.tags import TAG_EXTERNAL, TAG_DATA

router = APIRouter(prefix="/v2")


@router.get(
    "/products/retailers",
    tags=[TAG_DATA, TAG_EXTERNAL],
    response_model=ExternalRetailerOffersPage,
)
async def get_retailer_offers_no_filters(
    page: Optional[int] = 0,
    user: AuthMetadata = Depends(get_auth_data),
    db: Session = Depends(get_db),
):
    page_size = 500
    page_global_filter = PagedGlobalFilter(
        **{
            "page_number": page + 1,
            "page_size": page_size,
            "data_grid_filter": {
                "items": [
                    {"column": "available_at_retailer", "operator": "is", "value": True}
                ],
                "operator": "or",
            },
            "start_date": "2022-01-01",
            "countries": [],
            "retailers": [],
            "categories": [],
            "groups": [],
        }
    )

    products = crud.get_retailer_offers(db, user.client, page_global_filter)
    total_number_of_pages = (
        crud.count_retailer_offers(db, user.client, page_global_filter) // page_size + 1
    )

    return {
        "rows": products,
        "count": len(products),
        "page": page,
        "pages_count": total_number_of_pages,
    }
