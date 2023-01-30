from functools import lru_cache

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    firebase_api_key: str = Field()

    db_user: str = Field()
    db_pass: str = Field()
    db_name: str = Field()
    db_host: str = Field()

    magic_api_secret_key: str = Field()
    jwt_secret: str = Field()
    mailgun_api_key: str = Field()

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    return Settings()
