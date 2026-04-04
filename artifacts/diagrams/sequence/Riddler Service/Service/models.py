from sqlalchemy import Column, Integer, String, DateTime
from database import Base
import uuid
import datetime

class Riddle(Base):
    __tablename__ = "riddles"

    riddle_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category = Column(String, index=True)
    difficulty = Column(String, index=True)
    context = Column(String)
    question = Column(String)
    answer = Column(String)

class UserSession(Base):
    __tablename__ = "user_sessions"

    session_key = Column(String, primary_key=True) # Формат: "riddleId:userId"
    session_id = Column(String, default=lambda: str(uuid.uuid4()))
    attempts = Column(Integer, default=0)
    expires_at = Column(DateTime)
