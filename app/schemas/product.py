import datetime
import uuid
from typing import List, Optional, Union

from pydantic import BaseModel, Field, validator

from app.schemas.general import RetailerForProduct


class BrandCategoryScaffold(BaseModel):
    id: Union[str, uuid.UUID] = Field(
        description="The id of the category",
        example="31ef6c6c-be2d-4478-a948-10a66dad1d2a",
    )

    class Config:
        orm_mode = True


class MatchedBrandProductScaffold(BaseModel):
    """
    This is the information of the brand product sent together with a retailer product, and not on its own
    """

    id: Union[str, uuid.UUID] = Field(description="The id of the brand product")
    category: BrandCategoryScaffold
    sku: str

    class Config:
        orm_mode = True


class RetailerToBrandProductMatchScaffold(BaseModel):
    brand_product: MatchedBrandProductScaffold
    certainty: str

    @validator("certainty", pre=True)
    def convert_certainty_to_enum(cls, v):
        return v if isinstance(v, str) else v.value

    class Config:
        orm_mode = True
        use_enum_values = True


class MockRetailerProductGridItem(BaseModel):
    id: Union[str, uuid.UUID]
    url: Optional[str] = Field(
        description="The url from the retailer where we can find the product"
    )
    name: str = Field(
        description="The product name as defined by the retailer",
        example="Matgrupp Copenhagen med Matstol Comfort",
    )
    description: Optional[str] = Field(
        description="Meta hehe. Kidding. This is the description displayed by the retailer for this product",
        example="Imagine a very long description here",
    )
    gtin: Optional[str] = Field(
        description="The GTIN associated by the customer to the product",
        example="7350133230816",
    )
    retailer_name: str = Field(description="The name of the retailer")
    country: str = Field(
        description="The code representation of a country", example="SE"
    )
    price_standard: Optional[float] = Field(
        description="The price scraped at the retailer", example=3201
    )
    currency: Optional[str] = Field(
        description="The currency in which the product is being sold. Can be `None` if the price is not available",
        examples={"sweden": "SEK", "eu": "EUR"},
    )
    review_average: Optional[float] = Field(
        description="The rating of this product, average of the scores from the reviews the product received.",
        example=3.7,
    )
    number_of_reviews: Optional[int] = Field(description="Count of reviews", example=19)
    popularity_index: Optional[int] = Field(
        description="The ranking of this product inside its leaf category at the retailer",
        example=13,
    )
    retailer_images_count: Optional[int] = Field(
        description="The number of images the retailer shows", example=6
    )
    client_images_count: int = Field(
        description="The number of images recommended by the client", example=9
    )
    title_matching_score: Optional[float] = Field(
        description="A score showing how similar the retailer's title is to the title from the client",
        example=0.67,
    )
    environmental_images_count: int = Field(
        description="The number of environmental images shown for the product",
        example=5,
    )
    transparent_images_count: int = Field(
        description="The number of transparent images shown for the product", example=3
    )
    obsolete_images_count: int = Field(
        description="The number of obsolete images shown for the product", example=1
    )
    sku: Optional[str] = Field(
        description="The SKU from the retailer", example="16052-101"
    )
    wholesale_price: Optional[float] = Field(
        description="The price at which the client sells the item to the retailer (the value captured by the brand)",
        example=2602,
    )
    in_stock: bool = Field(
        default=True,
        description="Whether the product is in stock at the retailer",
        example=True,
    )
    matched_brand_product_id: Union[uuid.UUID, str] = Field(
        description="The id of the matched brand product"
    )
    brand_in_stock: Optional[bool] = Field(
        description="Whether the product is in stock at the retailer",
        example=True,
    )
    available_at_retailer: bool = Field(
        description="Whether the product is available at the retailer",
        example=True,
    )
    retailer_category_name: Optional[str] = Field(
        description="The name of the category at the retailer",
        example="Möbler > Matgrupper",
    )
    title_score: Optional[float] = Field(
        description="A score showing how similar the retailer's title is to the title from the client",
        example=0.67,
    )
    description_score: Optional[float] = Field(
        description="A score showing how similar the retailer's description is to the description from the client",
        example=0.67,
    )
    specs_score: Optional[float] = Field(
        description="A score showing how similar the retailer's specs are to the specs from the client",
        example=0.67,
    )
    text_score: Optional[float] = Field(
        description="A score showing how similar the retailer's title is to the title from the client",
        example=0.67,
    )
    image_score: Optional[float] = Field(
        description="A score showing how similar the retailer's images are to the images from the client",
        example=0.67,
    )
    content_score: Optional[float] = Field(
        description="A score showing how similar the retailer's content is to the content from the client",
        example=0.67,
    )
    is_discounted: Optional[bool] = Field(
        description="Whether the product is discounted at the retailer",
        example=True,
    )
    original_price_standard: Optional[float] = Field(
        description="The original price of the product at the retailer",
        example=3201,
    )
    fetched_at: Optional[datetime.date] = Field(
        description="The date at which the product was fetched from the retailer",
        example="2023-01-17",
    )
    created_at: Optional[datetime.date] = Field(
        description="The date at which the product was created in the database",
        example="2023-01-17",
    )
    brand_sku: Optional[str] = Field(
        description="The SKU assigned by the client", example="16052-101"
    )
    msrp_standard: Optional[float] = Field(
        description="The MSRP of the product at the retailer", example=320.15
    )
    msrp_currency: Optional[str] = Field(
        description="The currency of the MSRP of the product at the retailer",
        example="EUR",
    )
    price_deviation: Optional[float] = Field(
        description="The deviation of the price from the MSRP", example=0.1
    )
    wholesale_price_standard: Optional[float] = Field(
        description="The price at which the client sells the item to the retailer (the value captured by the brand)",
        example=2602,
    )
    wholesale_currency: Optional[str] = Field(
        description="The currency of the wholesale price",
        example="EUR",
    )
    markup_factor: Optional[float] = Field(
        description="The factor applied to wholesale price to reach the price at the retailer",
        example=2.3,
    )
    category_page_number: Optional[int] = Field(
        description="The page number at which the product was found",
        example=1,
    )
    category_pages_count: Optional[int] = Field(
        description="The total number of pages at the retailer for this category",
        example=12,
    )
    category_products_count: Optional[int] = Field(
        description="The total number of products at the retailer for this category",
        example=288,
    )
    deactivated_by_retailer: bool = Field(
        description="Whether the product is deactivated by the retailer",
        example=False,
    )

    class Config:
        orm_mode = True


