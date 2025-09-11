from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import get_config


class Base(DeclarativeBase):
    pass


def get_engine():
    config = get_config()
    connect_args = {"check_same_thread": False} if config.database_url.startswith("sqlite") else {}
    engine = create_engine(config.database_url, echo=False, future=True, connect_args=connect_args)
    return engine


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()