# Оставляем только нужные эндпоинты:
# - POST /stream
# - POST /generate
# - GET /models

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import asyncio

from app.models.session import get_db
from app.contracts.stream_interface import (
    LLMStreamInterface,
    StreamRequest,
    StreamStatus
)
from app.dependencies.auth import get_current_active_user
from app.models.models import User

router = APIRouter()

class StreamRequestAPI(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: Optional[str] = None
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    stream: bool = Field(True)

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: Optional[str] = None
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)

# class ModelInfo(BaseModel):
#     name: str
#     description: str
#     max_tokens: int
#     temperature_range: List[float]

# class HealthResponse(BaseModel):
#     status: str
#     service: str
#     version: str
#     models_available: int
#     uptime: str
#     response_time_ms: int
#     timestamp: float

class StreamController:
    def __init__(self, llm_service: LLMStreamInterface):
        self.llm_service = llm_service
    
    async def stream_chat_response(self, request: StreamRequestAPI) -> StreamingResponse:
        stream_request = StreamRequest(
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        async def generate_stream():
            try:
                async for chunk in self.llm_service.stream_generate(stream_request):
                    chunk_data = {
                        "content": chunk.content,
                        "status": chunk.status.value,
                        "chunk_id": chunk.chunk_id,
                        "timestamp": chunk.timestamp,
                        "metadata": chunk.metadata
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
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
        stream_request = StreamRequest(
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return await self.llm_service.generate(stream_request)

_controller_instance = None

def get_controller() -> StreamController:
    if _controller_instance is None:
        raise HTTPException(status_code=500, detail="Controller not initialized")
    return _controller_instance

def set_controller(controller: StreamController):
    global _controller_instance
    _controller_instance = controller

# ====== ОСТАВЛЕННЫЕ РУЧКИ ======

@router.post("/stream")
async def stream_response(
    request: StreamRequestAPI,
    current_user: User = Depends(get_current_active_user),
    controller: StreamController = Depends(get_controller)
):
    if not request.stream:
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
    return controller.llm_service.get_supported_models()

# ====== ЗАКОММЕНТИРОВАНО ======

# @router.get("/models/{model_name}", response_model=ModelInfo)
# async def get_model_info(...):
#     ...

# @router.get("/health", response_model=HealthResponse)
# async def health_check(...):
#     ...

# @router.get("/stats")
# async def get_usage_statistics(...):
#     ...

# @router.post("/conversation/summary")
# async def get_conversation_summary(...):
#     ...

# @router.post("/suggestions")
# async def get_question_suggestions(...):
#     ...

# @router.get("/test/stream-connection")
# async def test_stream_connection(...):
#     ...
