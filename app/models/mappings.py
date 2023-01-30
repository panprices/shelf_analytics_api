from sqlalchemy import Column, ForeignKey, Table

from app.database import Base

retailer_brand_association_table = Table(
    "retailer_to_brand_mapping",
    Base.metadata,
    Column("retailer_id", ForeignKey("retailer.id"), primary_key=True),
    Column("brand_id", ForeignKey("brand.id"), primary_key=True),
)


product_group_assignation_table = Table(
    "product_group_assignation",
    Base.metadata,
    Column("product_id", ForeignKey("brand_product.id"), primary_key=True),
    Column("product_group_id", ForeignKey("product_group.id"), primary_key=True),
)
