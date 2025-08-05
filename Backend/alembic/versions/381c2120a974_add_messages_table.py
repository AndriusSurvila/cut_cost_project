"""add messages table

Revision ID: 381c2120a974
Revises: 9d16f39db305
Create Date: 2025-08-03 20:50:07.210314

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_messages_table'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    message_status = sa.Enum(
        "sent", "seen", "failed", "generating",
        name="message_status",
        native_enum=False
    )

    # Создаем таблицу messages
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("chat_id", sa.Integer(), sa.ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", message_status, nullable=False, server_default="sent"),
        sa.Column("reply_id", sa.Integer(), sa.ForeignKey("messages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("like", sa.Boolean(), nullable=True, default=None),
        sa.Column("dislike", sa.Boolean(), nullable=True, default=None),
        sa.Column("llm_type", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("is_viewed", sa.Boolean(), nullable=False, server_default="0"),
    )

    # Индексы
    op.create_index("ix_messages_user_id", "messages", ["user_id"])
    op.create_index("ix_messages_chat_id", "messages", ["chat_id"])
    op.create_index("ix_messages_reply_id", "messages", ["reply_id"])
    op.create_index("ix_messages_status", "messages", ["status"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])

    # Создаем таблицу message_media
    op.create_table(
        "message_media",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("media_path", sa.String(500), nullable=False),
        sa.Column("media_type", sa.String(50), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_index("ix_message_media_message_id", "message_media", ["message_id"])
    op.create_index("ix_message_media_type", "message_media", ["media_type"])


def downgrade() -> None:
    op.drop_index("ix_message_media_type", table_name="message_media")
    op.drop_index("ix_message_media_message_id", table_name="message_media")
    op.drop_table("message_media")

    op.drop_index("ix_messages_created_at", table_name="messages")
    op.drop_index("ix_messages_status", table_name="messages")
    op.drop_index("ix_messages_reply_id", table_name="messages")
    op.drop_index("ix_messages_chat_id", table_name="messages")
    op.drop_index("ix_messages_user_id", table_name="messages")
    op.drop_table("messages")
