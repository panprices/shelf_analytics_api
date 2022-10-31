from typing import List

from pydantic import BaseModel, Field


class ScoreArchiveEntry(BaseModel):
    value: float = Field(description="the value of the score at the given date")
    date: str = Field(description="Data specified in the \"DD/MM/YYYY\" format")


class HistoricalScore(BaseModel):
    """
    Holds a score and its historical values. Used for the "Big Number Cards" in the UI
    """

    value: float = Field(description="The current value", example=0.77)
    history: List[ScoreArchiveEntry] = Field(
        description="The historical values for the score",
        example=[
            ScoreArchiveEntry(date="13/10/2022", value=0.69),
            ScoreArchiveEntry(date="14/10/2022", value=0.73)
        ]
    )


class AvailableProductsCount(BaseModel): 
    retailer: str
    available_products_count: int
    not_available_products_count: int
    
class AvailableProductsPerRetailer(BaseModel):
    """Used for Overview -> Available products per retailer"""
    data: List[AvailableProductsCount]
