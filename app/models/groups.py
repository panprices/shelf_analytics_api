from sqlalchemy import Column, String, Table, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models import UpdatableMixin, UUIDPrimaryKeyMixin
from app.models.mappings import product_group_assignation_table


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
