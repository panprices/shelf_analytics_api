from sqlalchemy import Column, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class RetailerBrandAssociation(Base):
    __tablename__ = "retailer_to_brand_mapping"

    retailer_id = Column(ForeignKey("retailer.id"), primary_key=True)
    brand_id = Column(ForeignKey("brand.id"), primary_key=True)
    shallow = Column(Boolean, default=False)

    retailer = relationship("Retailer", back_populates="brands")
    brand = relationship("Brand", back_populates="retailers")


product_group_assignation_table = Table(
    "product_group_assignation",
    Base.metadata,
    Column("product_id", ForeignKey("brand_product.id"), primary_key=True),
    Column("product_group_id", ForeignKey("product_group.id"), primary_key=True),
)
