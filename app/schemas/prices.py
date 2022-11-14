import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RetailerPriceHistoricalItem(BaseModel):
    x: datetime.date
    y: Optional[float] = Field(
        description="If the value is missing for a day, this field will be `None`"
    )


class RetailerHistoricalPrices(BaseModel):
    id: str
    data: List[RetailerPriceHistoricalItem]


class HistoricalPriceResponse(BaseModel):
    retailers: List[RetailerHistoricalPrices]
    max_value: float
    minimal_values: List[RetailerPriceHistoricalItem] = Field(
        description="An array with all the lowest price points"
    )
