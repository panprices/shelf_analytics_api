import datetime
from typing import List

from pydantic import BaseModel, Field


class RetailerPriceHistoricalItem(BaseModel):
    x: datetime.date
    y: float


class RetailerHistoricalPrices(BaseModel):
    id: str
    data: List[RetailerPriceHistoricalItem]


class HistoricalPriceResponse(BaseModel):
    retailers: List[RetailerHistoricalPrices]
    max_value: float
    minimal_values: List[RetailerPriceHistoricalItem] = Field(
        description="An array with all the lowest price points"
    )
