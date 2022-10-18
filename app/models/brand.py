import uuid

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.retailer import retailer_brand_association_table


class Brand(Base):
    __tablename__ = "brand"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    url = Column(String)

    categories = relationship("BrandCategory")
    retailers = relationship("Retailer", secondary=retailer_brand_association_table, back_populates='brands')


class BrandCategory(Base):
    __tablename__ = "brand_category"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    """
    There is an issue with detecting deep changes in JSON objects through ORM. 
    
    See there: 
    https://amercader.net/blog/beware-of-json-fields-in-sqlalchemy/
    
    For the initial implementation we chose to disregard this issue since the API is going to read this values, 
    apply transformation and pass them to the FE project, without writing changes to the objects themselves. 
    
    The data comes from the underlying services (scraping, matching, etc.) 
    """
    category_tree = Column(JSONB)
    url = Column(String)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brand.id"))
