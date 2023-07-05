from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import initialize_app
from jose import jwt, JWTError
from pydantic import ValidationError

from app.config.settings import get_settings
from app.schemas.auth import TokenData

firebase_app = initialize_app(
    options={"serviceAccountId": "panprices@appspot.gserviceaccount.com"}
)
JWT_SECRET_KEY = get_settings().jwt_secret
JWT_ALGORITHM = "HS256"


def get_user_data(
    credential: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> TokenData:
    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication is needed",
            headers={"WWW-Authenticate": 'Bearer error="invalid token"'},
        )

    try:
        token = credential.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return TokenData(**payload["data"])
    except (JWTError, ValidationError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
