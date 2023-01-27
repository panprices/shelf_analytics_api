from sqlalchemy import Column, String, Table, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models import UpdatableMixin, UUIDPrimaryKeyMixin


product_group_assignation_table = Table(
    "product_group_assignation",
    Base.metadata,
    Column("product_id", ForeignKey("brand_product.id"), primary_key=True),
    Column("brand_id", ForeignKey("brand.id"), primary_key=True),
)


class ProductGroup(Base, UUIDPrimaryKeyMixin, UpdatableMixin):
    __tablename__ = "product_group"

    name = Column(String)
    user_id = Column(String)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brand.id"))
    products = relationship(
        "BrandProduct",
        secondary=product_group_assignation_table,
        back_populates="groups",
    )
