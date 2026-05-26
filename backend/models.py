import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./backend.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="employee") # admin or employee

class SKU(Base):
    __tablename__ = "skus"
    id = Column(Integer, primary_key=True, index=True)
    sku_id = Column(String, index=True)
    site = Column(String) # target, walmart, bestbuy, topps
    quantity = Column(Integer, default=1)
    active = Column(Boolean, default=True)
    chrome_version = Column(String, default="auto")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    sku_id = Column(Integer, ForeignKey("skus.id"))
    status = Column(String, default="pending") # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    sku = relationship("SKU")

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    level = Column(String, default="info") # info, error, success

def init_db():
    Base.metadata.create_all(bind=engine)
    # Safe database migration: Add chrome_version column if it doesn't exist
    from sqlalchemy import text
    db = SessionLocal()
    try:
        cursor = db.execute(text("PRAGMA table_info(skus)"))
        columns = [row[1] for row in cursor.fetchall()]
        if "chrome_version" not in columns:
            db.execute(text("ALTER TABLE skus ADD COLUMN chrome_version VARCHAR DEFAULT 'auto'"))
            db.commit()
            print("Successfully migrated 'skus' table to include 'chrome_version' column.")
    except Exception as e:
        print(f"Error migrating database: {e}")
    finally:
        db.close()
