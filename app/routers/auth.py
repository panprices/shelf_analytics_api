from datetime import datetime, timedelta

import fastapi
import requests
from fastapi import Depends, Response, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth
from jose import jwt
from starlette import status

from app.config.settings import get_settings, Settings
from app.definitions.auth import AuthenticationRequest, AuthenticationResponse, TokenData
from app.security import firebase_app, JWT_ALGORITHM, JWT_SECRET_KEY

router = fastapi.APIRouter(prefix="/authenticate")
rest_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"


@router.post("/withEmailAndPassword", tags=["auth"], response_model=AuthenticationResponse)
def authenticate(user: AuthenticationRequest,
                 response: Response,
                 settings: Settings = Depends(get_settings)):
    """
    This endpoint can be directly used with the credentials (email + password)
    """

    firebase_response = requests.post(
        rest_api_url + "?key=" + settings.firebase_api_key,
        data={
            "email": user.email,
            "password": user.password,
            "returnSecureToken": True
        })
    if firebase_response.status_code != 200:
        response.status_code = firebase_response.status_code
        return AuthenticationResponse(success=False)

    uid = auth.get_user_by_email(user.email, app=firebase_app).uid
    token_data = TokenData(
        uid=uid, client="TODO", roles=[]
    )

    token = jwt.encode({
        "data": token_data.dict(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }, JWT_SECRET_KEY, JWT_ALGORITHM)

    return AuthenticationResponse(jwt=token, success=True)


@router.post("/withFirebaseToken", tags=["auth"], response_model=AuthenticationResponse)
def authenticate_with_firebase_token(
    credential: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
):
    """
    This method may be used if we are already logged into firebase through the frontend, so we use firebase's token
    to generate a backend token.

    Inspired by: https://stackoverflow.com/questions/72200552/fastapi-firebase-authentication-with-jwts
    """

    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication is needed",
            headers={"WWW-Authenticate": 'Bearer error="invalid token"'}
        )

    try:
        token = credential.credentials
        uid = auth.verify_id_token(token)['uid']

        token_data = TokenData(uid=uid, client="TODO", roles=[])

        token = jwt.encode({
            "data": token_data.dict(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }, JWT_SECRET_KEY, JWT_ALGORITHM)

        return AuthenticationResponse(jwt=token, success=True)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials, {err}",
            headers={"WWW-Authenticate": "Bearer"}
        )
