import uuid

from sqlalchemy import String, Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID


class UpdatableMixin:
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class GenericProductMixin:
    url = Column(String)
    name = Column(String)
    description = Column(String)
    specifications = Column(JSONB)
    sku = Column(String)
    gtin = Column(String)


class GenericCategoryMixin:
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


class UUIDPrimaryKeyMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class HistoricalMixin:
    time = Column(DateTime, primary_key=True)
