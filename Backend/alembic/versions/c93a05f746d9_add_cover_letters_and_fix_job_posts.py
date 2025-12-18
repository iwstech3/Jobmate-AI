"""add_cover_letters_and_fix_job_posts

Revision ID: c93a05f746d9
Revises: c577b68ff1f6
Create Date: 2025-12-18 20:39:58.417823

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c93a05f746d9'
down_revision: Union[str, Sequence[str], None] = 'c577b68ff1f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create cover_letters table
    op.create_table('cover_letters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job_id', sa.Integer(), nullable=False),
    sa.Column('parsed_cv_id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('customization_notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['job_id'], ['job_posts.id'], ),
    sa.ForeignKeyConstraint(['parsed_cv_id'], ['parsed_cvs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cover_letters_id'), 'cover_letters', ['id'], unique=False)

    # 2. Add analytics columns to job_posts SAFELY with server_defaults
    # Allows adding NOT NULL columns to a table that already has rows.
    op.add_column('job_posts', sa.Column('views_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('job_posts', sa.Column('applications_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('job_posts', sa.Column('saves_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('job_posts', sa.Column('status', sa.String(length=50), server_default='published', nullable=False))
    op.add_column('job_posts', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('job_posts', sa.Column('featured', sa.Boolean(), server_default='false', nullable=True))


def downgrade() -> None:
    op.drop_column('job_posts', 'featured')
    op.drop_column('job_posts', 'expires_at')
    op.drop_column('job_posts', 'status')
    op.drop_column('job_posts', 'saves_count')
    op.drop_column('job_posts', 'applications_count')
    op.drop_column('job_posts', 'views_count')
    op.drop_index(op.f('ix_cover_letters_id'), table_name='cover_letters')
    op.drop_table('cover_letters')
