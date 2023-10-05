from typing import List

from sqlalchemy import Column, String, ForeignKey, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.mappings import (
    product_group_assignation_table,
)
from app.models.matching import ProductMatching
from app.models.mixins import (
    GenericCategoryMixin,
    UpdatableMixin,
    GenericProductMixin,
    UUIDPrimaryKeyMixin,
    ImageMixin,
    ImageTypeMixin,
)


class Brand(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "brand"

    name = Column(String)
    url = Column(String)

    categories = relationship("BrandCategory", back_populates="brand")
    retailers = relationship("RetailerBrandAssociation", back_populates="brand")
    products = relationship("BrandProduct", back_populates="brand")


class BrandCategory(Base, UUIDPrimaryKeyMixin, GenericCategoryMixin):
    __tablename__ = "brand_category"
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brand.id"))
    brand = relationship("Brand", back_populates="categories")
    products = relationship("BrandProduct", back_populates="category")
    category_tree = Column(JSONB)


class BrandImageType(Base, ImageTypeMixin):
    __tablename__ = "brand_image_types"

    image_id = Column(
        UUID(as_uuid=True), ForeignKey("brand_image.id"), primary_key=True
    )

    brand_image = relationship("BrandImage", back_populates="type_predictions")


class BrandImage(Base, UUIDPrimaryKeyMixin, ImageMixin):
    __tablename__ = "brand_image"

    is_obsolete = Column(Boolean)
    brand_product_id = Column(UUID(as_uuid=True), ForeignKey("brand_product.id"))
    temp_wrong = Column(Boolean)

    product = relationship("BrandProduct", back_populates="images")
    matched_retailer_images = relationship(
        "ImageMatching", back_populates="brand_image"
    )
    type_predictions = relationship("BrandImageType", back_populates="brand_image")


class BrandKeywords(Base):
    __tablename__ = "brand_keywords"

    product_id = Column(
        UUID(as_uuid=True), ForeignKey("brand_product.id"), primary_key=True
    )
    language = Column(String, primary_key=True)
    title_keywords = Column(JSONB)
    description_keywords = Column(JSONB)
    specs_keywords = Column(JSONB)

    product = relationship("BrandProduct", back_populates="keywords")


class MSRP(Base):
    __tablename__ = "msrp"

    brand_product_id = Column(
        UUID(as_uuid=True), ForeignKey("brand_product.id"), primary_key=True
    )
    currency = Column(String, primary_key=True)
    price = Column(Float)
    country = Column(String, primary_key=True)

    brand_product = relationship("BrandProduct", back_populates="msrp")

    @hybrid_property
    def price_standard(self):
        if not self.price:
            return self.price
        return self.price / 100


class MockBrandProductWithMarketPrices(Base):
    __tablename__ = "mock_brand_product_with_market_prices"

    brand_product_id = Column(
        UUID(as_uuid=True), ForeignKey("brand_product.id"), primary_key=True
    )
    name = Column(String)
    gtin = Column(String)
    sku = Column(String)
    msrp_standard = Column(Float)
    msrp_currency = Column(String)
    msrp_country = Column(String, primary_key=True)
    msrp_client_currency = Column(Float)
    image_id = Column(UUID(as_uuid=True))
    image_url = Column(String)
    offers = Column(JSONB)


class BrandProduct(Base, UUIDPrimaryKeyMixin, GenericProductMixin, UpdatableMixin):
    __tablename__ = "brand_product"

    brand_id = Column(UUID(as_uuid=True), ForeignKey("brand.id"))
    category_id = Column(UUID(as_uuid=True), ForeignKey("brand_category.id"))

    matched_retailer_products: List[ProductMatching] = relationship(
        "ProductMatching", back_populates="brand_product"
    )
    brand = relationship("Brand", back_populates="products")
    images: List[BrandImage] = relationship("BrandImage", back_populates="product")
    category = relationship("BrandCategory", back_populates="products")
    groups = relationship(
        "ProductGroup",
        secondary=product_group_assignation_table,
        back_populates="products",
    )
    msrp: List[MSRP] = relationship("MSRP", back_populates="brand_product")

    keywords: List[BrandKeywords] = relationship(
        "BrandKeywords", back_populates="product"
    )

    @hybrid_property
    def processed_images(self):
        return [i for i in self.images if i.image_hash is not None and not i.temp_wrong]
