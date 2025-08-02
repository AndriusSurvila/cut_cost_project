from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.models import Message, Chat
from app.models.session import get_db

router = APIRouter()

class MessageUpdate(BaseModel):
    content: str

class MessageViewUpdate(BaseModel):
    is_viewed: bool


@router.patch("/messages/{message_id}/viewed")
async def update_message_viewed_status(
    message_id: int, 
    update_data: MessageViewUpdate,
    db: Session = Depends(get_db)
):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.is_viewed = update_data.is_viewed
    db.commit()
    db.refresh(message)
    return {"message": "Message viewed status updated", "is_viewed": message.is_viewed}


@router.put("/messages/{message_id}/content")
async def update_message_content(
    message_id: int,
    update_data: MessageUpdate,
    db: Session = Depends(get_db)
):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.content = update_data.content
    db.commit()
    db.refresh(message)
    return {"message": "Message content updated", "content": message.content}


@router.patch("/chats/{chat_id}/messages/mark-all-viewed")
async def mark_all_chat_messages_as_viewed(
    chat_id: int,
    db: Session = Depends(get_db)
):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    updated_count = (
        db.query(Message)
        .filter(Message.chat_id == chat_id, Message.is_viewed == False)
        .update({"is_viewed": True})
    )
    db.commit()
    return {
        "message": f"Marked {updated_count} messages as viewed",
        "chat_id": chat_id,
        "updated_count": updated_count
    }


@router.get("/chats/{chat_id}/unread-count")
async def get_unread_messages_count(
    chat_id: int,
    db: Session = Depends(get_db)
):
    unread_count = (
        db.query(Message)
        .filter(Message.chat_id == chat_id, Message.is_viewed == False)
        .count()
    )
    return {"chat_id": chat_id, "unread_count": unread_count}
