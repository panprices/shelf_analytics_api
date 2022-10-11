from functools import lru_cache

from pydantic import BaseSettings, Field
import firebase_admin


class Settings(BaseSettings):
    firebase_api_key: str = Field()

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    return Settings()
