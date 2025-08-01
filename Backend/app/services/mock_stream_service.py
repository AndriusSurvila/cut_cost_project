import asyncio
import time
import uuid
import random
from typing import AsyncGenerator, Dict, Any, List, Optional
from app.contracts.stream_interface import (
    LLMStreamInterface, 
    StreamRequest, 
    StreamChunk, 
    StreamStatus
)

class MockStreamService(LLMStreamInterface):
    """Мок-реализация для тестирования AI стрима"""
    
    def __init__(self):
        self.supported_models = ["mock-gpt-3.5", "mock-gpt-4", "mock-claude", "mock-llama"]
        self.model_info = {
            "mock-gpt-3.5": {
                "name": "Mock GPT-3.5",
                "description": "Mock implementation of GPT-3.5",
                "max_tokens": 4096,
                "temperature_range": [0.0, 2.0]
            },
            "mock-gpt-4": {
                "name": "Mock GPT-4",
                "description": "Mock implementation of GPT-4",
                "max_tokens": 8192,
                "temperature_range": [0.0, 2.0]
            },
            "mock-claude": {
                "name": "Mock Claude",
                "description": "Mock implementation of Claude",
                "max_tokens": 8192,
                "temperature_range": [0.0, 1.0]
            },
            "mock-llama": {
                "name": "Mock LLaMA",
                "description": "Mock implementation of LLaMA",
                "max_tokens": 2048,
                "temperature_range": [0.0, 1.5]
            }
        }
        
    def _get_mock_responses(self, prompt: str) -> List[str]:
        """Генерирует мок-ответы в зависимости от промпта"""
        prompt_lower = prompt.lower()
        
        if "python" in prompt_lower or "код" in prompt_lower:
            return [
                "Конечно! Вот пример кода на Python:\n\n",
                "```python\n",
                "def hello_world():\n",
                "    print('Hello, World!')\n",
                "    return 'Success'\n\n",
                "# Вызов функции\n",
                "result = hello_world()\n",
                "print(f'Результат: {result}')\n",
                "```\n\n",
                "Этот код демонстрирует базовую функцию в Python. ",
                "Функция выводит приветствие и возвращает статус выполнения."
            ]
        elif "погода" in prompt_lower or "weather" in prompt_lower:
            return [
                "К сожалению, у меня нет доступа к актуальным данным о погоде. ",
                "Однако я могу порекомендовать несколько способов узнать погоду:\n\n",
                "1. Воспользоваться сайтами: weather.com, gismeteo.ru\n",
                "2. Мобильные приложения погоды\n",
                "3. Голосовые помощники (Siri, Google Assistant)\n",
                "4. API сервисы для получения данных программно"
            ]
        elif "привет" in prompt_lower or "hello" in prompt_lower:
            return [
                "Привет! 👋 Рад тебя видеть! ",
                "Как дела? Чем могу помочь? ",
                "Готов ответить на твои вопросы и помочь с различными задачами. ",
                "Просто спроси о чём угодно!"
            ]
        elif "математика" in prompt_lower or "math" in prompt_lower:
            return [
                "Математика - это увлекательная наука! ",
                "Вот несколько интересных фактов:\n\n",
                "• Число π (пи) содержит бесконечное количество цифр\n",
                "• Золотое сечение φ ≈ 1.618 встречается в природе\n",
                "• Теорема Пифагора: a² + b² = c²\n",
                "• Формула Эйлера: e^(iπ) + 1 = 0\n\n",
                "С какой областью математики тебе нужна помощь?"
            ]
        else:
            return [
                "Интересный вопрос! ",
                "Позвольте мне подумать над этим... ",
                "Основываясь на вашем запросе, могу сказать следующее:\n\n",
                "Это довольно сложная тема, которая требует детального рассмотрения. ",
                "Рекомендую изучить дополнительные источники информации ",
                "и проконсультироваться со специалистами в данной области. ",
                "Если у вас есть более конкретные вопросы, ",
                "я буду рад помочь с ними!"
            ]

    async def stream_generate(
        self, 
        request: StreamRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """Асинхронная генерация стрима с мок-данными"""
        
        stream_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Стартовый чанк
        yield StreamChunk(
            content="",
            status=StreamStatus.STARTED,
            chunk_id=f"{stream_id}_start",
            timestamp=start_time,
            metadata={
                "stream_id": stream_id,
                "model": request.model or "mock-gpt-3.5",
                "temperature": request.temperature
            }
        )
        
        # Имитация задержки перед началом генерации
        await asyncio.sleep(0.5)
        
        try:
            mock_responses = self._get_mock_responses(request.prompt)
            
            for i, response_part in enumerate(mock_responses):
                # Разбиваем каждую часть на слова для более реалистичного стрима
                words = response_part.split()
                
                for j, word in enumerate(words):
                    chunk_content = word + " " if j < len(words) - 1 else word
                    
                    yield StreamChunk(
                        content=chunk_content,
                        status=StreamStatus.STREAMING,
                        chunk_id=f"{stream_id}_{i}_{j}",
                        timestamp=time.time(),
                        metadata={
                            "part_index": i,
                            "word_index": j,
                            "total_parts": len(mock_responses)
                        }
                    )
                    
                    # Случайная задержка для реалистичности
                    delay = random.uniform(0.05, 0.3)
                    await asyncio.sleep(delay)
            
            # Завершающий чанк
            completion_time = time.time() - start_time
            yield StreamChunk(
                content="",
                status=StreamStatus.COMPLETED,
                chunk_id=f"{stream_id}_end",
                timestamp=time.time(),
                metadata={
                    "completion_time": completion_time,
                    "total_tokens": sum(len(part.split()) for part in mock_responses),
                    "model_used": request.model or "mock-gpt-3.5"
                }
            )
            
        except Exception as e:
            yield StreamChunk(
                content="",
                status=StreamStatus.ERROR,
                chunk_id=f"{stream_id}_error",
                timestamp=time.time(),
                metadata={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )

    async def generate(self, request: StreamRequest) -> str:
        """Генерация полного ответа без стриминга"""
        mock_responses = self._get_mock_responses(request.prompt)
        
        # Имитация времени обработки
        processing_time = random.uniform(0.5, 2.0)
        await asyncio.sleep(processing_time)
        
        return "".join(mock_responses)

    def get_supported_models(self) -> List[str]:
        """Возвращает список поддерживаемых моделей"""
        return self.supported_models.copy()

    async def health_check(self) -> Dict[str, Any]:
        """Проверка состояния мок-сервиса"""
        return {
            "status": "healthy",
            "service": "MockStreamService",
            "version": "1.0.0",
            "models_available": len(self.supported_models),
            "uptime": "99.9%",
            "response_time_ms": random.randint(50, 200),
            "timestamp": time.time()
        }

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Получение информации о модели"""
        return self.model_info.get(model_name)

    # Дополнительные методы для расширенной функциональности
    
    async def get_conversation_summary(self, messages: List[str]) -> str:
        """Генерация краткого содержания беседы"""
        await asyncio.sleep(0.5)  # Имитация обработки
        
        total_messages = len(messages)
        total_words = sum(len(msg.split()) for msg in messages)
        
        return f"Краткое содержание беседы: {total_messages} сообщений, ~{total_words} слов. Основные темы: общение, вопросы и ответы."

    async def suggest_next_questions(self, context: str) -> List[str]:
        """Предложение следующих вопросов на основе контекста"""
        await asyncio.sleep(0.3)
        
        context_lower = context.lower()
        
        if "python" in context_lower:
            return [
                "Как работает декораторы в Python?",
                "Что такое list comprehensions?",
                "Как использовать async/await?",
                "Объясни различия между классами и функциями"
            ]
        elif "математика" in context_lower:
            return [
                "Что такое производные и интегралы?",
                "Как решать системы уравнений?",
                "Объясни теорию вероятностей",
                "Что такое матрицы и как с ними работать?"
            ]
        else:
            return [
                "Можешь рассказать подробнее?",
                "Приведи примеры использования",
                "Какие есть альтернативы?",
                "Где это применяется на практике?"
            ]

    def get_usage_statistics(self) -> Dict[str, Any]:
        """Получение статистики использования (мок-данные)"""
        return {
            "total_requests": random.randint(1000, 5000),
            "successful_streams": random.randint(900, 4500),
            "failed_requests": random.randint(10, 100),
            "average_response_time": random.uniform(0.5, 2.0),
            "most_used_model": random.choice(self.supported_models),
            "uptime_percentage": random.uniform(95.0, 99.9)
        }