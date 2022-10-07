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
        example=["SE", "NO", "DE", "FI"]
    )


class TrackedRetailerPool(BaseModel):
    """
    The list of retailers to be used for filtering
    """

    retailers: List[str] = Field(
        description=""""
        The list of retailers we are tracking for this client. 
        """,
        example=["Homeroom", "Trademax"]
    )


class ProductCategorisation(BaseModel):
    """
    The list of categories to be used for filtering
    """

    categories: List[str] = Field(
        description="""
        The list of categories, as used by the client. The categories from any of the targeted retailers is mapped 
        back to the categorisation of the client.
        """,
        # TODO: How we represent categories?
        example=[""]
    )
