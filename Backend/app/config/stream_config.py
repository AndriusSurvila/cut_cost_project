import os
from typing import Type
from app.contracts.stream_interface import LLMStreamInterface
from app.services.mock_stream_service import MockStreamService
from app.services.api_model_service import GeminiModelService
from app.controllers.stream_controller import StreamController, set_controller
from app.container import EnhancedContainer

class StreamConfig:
    """Конфигурация для настройки стрим-сервисов"""
    
    @staticmethod
    def get_llm_service_class() -> Type[LLMStreamInterface]:
        """Определяет какой сервис использовать на основе переменных окружения"""
        service_mode = os.getenv("LLM_SERVICE_MODE", "mock").lower()
        
        if service_mode == "mock":
            return MockStreamService
        elif service_mode == "gemini":
            return GeminiModelService
        else:
            # По умолчанию используем мок
            return MockStreamService
    
    @staticmethod
    def setup_container() -> EnhancedContainer:
        """Настройка DI контейнера"""
        container = EnhancedContainer()
        
        llm_service_class = StreamConfig.get_llm_service_class()
        container.register_singleton(LLMStreamInterface, llm_service_class)
        
        container.register_transient(StreamController, StreamController)
        
        return container
    
    @staticmethod
    def initialize_services() -> StreamController:
        """Инициализация всех сервисов"""
        container = StreamConfig.setup_container()
        
        controller = container.resolve(StreamController)
        
        # Устанавливаем глобальный экземпляр контроллера для зависимостей
        set_controller(controller)
        
        return controller
