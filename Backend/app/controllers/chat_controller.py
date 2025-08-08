from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.models.session import get_db
from app.models.models import Chat, Message, User
from app.dependencies.auth import get_current_active_user
from app.policies.policies import generate_ai_response, save_message_to_chat
from sqlalchemy import or_
# stream_ai_response, get_or_create_chat — не используем

router = APIRouter()

class ChatCreate(BaseModel):
    title: Optional[str] = "New Chat"

# class ChatUpdate(BaseModel):
#     title: str

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


# ====== ОСТАВЛЕННЫЕ РУЧКИ ======

@router.get("/chats", response_model=List[ChatResponse])
def get_all_chats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    chats = db.query(Chat).filter(Chat.user_id == current_user.id).all()
    return chats


@router.post("/chats", response_model=ChatResponse)
def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    chat = Chat(title=chat_data.title, user_id=current_user.id)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/chats/{chat_id}", response_model=ChatResponse)
def get_chat(
    chat_id: int = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.delete("/chats/{chat_id}")
def delete_chat(
    chat_id: int = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    db.delete(chat)
    db.commit()
    return {"message": "Chat deleted successfully"}


@router.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
def get_chat_messages(
    chat_id: int = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return db.query(Message).filter(Message.chat_id == chat_id).all()


@router.post("/chats/{chat_id}/messages")
def send_message(
    chat_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
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



@router.get("/chats/search", response_model=List[ChatResponse])
def search_chats(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Поиск по чату и сообщениям"""
    chats = db.query(Chat).join(Message).filter(
        Chat.user_id == current_user.id,
        or_(
            Chat.title.ilike(f"%{q}%"),
            Message.content.ilike(f"%{q}%")
        )
    ).distinct().all()
    
    return chats

# ====== ЗАКОММЕНТИРОВАНО ======

# @router.put("/chats/{chat_id}", response_model=ChatResponse)
# def update_chat(...):
#     ...

# @router.delete("/chats/{chat_id}/messages/{message_id}")
# def delete_message(...):
#     ...

# @router.post("/chats/{chat_id}/stream")
# def stream_chat_response(...):
#     ...

# @router.get("/chats/{chat_id}/export")
# def export_chat(...):
#     ...
