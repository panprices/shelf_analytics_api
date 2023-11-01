import datetime
import typing
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.product import PagedResponse


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
    min_value: Optional[float]
    minimal_values: Optional[List[RetailerHistoricalItem]] = Field(
        description="An array with all the lowest price points"
    )


class RetailerProductPriceInMarket(BaseModel):
    product_name: str
    retailer_name: str
    price: float
    currency: str
    price_msrp_currency: Optional[float]
    price_deviation: Optional[float]
    url: str


class PriceTableRowScaffold(BaseModel):
    brand_product_id: typing.Union[UUID, str]
    name: str
    gtin: Optional[str]
    sku: Optional[str]
    image_id: Optional[typing.Union[UUID, str]]
    image_url: Optional[str]
    msrp_standard: Optional[float]
    msrp_client_currency: Optional[float]
    client_currency: str
    msrp_currency: Optional[str]
    msrp_country: Optional[str]
    offers: List[RetailerProductPriceInMarket]

    class Config:
        orm_mode = True


class PriceTableData(PagedResponse):
    rows: List[PriceTableRowScaffold]

    class Config:
        orm_mode = True


class PriceChangeItem(BaseModel):
    brand_product_id: typing.Union[UUID, str]
    retailer_name: str
    retailer_country: str
    product_name: str
    price_diff: float
    sku: Optional[str]


class PriceChangeResponse(BaseModel):
    changes: List[PriceChangeItem]


class RetailerPricingOverviewItem(BaseModel):
    retailer_id: typing.Union[UUID, str]
    retailer_name: str
    retailer_country: str
    products_count: int
    cheapest_price_count: int
    price_changed_count: int
    average_market_price_deviation: float


class RetailerPricingOverviewResponse(BaseModel):
    rows: List[RetailerPricingOverviewItem]


class MSRPValueItem(BaseModel):
    price_standard: float
    currency: str
    country: str

    class Config:
        orm_mode = True


class MSRPValueResponse(BaseModel):
    msrp_values: List[MSRPValueItem]


class ComparisonProductItem(BaseModel):
    market_average: float
    image_url: str
    name: str
    is_client: bool


class ComparisonProductsResponse(BaseModel):
    products: List[ComparisonProductItem]
