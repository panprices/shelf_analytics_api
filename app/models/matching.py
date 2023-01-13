import enum

from sqlalchemy import ForeignKey, Column, Enum, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.mixins import UpdatableMixin, UUIDPrimaryKeyMixin


class MatchingType(enum.Enum):
    gtin_join = object()
    gtin_search = object()
    image = object()


class MatchingCertaintyType(enum.Enum):
    auto_high_confidence = object()
    manual_input = object()
    auto_low_confidence = object()
    not_match = object()


class ProductMatching(Base, UUIDPrimaryKeyMixin, UpdatableMixin):
    __tablename__ = "product_matching"

    brand_product_id = Column(UUID(as_uuid=True), ForeignKey("brand_product.id"))
    retailer_product_id = Column(UUID(as_uuid=True), ForeignKey("retailer_product.id"))
    type = Column(Enum(MatchingType))
    image_score = Column(Float)
    text_score = Column(Float)
    certainty = Column(Enum(MatchingCertaintyType))

    brand_product = relationship(
        "BrandProduct", back_populates="matched_retailer_products"
    )
    retailer_product = relationship(
        "RetailerProduct", back_populates="matched_brand_products"
    )
    image_matches = relationship("ImageMatching", back_populates="product_matching")

    @hybrid_property
    def is_matched(self):
        return self.certainty not in [
            MatchingCertaintyType.auto_low_confidence,
            MatchingCertaintyType.not_match,
        ]


class ImageMatching(Base, UUIDPrimaryKeyMixin, UpdatableMixin):
    __tablename__ = "image_matching"

    product_matching_id = Column(UUID(as_uuid=True), ForeignKey("product_matching.id"))
    brand_image_id = Column(UUID(as_uuid=True), ForeignKey("brand_image.id"))
    retailer_image_id = Column(UUID(as_uuid=True), ForeignKey("retailer_image.id"))
    distance = Column(Float)
    model_certainty = Column(Float)

    product_matching = relationship("ProductMatching", back_populates="image_matches")
    brand_image = relationship("BrandImage", back_populates="matched_retailer_images")
    retailer_image = relationship(
        "RetailerImage", back_populates="matched_brand_images"
    )
