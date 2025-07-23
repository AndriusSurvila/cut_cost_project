from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.session import get_db
from app.policies.policies import generate_ai_response, stream_ai_response
from app.contracts.stream_interface import LLMStreamInterface

router = APIRouter()

class StreamRequest(BaseModel):
    prompt: str

class AIGenerateRequest(BaseModel):
    prompt: str

class StreamController:
    def __init__(self, llm_service: LLMStreamInterface):
        self.llm_service = llm_service
    
    def stream(self, prompt: str) -> str:
        """Метод для получения ответа от LLM сервиса"""
        return self.llm_service.predict(prompt)

@router.post("/ai/generate")
def generate_ai(request: AIGenerateRequest, db: Session = Depends(get_db)):
    """Генерация AI ответа"""
    try:
        response = generate_ai_response(request.prompt, db)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def health_check():
    """Проверка состояния сервиса"""
    return {"status": "OK", "message": "Service is healthy"}

@router.post("/stream")
def stream_response(request: StreamRequest):
    """Стрим ответа AI"""
    if not request.prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    return stream_ai_response(request.prompt)