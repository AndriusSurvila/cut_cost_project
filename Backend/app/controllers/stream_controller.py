from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import SessionLocal
from app.models.models import Chat, Message
from app.policies.policies import generate_ai_response
from pydantic import BaseModel
from typing import List

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatCreate(BaseModel):
    title: str

class MessageCreate(BaseModel):
    content: str
    role: str  # user

@router.post("/chats", response_model=dict)
def create_chat(data: ChatCreate, db: Session = Depends(get_db)):
    chat = Chat(title=data.title)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return {"id": chat.id, "title": chat.title}

@router.get("/chats", response_model=List[dict])
def list_chats(db: Session = Depends(get_db)):
    chats = db.query(Chat).all()
    return [{"id": c.id, "title": c.title} for c in chats]

@router.post("/chats/{chat_id}/messages", response_model=dict)
def post_message(chat_id: int, data: MessageCreate, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    user_msg = Message(chat_id=chat_id, content=data.content, role="user")
    db.add(user_msg)

    # генерируем ответ
    ai_response = generate_ai_response(data.content)
    ai_msg = Message(chat_id=chat_id, content=ai_response, role="ai")
    db.add(ai_msg)

    db.commit()
    return {"user": user_msg.content, "ai": ai_msg.content}

@router.get("/chats/{chat_id}/messages", response_model=List[dict])
def get_messages(chat_id: int, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.chat_id == chat_id).all()
    return [{"role": m.role, "content": m.content} for m in messages]

@router.get("/chats/{chat_id}/export", response_model=dict)
def export_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return {
        "id": chat.id,
        "title": chat.title,
        "messages": [{"role": m.role, "content": m.content} for m in chat.messages]
    }
