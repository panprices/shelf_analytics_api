import json
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

import fastapi
import requests
import structlog
from fastapi import Depends, Response, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, firestore
from firebase_admin.auth import EmailAlreadyExistsError, UserNotFoundError
from firebase_admin.exceptions import FirebaseError
from jose import jwt
from magic_admin import Magic
from magic_admin.error import (
    MagicError,
)
from sqlalchemy.orm import Session
from starlette import status
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app import crud
from app.config.settings import get_settings, Settings
from app.database import get_db
from app.schemas.auth import (
    AuthenticationRequest,
    AuthenticationResponse,
    TokenData,
    UserMetadata,
    UserInvitation,
    CheckEnvelopeResponse,
    MagicAuthResponse,
    MagicAuthRequest,
    ExtraFeatureScaffold,
    AuthProbeRequest,
)
from app.security import firebase_app, JWT_ALGORITHM, JWT_SECRET_KEY, get_user_data
from app.tags import TAG_AUTH

router = fastapi.APIRouter(prefix="/authenticate")
logger = structlog.get_logger()
rest_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"


SHELF_ANALYTICS_USER_METADATA_COLLECTION = "shelf-analytics-user-metadata"
SHELF_ANALYTICS_ROLE_READER = "reader"
SHELF_ANALYTICS_ROLE_ADMIN = "admin"


def get_user_metadata(postgres_db: Session, uid: str) -> Optional[UserMetadata]:
    db = firestore.client()
    user_metadata = (
        db.collection(SHELF_ANALYTICS_USER_METADATA_COLLECTION).document(uid).get()
    )

    if not user_metadata.exists:
        return None

    extra_features = [
        ExtraFeatureScaffold.from_orm(feature)
        for feature in crud.get_extra_features(postgres_db, user_metadata.get("client"))
    ]

    client_name = crud.get_brand_name(postgres_db, user_metadata.get("client"))

    return UserMetadata(
        **user_metadata.to_dict(), features=extra_features, client_name=client_name
    )


def authenticate_verified_user(
    postgres_db: Session, uid: str
) -> AuthenticationResponse:
    """
    This method should only be called once the user has verified that they are who they pretend to be either by
    providing a password or a valid firebase token.
    """

    user_metadata = get_user_metadata(postgres_db, uid)
    if not user_metadata:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not properly fulfill the authentication request. User exists but no permissions assigned!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = TokenData(uid=uid, **user_metadata.dict())

    token = jwt.encode(
        {"data": token_data.dict(), "exp": datetime.utcnow() + timedelta(hours=3)},
        JWT_SECRET_KEY,
        JWT_ALGORITHM,
    )

    return AuthenticationResponse(jwt=token, success=True)


