from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings


def make_session_factory() -> sessionmaker[Session]:
    engine = create_engine(get_settings().database_url, echo=False)
    return sessionmaker(engine, expire_on_commit=False)
