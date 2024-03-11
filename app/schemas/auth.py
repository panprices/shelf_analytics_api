from typing import Optional, List

from pydantic import BaseModel, Field


class AuthenticationRequest(BaseModel):
    email: str = Field(
        description="The user email", example="robert-andrei.damian@panprices.com"
    )
    password: str = Field(description="The user password", example="ImiPlacCartofii")


class AuthenticationResponse(BaseModel):
    jwt: Optional[str] = Field(
        default=None, description="The JWT token to be used with future requests"
    )
    success: bool = Field(
        default=False, description="Whether the authentication worked"
    )


class ExtraFeatureScaffold(BaseModel):
    feature_name: str
    enabled: bool

    class Config:
        orm_mode = True


class UserMetadata(BaseModel):
    client: str
    first_name: str
    last_name: str
    roles: List[str]
    email: Optional[str]
    client_name: str
    features: Optional[List[ExtraFeatureScaffold]]


class TokenData(UserMetadata):
    uid: str


class UserInvitation(BaseModel):
    first_name: str
    last_name: str
    email: str
    domain: str


class CheckEnvelopeResponse(BaseModel):
    success: bool


class MagicAuthRequest(BaseModel):
    did_token: str


class MagicAuthResponse(AuthenticationResponse):
    firebase_token: Optional[str] = Field(
        default=None, description="The JWT token to be used with firebase"
    )


class AuthProbeRequest(BaseModel):
    email: str
