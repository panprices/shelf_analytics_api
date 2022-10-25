from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class HistoricalItem(BaseModel):
    time: datetime = Field(
        description="The time at which the state was created",
        example="2022-10-24T12:39:21.993787+00:00"
    )


class HistoricalStockStatusItem(HistoricalItem):
    available_count: int = Field(description="Number of 'in_stock' (or similar) products", example=514)
    unavailable_count: int = Field(description="Number of 'out_of_stock' (or similar) products", example=32)


class HistoricalStockStatus(BaseModel):
    history: List[HistoricalStockStatusItem] = Field(description="The historical values")


class HistoricalVisibilityItem(HistoricalItem):
    visible_count: int = Field(description="Number of visible products", example=514)
    not_visible_count: int = Field(description="Number of missing products", example=32)


class HistoricalVisibility(BaseModel):
    history: List[HistoricalVisibilityItem] = Field(description="The historical values")
