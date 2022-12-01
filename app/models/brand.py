from functools import reduce
from typing import List

from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.mixins import (
    GenericCategoryMixin,
    UpdatableMixin,
    GenericProductMixin,
    UUIDPrimaryKeyMixin,
    ImageMixin,
)
from app.models.retailer import retailer_brand_association_table
from app.utils.reducers import _reduce_to_dict_by_key


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


class BrandImage(Base, UUIDPrimaryKeyMixin, ImageMixin):
    __tablename__ = "brand_image"

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
    images: List[BrandImage] = relationship("BrandImage", back_populates="product")
    category = relationship("BrandCategory", back_populates="products")

    @hybrid_property
    def processed_images(self):
        dict_by_hash = reduce(
            _reduce_to_dict_by_key(lambda t: t.image_hash),
            [i for i in self.images if i.image_hash is not None],
            {},
        )

        return [v[0] for v in dict_by_hash.values()]
