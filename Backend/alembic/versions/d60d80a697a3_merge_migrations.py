"""merge migrations

Revision ID: d60d80a697a3
Revises: add_messages_table, 9d16f39db305
Create Date: 2025-08-03 20:51:30.703049

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd60d80a697a3'
down_revision: Union[str, Sequence[str], None] = ('add_messages_table', '9d16f39db305')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
