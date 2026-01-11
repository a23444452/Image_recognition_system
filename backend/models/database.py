"""
資料庫配置與連線
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 從環境變數讀取資料庫 URL，預設使用 SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./yolo.db")

# 建立引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 建立 SessionLocal 類別
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立 Base 類別
Base = declarative_base()


def get_db():
    """
    資料庫依賴注入
    使用方式: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """初始化資料庫（建立所有表）"""
    Base.metadata.create_all(bind=engine)
