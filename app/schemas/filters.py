from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, validator

from app.config.constants import DATE_FORMAT


class GlobalFilter(BaseModel):

    """
    Represents the model for filtering on the data showed through the UI.

    It corresponds to the filter widget showed at the top of every page in the FE.

    The date should be passed in the format: DD/MM/YYYY

    Countries are passed by the country code:
    - Sweden - SE
    - Norway - NO
    - Germany - DE
    ...

    Retailers and categories are passed by their literal values (as returned by this API).
    """
    start_date: datetime = Field(description="Test description", example="15/10/2022")
    countries: List[str] = Field(
        description="The list of desired countries. If no country is specified all countries are considered.",
        example=[]
    )
    retailers: List[str] = Field(
        description="The list of desired retailers. If no retailer is specified all retailers are considered.",
        example=[]
    )
    categories: List[str] = Field(
        description="The list of desired countries. If no country is specified all countries are considered.",
        # TODO: add an example for category selection
        example=[]
    )

    @validator('start_date', pre=True)
    def parse_start_date(cls, value):
        if not isinstance(value, str):
            return value

        return datetime.strptime(value, DATE_FORMAT)


class PagedGlobalFilter(GlobalFilter):
    page_number: int = Field(
        description="The number of the currently requested page in the pagination system. Index is 1 based.",
        example=1
    )
    page_size: int = Field(
        default=10,
        description="The number of results displayed per page.",
        example=10
    )

    def get_products_offset(self):
        return (self.page_number - 1) * self.page_size
