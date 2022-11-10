import uuid
from typing import List

from pydantic import BaseModel, Field


class ActiveMarket(BaseModel):
    """
    The list of countries to be used for filtering
    """

    countries: List[str] = Field(
        description="""
        The list of markets (countries) where the client is selling its products. 
        
        Each country is represented by its code as specified in the **GlobalFilter**
        """,
        example=["SE", "NO", "DE", "FI"],
    )


class NamedRetailer(BaseModel):
    name: str = Field(description="The name of the retailer")
    country: str = Field(description="The country in which this retailer activates")
    id: uuid.UUID = Field(description="The id of the retailer in the database")

    class Config:
        orm_mode = True


class TrackedRetailerPool(BaseModel):
    """
    The list of retailers to be used for filtering
    """

    retailers: List[NamedRetailer] = Field(
        description=""""
        The list of retailers we are tracking for this client. 
        """,
        example=[
            {"name": "Homeroom", "id": "14011acc-77c6-4aea-998e-12af3fd9a5d1"},
            {"name": "Trademax", "id": "07da79c0-995c-46e6-ae7b-26b5663afab5"},
        ],
    )


class NamedProductCategory(BaseModel):
    name: str = Field(
        description="The name of the category. This is the name of the leaf category"
    )
    id: uuid.UUID = Field(description="The id of the category in the database")

    class Config:
        orm_mode = True


class ProductCategorisation(BaseModel):
    """
    The list of categories to be used for filtering
    """

    categories: List[NamedProductCategory] = Field(
        description="""
        The list of categories, as used by the client. The categories from any of the targeted retailers is mapped 
        back to the categorisation of the client.
        """,
        example=[{"name": "Utemobler", "id": "ab7b09e7-18b4-49c8-8cc6-57132eb8b820"}],
    )
