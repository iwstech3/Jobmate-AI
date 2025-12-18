"""merge_heads

Revision ID: c577b68ff1f6
Revises: be197a02c1ed, 92c10546a32a
Create Date: 2025-12-18 20:33:07.221023

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c577b68ff1f6'
down_revision: Union[str, Sequence[str], None] = ('be197a02c1ed', '92c10546a32a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
