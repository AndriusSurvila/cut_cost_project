import os
import json
import logging
import requests
from typing import List, Dict, Generator, Optional
from fastapi import HTTPException
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.models import Chat, Message

# Импорт gpt4free (только если нужен)
try:
    import g4f
    from g4f.client import Client
    GPT4FREE_AVAILABLE = True
except ImportError:
    GPT4FREE_AVAILABLE = False
    g4f = None
    Client = None

logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
LLM_SERVICE_MODE = os.getenv("LLM_SERVICE_MODE", "mock")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

# GPT4Free настройки
GPT4FREE_MODEL = os.getenv("GPT4FREE_MODEL", "gpt-3.5-turbo")
GPT4FREE_TIMEOUT = int(os.getenv("GPT4FREE_TIMEOUT", "90"))
GPT4FREE_TEMPERATURE = float(os.getenv("GPT4FREE_TEMPERATURE", "0.7"))
GPT4FREE_MAX_TOKENS = int(os.getenv("GPT4FREE_MAX_TOKENS", "2048"))

# Инициализация GPT4Free клиента
gpt4free_client = None
if LLM_SERVICE_MODE == "gpt4free":
    if GPT4FREE_AVAILABLE:
        try:
            gpt4free_client = Client()
            logger.info("GPT4Free client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GPT4Free client: {str(e)}")
    else:
        logger.error("GPT4Free is not installed. Install with: pip install g4f")

logger.info(f"LLM Service Mode: {LLM_SERVICE_MODE}")

def get_chat_history(db: Session, chat_id: int, limit: int = 10) -> list:
    """
    Получает последние N сообщений из чата для формирования контекста
    
    Args:
        db: Database session
        chat_id: ID чата
        limit: Количество последних сообщений для включения в историю
    
    Returns:
        List of messages ordered by creation time (oldest first for context)
    """
    try:
        messages = db.query(Message)\
            .filter(Message.chat_id == chat_id)\
            .filter(Message.role.in_(["user", "assistant"]))\
            .order_by(Message.created_at.desc())\
            .limit(limit)\
            .all()
        
        # Возвращаем в прямом порядке (от старых к новым) для правильного контекста
        return list(reversed(messages))
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        return []

def format_chat_history_for_gpt(messages: list) -> List[Dict[str, str]]:
    """Форматирует историю для GPT API"""
    formatted_messages = []
    
    # Системное сообщение
    formatted_messages.append({
        "role": "system",
        "content": "Ты полезный AI ассистент. Отвечай корректно и по делу на русском языке."
    })
    
    # История сообщений
    for msg in messages:
        role = "assistant" if msg.role == "assistant" else "user"
        formatted_messages.append({
            "role": role,
            "content": msg.content
        })
    
    return formatted_messages

def format_chat_history_for_ollama(messages: list) -> str:
    """Форматирует историю для Ollama"""
    if not messages:
        return ""
    
    context_parts = ["Контекст предыдущей беседы:"]
    
    for msg in messages:
        role_name = "Пользователь" if msg.role == "user" else "Ассистент"
        context_parts.append(f"{role_name}: {msg.content}")
    
    context_parts.append("\nНовое сообщение пользователя:")
    return "\n".join(context_parts)

# =============================================================================
# MOCK IMPLEMENTATION
# =============================================================================

def _generate_mock_response(prompt: str) -> str:
    """Генерирует мок-ответ для тестирования"""
    mock_responses = [
        f"Это мок-ответ на ваше сообщение: '{prompt[:50]}...'",
        "Мок-режим активирован. Привет! Как дела?",
        "Тестовый ответ от мок-сервиса. Все работает!",
        f"Получено сообщение длиной {len(prompt)} символов. Отвечаю в тестовом режиме.",
    ]
    
    # Простая логика выбора ответа
    response_index = len(prompt) % len(mock_responses)
    return mock_responses[response_index]

def _stream_mock_response(prompt: str) -> Generator[str, None, None]:
    """Генерирует потоковый мок-ответ"""
    response = _generate_mock_response(prompt)
    words = response.split()
    
    for word in words:
        yield word + " "

# =============================================================================
# OLLAMA IMPLEMENTATION  
# =============================================================================

