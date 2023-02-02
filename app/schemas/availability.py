from typing import List

from pydantic import BaseModel, Field

from app.schemas.scores import HistoricalItem


class HistoricalVisibilityItem(HistoricalItem):
    visible_count: int = Field(description="Number of visible products", example=514)
    not_visible_count: int = Field(description="Number of missing products", example=32)


class HistoricalVisibility(BaseModel):
    history: List[HistoricalVisibilityItem] = Field(description="The historical values")


class HistoricalComplianceItem(HistoricalItem):
    compliant_count: int = Field(description="The number of compliant products")
    non_compliant_count: int = Field(description="The number of non compliant products")


class HistoricalCompliance(BaseModel):
    history: List[HistoricalComplianceItem] = Field(description="The historical values")
