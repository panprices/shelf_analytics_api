import random
import string
from typing import Optional, Union

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from firebase_admin import initialize_app
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from structlog import get_logger

from app import crud
from app.config.settings import get_settings
from app.database import get_db
from app.schemas.auth import TokenData, AuthMetadata

logger = get_logger()

firebase_app = initialize_app(
    options={"serviceAccountId": "panprices@appspot.gserviceaccount.com"}
)
JWT_SECRET_KEY = get_settings().jwt_secret
JWT_ALGORITHM = "HS256"


def __get_jwt_data(
    credential: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> Optional[TokenData]:
    if credential is None:
        return None

    try:
        token = credential.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return TokenData(**payload["data"])
    except (JWTError, ValidationError) as err:
        return None


def __get_api_key_data(
    api_key_header: Optional[str] = Security(
        APIKeyHeader(name="X-API-Key", auto_error=False)
    ),
    db: Session = Depends(get_db),
) -> Optional[AuthMetadata]:
    if not api_key_header:
        return None

    api_key_entry = crud.check_api_key(db, api_key_header)
    if api_key_entry is None:
        return None

    return AuthMetadata(client=api_key_entry.client_id)


def get_auth_data(
    jwt_data=Depends(__get_jwt_data),
    api_key_data=Depends(__get_api_key_data),
) -> Union[TokenData, AuthMetadata]:
    if jwt_data is None and api_key_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return jwt_data if jwt_data is not None else api_key_data


def get_logged_in_user_data(jwt_data=Depends(__get_jwt_data)):
    if jwt_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return jwt_data


def generate_api_key() -> str:
    return "loupe_" + "".join(
        [random.choice(string.ascii_letters + string.digits) for _ in range(48)]
    )
