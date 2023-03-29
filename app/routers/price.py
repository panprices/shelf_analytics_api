from fastapi import APIRouter, Depends
from requests import Session

from app import crud
from app.crud.utils import process_historical_value_per_retailer
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.filters import GlobalFilter, PagedGlobalFilter
from app.schemas.prices import PriceTableData, HistoricalPerRetailerResponse
from app.security import get_user_data
from app.tags import TAG_DATA, TAG_PRICE

router = APIRouter(prefix="/price")


@router.post("/data", tags=[TAG_PRICE, TAG_DATA], response_model=PriceTableData)
def get_price_table_data(
    global_filter: PagedGlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    result = crud.get_price_table_data(db, global_filter, user.client)

    return {
        "rows": result,
        "count": len(result),
        "offset": global_filter.get_products_offset(),
        "total_count": crud.count_price_table_data(db, global_filter, user.client),
    }


@router.post(
    "/msrp",
    tags=[TAG_PRICE],
    response_model=HistoricalPerRetailerResponse,
)
def get_historical_msrp_deviation_per_retailer(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    history = crud.get_historical_msrp_deviation_per_retailer(
        db, global_filter, user.client
    )

    return process_historical_value_per_retailer(history, "average_price_deviation")
