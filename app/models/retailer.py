import uuid

from sqlalchemy import Column, String, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


retailer_brand_association_table = Table(
    "retailer_to_brand_mapping",
    Base.metadata,
    Column("retailer_id", ForeignKey("retailer.id"), primary_key=True),
    Column("brand_id", ForeignKey("brand.id"), primary_key=True)
)


class Retailer(Base):
    __tablename__ = "retailer"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    url = Column(String)
    country = Column(String)

    brands = relationship("Brand", secondary=retailer_brand_association_table, back_populates='retailers')
