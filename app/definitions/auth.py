from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class AuthenticationRequest(BaseModel):
    email: str = Field(description="The user email", example="robert-andrei.damian@panprices.com")
    password: str = Field(description="The user password", example="ImiPlacCartofii")


class AuthenticationResponse(BaseModel):
    jwt: Optional[str] = Field(default=None, description="The JWT token to be used with future requests")
    success: bool = Field(default=False, description="Whether the authentication worked")


class TokenData(BaseModel):
    uid: str
    client: str
    roles: List[str]
