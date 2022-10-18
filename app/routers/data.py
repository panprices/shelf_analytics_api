from fastapi import APIRouter, Depends

from app.schemas.auth import TokenData
from app.schemas.filters import PagedGlobalFilter
from app.schemas.product import ProductPage
from app.security import get_user_id
from app.tags import TAG_DATA

router = APIRouter(prefix="/products")


@router.post("/", tags=[TAG_DATA], response_model=ProductPage)
def get_products(page_global_filter: PagedGlobalFilter, user: TokenData = Depends(get_user_id)):
    """
    This method is used to fetch the products to show in the table on the **Data** page.
    """
    print(f"Authenticated user: {user.uid}")
    print(f"Belongs to client: {user.client}")

    return ProductPage(products=[])
