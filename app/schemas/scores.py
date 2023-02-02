from datetime import date
from typing import List

from pydantic import BaseModel, Field


class HistoricalItem(BaseModel):
    time: date = Field(
        description="The time at which the state was created",
        example="2022-10-24T12:39:21.993787+00:00",
    )


class HistoricalScoreItem(HistoricalItem):
    score: float = Field(description="The score")


class HistoricalScore(BaseModel):
    history: List[HistoricalScoreItem] = Field(description="The historical values")


class AvailableProductsCount(BaseModel):
    retailer: str
    available_products_count: int
    not_available_products_count: int


class AvailableProductsPerRetailer(BaseModel):
    """Used for Overview -> Available products per retailer"""

    data: List[AvailableProductsCount]


class ContentScoreItem(BaseModel):
    retailer: str
    score: float


class ContentScorePerRetailer(BaseModel):
    """Used for Overview -> Content score per retailer"""

    data: List[ContentScoreItem]
