import enum

from sqlalchemy import ForeignKey, Column, Enum, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.mixins import UpdatableMixin


class MatchingType(enum.Enum):
    gtin_join = object()
    gtin_search = object()
    image = object()


class MatchingCertaintyType(enum.Enum):
    auto_high_confidence = object()
    manual_input = object()
    auto_low_confidence = object()


class ProductMatching(Base, UpdatableMixin):
    __tablename__ = "product_matching"

    brand_product_id = Column(UUID(as_uuid=True), ForeignKey("brand_product.id"))
    retailer_product_id = Column(UUID(as_uuid=True), ForeignKey("retailer_product.id"))
    type = Column(Enum(MatchingType))
    image_score = Column(Float)
    text_score = Column(Float)
    certainty = Column(Enum(MatchingCertaintyType))

    brand_product = relationship("BrandProduct", back_populates="matched_retailer_products")
    retailer_product = relationship("RetailerProduct", back_populates="matched_brand_products")