def _generate_ollama_response(prompt: str, history_messages: list = None) -> str:
    """Генерирует ответ через Ollama"""
    full_prompt = prompt.strip()
    
    if history_messages:
        history_context = format_chat_history_for_ollama(history_messages)
        full_prompt = f"{history_context}\n{prompt.strip()}"
    
    data = {
        "model": "mistral",
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2048
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=data, timeout=90)
        response.raise_for_status()
        
        result = response.json()
        ai_response = result.get("response", "").strip()
        
        if not ai_response:
            raise HTTPException(status_code=502, detail="Empty response from Ollama")
            
        return ai_response
    
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Ollama service timeout")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ollama service error: {str(e)}")

def _stream_ollama_response(prompt: str, history_messages: list = None) -> Generator[str, None, None]:
    """Генерирует потоковый ответ через Ollama"""
    full_prompt = prompt.strip()
    
    if history_messages:
        history_context = format_chat_history_for_ollama(history_messages)
        full_prompt = f"{history_context}\n{prompt.strip()}"
        
    data = {
        "model": "mistral", 
        "prompt": full_prompt,
        "stream": True,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2048
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=data, stream=True, timeout=90)
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    json_response = json.loads(line.decode("utf-8"))
                    if "response" in json_response:
                        chunk = json_response["response"]
                        if chunk:
                            yield chunk
                    if json_response.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue
                        
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Ollama service timeout")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ollama service error: {str(e)}")

# =============================================================================
# GPT4FREE IMPLEMENTATION
# =============================================================================

def _generate_gpt4free_response(prompt: str, history_messages: list = None) -> str:
    """Генерирует ответ через GPT4Free"""
    if not gpt4free_client:
        raise HTTPException(status_code=503, detail="GPT4Free service is not available")
    
    # Формируем сообщения для API
    messages = []
    
    if history_messages:
        messages = format_chat_history_for_gpt(history_messages)
    else:
        messages.append({
            "role": "system",
            "content": "Ты полезный AI ассистент. Отвечай корректно и по делу на русском языке."
        })
    
    # Добавляем текущий промпт
    messages.append({
        "role": "user",
        "content": prompt.strip()
    })
    
    # Ограничиваем количество сообщений
    if len(messages) > 20:
        messages = messages[:1] + messages[-(19):]

    try:
        response = gpt4free_client.chat.completions.create(
            model=GPT4FREE_MODEL,
            messages=messages,
            stream=False,
            # temperature=GPT4FREE_TEMPERATURE,
            # max_tokens=GPT4FREE_MAX_TOKENS,
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        if not ai_response:
            raise HTTPException(status_code=502, detail="Empty response from GPT4Free")
            
        return ai_response
    
    except Exception as e:
        logger.error(f"GPT4Free error: {str(e)}")
        if "timeout" in str(e).lower():
            raise HTTPException(status_code=504, detail="GPT4Free timeout")
        elif "rate limit" in str(e).lower():
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        else:
            raise HTTPException(status_code=502, detail=f"GPT4Free error: {str(e)}")

def _stream_gpt4free_response(prompt: str, history_messages: list = None) -> Generator[str, None, None]:
    """Генерирует потоковый ответ через GPT4Free"""
    if not gpt4free_client:
        yield "[Ошибка] GPT4Free сервис недоступен"
        return
    
    # Формируем сообщения
    messages = []
    
    if history_messages:
        messages = format_chat_history_for_gpt(history_messages)
    else:
        messages.append({
            "role": "system",
            "content": "Ты полезный AI ассистент. Отвечай корректно и по делу на русском языке."
        })
    
    messages.append({
        "role": "user", 
        "content": prompt.strip()
    })
    
    if len(messages) > 20:
        messages = messages[:1] + messages[-(19):]

    try:
        response = gpt4free_client.chat.completions.create(
            model=GPT4FREE_MODEL,
            messages=messages,
            stream=True,
            # temperature=GPT4FREE_TEMPERATURE,
            # max_tokens=GPT4FREE_MAX_TOKENS,
        )
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
                    
    except Exception as e:
        logger.error(f"GPT4Free stream error: {str(e)}")
        yield f"[Ошибка] {str(e)}"

# =============================================================================
# PUBLIC API - УНИВЕРСАЛЬНЫЕ ФУНКЦИИ
# =============================================================================

def generate_ai_response(prompt: str, db: Session = None, chat_id: int = None, history_limit: int = 10) -> str:
    """
    Генерирует ответ от AI модели с учетом истории сообщений
    
    Args:
        prompt: Новое сообщение пользователя
        db: Database session
        chat_id: ID чата для получения истории
        history_limit: Количество сообщений истории для контекста
    
    Returns:
        AI response string
    """
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    # Получаем историю сообщений
    history_messages = []
    if db and chat_id:
        try:
            history_messages = get_chat_history(db, chat_id, history_limit)
            if history_messages:
                logger.info(f"Added {len(history_messages)} messages to context for chat {chat_id}")
        except Exception as e:
            logger.warning(f"Failed to fetch chat history: {str(e)}. Proceeding without history.")
    
    # Выбираем реализацию в зависимости от режима
    if LLM_SERVICE_MODE == "mock":
        return _generate_mock_response(prompt)
    elif LLM_SERVICE_MODE == "ollama":
        return _generate_ollama_response(prompt, history_messages)
    elif LLM_SERVICE_MODE == "gpt4free":
        return _generate_gpt4free_response(prompt, history_messages)
    else:
        raise HTTPException(status_code=500, detail=f"Unknown LLM service mode: {LLM_SERVICE_MODE}")

def stream_ai_response(prompt: str, db: Session = None, chat_id: int = None, history_limit: int = 10):
    """
    Стримит ответ от AI модели с учетом истории сообщений
    """
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    # Получаем историю сообщений
    history_messages = []
    if db and chat_id:
        try:
            history_messages = get_chat_history(db, chat_id, history_limit)
            if history_messages:
                logger.info(f"Added {len(history_messages)} messages to streaming context for chat {chat_id}")
        except Exception as e:
            logger.warning(f"Failed to fetch chat history for streaming: {str(e)}. Proceeding without history.")

    def generate() -> Generator[str, None, None]:
        try:
            # Выбираем реализацию в зависимости от режима
            if LLM_SERVICE_MODE == "mock":
                yield from _stream_mock_response(prompt)
            elif LLM_SERVICE_MODE == "ollama":
                yield from _stream_ollama_response(prompt, history_messages)
            elif LLM_SERVICE_MODE == "gpt4free":
                yield from _stream_gpt4free_response(prompt, history_messages)
            else:
                yield f"[Ошибка] Неизвестный режим LLM: {LLM_SERVICE_MODE}"
        except Exception as e:
            logger.error(f"Error in stream generation: {str(e)}")
            yield f"[Ошибка] Поток прерван: {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain")

