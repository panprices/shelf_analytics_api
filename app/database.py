from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config.settings import get_settings

settings = get_settings()

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{settings.db_user}:{settings.db_pass}@{settings.db_host}/{settings.db_name}"
    if not settings.db_host.startswith("/")
    else f"postgresql://{settings.db_user}:{settings.db_pass}@/{settings.db_name}?host={settings.db_host}"
)  # unix socket

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True if settings.panprices_environment == "local" else False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
