from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from main import app, get_db
from database import Base
from models import Riddle, UserSession
import datetime
import uuid

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_riddler.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_and_get_riddle():
    # 1. Create a riddle
    response = client.post(
        "/v1/riddle",
        headers={"x-user-id": "user123"},
        json={
            "category": "Логика",
            "difficulty": "Сложная",
            "context": "Тест",
            "question": "Зимой и летом одним цветом?",
            "answer": "Елка"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    riddle_id = data["data"]["riddleId"]

    # 2. Get the riddle
    response = client.get(
        "/v1/riddle",
        headers={"x-user-id": "user123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["riddleId"] == riddle_id
    assert data["data"]["question"] == "Зимой и летом одним цветом?"

def test_submit_answer_correct():
    db = TestingSessionLocal()
    riddle_id = str(uuid.uuid4())
    db.add(Riddle(riddle_id=riddle_id, category="Test", difficulty="Easy", context="Ctx", question="2+2?", answer="4"))
    session_key = f"{riddle_id}:user1"
    db.add(UserSession(session_key=session_key, session_id="sess-1", attempts=0, expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=1)))
    db.commit()
    db.close()

    response = client.post(
        f"/v1/riddle/{riddle_id}/answer",
        headers={"x-user-id": "user1"},
        json={"answer": "4"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["verdict"] == "CORRECT"

def test_submit_answer_wrong():
    db = TestingSessionLocal()
    riddle_id = str(uuid.uuid4())
    db.add(Riddle(riddle_id=riddle_id, category="Test", difficulty="Easy", context="Ctx", question="2+2?", answer="4"))
    session_key = f"{riddle_id}:user2"
    db.add(UserSession(session_key=session_key, session_id="sess-2", attempts=0, expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=1)))
    db.commit()
    db.close()

    response = client.post(
        f"/v1/riddle/{riddle_id}/answer",
        headers={"x-user-id": "user2"},
        json={"answer": "5"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["verdict"] == "WRONG"

def test_submit_answer_failed():
    db = TestingSessionLocal()
    riddle_id = str(uuid.uuid4())
    db.add(Riddle(riddle_id=riddle_id, category="Test", difficulty="Easy", context="Ctx", question="2+2?", answer="4"))
    session_key = f"{riddle_id}:user3"
    db.add(UserSession(session_key=session_key, session_id="sess-3", attempts=2, expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=1)))
    db.commit()
    db.close()

    response = client.post(
        f"/v1/riddle/{riddle_id}/answer",
        headers={"x-user-id": "user3"},
        json={"answer": "5"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["verdict"] == "FAILED"
    assert data["data"]["revealAnswer"] == "4"

def test_search_riddles():
    db = TestingSessionLocal()
    db.add(Riddle(riddle_id=str(uuid.uuid4()), category="A", difficulty="Easy", context="C", question="Q1", answer="A1"))
    db.add(Riddle(riddle_id=str(uuid.uuid4()), category="A", difficulty="Hard", context="C", question="Q2", answer="A2"))
    db.add(Riddle(riddle_id=str(uuid.uuid4()), category="B", difficulty="Easy", context="C", question="Q3", answer="A3"))
    db.commit()
    db.close()

    response = client.get(
        "/v1/riddles/search?category=A",
        headers={"x-user-id": "user"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2

    response2 = client.get(
        "/v1/riddles/search?category=A&difficulty=Hard",
        headers={"x-user-id": "user"}
    )
    assert len(response2.json()["data"]) == 1


def test_get_riddle_not_found():
    response = client.get(
        "/v1/riddle?category=Nonexisting",
        headers={"x-user-id": "user404"}
    )
    assert response.status_code == 404


def test_submit_answer_session_not_found():
    riddle_id = str(uuid.uuid4())
    db = TestingSessionLocal()
    db.add(Riddle(riddle_id=riddle_id, category="Test", difficulty="Easy", context="Ctx", question="2+2?", answer="4"))
    db.commit()
    db.close()

    response = client.post(
        f"/v1/riddle/{riddle_id}/answer",
        headers={"x-user-id": "user_no_session"},
        json={"answer": "4"}
    )
    assert response.status_code == 400


def test_update_riddle_success():
    db = TestingSessionLocal()
    riddle_id = str(uuid.uuid4())
    db.add(Riddle(riddle_id=riddle_id, category="Test", difficulty="Easy", context="Ctx", question="Q", answer="A"))
    db.commit()
    db.close()

    response = client.put(
        f"/v1/riddle/{riddle_id}",
        headers={"x-user-id": "user_editor"},
        json={"difficulty": "Hard", "question": "Updated?"}
    )
    assert response.status_code == 200
    assert response.json()["code"] == 0

    db = TestingSessionLocal()
    updated = db.query(Riddle).filter(Riddle.riddle_id == riddle_id).first()
    db.close()
    assert updated.difficulty == "Hard"
    assert updated.question == "Updated?"


def test_update_riddle_not_found():
    response = client.put(
        "/v1/riddle/nonexistent",
        headers={"x-user-id": "user_editor"},
        json={"difficulty": "Hard"}
    )
    assert response.status_code == 404


def test_delete_riddle_success():
    db = TestingSessionLocal()
    riddle_id = str(uuid.uuid4())
    db.add(Riddle(riddle_id=riddle_id, category="Test", difficulty="Easy", context="Ctx", question="Q", answer="A"))
    db.commit()
    db.close()

    response = client.delete(
        f"/v1/riddle/{riddle_id}",
        headers={"x-user-id": "user_admin"}
    )
    assert response.status_code == 200
    assert response.json()["code"] == 0

    db = TestingSessionLocal()
    deleted = db.query(Riddle).filter(Riddle.riddle_id == riddle_id).first()
    db.close()
    assert deleted is None


def test_delete_riddle_not_found():
    response = client.delete(
        "/v1/riddle/nonexistent",
        headers={"x-user-id": "user_admin"}
    )
    assert response.status_code == 404


def test_search_riddles_no_results():
    response = client.get(
        "/v1/riddles/search?category=DoesNotExist",
        headers={"x-user-id": "user"}
    )
    assert response.status_code == 200
    assert response.json()["data"] == []


def test_missing_user_id_header():
    response = client.get("/v1/riddle")
    assert response.status_code == 400
    assert "x-user-id header is required" in response.json()["detail"]


def test_empty_user_id_header():
    response = client.get("/v1/riddle", headers={"x-user-id": ""})
    assert response.status_code == 400
    assert "x-user-id header is required" in response.json()["detail"]

