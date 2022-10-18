from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import initialize_app
from jose import jwt, JWTError

from app.schemas.auth import TokenData

firebase_app = initialize_app()
JWT_SECRET_KEY = "ba3f8bc7627f332af25174ddf4bc8765a31d82d160238176dfe411abf0a21916"
JWT_ALGORITHM = "HS256"


def get_user_id(
    credential: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> TokenData:
    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication is needed",
            headers={"WWW-Authenticate": 'Bearer error="invalid token"'}
        )

    try:
        token = credential.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return TokenData(**payload['data'])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
