from functools import lru_cache

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    panprices_environment: str = Field(default="local")

    db_user: str = Field()
    db_pass: str = Field()
    db_name: str = Field()
    db_host: str = Field()

    firebase_api_key: str = Field()
    magic_api_secret_key: str = Field()
    postmark_api_token: str = Field()
    jwt_secret: str = Field()

    fernet_secret_key: str = Field()
    api_keys_secret_salt: str = Field()

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    return Settings()
