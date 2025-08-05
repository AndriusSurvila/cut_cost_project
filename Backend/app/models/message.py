import enum
from sqlalchemy import (
    Column, Integer, ForeignKey, Text, DateTime, Boolean, String,
    func, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.models.models import Base


class MessageStatusEnum(str, enum.Enum):
    SENT = "sent"
    SEEN = "seen"
    FAILED = "failed"
    GENERATING = "generating"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(
        SAEnum(MessageStatusEnum, name="message_status", native_enum=False),
        nullable=False,
        server_default="sent"
    )
    reply_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    like = Column(Boolean, nullable=True, default=None)
    dislike = Column(Boolean, nullable=True, default=None)
    llm_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_viewed = Column(Boolean, nullable=False, server_default="0")  # SQLite default false

    # Relationships
    chat = relationship("Chat", back_populates="messages")
    user = relationship("User", back_populates="messages")
    reply_to = relationship("Message", remote_side=[id], backref="replies")
    media = relationship("MessageMedia", back_populates="message", cascade="all, delete-orphan")
