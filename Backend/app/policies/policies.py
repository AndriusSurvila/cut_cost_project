import requests
from fastapi import HTTPException
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.models import Chat, Message
import os
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

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

def format_chat_history(messages: list) -> str:
    """
    Форматирует историю сообщений в текстовый контекст для LLM
    
    Args:
        messages: List of Message objects
    
    Returns:
        Formatted string with conversation history
    """
    if not messages:
        return ""
    
    context_parts = ["Контекст предыдущей беседы:"]
    
    for msg in messages:
        role_name = "Пользователь" if msg.role == "user" else "Ассистент"
        context_parts.append(f"{role_name}: {msg.content}")
    
    context_parts.append("\nНовое сообщение пользователя:")
    
    return "\n".join(context_parts)

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
    
    # Формируем полный контекст с историей
    full_prompt = prompt.strip()
    
    if db and chat_id:
        try:
            # Получаем историю сообщений
            history_messages = get_chat_history(db, chat_id, history_limit)
            
            if history_messages:
                # Форматируем историю и добавляем к промпту
                history_context = format_chat_history(history_messages)
                full_prompt = f"{history_context}\n{prompt.strip()}"
                
                logger.info(f"Added {len(history_messages)} messages to context for chat {chat_id}")
        except Exception as e:
            logger.warning(f"Failed to fetch chat history: {str(e)}. Proceeding without history.")
    
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
            raise HTTPException(status_code=502, detail="Empty response from AI model")
            
        logger.info(f"Generated AI response for chat {chat_id}")
        return ai_response
    
    except requests.Timeout:
        logger.error("Ollama request timeout")
        raise HTTPException(status_code=504, detail="AI service timeout")
    except requests.RequestException as e:
        logger.error(f"Ollama request error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        raise HTTPException(status_code=502, detail="Invalid response from AI service")

def stream_ai_response(prompt: str, db: Session = None, chat_id: int = None, history_limit: int = 10):
    """
    Стримит ответ от AI модели с учетом истории сообщений
    
    Args:
        prompt: Новое сообщение пользователя  
        db: Database session
        chat_id: ID чата для получения истории
        history_limit: Количество сообщений истории для контекста
    """
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    # Формируем полный контекст с историей (аналогично generate_ai_response)
    full_prompt = prompt.strip()
    
    if db and chat_id:
        try:
            history_messages = get_chat_history(db, chat_id, history_limit)
            if history_messages:
                history_context = format_chat_history(history_messages)
                full_prompt = f"{history_context}\n{prompt.strip()}"
                logger.info(f"Added {len(history_messages)} messages to streaming context for chat {chat_id}")
        except Exception as e:
            logger.warning(f"Failed to fetch chat history for streaming: {str(e)}. Proceeding without history.")
        
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

        def generate():
            try:
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
                            logger.warning(f"Failed to decode JSON: {line}")
                            continue
                        except Exception as e:
                            logger.error(f"Error processing stream chunk: {str(e)}")
                            continue
            except Exception as e:
                logger.error(f"Error in stream generation: {str(e)}")
                yield f"[Error] Stream interrupted: {str(e)}"

        return StreamingResponse(generate(), media_type="text/plain")

    except requests.Timeout:
        logger.error("Ollama stream timeout")
        raise HTTPException(status_code=504, detail="AI service timeout")
    except requests.RequestException as e:
        logger.error(f"Ollama stream error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")

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