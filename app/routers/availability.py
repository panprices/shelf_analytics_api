from fastapi import APIRouter

from app.definitions.filters import GlobalFilter
from app.definitions.scores import HistoricalScore
from app.tags import TAG_AVAILABILITY, TAG_OVERVIEW

router = APIRouter(prefix="/availability")


@router.post("/score", tags=[TAG_AVAILABILITY, TAG_OVERVIEW], response_model=HistoricalScore)
def get_overall_availability_score(client_id: str, global_filter: GlobalFilter):
    """
    Returns the overall availability score corresponding to the applied filters. This is the same as the score that
    is visible when looking at the overview page in the FE.
    """
    pass


@router.post("/score/image", tags=[TAG_AVAILABILITY], response_model=HistoricalScore)
def get_image_compliance_score(client_id: str, global_filter: GlobalFilter):
    """
    Returns the image compliance score corresponding to the applied filters.
    """
    pass


@router.post("/score/text", tags=[TAG_AVAILABILITY], response_model=HistoricalScore)
def get_text_compliance_score(client_id: str, global_filter: GlobalFilter):
    """
    Returns the text compliance score corresponding to the applied filters.
    """
    pass
