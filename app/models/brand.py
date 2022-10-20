import uuid

from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.mixins import GenericCategoryMixin, UpdatableMixin, GenericProductMixin
from app.models.retailer import retailer_brand_association_table


class Brand(Base):
    __tablename__ = "brand"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    url = Column(String)

    categories = relationship("BrandCategory", back_populates="brand")
    retailers = relationship("Retailer", secondary=retailer_brand_association_table, back_populates='brands')
    products = relationship("BrandProduct", back_populates="brand")


class BrandCategory(Base, GenericCategoryMixin):
    __tablename__ = "brand_category"
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brand.id"))
    brand = relationship("Brand", back_populates="categories")
    products = relationship("BrandProduct", back_populates="category")


class BrandImage(Base):
    __tablename__ = "brand_image"

    url = Column(String)
    is_obsolete = Column(Boolean)
    brand_product_id = Column(UUID, ForeignKey("brand_product.id"))

    product = relationship("BrandProduct", back_populates="images")


class BrandProduct(Base, GenericProductMixin, UpdatableMixin):
    __tablename__ = "brand_product"

    brand_id = Column(UUID, ForeignKey("brand.id"))
    category_id = Column(UUID, ForeignKey("brand_category.id"))

    matched_retailer_products = relationship("ProductMatching", back_populates="brand_product")
    brand = relationship("Brand", back_populates="products")
    images = relationship("BrandImage", back_populates="product")
    category = relationship("BrandCategory", back_populates="products")