@router.post(
    "/withEmailAndPassword", tags=[TAG_AUTH], response_model=AuthenticationResponse
)
def authenticate(
    user: AuthenticationRequest,
    response: Response,
    postgres_db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    This endpoint can be directly used with the credentials (email + password)

    We generate our own JWT token as opposed to simply using the one provided by firebase because we want to be able to
    include other information in the token, such as the client that the user works for, and the roles they have.
    Firebase has some documentation on creating custom tokens:
    https://firebase.google.com/docs/auth/admin/create-custom-tokens#using_a_service_account_json_file but there is no
    easy way to later check if those tokens are valid later, when we receive them in the backend. It seems like the
    purpose of these custom tokens is to allow for custom fields when writing rules for firestore (what a user can and
    can not do over there).
    """

    firebase_response = requests.post(
        rest_api_url + "?key=" + settings.firebase_api_key,
        data={
            "email": user.email,
            "password": user.password,
            "returnSecureToken": True,
        },
    )
    if firebase_response.status_code != 200:
        response.status_code = firebase_response.status_code
        return AuthenticationResponse(success=False)

    uid = auth.get_user_by_email(user.email, app=firebase_app).uid
    return authenticate_verified_user(postgres_db, uid)


@router.post(
    "/withFirebaseToken", tags=[TAG_AUTH], response_model=AuthenticationResponse
)
def authenticate_with_firebase_token(
    credential: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    postgres_db: Session = Depends(get_db),
):
    """
    This method may be used if we are already logged into firebase through the frontend, so we use firebase's token
    to generate a backend token.

    It is the only endpoint in this API where the expected authentication is different. Here we expect a Firebase Bearer
    token, for all the other authenticated endpoints we expect a token generated by this app (through this method or the
    method that takes a username and password).

    Inspired by: https://stackoverflow.com/questions/72200552/fastapi-firebase-authentication-with-jwts
    """

    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication is needed",
            headers={"WWW-Authenticate": 'Bearer error="invalid token"'},
        )

    try:
        token = credential.credentials
        uid = auth.verify_id_token(token)["uid"]
        return authenticate_verified_user(postgres_db, uid)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials, {err}",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/invite", tags=[TAG_AUTH], response_model=CheckEnvelopeResponse)
def invite_user_by_mail(
    invitation: UserInvitation,
    response: Response,
    inviting_user: TokenData = Depends(get_user_data),
    postgres_db=Depends(get_db),
):
    if SHELF_ANALYTICS_ROLE_ADMIN not in inviting_user.roles:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False}

    brand_name = crud.get_brand_name(postgres_db, inviting_user.client)
    settings = get_settings()

    email_env = Environment(
        loader=FileSystemLoader("resources/email"), autoescape=select_autoescape()
    )
    template = email_env.get_template("invite.html")
    template_data = {
        "inviter_name": inviting_user.first_name + " " + inviting_user.last_name,
        "brand_name": brand_name,
        "invite_link": f"{invitation.domain}/login?email={invitation.email}",
    }
    email_body = template.render(**template_data)
    email_response = requests.post(
        "https://api.postmarkapp.com/email",
        headers={
            "X-Postmark-Server-Token": settings.postmark_api_token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        json={
            "From": "Loupe <info@getloupe.co>",
            "To": f"{invitation.first_name} {invitation.last_name} <{invitation.email}>",
            "Subject": f"{inviting_user.first_name} {inviting_user.last_name} invited you to join the {brand_name} team",
            "HtmlBody": email_body,
            "MessageStream": "outbound",
        },
    )
    if email_response.status_code >= 300:
        logger.error("Error when sending email", response=email_response.json())
        raise HTTPException(500, detail="Error when sending email")

    alphabet = string.ascii_letters + string.digits
    password = "".join(secrets.choice(alphabet) for _ in range(20))

    try:
        new_user = auth.create_user(email=invitation.email, password=password)
        db = firestore.client()
        db.collection(SHELF_ANALYTICS_USER_METADATA_COLLECTION).document(
            new_user.uid
        ).set(
            {
                **invitation.dict(),
                "roles": [SHELF_ANALYTICS_ROLE_READER],
                "client": inviting_user.client,
            }
        )
    except EmailAlreadyExistsError:
        pass

    return {"success": True}


@router.post("/magic", tags=[TAG_AUTH], response_model=MagicAuthResponse)
def authenticate_with_magic_link(
    magic_request: MagicAuthRequest, postgres_db: Session = Depends(get_db)
):
    magic = Magic(api_secret_key=get_settings().magic_api_secret_key)
    try:
        magic.Token.validate(magic_request.did_token)
        metadata = magic.User.get_metadata_by_token(magic_request.did_token)
        email = metadata.data["email"]
        user = auth.get_user_by_email(email)
        authentication_response = authenticate_verified_user(postgres_db, user.uid)
        firebase_token = auth.create_custom_token(user.uid, app=firebase_app)
        return {**authentication_response.dict(), "firebase_token": firebase_token}
    except MagicError as e:
        return AuthenticationResponse(success=False)


@router.post("/probe", tags=[TAG_AUTH], response_model=CheckEnvelopeResponse)
def probe_user(
    body: AuthProbeRequest,
):
    try:
        auth.get_user_by_email(body.email)

        return {"success": True}
    except (ValueError, UserNotFoundError, FirebaseError) as e:
        return {"success": False}
