from fastapi import FastAPI, Header, Query, Path, Body, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
import datetime
import logging

from database import engine, Base, get_db
from models import Riddle, UserSession

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем таблицы в БД
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Riddle Service (Синхронное API)",
    description="Синхронное API для управления каталогом загадок и оркестрации процесса отгадывания.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    logger.info("Starting Riddler Service")
    db = next(get_db())
    if db.query(Riddle).count() == 0:
        default_id = str(uuid.uuid4())
        db.add(Riddle(
            riddle_id=default_id,
            category="Логика",
            difficulty="Средняя",
            context="Для всех",
            question="А, И, Б сидели на трубе. А упала, Б пропала, кто остался на трубе?",
            answer="И"
        ))
        db.commit()
        logger.info(f"Default riddle added with ID: {default_id}")
    db.close()

class BaseResponse(BaseModel):
    code: int = 0
    message: str = "OK"

class RiddleData(BaseModel):
    riddleId: str
    category: str
    difficulty: str
    context: str
    question: Optional[str] = None

class GetRiddleResponse(BaseResponse):
    data: RiddleData

class SearchRiddleItem(BaseModel):
    riddleId: str
    category: str
    difficulty: str
    question: str

class SearchRiddlesResponse(BaseResponse):
    data: List[SearchRiddleItem]

class SubmitAnswerRequest(BaseModel):
    answer: str = Field(..., json_schema_extra={"example": "И"})

class SubmitAnswerData(BaseModel):
    verdict: str
    hint: Optional[str] = None
    revealAnswer: Optional[str] = None

class SubmitAnswerResponse(BaseResponse):
    data: SubmitAnswerData

class CreateRiddleRequest(BaseModel):
    category: str = Field(..., json_schema_extra={"example": "Логика"})
    difficulty: str = Field(..., json_schema_extra={"example": "Средняя"})
    context: str = Field(..., json_schema_extra={"example": "Для детей"})
    question: str = Field(..., json_schema_extra={"example": "А, И, Б сидели на трубе..."})
    answer: str = Field(..., json_schema_extra={"example": "И"})

class CreateRiddleData(BaseModel):
    riddleId: str

class CreateRiddleResponse(BaseResponse):
    data: CreateRiddleData

class UpdateRiddleRequest(BaseModel):
    category: Optional[str] = None
    difficulty: Optional[str] = None
    context: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None

MAX_ATTEMPTS = 3

def validate_user_id(x_user_id: str = Header(..., alias="x-user-id")):
    if not x_user_id or len(x_user_id.strip()) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="x-user-id header is required")
    return x_user_id.strip()

@app.get("/v1/riddle", response_model=GetRiddleResponse, tags=["Process"])
def get_riddle(
    x_user_id: str = Depends(validate_user_id),
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    context: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Riddle)
    if category:
        query = query.filter(Riddle.category == category)
    if difficulty:
        query = query.filter(Riddle.difficulty == difficulty)

    candidates = query.all()
    if not candidates:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching riddle found")

    riddle = random.choice(candidates)

    session_key = f"{riddle.riddle_id}:{x_user_id}"
    user_session = db.query(UserSession).filter(UserSession.session_key == session_key).first()

    if not user_session:
        user_session = UserSession(
            session_key=session_key,
            session_id=str(uuid.uuid4()),
            attempts=0,
            expires_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
        )
        db.add(user_session)
    else:
        user_session.attempts = 0
        user_session.expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)

    db.commit()

    return GetRiddleResponse(
        code=0,
        message="OK",
        data=RiddleData(
            riddleId=riddle.riddle_id,
            category=riddle.category,
            difficulty=riddle.difficulty,
            context=riddle.context,
            question=riddle.question
        )
    )

@app.post("/v1/riddle", response_model=CreateRiddleResponse, tags=["Management"])
def create_riddle(
    request: CreateRiddleRequest,
    x_user_id: str = Depends(validate_user_id),
    db: Session = Depends(get_db)
):
    riddle_id = str(uuid.uuid4())
    db_riddle = Riddle(
        riddle_id=riddle_id,
        category=request.category,
        difficulty=request.difficulty,
        context=request.context,
        question=request.question,
        answer=request.answer
    )
    db.add(db_riddle)
    db.commit()
    return CreateRiddleResponse(
        code=0,
        message="OK",
        data=CreateRiddleData(riddleId=riddle_id)
    )

@app.get("/v1/riddles/search", response_model=SearchRiddlesResponse, tags=["Management"])
def search_riddles(
    x_user_id: str = Depends(validate_user_id),
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Riddle)
    if category:
        query = query.filter(Riddle.category == category)
    if difficulty:
        query = query.filter(Riddle.difficulty == difficulty)

    paginated = query.offset(offset).limit(limit).all()

    return SearchRiddlesResponse(
        code=0,
        message="OK",
        data=[
            SearchRiddleItem(
                riddleId=r.riddle_id,
                category=r.category,
                difficulty=r.difficulty,
                question=r.question or ""
            ) for r in paginated
        ]
    )

@app.put("/v1/riddle/{riddleId}", response_model=BaseResponse, tags=["Management"])
def update_riddle(
    riddleId: str = Path(...),
    request: UpdateRiddleRequest = Body(...),
    x_user_id: str = Depends(validate_user_id),
    db: Session = Depends(get_db)
):
    riddle = db.query(Riddle).filter(Riddle.riddle_id == riddleId).first()
    if not riddle:
        raise HTTPException(status_code=404, detail="Riddle not found")

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(riddle, key, value)

    db.commit()
    return BaseResponse(code=0, message="OK")

@app.delete("/v1/riddle/{riddleId}", response_model=BaseResponse, tags=["Management"])
def delete_riddle(
    riddleId: str = Path(...),
    x_user_id: str = Depends(validate_user_id),
    db: Session = Depends(get_db)
):
    riddle = db.query(Riddle).filter(Riddle.riddle_id == riddleId).first()
    if not riddle:
        raise HTTPException(status_code=404, detail="Riddle not found")
    db.delete(riddle)
    db.commit()
    return BaseResponse(code=0, message="OK")

@app.post("/v1/riddle/{riddleId}/answer", response_model=SubmitAnswerResponse, tags=["Process"])
def submit_answer(
    riddleId: str = Path(...),
    request: SubmitAnswerRequest = Body(...),
    x_user_id: str = Depends(validate_user_id),
    db: Session = Depends(get_db)
):
    session_key = f"{riddleId}:{x_user_id}"
    user_session = db.query(UserSession).filter(UserSession.session_key == session_key).first()

    if not user_session:
        raise HTTPException(status_code=400, detail="Session not found or expired")

    riddle = db.query(Riddle).filter(Riddle.riddle_id == riddleId).first()
    if not riddle:
        raise HTTPException(status_code=500, detail="Riddle data corrupted")

    correct_answer = riddle.answer
    is_correct = request.answer.strip().lower() == correct_answer.strip().lower()

    if is_correct:
        verdict = "CORRECT"
        db.delete(user_session)
        hint = None
        reveal = None
    else:
        user_session.attempts += 1
        if user_session.attempts >= MAX_ATTEMPTS:
            verdict = "FAILED"
            reveal = correct_answer
            hint = "Попытки исчерпаны."
            db.delete(user_session)
        else:
            verdict = "WRONG"
            hint = f"Неверно. Осталось попыток: {MAX_ATTEMPTS - user_session.attempts}"
            reveal = None

    db.commit()

    return SubmitAnswerResponse(
        code=0,
        message="OK",
        data=SubmitAnswerData(
            verdict=verdict,
            hint=hint,
            revealAnswer=reveal
        )
    )
