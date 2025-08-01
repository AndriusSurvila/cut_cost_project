from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import asyncio

from app.models.session import get_db
from app.contracts.stream_interface import (
    LLMStreamInterface, 
    StreamRequest, 
    StreamChunk, 
    StreamStatus
)
from app.dependencies.auth import get_current_active_user
from app.models.models import User

router = APIRouter()

class StreamRequestAPI(BaseModel):
    """API модель для запроса стрима"""
    prompt: str = Field(..., min_length=1, description="Текст промпта")
    model: Optional[str] = Field(None, description="Название модели")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Температура генерации")
    max_tokens: Optional[int] = Field(None, gt=0, description="Максимальное количество токенов")
    stream: bool = Field(True, description="Включить стриминг")

class GenerateRequest(BaseModel):
    """API модель для генерации без стрима"""
    prompt: str = Field(..., min_length=1)
    model: Optional[str] = None
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)

class ModelInfo(BaseModel):
    """Информация о модели"""
    name: str
    description: str
    max_tokens: int
    temperature_range: List[float]

class HealthResponse(BaseModel):
    """Ответ проверки здоровья"""
    status: str
    service: str
    version: str
    models_available: int
    uptime: str
    response_time_ms: int
    timestamp: float

class StreamController:
    """Улучшенный контроллер для работы со стримом"""
    
    def __init__(self, llm_service: LLMStreamInterface):
        self.llm_service = llm_service
    
    async def stream_chat_response(self, request: StreamRequestAPI) -> StreamingResponse:
        """Стриминг ответа чата"""
        stream_request = StreamRequest(
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        async def generate_stream():
            """Генератор для стрима"""
            try:
                async for chunk in self.llm_service.stream_generate(stream_request):
                    # Преобразуем chunk в JSON для отправки
                    chunk_data = {
                        "content": chunk.content,
                        "status": chunk.status.value,
                        "chunk_id": chunk.chunk_id,
                        "timestamp": chunk.timestamp,
                        "metadata": chunk.metadata
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    
                    # Если стрим завершен или произошла ошибка, выходим
                    if chunk.status in [StreamStatus.COMPLETED, StreamStatus.ERROR]:
                        break
                        
            except Exception as e:
                error_chunk = {
                    "content": "",
                    "status": StreamStatus.ERROR.value,
                    "chunk_id": "error",
                    "timestamp": asyncio.get_event_loop().time(),
                    "metadata": {"error": str(e)}
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
            
            # Сигнал завершения стрима
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )
    
    async def generate_response(self, request: GenerateRequest) -> str:
        """Генерация полного ответа"""
        stream_request = StreamRequest(
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return await self.llm_service.generate(stream_request)

# Инициализация контроллера (будет переопределено в DI контейнере)
_controller_instance = None

def get_controller() -> StreamController:
    """Получение экземпляра контроллера"""
    if _controller_instance is None:
        raise HTTPException(status_code=500, detail="Controller not initialized")
    return _controller_instance

def set_controller(controller: StreamController):
    """Установка экземпляра контроллера"""
    global _controller_instance
    _controller_instance = controller

# API Endpoints

@router.post("/stream")
async def stream_response(
    request: StreamRequestAPI,
    current_user: User = Depends(get_current_active_user),
    controller: StreamController = Depends(get_controller)
):
    """
    Стриминг ответа AI
    Возвращает Server-Sent Events (SSE) поток
    """
    if not request.stream:
        # Если стриминг отключен, возвращаем полный ответ
        response = await controller.generate_response(
            GenerateRequest(
                prompt=request.prompt,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        )
        return {"response": response, "user": current_user.username}
    
    return await controller.stream_chat_response(request)

@router.post("/generate")
async def generate_response(
    request: GenerateRequest,
    current_user: User = Depends(get_current_active_user),
    controller: StreamController = Depends(get_controller)
):
    """Генерация полного ответа без стриминга"""
    try:
        response = await controller.generate_response(request)
        return {
            "response": response,
            "user": current_user.username,
            "model": request.model or "default",
            "temperature": request.temperature
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@router.get("/models", response_model=List[str])
async def get_available_models(
    current_user: User = Depends(get_current_active_user),
    controller: StreamController = Depends(get_controller)
):
    """Получение списка доступных моделей"""
    return controller.llm_service.get_supported_models()

@router.get("/models/{model_name}", response_model=ModelInfo)
async def get_model_info(
    model_name: str,
    current_user: User = Depends(get_current_active_user),
    controller: StreamController = Depends(get_controller)
):
    """Получение информации о конкретной модели"""
    model_info = controller.llm_service.get_model_info(model_name)
    if not model_info:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    return ModelInfo(**model_info)

@router.get("/health", response_model=HealthResponse)
async def health_check(
    controller: StreamController = Depends(get_controller)
):
    """Проверка состояния AI сервиса"""
    health_data = await controller.llm_service.health_check()
    return HealthResponse(**health_data)

@router.get("/stats")
async def get_usage_statistics(
    current_user: User = Depends(get_current_active_user),
    controller: StreamController = Depends(get_controller)
):
    """Получение статистики использования (если доступна)"""
    if hasattr(controller.llm_service, 'get_usage_statistics'):
        stats = controller.llm_service.get_usage_statistics()
        return {"statistics": stats, "user": current_user.username}
    else:
        return {"message": "Statistics not available for this service"}

@router.post("/conversation/summary")
async def get_conversation_summary(
    messages: List[str],
    current_user: User = Depends(get_current_active_user),
    controller: StreamController = Depends(get_controller)
):
    """Генерация краткого содержания беседы"""
    if hasattr(controller.llm_service, 'get_conversation_summary'):
        summary = await controller.llm_service.get_conversation_summary(messages)
        return {"summary": summary, "message_count": len(messages)}
    else:
        return {"summary": "Conversation summary not available"}

@router.post("/suggestions")
async def get_question_suggestions(
    context: str,
    limit: int = Query(4, ge=1, le=10),
    current_user: User = Depends(get_current_active_user),
    controller: StreamController = Depends(get_controller)
):
    """Получение предложений для следующих вопросов"""
    if hasattr(controller.llm_service, 'suggest_next_questions'):
        suggestions = await controller.llm_service.suggest_next_questions(context)
        return {"suggestions": suggestions[:limit], "context_analyzed": True}
    else:
        return {"suggestions": [], "context_analyzed": False}

# Дополнительные утилиты

class AsyncStreamTester:
    """Утилита для тестирования асинхронного стрима"""
    
    @staticmethod
    async def test_stream_connection(
        controller: StreamController,
        test_prompt: str = "Привет, это тест стрима"
    ) -> Dict[str, Any]:
        """Тестирование соединения со стримом"""
        start_time = asyncio.get_event_loop().time()
        chunks_received = 0
        total_content_length = 0
        
        try:
            request = StreamRequest(prompt=test_prompt)
            
            async for chunk in controller.llm_service.stream_generate(request):
                chunks_received += 1
                total_content_length += len(chunk.content)
                
                if chunk.status == StreamStatus.COMPLETED:
                    break
                elif chunk.status == StreamStatus.ERROR:
                    return {
                        "success": False,
                        "error": chunk.metadata.get("error", "Unknown error"),
                        "chunks_received": chunks_received
                    }
            
            end_time = asyncio.get_event_loop().time()
            
            return {
                "success": True,
                "chunks_received": chunks_received,
                "total_content_length": total_content_length,
                "duration_seconds": end_time - start_time,
                "average_chunk_size": total_content_length / chunks_received if chunks_received > 0 else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chunks_received": chunks_received
            }

@router.get("/test/stream-connection")
async def test_stream_connection(
    test_prompt: str = Query("Привет, это тест стрима"),
    current_user: User = Depends(get_current_active_user),
    controller: StreamController = Depends(get_controller)
):
    """Тестирование соединения со стримом"""
    tester = AsyncStreamTester()
    result = await tester.test_stream_connection(controller, test_prompt)
    return result