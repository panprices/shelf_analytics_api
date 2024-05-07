from hashlib import pbkdf2_hmac

from cachetools import cached, TTLCache
from sqlalchemy import func
from sqlalchemy.orm import Session
from structlog import get_logger

from app import crud
from app.config.settings import get_settings
from app.models import ApiKey
from app.schemas.auth import TokenData

logger = get_logger()


# We have a secret salt loaded from google cloud secrets, but we also add a hardcoded one
# This means that an eventual bad actor will have to have access both to the code and to our google cloud secrets
API_KEYS_HARDCODED_SALT = """3Gp}Z'-oP[1"]0{M"-INWI"6q~FQds{J"""


def mask_api_key(api_key: str) -> str:
    return api_key[0:8] + "..." + api_key[-4:]


def hash_api_key(api_key: str) -> bytes:
    settings = get_settings()

    return pbkdf2_hmac(
        "sha256",
        api_key.encode(),
        f"{settings.api_keys_secret_salt}:{API_KEYS_HARDCODED_SALT}".encode(),
        50_000,
    )


def save_api_key(db: Session, key: str, user: TokenData):
    hashed_api_key = crud.hash_api_key(key)
    masked_key = crud.mask_api_key(key)
    api_key_obj = ApiKey(
        client_id=user.client, hashed_key=hashed_api_key, masked_key=masked_key
    )
    db.add(api_key_obj)
    db.commit()


def get_api_keys(db: Session, user: TokenData):
    return db.query(ApiKey).filter(ApiKey.client_id == user.client).all()


def delete_api_key(db: Session, key_id: str, user: TokenData):
    deleted_count = (
        db.query(ApiKey)
        .filter(ApiKey.id == key_id)
        .filter(ApiKey.client_id == user.client)
        .delete()
    )
    db.commit()
    return deleted_count


@cached(cache=TTLCache(maxsize=128, ttl=600))
def check_api_key(db: Session, api_key_header: str):
    """
    Check if the api key is valid.

    The result of this function is cached for 10 minutes to avoid unnecessary queries to the database.

    :param db:
    :param api_key_header:
    :return:
    """
    hashed_key = hash_api_key(api_key_header)
    api_key_entry = (
        db.query(ApiKey)
        .filter_by(hashed_key=hashed_key)
        .filter(ApiKey.expires_at > func.current_date())
        .first()
    )
    if not api_key_entry:
        return None
    # Good practice to keep track of the keys that are being used
    logger.info(f"API key {api_key_entry.id} used")
    api_key_entry.last_used_at = func.current_timestamp()
    db.commit()

    return api_key_entry
