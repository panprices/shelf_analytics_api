from typing import List

from pydantic import BaseModel, Field

from app.schemas.product import BrandProductScaffold, MatchedRetailerProductScaffold


class MatchingTaskScaffold(BaseModel):
    brand_product: BrandProductScaffold = Field(description="The brand product")
    retailer_candidates: List[MatchedRetailerProductScaffold] = Field(
        description="The list of retailer products"
    )
    brand_name: str = Field(description="The brand name")
    retailer_name: str = Field(description="The retailer name")


class MatchingSolutionScaffold(BaseModel):
    brand_product_id: str = Field(description="The brand product id")
    retailer_product_id: str = Field(
        description="The retailer product id of the selected match"
    )
