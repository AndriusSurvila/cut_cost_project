"""add user_id and message_media - SQLite compatible

Revision ID: sqlite_user_media_fix
Revises: d60d80a697a3
Create Date: 2025-08-03 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'sqlite_user_media_fix'
down_revision: Union[str, None] = 'd60d80a697a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Проверяем существующие колонки в messages
    columns = [col['name'] for col in inspector.get_columns('messages')]
    
    # Добавляем user_id если его нет
    if 'user_id' not in columns:
        # Добавляем колонку user_id как nullable сначала
        op.add_column('messages', sa.Column('user_id', sa.Integer(), nullable=True))
        
        # Обновляем существующие записи - берем user_id из связанного чата
        # Для сообщений пользователя (role='user') используем user_id из chat
        # Для сообщений AI оставляем NULL или можно тоже взять из chat
        op.execute("""
            UPDATE messages 
            SET user_id = (
                SELECT chats.user_id 
                FROM chats 
                WHERE chats.id = messages.chat_id
            )
            WHERE messages.role = 'user' OR messages.role IS NULL
        """)
        
        # Для AI сообщений можно оставить NULL или тоже заполнить user_id
        # op.execute("""
        #     UPDATE messages 
        #     SET user_id = (
        #         SELECT chats.user_id 
        #         FROM chats 
        #         WHERE chats.id = messages.chat_id
        #     )
        #     WHERE messages.user_id IS NULL
        # """)
        
        # Создаем foreign key constraint
        op.create_foreign_key(
            'fk_messages_user_id', 
            'messages', 
            'users', 
            ['user_id'], 
            ['id'], 
            ondelete='CASCADE'
        )
    
    # Создаем таблицу message_media если её нет
    if 'message_media' not in inspector.get_table_names():
        op.create_table('message_media',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('message_id', sa.Integer(), nullable=False),
            sa.Column('media_path', sa.String(500), nullable=False),
            sa.Column('media_type', sa.String(50), nullable=False),
            sa.Column('original_name', sa.String(255), nullable=True),
            sa.Column('file_size', sa.BigInteger(), nullable=True),
            sa.Column('mime_type', sa.String(100), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        )
        
        # Создаем индексы
        op.create_index('ix_message_media_message_id', 'message_media', ['message_id'])
        op.create_index('ix_message_media_type', 'message_media', ['media_type'])

def downgrade() -> None:
    # Удаляем таблицу message_media
    op.drop_table('message_media')
    
    # Удаляем foreign key и колонку user_id
    try:
        op.drop_constraint('fk_messages_user_id', 'messages', type_='foreignkey')
    except:
        pass  # Constraint может не существовать
    
    try:
        op.drop_column('messages', 'user_id')
    except:
        pass  # Колонка может не существовать