from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# "postgresql://user:pass@145.223.18.225:5432/agents_db"
# "postgresql://user:pass@localhost:5432/agents_db"

DATABASE_URL = "postgresql://user:pass@127.0.0.1:5432/agents_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()