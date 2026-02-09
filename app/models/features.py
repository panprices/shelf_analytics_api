from sqlalchemy import Column, ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ExtraFeaturesRegistry(Base):
    __tablename__ = "extra_features_registry"

    client_id = Column(UUID(as_uuid=True), ForeignKey("brand.id"), primary_key=True)
    feature_name = Column(String, primary_key=True)
    enabled = Column(Boolean, nullable=False)
