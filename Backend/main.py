import os
from pathlib import Path

def load_env():
    """Загружает переменные окружения из .env файла"""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from app.models.models import Base
from app.models.session import engine

from app.container import Container
from app.services.api_model_service import CladeModelService
from app.contracts.stream_interface import LLMStreamInterface
from app.controllers.stream_controller import StreamController
from app.dependencies.auth import get_current_active_user
from app.models.models import User

from app.controllers import stream_controller
from app.controllers import chat_controller
from app.controllers import webhook_controller
from app.controllers import auth_controller

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging

def create_tables():
    """Создание всех таблиц в БД"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise

def setup_container():
    """Настройка DI контейнера"""
    container = Container()
    container.bind(LLMStreamInterface, CladeModelService)
    return container.resolve(StreamController)

def create_app():
    """Создание и настройка FastAPI приложения"""
    
    create_tables()
    
    stream_controller_instance = setup_container()
    
    app = FastAPI(
        title="ChatGPT-like AI API with Authentication",
        description="REST API for a chat-based AI assistant with JWT authentication",
        version="1.0.0"
    )

    app.include_router(auth_controller.router, prefix="/auth", tags=["Authentication"])
    app.include_router(stream_controller.router, tags=["AI Stream"])
    app.include_router(chat_controller.router, prefix="/api", tags=["Chats"])
    app.include_router(webhook_controller.router, tags=["Webhooks"])

    app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


    class QuestionRequest(BaseModel):
        question: str

    @app.post("/ask")
    def ask(
        request: QuestionRequest,
        current_user: User = Depends(get_current_active_user)
    ):
        """
        Многоступенчатая обработка вопроса с аутентификацией:
        1. Определение языка и перевод на английский
        2. Получение ответа на английском
        3. Перевод ответа обратно на исходный язык
        """
        user_question = request.question.strip()

        step1_prompt = f"""
    Detect the language of the question and translate it into English.
    Return ONLY the translated English version, no comments.

    Question: {user_question}
    """
        english_question = stream_controller_instance.stream(step1_prompt)

        step2_prompt = f"""
    Answer the following question in English, clearly and concisely:

    {english_question}
    """
        english_answer = stream_controller_instance.stream(step2_prompt)

        step3_prompt = f"""
    The original question was: "{user_question}"
    The answer in English is: "{english_answer}"
    Detect the original language and translate the answer BACK into it.
    Return ONLY the translated answer, with no extra text.
    """
        final_answer = stream_controller_instance.stream(step3_prompt)

        return {
            "answer": final_answer,
            "user": current_user.username
        }

    @app.get("/")
    def root():
        """Корневой эндпоинт"""
        return {
            "message": "ChatGPT-like AI API with Authentication",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
            "auth_endpoints": {
                "register": "/auth/register",
                "login": "/auth/login",
                "refresh": "/auth/refresh",
                "me": "/auth/me"
            }
        }

    return app

app = create_app()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error occurred"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)