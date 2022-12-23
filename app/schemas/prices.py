import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RetailerHistoricalItem(BaseModel):
    x: datetime.date
    y: Optional[float] = Field(
        description="If the value is missing for a day, this field will be `None`"
    )


class RetailerHistoricalValues(BaseModel):
    id: str
    data: List[RetailerHistoricalItem]


class HistoricalPerRetailerResponse(BaseModel):
    retailers: List[RetailerHistoricalValues]
    max_value: Optional[float]
    minimal_values: Optional[List[RetailerHistoricalItem]] = Field(
        description="An array with all the lowest price points"
    )
