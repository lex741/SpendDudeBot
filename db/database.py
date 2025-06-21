from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# для простоты – SQLite в файле
DATABASE_URL = "sqlite:///./data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
