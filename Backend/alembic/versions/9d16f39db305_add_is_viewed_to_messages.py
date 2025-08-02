"""Add is_viewed to messages

Revision ID: 9d16f39db305
Revises: 0c2af342d315
Create Date: 2025-08-01 15:33:56.082625

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9d16f39db305'
down_revision: Union[str, Sequence[str], None] = '0c2af342d315'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('messages', sa.Column('is_viewed', sa.Boolean(), nullable=False, default=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('messages', 'is_viewed')