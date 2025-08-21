import os
import httpx
import asyncio
import time
import uuid
from typing import AsyncGenerator, List, Dict, Any

from app.contracts.stream_interface import (
    LLMStreamInterface,
    StreamRequest,
    StreamChunk,
    StreamStatus
)

class GeminiModelService(LLMStreamInterface):
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.supported_models = ["gemini-1.5-flash", "gemini-1.5-pro"]

    async def stream_generate(
        self, request: StreamRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        stream_id = str(uuid.uuid4())
        start_time = time.time()
        model = request.model or "gemini-1.5-flash"

        yield StreamChunk(
            content="",
            status=StreamStatus.STARTED,
            chunk_id=f"{stream_id}_start",
            timestamp=start_time,
            metadata={"stream_id": stream_id, "model": model}
        )

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/{model}:generateContent?key={self.api_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": request.prompt}]}],
                        "generationConfig": {
                            "temperature": request.temperature,
                            "maxOutputTokens": request.max_tokens or 512
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]

                for i, word in enumerate(text.split()):
                    yield StreamChunk(
                        content=word + " ",
                        status=StreamStatus.STREAMING,
                        chunk_id=f"{stream_id}_{i}",
                        timestamp=time.time(),
                        metadata={"word_index": i}
                    )
                    await asyncio.sleep(0.05)

            yield StreamChunk(
                content="",
                status=StreamStatus.COMPLETED,
                chunk_id=f"{stream_id}_end",
                timestamp=time.time(),
                metadata={"completion_time": time.time() - start_time}
            )

        except Exception as e:
            yield StreamChunk(
                content="",
                status=StreamStatus.ERROR,
                chunk_id=f"{stream_id}_error",
                timestamp=time.time(),
                metadata={"error": str(e)}
            )

    async def generate(self, request: StreamRequest) -> str:
        model = request.model or "gemini-1.5-flash"
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/{model}:generateContent?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": request.prompt}]}],
                    "generationConfig": {
                        "temperature": request.temperature,
                        "maxOutputTokens": request.max_tokens or 512
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    def get_supported_models(self) -> List[str]:
        return self.supported_models

    # ADD THESE TWO MISSING METHODS:
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Return information about the Gemini model service"""
        return {
            "service_name": "Gemini",
            "provider": "Google",
            "supported_models": self.supported_models,
            "base_url": self.base_url,
            "api_configured": bool(self.api_key),
            "version": "1.5",
            "features": ["text_generation", "streaming", "temperature_control"]
        }

    async def health_check(self) -> bool:
        """Check if the Gemini service is healthy and accessible"""
        if not self.api_key:
            return False
        
        try:
            # Perform a simple test request to verify the service is working
            async with httpx.AsyncClient(timeout=10) as client:
                # Use a minimal test request
                response = await client.post(
                    f"{self.base_url}/gemini-1.5-flash:generateContent?key={self.api_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": "Hi"}]}],
                        "generationConfig": {
                            "maxOutputTokens": 10
                        }
                    }
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Gemini health check failed: {e}")
            return False