class MockBrandProductGridItem(BaseModel):
    id: Union[str, uuid.UUID] = Field(
        description="UUID identifying the product uniquely",
        example="31ef6c6c-be2d-4478-a948-10a66dad1d2a",
    )
    name: str = Field(
        description="The name of the product",
        example="Matgrupp Copenhagen med Matstol Comfort",
    )
    description: Optional[str] = Field(
        description="The description of the product", example="Some description"
    )
    sku: Optional[str] = Field(
        description="The SKU assigned by the client", example="16052-101"
    )
    gtin: Optional[str] = Field(
        description="The GTIN assigned by the client", example="7350133230816"
    )
    brand_in_stock: bool = Field(
        description="Whether the product is in stock at the brand", example=False
    )
    retailers_count: int = Field(
        description="The number of retailers selling this product", example=2
    )
    markets_count: int = Field(
        description="The number of markets selling this product", example=2
    )
    retailer_coverage_rate: float = Field(
        description="The percentage of markets selling this product", example=50.0
    )

    class Config:
        orm_mode = True


class BaseRetailerProductScaffold(BaseModel):
    id: Union[str, uuid.UUID] = Field(
        description="""
            UUID identifying the product uniquely. This id identifies the product, not the offer. 
            To fetch the same offer a query should include both this id and the retailer
            """,
        example="31ef6c6c-be2d-4478-a948-10a66dad1d2a",
    )
    url: Optional[str] = Field(
        description="The url from the retailer where we can find the product"
    )
    name: str = Field(
        description="The product name as defined by the retailer",
        example="Matgrupp Copenhagen med Matstol Comfort",
    )
    description: Optional[str] = Field(
        description="Meta hehe. Kidding. This is the description displayed by the retailer for this product",
        example="Imagine a very long description here",
    )
    gtin: Optional[str] = Field(
        description="The GTIN associated by the customer to the product",
        example="7350133230816",
    )
    retailer: RetailerForProduct = Field(
        description="The retailer selling this product", example="Trademax"
    )
    country: str = Field(
        description="The code representation of a country", example="SE"
    )
    price_standard: Optional[float] = Field(
        description="The price scraped at the retailer", example=3201
    )
    currency: str = Field(
        description="The currency in which the product is being sold",
        examples={"sweden": "SEK", "eu": "EUR"},
    )
    review_average: Optional[float] = Field(
        description="The rating of this product, average of the scores from the reviews the product received.",
        example=3.7,
    )
    number_of_reviews: Optional[int] = Field(description="Count of reviews", example=19)
    popularity_index: Optional[int] = Field(
        description="The ranking of this product inside its leaf category at the retailer",
        example=13,
    )
    retailer_images_count: int = Field(
        description="The number of images the retailer shows", example=6
    )
    environmental_images_count: int = Field(
        description="The number of environmental images shown for the product",
        example=5,
    )
    transparent_images_count: int = Field(
        description="The number of transparent images shown for the product", example=3
    )


class PagedResponse(BaseModel):
    offset: int = Field(description="How many items we skipped", example=100)
    count: int = Field(description="The number of offers returned", example=20)
    total_count: int = Field(
        description="The total number of available offers", example=8121
    )


