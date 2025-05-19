"""Add master items and file metadata tables

Revision ID: add_master_items_and_file_metadata
Revises: 
Create Date: 2025-05-19 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_master_items_and_file_metadata'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create master_items table
    op.create_table('master_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('value', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category', 'key', name='uix_category_key')
    )
    
    # Create file_metadata table
    op.create_table('file_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_path')
    )


def downgrade():
    op.drop_table('file_metadata')
    op.drop_table('master_items')