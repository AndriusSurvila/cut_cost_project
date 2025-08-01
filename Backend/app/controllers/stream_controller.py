from pydantic import BaseModel, validator
from typing import Optional, List

class StreamRequestAPI(BaseModel):
    """API модель для запроса стрима"""
    prompt: str
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: bool = True

    @validator('prompt')
    def validate_prompt(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Prompt cannot be empty')
        return v

    @validator('temperature')
    def validate_temperature(cls, v):
        if v is not None and not (0.0 <= v <= 2.0):
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v

    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        if v is not None and v <= 0:
            raise ValueError('max_tokens must be greater than 0')
        return v

class GenerateRequest(BaseModel):
    """API модель для генерации без стрима"""
    prompt: str
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

    @validator('prompt')
    def validate_prompt(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Prompt cannot be empty')
        return v

    @validator('temperature')
    def validate_temperature(cls, v):
        if v is not None and not (0.0 <= v <= 2.0):
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v

    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        if v is not None and v <= 0:
            raise ValueError('max_tokens must be greater than 0')
        return v

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
