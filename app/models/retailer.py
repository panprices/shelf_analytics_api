import enum
from typing import List

from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Table,
    Integer,
    Enum,
    BigInteger,
    Float,
    Boolean,
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
)

retailer_brand_association_table = Table(
    "retailer_to_brand_mapping",
    Base.metadata,
    Column("retailer_id", ForeignKey("retailer.id"), primary_key=True),
    Column("brand_id", ForeignKey("brand.id"), primary_key=True),
)


class Retailer(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "retailer"

    name = Column(String)
    url = Column(String)
    country = Column(String)

    brands = relationship(
        "Brand", secondary=retailer_brand_association_table, back_populates="retailers"
    )
    categories = relationship("RetailerCategory", back_populates="retailer")
    products = relationship("RetailerProduct", back_populates="retailer")


class RetailerCategory(Base, UUIDPrimaryKeyMixin, GenericCategoryMixin):
    __tablename__ = "retailer_category"

    retailer_id = Column(UUID(as_uuid=True), ForeignKey("retailer.id"))

    retailer = relationship("Retailer", back_populates="categories")
    products = relationship("RetailerProduct", back_populates="category")


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


class RetailerImage(Base, UUIDPrimaryKeyMixin, ImageMixin):
    __tablename__ = "retailer_image"

    retailer_product_id = Column(UUID(as_uuid=True), ForeignKey("retailer_product.id"))

    retailer_product = relationship("RetailerProduct", back_populates="images")
    matched_brand_images = relationship(
        "ImageMatching", back_populates="retailer_image"
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

    category_id = Column(UUID(as_uuid=True), ForeignKey("retailer_category.id"))
    category = relationship("RetailerCategory", back_populates="products")

    retailer_id = Column(UUID(as_uuid=True), ForeignKey("retailer.id"))
    retailer = relationship("Retailer", back_populates="products", lazy="joined")

    matched_brand_products = relationship(
        "ProductMatching", back_populates="retailer_product"
    )
    images: List[RetailerImage] = relationship(
        "RetailerImage", back_populates="retailer_product"
    )
    historical_data = relationship("RetailerProductHistory", back_populates="product")

    @hybrid_property
    def retailer_images_count(self):
        return len(self.images)

    @hybrid_property
    def client_images_count(self):
        if not self.matched_brand_products:
            return 0

        return len(self.matched_brand_products[0].brand_product.images)

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
        return self.price / 100

    @hybrid_property
    def processed_images(self):
        return [i for i in self.images if i.image_hash is not None]
