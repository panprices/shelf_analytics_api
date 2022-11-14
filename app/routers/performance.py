from functools import reduce
from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas.auth import TokenData
from app.schemas.filters import GlobalFilter
from app.schemas.performance import (
    RetailerPerformance,
    RetailersCategoryPerformanceDetails,
    IndividualRetailerCategoryPerformanceDetails,
)
from app.security import get_user_data
from app.tags import TAG_PERFORMANCE, TAG_DATA

router = APIRouter(prefix="/performance")


@router.post("", tags=[TAG_PERFORMANCE], response_model=RetailerPerformance)
async def get_category_performance(
    global_filter: GlobalFilter,
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    if len(global_filter.retailers) == 0:
        return {"categories": []}

    def append_result(result: Dict[str, Dict[str, any]], element: Dict[str, any]):
        result[element["category_id"]] = result.get(
            element["category_id"],
            {
                "category_name": element["category_name"],
                "split": [],
                "total_products": 0,
            },
        )

        result[element["category_id"]]["split"].append(
            {"brand": element["brand"], "product_count": element["product_count"]}
        )
        result[element["category_id"]]["total_products"] += element["product_count"]
        return result

    category_split = crud.get_categories_split(db, user.client, global_filter)

    result_as_dict = reduce(append_result, category_split, {})
    return {"categories": [{"category_id": k, **v} for k, v in result_as_dict.items()]}


@router.post(
    "/categories",
    tags=[TAG_PERFORMANCE, TAG_DATA],
    response_model=RetailersCategoryPerformanceDetails,
)
async def get_performance_for_categories(
    categories: List[str],
    user: TokenData = Depends(get_user_data),
    db: Session = Depends(get_db),
):
    categories_performance_details = crud.get_individual_category_performance_details(
        db, categories
    )

    return {
        "categories": {
            c["id"]: IndividualRetailerCategoryPerformanceDetails(**c)
            for c in categories_performance_details
        }
    }
