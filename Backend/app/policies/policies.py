import requests
from fastapi import HTTPException
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.models import Chat, Message
import os
import json

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

def generate_ai_response(prompt: str, db: Session = None) -> str:
    """Генерирует ответ от AI модели (без стриминга)"""
    data = {
        "model": "mistral",
        "prompt": prompt.strip(),
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=data, timeout=90)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Ollama timeout")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {str(e)}")

def stream_ai_response(prompt: str):
    """Стримит ответ от AI модели"""
    data = {
        "model": "mistral", 
        "prompt": prompt.strip(),
        "stream": True
    }

    try:
        response = requests.post(OLLAMA_URL, json=data, stream=True, timeout=90)
        response.raise_for_status()

        def generate():
            for line in response.iter_lines():
                if line:
                    try:
                        json_response = json.loads(line.decode("utf-8"))
                        if "response" in json_response:
                            yield json_response["response"]
                    except json.JSONDecodeError:
                        continue

        return StreamingResponse(generate(), media_type="text/plain")

    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Ollama timeout")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {str(e)}")

def save_message_to_chat(db: Session, chat_id: int, role: str, content: str) -> Message:
    """Сохраняет сообщение в чат"""
    message = Message(chat_id=chat_id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_or_create_chat(db: Session, chat_id: int = None, title: str = "New Chat") -> Chat:
    """Получает существующий чат или создает новый"""
    if chat_id:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if chat:
            return chat
    
    # Создаем новый чат
    chat = Chat(title=title)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat