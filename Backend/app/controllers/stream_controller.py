from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from app.contracts.stream_interface import LLMStreamInterface
from typing import AsyncGenerator, Generator
import asyncio
import json

class StreamController:
    def __init__(self, streamer: LLMStreamInterface):
        self.llm = streamer

    async def predict(self, prompt: str) -> str:
        """Получить полный ответ от LLM"""
        try:
            if not prompt or not prompt.strip():
                raise HTTPException(status_code=400, detail="Prompt cannot be empty")
            
            result = await self.llm.predict(prompt)
            
            if not result:
                raise HTTPException(status_code=500, detail="LLM returned empty response")
            
            return result
            
        except HTTPException:
            raise  # Пробрасываем HTTP ошибки как есть
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    async def stream_response(self, prompt: str) -> StreamingResponse:
        """Стриминговый ответ для FastAPI"""
        try:
            if not prompt or not prompt.strip():
                raise HTTPException(status_code=400, detail="Prompt cannot be empty")
            
            async def generate_stream():
                try:
                    async for chunk in self.llm.predict_stream(prompt):
                        if chunk:
                            # Отправляем данные в формате Server-Sent Events
                            yield f"data: {json.dumps({'content': chunk, 'type': 'content'})}\n\n"
                    
                    # Сигнал завершения
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    
                except Exception as e:
                    # Отправляем ошибку через стрим
                    error_data = {
                        'type': 'error', 
                        'error': str(e)
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*"
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Stream initialization failed: {str(e)}")

    async def stream_generator(self, prompt: str) -> AsyncGenerator[str, None]:
        """Генератор для стриминга (если нужен отдельно)"""
        try:
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            async for chunk in self.llm.predict_stream(prompt):
                if chunk:
                    yield chunk
                    
        except Exception as e:
            raise Exception(f"Stream generation failed: {str(e)}")

    def validate_prompt(self, prompt: str, max_length: int = 4000) -> bool:
        """Валидация промпта"""
        if not prompt or not prompt.strip():
            return False
        
        if len(prompt) > max_length:
            return False
        
        return True

    async def predict_with_validation(self, prompt: str, max_length: int = 4000) -> str:
        """Предсказание с валидацией"""
        if not self.validate_prompt(prompt, max_length):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid prompt. Must be non-empty and less than {max_length} characters"
            )
        
        return await self.predict(prompt)