def save_message_to_chat(db: Session, chat_id: int, role: str, content: str) -> Message:
    """Сохраняет сообщение в чат"""
    if not content.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty")
    
    if role not in ["user", "assistant", "system"]:
        raise HTTPException(status_code=400, detail="Invalid message role")
    
    try:
        message = Message(chat_id=chat_id, role=role, content=content.strip())
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving message: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save message")

def get_or_create_chat(db: Session, user_id: int, chat_id: int = None, title: str = "New Chat") -> Chat:
    """Получает существующий чат или создает новый"""
    try:
        if chat_id:
            chat = db.query(Chat).filter(
                Chat.id == chat_id,
                Chat.user_id == user_id
            ).first()
            if chat:
                return chat
        
        chat = Chat(title=title.strip() or "New Chat", user_id=user_id)
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating/getting chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create chat")

def get_service_info() -> Dict[str, str]:
    """Возвращает информацию о текущем LLM сервисе"""
    info = {
        "mode": LLM_SERVICE_MODE,
        "status": "unknown"
    }
    
    if LLM_SERVICE_MODE == "mock":
        info["status"] = "healthy"
        info["model"] = "mock"
    elif LLM_SERVICE_MODE == "ollama":
        info["url"] = OLLAMA_URL
        info["model"] = "mistral"
        # Можно добавить проверку здоровья Ollama
        info["status"] = "healthy"  # Упрощенно
    elif LLM_SERVICE_MODE == "gpt4free":
        info["model"] = GPT4FREE_MODEL
        info["available"] = str(GPT4FREE_AVAILABLE)
        info["client_initialized"] = str(gpt4free_client is not None)
        info["status"] = "healthy" if gpt4free_client else "error"
    
    return info