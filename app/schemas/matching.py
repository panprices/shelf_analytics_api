import uuid
from typing import List, Optional, Union

from pydantic import BaseModel, Field

from app.schemas.filters import GlobalFilter
from app.schemas.product import BrandProductScaffold, MatchedRetailerProductScaffold


class MatchingTaskScaffold(BaseModel):
    brand_product: BrandProductScaffold = Field(description="The brand product")
    retailer_id: Union[str, uuid.UUID] = Field(description="The retailer id")
    retailer_candidates: List[MatchedRetailerProductScaffold] = Field(
        description="The list of retailer products"
    )
    brand_name: str = Field(description="The brand name")
    retailer_name: str = Field(description="The retailer name")
    tasks_count: int = Field(description="The total number of tasks")


class MatchingSolutionScaffold(BaseModel):
    """
    The matching solution which consists of either the matched retailer product id or an url where the matching product
    can be found.
    """

    brand_product_id: str = Field(description="The brand product id")
    retailer_id: str = Field(description="The retailer id")
    retailer_product_id: Optional[str] = Field(
        description="The retailer product id of the selected match"
    )
    url: Optional[str] = Field(description="The url of the retailer product")


class MatchingTaskIdentifierScaffold(BaseModel):
    brand_product_id: str = Field(description="The brand product id")
    retailer_id: str = Field(description="The retailer id")


class MatchingTaskDeterministicRequest(BaseModel):
    identifier: MatchingTaskIdentifierScaffold = Field(
        description="The identifier of the task"
    )
    global_filter: GlobalFilter = Field(description="The global filter")
