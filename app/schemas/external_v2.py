from typing import List

from pydantic import BaseModel, Field

from app.schemas.product import MockRetailerProductGridItem


class ExternalPagedResponse(BaseModel):
    """
    Internally we are working with the total number of products and offsets, but for the external API we want the
    pagination logic to work with page numbers instead of absolute number of products
    """

    page: int
    pages_count: int
    count: int


class ExternalRetailerOffersPage(ExternalPagedResponse):
    """
    Holds the data for a page of products as showed on the retailer offers table.
    """

    rows: List[MockRetailerProductGridItem] = Field(
        description="The list of retailer offers",
    )
