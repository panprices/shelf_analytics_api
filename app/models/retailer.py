import enum

from sqlalchemy import Column, String, ForeignKey, Table, Integer, Enum, BigInteger, Float, Boolean, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, column_property

from app.database import Base
from app.models.mixins import GenericProductMixin, UpdatableMixin, GenericCategoryMixin

retailer_brand_association_table = Table(
    "retailer_to_brand_mapping",
    Base.metadata,
    Column("retailer_id", ForeignKey("retailer.id"), primary_key=True),
    Column("brand_id", ForeignKey("brand.id"), primary_key=True)
)


class Retailer(Base):
    __tablename__ = "retailer"

    name = Column(String)
    url = Column(String)
    country = Column(String)

    brands = relationship("Brand", secondary=retailer_brand_association_table, back_populates='retailers')
    categories = relationship("RetailerCategory", back_populates="retailer")
    products = relationship("RetailerProduct", back_populates="retailer")


class RetailerCategory(Base, GenericCategoryMixin):
    __tablename__ = "retailer_category"

    retailer_id = Column(UUID, ForeignKey("retailer.id"))

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


class RetailerImage(Base):
    __tablename__ = "retailer_image"

    url = Column(String)
    retailer_product_id = Column(UUID, ForeignKey("retailer_product.id"))

    retailer_product = relationship("RetailerProduct", back_populates="images")


class RetailerProduct(Base, GenericProductMixin, UpdatableMixin):
    __tablename__ = "retailer_product"

    popularity_index = Column(Integer)
    availability = Column(Enum(AvailabilityStatus))
    price = Column(BigInteger)
    currency = Column(String)
    reviews = Column(JSONB)
    review_average = Column(Float)
    is_discounted = Column(Boolean)
    original_price = Column(BigInteger)

    category_id = Column(UUID, ForeignKey("retailer_category.id"))
    category = relationship("RetailerCategory", back_populates="products")

    retailer_id = Column(UUID, ForeignKey("retailer.id"))
    retailer = relationship("Retailer", back_populates="products", lazy="joined")

    matched_brand_products = relationship("ProductMatching", back_populates="retailer_product")
    images = relationship("RetailerImage", back_populates="retailer_product")

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
        return self.availability in [AvailabilityStatus.in_stock,
                                     AvailabilityStatus.in_store_only,
                                     AvailabilityStatus.online_only,
                                     AvailabilityStatus.limited_availability,
                                     AvailabilityStatus.discounted]

    @hybrid_property
    def number_of_reviews(self) -> int:
        return self.reviews.get('reviewCount', 0)

    @hybrid_property
    def country(self) -> str:
        return self.retailer.country
