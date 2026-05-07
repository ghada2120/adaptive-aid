from collections.abc import AsyncGenerator
import uuid

from sqlmodel import SQLModel, Session, create_engine
from datetime import datetime, timezone

DATABASE_URL="sqlite:///./app.db"

engine = create_engine(DATABASE_URL, echo=True)

async def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session