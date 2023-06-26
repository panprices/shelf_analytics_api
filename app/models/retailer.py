import enum
from typing import List

from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Integer,
    Enum,
    BigInteger,
    Float,
    Boolean,
    DateTime,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.mixins import (
    GenericProductMixin,
    UpdatableMixin,
    GenericCategoryMixin,
    UUIDPrimaryKeyMixin,
    HistoricalMixin,
    ImageMixin,
    ImageTypeMixin,
)


class CountryToLanguage(Base):
    __tablename__ = "country_to_language"

    country = Column(String, primary_key=True, unique=True)
    language = Column(String, primary_key=True)


class Retailer(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "retailer"

    name = Column(String)
    url = Column(String)
    country = Column(String, ForeignKey("country_to_language.country"))

    brands = relationship("RetailerBrandAssociation", back_populates="retailer")
    categories = relationship("RetailerCategory", back_populates="retailer")
    products = relationship("RetailerProduct", back_populates="retailer")

    country_to_language = relationship("CountryToLanguage")


class RetailerCategory(Base, UUIDPrimaryKeyMixin, GenericCategoryMixin):
    __tablename__ = "retailer_category"

    retailer_id = Column(UUID(as_uuid=True), ForeignKey("retailer.id"))

    retailer = relationship("Retailer", back_populates="categories")
    products = relationship(
        "RetailerProduct",
        foreign_keys="RetailerProduct.popularity_category_id",
        back_populates="category",
    )


class AvailabilityStatus(enum.Enum):
    """
    The values of the enum are used by the database according to the documentation:
    https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.Enum

    So we care only about the names of the elements.
    Because we have no use for the values in the middleware either, we initialize each one to a new blank object
    according to: https://docs.python.org/3/library/enum.html
    """

    back_order = object()
    discounted = object()
    in_stock = object()
    in_store_only = object()
    limited_availability = object()
    online_only = object()
    out_of_stock = object()
    pre_order = object()
    pre_sale = object()
    sold_out = object()

    @staticmethod
    def available_status_list() -> List["AvailabilityStatus"]:
        return [
            AvailabilityStatus.in_stock,
            AvailabilityStatus.in_store_only,
            AvailabilityStatus.online_only,
            AvailabilityStatus.limited_availability,
            AvailabilityStatus.discounted,
        ]


class RetailerImageType(Base, ImageTypeMixin):
    __tablename__ = "retailer_image_types"

    image_id = Column(
        UUID(as_uuid=True), ForeignKey("retailer_image.id"), primary_key=True
    )

    retailer_image = relationship("RetailerImage", back_populates="type_predictions")


class RetailerImage(Base, UUIDPrimaryKeyMixin, ImageMixin):
    __tablename__ = "retailer_image"

    retailer_product_id = Column(UUID(as_uuid=True), ForeignKey("retailer_product.id"))

    retailer_product = relationship("RetailerProduct", back_populates="images")
    matched_brand_images = relationship(
        "ImageMatching", back_populates="retailer_image"
    )
    type_predictions = relationship(
        "RetailerImageType", back_populates="retailer_image"
    )


class RetailerProductHistory(Base, HistoricalMixin):
    __tablename__ = "retailer_product_time_series"

    product_id = Column(
        UUID(as_uuid=True), ForeignKey("retailer_product.id"), primary_key=True
    )
    price = Column(BigInteger)
    currency = Column(String)
    availability = Column(Enum(AvailabilityStatus))

    product = relationship("RetailerProduct", back_populates="historical_data")

    @hybrid_property
    def price_standard(self):
        if not self.price:
            return self.price
        return self.price / 100


class MockRetailerProductGridItem(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "__mocked__"
    url = Column(String)
    name = Column(String)
    description = Column(String)
    specifications = Column(JSONB)
    sku = Column(String)
    gtin = Column(String)

    retailer_name = Column(String)
    country = Column(String)
    popularity_index = Column(Integer)
    availability = Column(Enum(AvailabilityStatus))
    price_standard = Column(Float)
    currency = Column(String)
    review_average = Column(Float)
    number_of_reviews = Column(Integer)
    retailer_images_count = Column(Integer)
    client_images_count = Column(Integer)
    title_score = Column(Float)
    description_score = Column(Float)
    specs_score = Column(Float)
    text_score = Column(Float)
    image_score = Column(Float)
    content_score = Column(Float)
    transparent_images_count = Column(Integer)
    environmental_images_count = Column(Integer)
    wholesale_price = Column(Float)
    in_stock = Column(Boolean)
    is_discounted = Column(Boolean)
    original_price = Column(BigInteger)
    matched_brand_product_id = Column(String)
    brand_in_stock = Column(Boolean)
    available_at_retailer = Column(Boolean)
    retailer_category_name = Column(String)
    original_price_standard = Column(Float)
    fetched_at = Column(DateTime)
    created_at = Column(DateTime)
    brand_sku = Column(String)
    msrp_standard = Column(Float)
    msrp_currency = Column(String)
    price_deviation = Column(Float)
    wholesale_price_standard = Column(Float)
    wholesale_currency = Column(String)
    markup_factor = Column(Float)
    category_page_number = Column(Integer)
    category_pages_count = Column(Integer)
    category_products_count = Column(Integer)


class RetailerProduct(Base, UUIDPrimaryKeyMixin, GenericProductMixin, UpdatableMixin):
    __tablename__ = "retailer_product"

    popularity_index = Column(Integer)
    availability = Column(Enum(AvailabilityStatus))
    price = Column(BigInteger)
    currency = Column(String)
    reviews = Column(JSONB)
    review_average = Column(Float)
    is_discounted = Column(Boolean)
    original_price = Column(BigInteger)
    fetched_at = Column(DateTime)
    created_at = Column(DateTime)

    # category_id = Column(UUID(as_uuid=True), ForeignKey("retailer_category.id"))
    # category = relationship("RetailerCategory", back_populates="products")
    popularity_category_id = Column(
        UUID(as_uuid=True), ForeignKey("retailer_category.id")
    )
    category = relationship(
        "RetailerCategory",
        back_populates="products",
    )

    retailer_id = Column(UUID(as_uuid=True), ForeignKey("retailer.id"))
    retailer = relationship("Retailer", back_populates="products", lazy="joined")

    matched_brand_products = relationship(
        "ProductMatching",
        back_populates="retailer_product",
    )
    images: List[RetailerImage] = relationship(
        "RetailerImage", back_populates="retailer_product"
    )
    historical_data = relationship("RetailerProductHistory", back_populates="product")

    @hybrid_property
    def retailer_images_count(self):
        return len(self.images)

    @hybrid_property
    def in_stock(self) -> bool:
        return self.availability in AvailabilityStatus.available_status_list()

    @hybrid_property
    def number_of_reviews(self) -> int:
        return self.reviews.get("reviewCount", 0)

    @hybrid_property
    def country(self) -> str:
        return self.retailer.country

    @hybrid_property
    def price_standard(self):
        return self.price / 100 if self.price else None
