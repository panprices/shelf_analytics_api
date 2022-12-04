import uuid
from typing import List, Optional, Union

from pydantic import BaseModel, Field

from app.schemas.general import NamedRetailer


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
    retailer: NamedRetailer = Field(
        description="The retailer selling this product", example="Trademax"
    )
    country: str = Field(
        description="The code representation of a country", example="SE"
    )
    price_standard: float = Field(
        description="The price scraped at the retailer", example=3201
    )
    currency: str = Field(
        description="The currency in which the product is being sold",
        examples={"sweden": "SEK", "eu": "EUR"},
    )
    review_average: float = Field(
        description="The rating of this product, average of the scores from the reviews the product received.",
        example=3.7,
    )
    number_of_reviews: int = Field(description="Count of reviews", example=19)
    popularity_index: int = Field(
        description="The ranking of this product inside its leaf category at the retailer",
        example=13,
    )
    retailer_images_count: int = Field(
        description="The number of images the retailer shows", example=6
    )
    client_images_count: int = Field(
        description="The number of images recommended by the client", example=9
    )
    title_matching_score: Optional[float] = Field(
        description="A score showing how similar the retailer's title is to the title from the client",
        example=0.67,
    )
    environmental_image_count: int = Field(
        description="The number of environmental images shown for the product",
        example=5,
    )
    transparent_image_count: int = Field(
        description="The number of transparent images shown for the product", example=3
    )


class RetailerProductScaffold(BaseRetailerProductScaffold):
    """
    Holds the *scaffold* data for a product, meaning only the high level data directly visible in the data table,
    plus the product id to be used for further querying.

    This is the result by itself, as opposed to `MatchedRetailerProductScaffold`.
    """

    margin: Optional[float] = Field(
        description="The margin of profit obtained by the retailer on this product",
        example=0.56,
    )
    sku: Optional[str] = Field(
        description="The SKU assigned by the client", example="16052-101"
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
    matched_brand_products: List[RetailerToBrandProductMatchScaffold] = Field(
        description="List of matching candidates"
    )

    class Config:
        orm_mode = True


class ProductPage(BaseModel):
    """
    Holds the data for a page of products as showed on the data page in FE.
    """

    products: List[RetailerProductScaffold] = Field(
        description="The list of products",
        example=[
            RetailerProductScaffold(
                id="31ef6c6c-be2d-4478-a948-10a66dad1d2a",
                name="Matgrupp Copenhagen med Matstol Comfort",
                gtin="7350133230816",
                retailer={
                    "id": "07da79c0-995c-46e6-ae7b-26b5663afab5",
                    "country": "SE",
                    "name": "Trademax",
                },
                country="SE",
                price_standard=3201,
                currency="SEK",
                margin=0.56,
                retailer_images_count=6,
                client_images_count=9,
                title_matching_score=0.67,
                sku="GR22606",
                wholesale_price=2503,
                popularity_index=13,
                description="""
                    En trendsäker matgrupp i skandinavisk design! Vårt omtyckta, rektangulära matbord 
                    Kenya har en tidlös design med ribbat utförande i smakfull teak. Kryssbenen ger ett stadigt och 
                    charmigt intryck. Mått: 120x70 cm. Här i smäcker kombination med 4st läckra matstolar från samma 
                    serie. Stolarna är också i teak och är hopfällbara för praktisk förvaring. Möblera uteplatsen 
                    inbjudande och skapa ett blickfång som imponerar!""",
                review_average=3.7,
                number_of_reviews=19,
                environmental_image_count=5,
                transparent_image_count=3,
                in_stock=True,
                matched_brand_products=[],
            ),
            RetailerProductScaffold(
                id="1a3eff7b-cf8f-4019-959d-e68983322707",
                name="KENYA Matbord",
                gtin="7350133230725",
                retailer={
                    "name": "Trademax",
                    "country": "SE",
                    "id": "07da79c0-995c-46e6-ae7b-26b5663afab5",
                },
                country="DK",
                price_standard=10350,
                currency="DKK",
                margin=0.25,
                retailer_images_count=3,
                client_images_count=5,
                title_matching_score=0.75,
                sku="9525-244",
                wholesale_price=8230,
                popularity_index=4,
                description="""
                    Det ovala matbordet Kenya passar till altanen, uteplatsen och trädgården. Bordet 
                    rymmer sex stycken sittplatser och är perfekt till en somrig middagsbjudning. Produkten är producerad 
                    i  tåligt teak-material. Skötselråd: Våra teakmöbler produceras av certifierad teak som är odlad för 
                    ändamålet och inte skövlade från ömtålig regnskog. Som ett av de tåligaste träslagen innehåller teak 
                    mycket olja som sedvanligt behövs för att inte materialet ska spricka. Eftersom träslaget innehåller 
                    naturligt mycket behöver inte möblerna impregneras lika ofta.""",
                review_average=4.4,
                number_of_reviews=32,
                environmental_image_count=5,
                transparent_image_count=3,
                in_stock=True,
                matched_brand_products=[],
            ),
        ],
    )

    offset: int = Field(description="How many items we skipped", example=100)
    count: int = Field(description="The number of offers returned", example=20)
    total_count: int = Field(
        description="The total number of available offers", example=8121
    )


class MatchedRetailerProductCategoryScaffold(BaseModel):
    id: Union[str, uuid.UUID]
    full_name: str
    url: str

    class Config:
        orm_mode = True


class GenericProductImageScaffold(BaseModel):
    id: Union[uuid.UUID, str] = Field(description="The id of the image")
    url: str = Field(description="The url of the image")
    image_hash: str = Field(description="The computed hash of the image")

    class Config:
        orm_mode = True


class RetailerToBrandImageMatchScaffold(BaseModel):
    brand_image_id: Union[uuid.UUID, str] = Field(
        description="The id of the matched brand image"
    )

    class Config:
        orm_mode = True


class BrandProductImageScaffold(GenericProductImageScaffold):
    pass


class RetailerProductImageScaffold(GenericProductImageScaffold):
    matched_brand_images: List[RetailerToBrandImageMatchScaffold] = Field(
        description="List of matching brand images"
    )


class MatchedRetailerProductScaffold(BaseRetailerProductScaffold):
    """
    This is the information of the retailer product sent together with a brand product, and not on its own.
    """

    category: MatchedRetailerProductCategoryScaffold
    processed_images: List[RetailerProductImageScaffold] = Field(
        description="The images set by the retailer"
    )

    class Config:
        orm_mode = True


class BrandProductMatchesScaffold(BaseModel):
    matches: List[MatchedRetailerProductScaffold]

    class Config:
        orm_mode = True


class BrandKeywordsScaffold(BaseModel):
    title_keywords: List[List[str]] = Field(description="The actual list of keywords")
    description_keywords: List[List[str]] = Field(
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
