from typing import List

from sqlalchemy.orm import Session

from app.models.features import ExtraFeaturesRegistry


def get_extra_features(db: Session, client_id: str) -> List[ExtraFeaturesRegistry]:
    return (
        db.query(ExtraFeaturesRegistry)
        .filter(ExtraFeaturesRegistry.client_id == client_id)
        .all()
    )
