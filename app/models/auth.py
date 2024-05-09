from sqlalchemy import ForeignKey, Column, DateTime, String, FetchedValue
from sqlalchemy.dialects.postgresql import UUID, BYTEA

from app.database import Base
from app.models import UUIDPrimaryKeyMixin


class ApiKey(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "api_key"

    client_id = Column(UUID(as_uuid=False), ForeignKey("brand.id"))
    name = Column(String, nullable=False)
    hashed_key = Column(BYTEA, nullable=False)
    encrypted_key = Column(BYTEA, nullable=False)
    masked_key = Column(String, nullable=False)

    created_at = Column(DateTime, nullable=False, server_default=FetchedValue())
    last_used_at = Column(DateTime, nullable=False, server_default=FetchedValue())
