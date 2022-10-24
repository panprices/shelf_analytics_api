from typing import TypeVar

from requests import Session

from app.crud import get_retailers, get_brand_categories, get_countries
from app.schemas.filters import GlobalFilter


T = TypeVar("T", bound=GlobalFilter)


def preprocess_global_filters(db: Session, brand_id: str, global_filter: T) -> T:
    if not global_filter.retailers:
        global_filter.retailers = [r.id.hex for r in get_retailers(db, brand_id)]

    if not global_filter.categories:
        global_filter.categories = [c.id.hex for c in get_brand_categories(db, brand_id)]

    if not global_filter.countries:
        global_filter.countries = [c[0] for c in get_countries(db, brand_id)]

    return global_filter
