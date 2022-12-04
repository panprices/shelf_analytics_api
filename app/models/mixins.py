import enum
import uuid
from datetime import timedelta
from typing import List

from sqlalchemy import String, Column, DateTime, Enum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.hybrid import hybrid_property


class UpdatableMixin:
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class ImageType(enum.Enum):
    environmental = object()
    transparent = object()


class ImageMixin:
    image_hash = Column(String)
    url = Column(String)
    image_type = Column(Enum(ImageType))


class GenericProductMixin:
    url = Column(String)
    name = Column(String)
    description = Column(String)
    specifications = Column(JSONB)
    sku = Column(String)
    gtin = Column(String)
    images: List[ImageMixin] = Column()

    @hybrid_property
    def processed_images(self):
        return [i for i in self.images if i.image_hash is not None]

    @hybrid_property
    def environmental_images_count(self):
        return len([i for i in self.images if i.image_type == ImageType.environmental])

    @hybrid_property
    def transparent_images_count(self):
        return len([i for i in self.images if i.image_hash == ImageType.transparent])


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

    @hybrid_property
    def full_name(self) -> str:
        return " > ".join([p["name"] for p in self.category_tree])


class UUIDPrimaryKeyMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class HistoricalMixin:
    time = Column(DateTime, primary_key=True)

    @hybrid_property
    def time_as_date(self):
        return self.time.date()

    @hybrid_property
    def time_as_week(self):
        return self.time_as_date - timedelta(days=self.time_as_date.weekday())
