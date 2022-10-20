from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.filters import PagedGlobalFilter
from app.schemas.product import ProductPage
from app.security import get_user_data
from app.tags import TAG_DATA

router = APIRouter(prefix="/products")


@router.post("/", tags=[TAG_DATA], response_model=ProductPage)
def get_products(page_global_filter: PagedGlobalFilter,
                 user: TokenData = Depends(get_user_data),
                 db: Session = Depends(get_db)):
    products = crud.get_products(db, user.client, page_global_filter)

    return {
        "products": products,
        "count": len(products)
    }
