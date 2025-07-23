from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.models.session import get_db
from app.models.models import Chat, Message
from app.policies.policies import generate_ai_response, stream_ai_response, save_message_to_chat, get_or_create_chat
import json

router = APIRouter()

class ChatCreate(BaseModel):
    title: Optional[str] = "New Chat"

class ChatUpdate(BaseModel):
    title: str

class MessageCreate(BaseModel):
    role: str = "user"
    content: str

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: str

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    id: int
    title: str
    created_at: str
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

@router.get("/chats", response_model=List[ChatResponse])
def get_all_chats(db: Session = Depends(get_db)):
    """Получить все чаты"""
    chats = db.query(Chat).all()
    return chats

@router.post("/chats", response_model=ChatResponse)
def create_chat(chat_data: ChatCreate, db: Session = Depends(get_db)):
    """Создать новый чат"""
    chat = Chat(title=chat_data.title)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat

@router.get("/chats/{chat_id}", response_model=ChatResponse)
def get_chat(chat_id: int = Path(...), db: Session = Depends(get_db)):
    """Получить чат по ID"""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@router.put("/chats/{chat_id}", response_model=ChatResponse)
def update_chat(chat_id: int, chat_data: ChatUpdate, db: Session = Depends(get_db)):
    """Обновить название чата"""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat.title = chat_data.title
    db.commit()
    db.refresh(chat)
    return chat

@router.delete("/chats/{chat_id}")
def delete_chat(chat_id: int = Path(...), db: Session = Depends(get_db)):
    """Удалить чат"""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    db.delete(chat)
    db.commit()
    return {"message": "Chat deleted successfully"}

@router.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
def get_chat_messages(chat_id: int = Path(...), db: Session = Depends(get_db)):
    """Получить все сообщения чата"""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = db.query(Message).filter(Message.chat_id == chat_id).all()
    return messages

@router.post("/chats/{chat_id}/messages")
def send_message(
    chat_id: int, 
    message_data: MessageCreate, 
    db: Session = Depends(get_db)
):
    """Отправить сообщение и получить ответ от AI"""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    user_message = save_message_to_chat(db, chat_id, "user", message_data.content)
    
    try:
        ai_response = generate_ai_response(message_data.content, db)
        
        ai_message = save_message_to_chat(db, chat_id, "assistant", ai_response)
        
        return {
            "user_message": {
                "id": user_message.id,
                "role": user_message.role,
                "content": user_message.content,
                "created_at": user_message.created_at.isoformat()
            },
            "ai_message": {
                "id": ai_message.id,
                "role": ai_message.role,
                "content": ai_message.content,
                "created_at": ai_message.created_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI response failed: {str(e)}")

@router.delete("/chats/{chat_id}/messages/{message_id}")
def delete_message(
    chat_id: int = Path(...), 
    message_id: int = Path(...), 
    db: Session = Depends(get_db)
):
    """Удалить сообщение"""
    message = db.query(Message).filter(
        Message.id == message_id, 
        Message.chat_id == chat_id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    db.delete(message)
    db.commit()
    return {"message": "Message deleted successfully"}

@router.post("/chats/{chat_id}/stream")
def stream_chat_response(chat_id: int, request: dict, db: Session = Depends(get_db)):
    """Стрим ответа AI"""
    prompt = request.get("prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    save_message_to_chat(db, chat_id, "user", prompt)
    
    return stream_ai_response(prompt)

@router.get("/chats/{chat_id}/export")
def export_chat(chat_id: int = Path(...), db: Session = Depends(get_db)):
    """Экспорт чата в JSON"""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = db.query(Message).filter(Message.chat_id == chat_id).all()
    
    export_data = {
        "chat_id": chat.id,
        "title": chat.title,
        "created_at": chat.created_at.isoformat(),
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }
    
    return export_data