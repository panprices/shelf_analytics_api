import uuid
from typing import Union, List, Optional, Dict

from pydantic import BaseModel, Field


class CategorySplit(BaseModel):
    brand: Optional[str] = Field(description="The name of the brand")
    product_count: int = Field(
        description="The number of products the brand has in that category"
    )


class CategoryPerformance(BaseModel):
    category_name: str = Field(description="The name of the category")
    category_id: Union[str, uuid.UUID] = Field(description="The id of the category")
    total_products: int = Field(
        description="The total number of products in the category"
    )

    split: List[CategorySplit] = Field(
        description="The brands visible in the category with their share"
    )


class RetailerPerformance(BaseModel):
    categories: List[CategoryPerformance] = Field(
        description="The split per category for the current retailer"
    )


class IndividualRetailerCategoryPerformanceDetails(BaseModel):
    products_count: int = Field(description="Number of products in the category")
    page_size: int = Field(description="Number of products per page")
    full_name: str = Field(description="Full name with all sub categories in path")


class RetailersCategoryPerformanceDetails(BaseModel):
    categories: Dict[
        Union[str, uuid.UUID], IndividualRetailerCategoryPerformanceDetails
    ] = Field(description="A dict where the key is the retailer id")


class IndividualCategoryBracketDetails(BaseModel):
    n: int
    customer_products_count: int
    customer_products_percentage: float


class IndividualRetailerCategoryTopNDetails(BaseModel):
    category_name: str = Field(description="The name of the category")
    category_id: Union[str, uuid.UUID] = Field(description="The id of the category")
    brackets: List[IndividualCategoryBracketDetails] = Field(
        description="A list of brackets"
    )


class RetailerCategoryPerformanceTopN(BaseModel):
    categories: List[IndividualRetailerCategoryTopNDetails]
