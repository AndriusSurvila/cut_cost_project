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
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value

load_env()

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import logging

from sqlalchemy.exc import SQLAlchemyError
from app.models.models import Base, User
from app.models.session import engine
from app.config.stream_config import StreamConfig
from app.controllers import (
    chat_controller,
    webhook_controller,
    auth_controller,
    stream_controller,
    message_controller
)
from app.dependencies.auth import get_current_active_user

def create_tables():
    """Создание всех таблиц в БД"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise

def create_app():
    """Создание и настройка FastAPI приложения"""
    
    create_tables()
    
    try:
        stream_controller_instance = StreamConfig.initialize_services()
        print(f"✅ Stream services initialized with {type(stream_controller_instance.llm_service).__name__}")
    except Exception as e:
        print(f"❌ Error initializing stream services: {e}")
        raise
    
    app = FastAPI(
        title="Enhanced ChatGPT-like AI API with Authentication",
        description="REST API for a chat-based AI assistant with JWT authentication and advanced streaming",
        version="2.0.0"
    )

    # Подключаем роутеры
    app.include_router(auth_controller.router, prefix="/auth", tags=["Authentication"])
    app.include_router(stream_controller.router, prefix="/stream", tags=["AI Stream"])
    app.include_router(chat_controller.router, prefix="/api", tags=["Chats"])
    app.include_router(webhook_controller.router, tags=["Webhooks"])
    app.include_router(message_controller.router, prefix="/api", tags=["messages"])

    # Настраиваем CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ====== Дополнительный эндпоинт /ask ======
    class QuestionRequest(BaseModel):
        question: str

    @app.post("/ask")
    async def ask(
        request: QuestionRequest,
        current_user: User = Depends(get_current_active_user)
    ):
        """3-шаговый переводчик с использованием AI"""
        user_question = request.question.strip()

        from app.controllers.stream_controller import get_controller, GenerateRequest
        controller = get_controller()

        try:
            # 1. Перевод вопроса на английский
            step1_prompt = f"""
Detect the language of the question and translate it into English.
Return ONLY the translated English version, no comments.

Question: {user_question}
"""
            english_question = await controller.generate_response(
                GenerateRequest(prompt=step1_prompt)
            )

            # 2. Получение ответа на английском
            step2_prompt = f"""
Answer the following question in English, clearly and concisely:

{english_question}
"""
            english_answer = await controller.generate_response(
                GenerateRequest(prompt=step2_prompt)
            )

            # 3. Перевод ответа обратно
            step3_prompt = f"""
The original question was: "{user_question}"
The answer in English is: "{english_answer}"
Detect the original language and translate the answer BACK into it.
Return ONLY the translated answer, with no extra text.
"""
            final_answer = await controller.generate_response(
                GenerateRequest(prompt=step3_prompt)
            )

            return {
                "answer": final_answer,
                "user": current_user.username,
                "service_mode": os.getenv("LLM_SERVICE_MODE", "mock")
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    @app.get("/")
    def root():
        """Корневой эндпоинт"""
        service_mode = os.getenv("LLM_SERVICE_MODE", "mock")
        
        return {
            "message": "Enhanced ChatGPT-like AI API with Authentication",
            "version": "2.0.0",
            "service_mode": service_mode,
            "docs": "/docs",
            "endpoints": {
                "auth": {
                    "register": "/auth/register",
                    "login": "/auth/login",
                    "refresh": "/auth/refresh",
                    "me": "/auth/me"
                },
                "stream": {
                    "stream_chat": "/stream/stream",
                    "generate": "/stream/generate",
                    "models": "/stream/models"
                },
                "chat": {
                    "list": "/api/chats",
                    "create": "/api/chats",
                    "get": "/api/chats/{chat_id}",
                    "messages": "/api/chats/{chat_id}/messages"
                }
            }
        }

    return app

# Создание приложения
app = create_app()

# Логирование и обработка ошибок
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(status_code=500, content={"detail": "Database error occurred"})

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)