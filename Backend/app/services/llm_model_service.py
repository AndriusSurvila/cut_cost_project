import g4f
from g4f.client import Client
from typing import Optional, List, Dict
import logging
from sqlalchemy.orm import Session

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMModelService:
    def __init__(self):
        self.client = Client()
        self.default_model = "gpt-3.5-turbo"
    
    def generate_response(self, 
                         prompt: str, 
                         conversation_history: List[Dict[str, str]] = None,
                         model: str = None) -> str:
        """
        Генерирует ответ с учетом истории разговора
        
        Args:
            prompt (str): Текущее сообщение пользователя
            conversation_history (List[Dict]): История сообщений [{"role": "user/assistant", "content": "..."}]
            model (str): Модель для использования
            
        Returns:
            str: Ответ от AI модели
        """
        try:
            model = model or self.default_model
            logger.info(f"Генерация ответа с моделью {model}")
            
            # Формируем историю сообщений для контекста
            messages = []
            
            # Добавляем системное сообщение
            messages.append({
                "role": "system",
                "content": "Ты полезный AI ассистент. Отвечай корректно и по делу на русском языке."
            })
            
            # Добавляем историю разговора
            if conversation_history:
                messages.extend(conversation_history)
            
            # Добавляем текущий запрос
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Ограничиваем количество сообщений для контекста
            if len(messages) > 20:  # Оставляем последние 19 сообщений + системное
                messages = messages[:1] + messages[-(19):]
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=False
            )
            
            result = response.choices[0].message.content
            logger.info("Ответ успешно сгенерирован")
            return result
            
        except Exception as e:
            error_msg = f"Ошибка при генерации ответа: {str(e)}"
            logger.error(error_msg)
            # Возвращаем дружелюбное сообщение об ошибке
            return "Извините, произошла ошибка при генерации ответа. Попробуйте еще раз."
    
    def generate_stream_response(self, 
                               prompt: str, 
                               conversation_history: List[Dict[str, str]] = None,
                               model: str = None):
        """
        Генерирует потоковый ответ
        """
        try:
            model = model or self.default_model
            logger.info(f"Генерация потокового ответа с моделью {model}")
            
            messages = []
            messages.append({
                "role": "system",
                "content": "Ты полезный AI ассистент. Отвечай корректно и по делу на русском языке."
            })
            
            if conversation_history:
                messages.extend(conversation_history)
            
            messages.append({
                "role": "user", 
                "content": prompt
            })
            
            if len(messages) > 20:
                messages = messages[:1] + messages[-(19):]
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            error_msg = f"Ошибка при потоковой генерации: {str(e)}"
            logger.error(error_msg)
            yield "Извините, произошла ошибка при генерации ответа."
    
    def get_available_models(self) -> List[str]:
        """Возвращает список доступных моделей"""
        return [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo-preview", 
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "gemini-pro"
        ]

# Создаем глобальный экземпляр сервиса
llm_service = LLMModelService()

def get_conversation_history_from_db(db: Session, chat_id: int, limit: int = 10) -> List[Dict[str, str]]:
    """
    Получает историю сообщений из базы данных
    
    Args:
        db: Сессия базы данных
        chat_id: ID чата
        limit: Количество последних сообщений для загрузки
        
    Returns:
        List[Dict]: Список сообщений в формате [{"role": "user/assistant", "content": "..."}]
    """
    try:
        from app.models.models import Message
        
        # Получаем последние сообщения из чата
        messages = db.query(Message).filter(
            Message.chat_id == chat_id
        ).order_by(Message.created_at.desc()).limit(limit).all()
        
        # Переворачиваем порядок (от старых к новым)
        messages = list(reversed(messages))
        
        # Конвертируем в нужный формат
        history = []
        for msg in messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return history[:-1]  # Исключаем последнее сообщение (это текущий запрос)
        
    except Exception as e:
        logger.error(f"Ошибка при получении истории: {e}")
        return []


# Функции для интеграции с существующим кодом
def generate_ai_response(prompt: str, 
                        db: Session = None, 
                        chat_id: int = None, 
                        history_limit: int = 10,
                        model: str = None) -> str:
    """
    Основная функция для генерации AI ответа с учетом контекста
    Совместима с вашим существующим кодом
    """
    conversation_history = []
    
    # Если переданы параметры для получения истории из БД
    if db and chat_id:
        conversation_history = get_conversation_history_from_db(db, chat_id, history_limit)
    
    return llm_service.generate_response(
        prompt=prompt,
        conversation_history=conversation_history,
        model=model
    )

def stream_ai_response(prompt: str,
                      db: Session = None,
                      chat_id: int = None,
                      history_limit: int = 10,
                      model: str = None):
    """
    Функция для потоковой генерации AI ответа
    """
    conversation_history = []
    
    if db and chat_id:
        conversation_history = get_conversation_history_from_db(db, chat_id, history_limit)
    
    return llm_service.generate_stream_response(
        prompt=prompt,
        conversation_history=conversation_history,
        model=model
    )


# Тестирование
if __name__ == "__main__":
    test_prompt = "Привет! Как дела?"
    print("Тест базовой функциональности:")
    result = generate_ai_response(test_prompt)
    print(f"Результат: {result}")
    
    print("\n" + "="*50 + "\n")
    
    print("Тест с историей:")
    history = [
        {"role": "user", "content": "Меня зовут Алексей"},
        {"role": "assistant", "content": "Приятно познакомиться, Алексей!"},
        {"role": "user", "content": "Как меня зовут?"}
    ]
    
    result2 = llm_service.generate_response("Как меня зовут?", history[:-1])
    print(f"Результат: {result2}")