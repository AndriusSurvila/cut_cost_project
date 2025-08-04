from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MessageStatus(str, Enum):
    SENT = "sent"
    SEEN = "seen"
    FAILED = "failed"
    GENERATING = "generating"

class MessageMediaBase(BaseModel):
    media_path: str
    media_type: str
    original_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None

class MessageMediaCreate(MessageMediaBase):
    pass

class MessageMediaResponse(MessageMediaBase):
    id: int
    message_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    content: Optional[str] = None
    reply_id: Optional[int] = None
    llm_type: Optional[str] = None

class MessageCreate(MessageBase):
    chat_id: int
    media: Optional[List[MessageMediaCreate]] = []

class MessageUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[MessageStatus] = None
    like: Optional[bool] = None
    dislike: Optional[bool] = None

class MessageReaction(BaseModel):
    like: Optional[bool] = None
    dislike: Optional[bool] = None

class MessageResponse(MessageBase):
    id: int
    user_id: int
    chat_id: int
    status: MessageStatus = MessageStatus.SENT
    like: Optional[bool] = None
    dislike: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    media: List[MessageMediaResponse] = []
    
    # Информация о пользователе (можно добавить при необходимости)
    # user: Optional[UserResponse] = None
    # reply_to: Optional["MessageResponse"] = None
    
    class Config:
        from_attributes = True

# Для поддержки self-reference в reply_to
MessageResponse.model_rebuild()

class MessagesListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    page: int
    size: int
    has_next: bool