import uuid
from typing import List, Optional, Dict, Any

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


class CountryToLanguageScaffold(BaseModel):
    country: str = Field(description="Country of the retailer")
    language: str = Field(description="Language to use with the country")

    class Config:
        orm_mode = True


class RetailerBrandAssociationScaffold(BaseModel):
    shallow: bool = Field(description="Whether the retailer is shallow or not")

    class Config:
        orm_mode = True


class NamedBrand(BaseModel):
    name: str = Field(description="The name of the brand")
    id: uuid.UUID = Field(description="The id of the brand in the database")

    class Config:
        orm_mode = True


class NamedRetailer(BaseModel):
    name: str = Field(description="The name of the retailer")
    country: str = Field(description="The country in which this retailer activates")
    id: uuid.UUID = Field(description="The id of the retailer in the database")

    class Config:
        orm_mode = True


class FilterRetailer(NamedRetailer):
    language: str = Field(description="The language to use with the retailer")
    shallow: bool = Field(description="Whether the retailer is shallow or not")
    status: str = Field(description="The status of the retailer")


class RetailerForProduct(NamedRetailer):
    retailer_specific_language: Optional[str] = Field(
        description="Overwrites the language of the country for this retailer"
    )
    country_to_language: CountryToLanguageScaffold = Field(
        description="The language available for the retailer's country"
    )


class TrackedRetailerPool(BaseModel):
    """
    The list of retailers to be used for filtering
    """

    retailers: List[FilterRetailer] = Field(
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
    id: Optional[uuid.UUID] = Field(
        description="The id of the category in the database"
    )
    children: Optional[List["NamedProductCategory"]] = Field(
        description="The list of children categories"
    )

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


class ProductGrouping(BaseModel):
    groups: List[NamedProductCategory] = Field(
        description="The list of groups defined by the client to be used for filtering",
    )


class OverviewStatsResponse(BaseModel):
    products_count: int = Field(
        description="The number of products in the database for this client"
    )
    retailers_count: int = Field(
        description="The number of retailers in the database for this client"
    )
    markets_count: int = Field(
        description="The number of markets in the database for this client"
    )
    matches_count: int = Field(
        description="The number of matches in the database for this client"
    )
