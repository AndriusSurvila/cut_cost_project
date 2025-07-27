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

def generate_ai_response(prompt: str, db: Session = None) -> str:
    """Генерирует ответ от AI модели (без стриминга)"""
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    data = {
        "model": "mistral",
        "prompt": prompt.strip(),
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=data, timeout=90)
        response.raise_for_status()
        
        result = response.json()
        ai_response = result.get("response", "").strip()
        
        if not ai_response:
            raise HTTPException(status_code=502, detail="Empty response from AI model")
            
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

def stream_ai_response(prompt: str):
    """Стримит ответ от AI модели"""
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
    data = {
        "model": "mistral", 
        "prompt": prompt.strip(),
        "stream": True
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