"""add users table

Revision ID: 0c2af342d315
Revises: ba3c343568d3
Create Date: 2025-07-25 12:50:32.325390

"""

from alembic import op
import sqlalchemy as sa

revision = '0c2af342d315'
down_revision = 'ba3c343568d3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.add_column('chats', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_chats_user_id_users',
        'chats', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    op.drop_constraint('fk_chats_user_id_users', 'chats', type_='foreignkey')
    op.drop_column('chats', 'user_id')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')