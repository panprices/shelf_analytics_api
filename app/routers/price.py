from fastapi import APIRouter, Depends
from requests import Session

from app import crud
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.filters import GlobalFilter
from app.schemas.prices import PriceTableData
from app.security import get_user_data
from app.tags import TAG_DATA, TAG_PRICE

router = APIRouter(prefix="/price")


@router.post("/data", tags=[TAG_PRICE, TAG_DATA], response_model=PriceTableData)
def get_price_table_data(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    result = crud.get_price_table_data(db, global_filter, user.client)

    return {"brand_products": result}
