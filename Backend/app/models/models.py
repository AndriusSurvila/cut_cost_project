
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class MessageStatus(str, enum.Enum):
    SENT = "sent"
    SEEN = "seen"
    FAILED = "failed"
    GENERATING = "generating"

class Feedback(str, enum.Enum):
    NONE = "none"
    LIKE = "like"
    DISLIKE = "dislike"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="New Chat")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_viewed = Column(Boolean, default=False, nullable=False)

    reply_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    reply = relationship("Message", remote_side=[id])

    status = Column(Enum(MessageStatus), default=MessageStatus.GENERATING, nullable=False)

    feedback = Column(Enum(Feedback), default=Feedback.NONE, nullable=False)

    llm_type = Column(String, nullable=True)

    chat = relationship("Chat", back_populates="messages")