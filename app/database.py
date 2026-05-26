from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


#TODO: Add to environment variable
SQLALCHEMY_DATABASE_URL  = settings.database_url


# engine manages the connection
engine = create_engine(SQLALCHEMY_DATABASE_URL)


# note that SessionLocal uses a PascalCase because it's a factory or class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# All your models will inherit from this Base class
class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()