class RetailerOffersPage(PagedResponse):
    """
    Holds the data for a page of products as showed on the retailer offers table.
    """

    rows: List[MockRetailerProductGridItem] = Field(
        description="The list of retailer offers",
    )


class BrandProductsPage(PagedResponse):
    """
    Holds the data for a page of products as showed on the brand products table.
    """

    rows: List[MockBrandProductGridItem] = Field(description="The list of products")


class MatchedRetailerProductCategoryScaffold(BaseModel):
    id: Union[str, uuid.UUID]
    full_name: str
    url: str

    class Config:
        orm_mode = True


class ImageTypeScaffold(BaseModel):
    prediction: str
    confidence: float
    model: str
    version: int

    class Config:
        orm_mode = True


class GenericProductImageScaffold(BaseModel):
    id: Union[uuid.UUID, str] = Field(description="The id of the image")
    url: str = Field(description="The url of the image")
    image_hash: str = Field(description="The computed hash of the image")

    type_predictions: List[ImageTypeScaffold] = Field(
        description="Predictions for the type of the image"
    )

    class Config:
        orm_mode = True


class RetailerToBrandImageMatchScaffold(BaseModel):
    retailer_image_id: Union[uuid.UUID, str] = Field(
        description="The id of the retailer image"
    )
    brand_image_id: Union[uuid.UUID, str] = Field(
        description="The id of the matched brand image"
    )
    model_certainty: Optional[float] = Field(
        description="The confidence of the model in the match", example=0.9
    )

    class Config:
        orm_mode = True


class BrandProductImageScaffold(GenericProductImageScaffold):
    is_obsolete: bool = Field(
        description="Whether the image is obsolete or not", example=False
    )


class RetailerProductImageScaffold(GenericProductImageScaffold):
    matched_brand_images: List[RetailerToBrandImageMatchScaffold] = Field(
        description="List of matching brand images"
    )


class SpecificationScaffold(BaseModel):
    key: str
    value: str

    class Config:
        orm_mode = True


class MatchedRetailerProductScaffold(BaseRetailerProductScaffold):
    """
    This is the information of the retailer product sent together with a brand product, and not on its own.
    """

    category: Optional[MatchedRetailerProductCategoryScaffold]
    processed_images: List[RetailerProductImageScaffold] = Field(
        description="The images set by the retailer"
    )
    specifications: Optional[List[SpecificationScaffold]] = Field(
        description="The specifications of the product"
    )
    matched_brand_products: Optional[List[RetailerToBrandProductMatchScaffold]] = Field(
        description="List of matching brand products"
    )

    class Config:
        orm_mode = True


class BrandToRetailerProductMatchingScaffold(BaseModel):
    retailer_product: MatchedRetailerProductScaffold
    image_score: Optional[float] = Field(description="Image score up to 100", default=0)
    title_score: Optional[float] = Field(description="Title score up to 100", default=0)
    description_score: Optional[float] = Field(
        description="Description score up to 100", default=0
    )
    specs_score: Optional[float] = Field(description="Specs score up to 100", default=0)
    text_score: Optional[float] = Field(description="Text score up to 100", default=0)

    image_matches: Optional[List[RetailerToBrandImageMatchScaffold]] = Field(
        description="List of matching brand images"
    )

    class Config:
        orm_mode = True


class BrandProductMatchesScaffold(BaseModel):
    matches: List[BrandToRetailerProductMatchingScaffold]

    class Config:
        orm_mode = True


class BrandKeywordsScaffold(BaseModel):
    title_keywords: List[List[str]] = Field(description="The actual list of keywords")
    description_keywords: Optional[List[List[str]]] = Field(
        description="The actual list of keywords",
    )
    specs_keywords: Optional[List[List[str]]] = Field(
        description="The actual list of keywords"
    )
    language: str = Field(description="The language for the keywords")

    class Config:
        orm_mode = True


class BrandProductScaffold(BaseModel):
    """
    This is the brand product sent when we query for brand products and in it, we will have matched retailer product.

    Not to be confused with `MatchedBrandProductScaffold` that is returned when we query primarily for retailer
    products, and we returned little information about the matched brand product.
    """

    id: Union[str, uuid.UUID] = Field(description="The id of the brand product")
    description: Optional[str] = Field(
        description="The description of the product set by the brand"
    )
    name: str = Field(description="The name of the product as set by the brand")
    gtin: Optional[str] = Field(description="The gtin of the product")
    sku: Optional[str] = Field(description="The sku of the product as set by the brand")
    processed_images: List[BrandProductImageScaffold] = Field(
        description="URLs to the images set for the product by the brand"
    )
    keywords: List[BrandKeywordsScaffold] = Field(
        description="The keywords we had defined"
    )

    class Config:
        orm_mode = True
