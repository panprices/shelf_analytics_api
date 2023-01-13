from sqlalchemy import Column, ForeignKey, Table

from app.database import Base

retailer_brand_association_table = Table(
    "retailer_to_brand_mapping",
    Base.metadata,
    Column("retailer_id", ForeignKey("retailer.id"), primary_key=True),
    Column("brand_id", ForeignKey("brand.id"), primary_key=True),
)
