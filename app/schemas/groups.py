from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, fields

from app.schemas.filters import DataPageFilter


class BaseBrandProductGroupScaffold(BaseModel):

    products: Optional[List[Union[UUID, str]]] = fields.Field(
        description="The list of products in the group (by id)",
        # UUID examples
        example=[
            "14011acc-77c6-4aea-998e-12af3fd9a5d1",
            "07da79c0-995c-46e6-ae7b-26b5663afab5",
        ],
    )
    retailer_products: Optional[List[str]] = fields.Field(
        description="The list of retailer products matching with brand products in the group (by id)",
    )
    filter: Optional[DataPageFilter] = fields.Field(
        description="The filters to apply for finding the products in the group",
    )


class BrandProductGroupCreationScaffold(BaseBrandProductGroupScaffold):
    """
    A brand product group can be defined by a list of ids, or by a filter that will be used to retrieve the products.
    """

    name: str = fields.Field(
        description="The name of the product group",
        example="Bathroom",
    )


class BrandProductGroupAppendScaffold(BaseBrandProductGroupScaffold):
    id: Union[UUID, str] = fields.Field(
        description="The id of the group to append products to",
        example="14011acc-77c6-4aea-998e-12af3fd9a5d1",
    )
