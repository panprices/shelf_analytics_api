import uuid
from typing import List, Optional, Union

from pydantic import BaseModel, Field

from app.schemas.general import NamedRetailer


class BrandCategoryScaffold(BaseModel):
    url: str = Field(description="The url to the category",
                     example="https://www.venturedesign.se/utemobler/bord/cafbord")
    id: Union[str, uuid.UUID] = Field(description="The id of the category",
                                      example="31ef6c6c-be2d-4478-a948-10a66dad1d2a")

    class Config:
        orm_mode = True


class MatchedBrandProductScaffold(BaseModel):
    category: BrandCategoryScaffold

    class Config:
        orm_mode = True


class MatchScaffold(BaseModel):
    brand_product: MatchedBrandProductScaffold

    class Config:
        orm_mode = True


class ProductScaffold(BaseModel):

    def __int__(self, **kwargs):
        super(ProductScaffold).__init__(**kwargs)

    """
    Holds the *scaffold* data for a product, meaning only the high level data directly visible in the data table,
    plus the product id to be used for further querying.
    """

    id: Union[str, uuid.UUID] = Field(
        description="""
        UUID identifying the product uniquely. This id identifies the product, not the offer. 
        To fetch the same offer a query should include both this id and the retailer
        """,
        example="31ef6c6c-be2d-4478-a948-10a66dad1d2a"
    )
    name: str = Field(
        description="The product name as defined by the retailer",
        example="Matgrupp Copenhagen med Matstol Comfort"
    )
    gtin: Optional[str] = Field(
        description="The GTIN associated by the customer to the product",
        example="7350133230816"
    )
    retailer: NamedRetailer = Field(
        description="The retailer selling this product",
        example="Trademax"
    )
    country: str = Field(
        description="The code representation of a country",
        example="SE"
    )
    price: float = Field(
        description="The price scraped at the retailer",
        example=3201
    )
    currency: str = Field(
        description="The currency in which the product is being sold",
        examples={
            'sweden': "SEK",
            'eu': "EUR"
        }
    )
    margin: Optional[float] = Field(
        description="The margin of profit obtained by the retailer on this product",
        example=0.56
    )
    retailer_images_count: int = Field(
        description="The number of images the retailer shows",
        example=6
    )
    client_images_count: int = Field(
        description="The number of images recommended by the client",
        example=9
    )
    title_matching_score: Optional[float] = Field(
        description="A score showing how similar the retailer's title is to the title from the client",
        example=0.67
    )
    sku: Optional[str] = Field(
        description="The SKU assigned by the client",
        example="16052-101"
    )
    wholesale_price: Optional[float] = Field(
        description="The price at which the client sells the item to the retailer (the value captured by the brand)",
        example=2602
    )
    popularity_index: int = Field(
        description="The ranking of this product inside its leaf category at the retailer",
        example=13
    )
    description: str = Field(
        description="Meta hehe. Kidding. This is the description displayed by the retailer for this product",
        example="Imagine a very long description here"
    )
    review_average: float = Field(
        description="The rating of this product, average of the scores from the reviews the product received.",
        example=3.7
    )
    number_of_reviews: int = Field(
        description="Count of reviews",
        example=19
    )
    in_stock: bool = Field(
        default=True,
        description="Whether the product is in stock at the retailer",
        example=True
    )
    matched_brand_products: List[MatchScaffold] = Field(
        description="List of matching candidates"
    )

    class Config:
        orm_mode = True


class ProductPage(BaseModel):
    """
    Holds the data for a page of products as showed on the data page in FE.
    """
    products: List[ProductScaffold] = Field(
        description="The list of products",
        example=[
            ProductScaffold(
                id="31ef6c6c-be2d-4478-a948-10a66dad1d2a",
                name="Matgrupp Copenhagen med Matstol Comfort",
                gtin="7350133230816",
                retailer={
                    "id": "07da79c0-995c-46e6-ae7b-26b5663afab5",
                    "name": "Trademax"
                },
                country="SE",
                price=3201,
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
                in_stock=True,
                matched_brand_products=[]
            ),
            ProductScaffold(
                id="1a3eff7b-cf8f-4019-959d-e68983322707",
                name="KENYA Matbord",
                gtin="7350133230725",
                retailer={
                    "name": "Trademax",
                    "id": "07da79c0-995c-46e6-ae7b-26b5663afab5"
                },
                country="DK",
                price=10350,
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
                in_stock=True,
                matched_brand_products=[]
            )
        ]
    )

    offset: int = Field(description="How many items we skipped", example=100)
    count: int = Field(description="The number of offers returned", example=20)
    total_count: int = Field(description="The total number of available offers", example=8121)
