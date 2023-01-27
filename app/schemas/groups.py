from typing import List

from pydantic import BaseModel, fields


class BrandProductGroupScaffold(BaseModel):
    name: str = fields.Field(
        description="The name of the product group",
        example="Bathroom",
    )
    products: List[str] = fields.Field(
        description="The list of products in the group (by id)",
        # UUID examples
        example=[
            "14011acc-77c6-4aea-998e-12af3fd9a5d1",
            "07da79c0-995c-46e6-ae7b-26b5663afab5",
        ],
    )
