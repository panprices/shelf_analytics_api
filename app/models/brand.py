from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.mixins import (
    GenericCategoryMixin,
    UpdatableMixin,
    GenericProductMixin,
    UUIDPrimaryKeyMixin,
)
from app.models.retailer import retailer_brand_association_table


class Brand(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "brand"

    name = Column(String)
    url = Column(String)

    categories = relationship("BrandCategory", back_populates="brand")
    retailers = relationship(
        "Retailer", secondary=retailer_brand_association_table, back_populates="brands"
    )
    products = relationship("BrandProduct", back_populates="brand")


class BrandCategory(Base, UUIDPrimaryKeyMixin, GenericCategoryMixin):
    __tablename__ = "brand_category"
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brand.id"))
    brand = relationship("Brand", back_populates="categories")
    products = relationship("BrandProduct", back_populates="category")


class BrandImage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "brand_image"

    url = Column(String)
    is_obsolete = Column(Boolean)
    brand_product_id = Column(UUID(as_uuid=True), ForeignKey("brand_product.id"))

    product = relationship("BrandProduct", back_populates="images")
    matched_retailer_images = relationship(
        "ImageMatching", back_populates="brand_image"
    )


class BrandProduct(Base, UUIDPrimaryKeyMixin, GenericProductMixin, UpdatableMixin):
    __tablename__ = "brand_product"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brand.id"))
    category_id = Column(UUID(as_uuid=True), ForeignKey("brand_category.id"))

    matched_retailer_products = relationship(
        "ProductMatching", back_populates="brand_product"
    )
    brand = relationship("Brand", back_populates="products")
    images = relationship("BrandImage", back_populates="product")
    category = relationship("BrandCategory", back_populates="products")
