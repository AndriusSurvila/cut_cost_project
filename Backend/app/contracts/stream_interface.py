from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional, List
from pydantic import BaseModel
from enum import Enum

class StreamStatus(Enum):
    """Статусы стрима"""
    STARTED = "started"
    STREAMING = "streaming"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"

class StreamChunk(BaseModel):
    """Модель для чанка стрима"""
    content: str
    status: StreamStatus = StreamStatus.STREAMING
    metadata: Optional[Dict[str, Any]] = None
    chunk_id: Optional[str] = None
    timestamp: Optional[float] = None

class StreamRequest(BaseModel):
    """Модель запроса для стрима"""
    prompt: str
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream_options: Optional[Dict[str, Any]] = None

class StreamResponse(BaseModel):
    """Модель ответа стрима"""
    stream_id: str
    status: StreamStatus
    total_tokens: Optional[int] = None
    completion_time: Optional[float] = None
    error_message: Optional[str] = None

class LLMStreamInterface(ABC):
    """Интерфейс для стриминга LLM ответов"""
    
    @abstractmethod
    async def stream_generate(
        self, 
        request: StreamRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Асинхронная генерация стрима ответов
        
        Args:
            request: Параметры запроса
            
        Yields:
            StreamChunk: Чанки ответа
        """
        pass
    
    @abstractmethod
    async def generate(self, request: StreamRequest) -> str:
        """
        Генерация полного ответа без стриминга
        
        Args:
            request: Параметры запроса
            
        Returns:
            str: Полный ответ
        """
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """
        Получение списка поддерживаемых моделей
        
        Returns:
            List[str]: Список названий моделей
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Проверка состояния сервиса
        
        Returns:
            Dict[str, Any]: Информация о состоянии
        """
        pass
    
    @abstractmethod
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о модели
        
        Args:
            model_name: Название модели
            
        Returns:
            Optional[Dict[str, Any]]: Информация о модели или None
        """
        pass