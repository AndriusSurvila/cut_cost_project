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

# Создаем enum для статусов сообщений
message_status = postgresql.ENUM(
    'sent', 'seen', 'failed', 'generating',
    name='message_status'
)

def upgrade() -> None:
    # Создаем enum тип
    message_status.create(op.get_bind())
    
    # Создаем таблицу сообщений
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('status', message_status, nullable=False, default='sent'),
        sa.Column('reply_id', sa.Integer(), nullable=True),
        sa.Column('like', sa.Boolean(), nullable=True, default=None),
        sa.Column('dislike', sa.Boolean(), nullable=True, default=None),
        sa.Column('llm_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['reply_id'], ['messages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ondelete='CASCADE'),
    )
    
    # Создаем индексы для оптимизации
    op.create_index('ix_messages_user_id', 'messages', ['user_id'])
    op.create_index('ix_messages_chat_id', 'messages', ['chat_id'])
    op.create_index('ix_messages_reply_id', 'messages', ['reply_id'])
    op.create_index('ix_messages_status', 'messages', ['status'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])
    
    # Создаем пивот таблицу для медиа файлов
    op.create_table('message_media',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('media_path', sa.String(500), nullable=False),
        sa.Column('media_type', sa.String(50), nullable=False),  # image, video, audio, document
        sa.Column('original_name', sa.String(255), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
    )
    
    op.create_index('ix_message_media_message_id', 'message_media', ['message_id'])
    op.create_index('ix_message_media_type', 'message_media', ['media_type'])


def downgrade() -> None:
    # Удаляем таблицы
    op.drop_table('message_media')
    op.drop_table('messages')
    
    # Удаляем enum
    message_status.drop(op.get_bind())