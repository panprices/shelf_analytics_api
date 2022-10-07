from fastapi import APIRouter

from app.definitions.filters import GlobalFilter
from app.definitions.general import TrackedRetailerPool, ProductCategorisation, ActiveMarket
from app.definitions.scores import HistoricalScore
from app.tags import TAG_OVERVIEW, TAG_FILTERING

router = APIRouter(prefix="")


@router.post("/score", tags=[TAG_OVERVIEW], response_model=HistoricalScore)
def get_overall_scores(client_id: str, global_filter: GlobalFilter):
    """
    Returns the overall score corresponding to the applied filters.

    This same method can be used for showing the breakdown values at the bottom of the overview page. The idea is that
    method would be called with filters corresponding to the displayed value, for example a filter that only selects
    Sweden as a country, or only selects Trademax as a retailer, etc.
    """
    pass


@router.get("/countries", tags=[TAG_OVERVIEW, TAG_FILTERING], response_model=ActiveMarket)
def get_countries(client_id: str):
    pass


@router.get("/retailers", tags=[TAG_OVERVIEW, TAG_FILTERING], response_model=TrackedRetailerPool)
def get_retailers(client_id: str):
    pass


@router.get("/categories", tags=[TAG_OVERVIEW, TAG_FILTERING], response_model=ProductCategorisation)
def get_categories(client_id: str):
    pass
