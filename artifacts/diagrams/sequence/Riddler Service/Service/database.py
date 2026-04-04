from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Использование SQLite для локальной работы, т.к. MySQL сервер не установлен в окружении.
# Для переключения на MySQL достаточно заменить строку подключения на:
# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://user:password@localhost/riddler_db"
SQLALCHEMY_DATABASE_URL = "sqlite:///./riddler.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
