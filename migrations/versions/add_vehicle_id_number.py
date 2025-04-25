"""Add vehicle_id_number to forklift model

Revision ID: add_vehicle_id_number
Revises: 003
Create Date: 2025-04-23 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_vehicle_id_number'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Add vehicle_id_number column to forklifts table
    op.add_column('forklifts', sa.Column('vehicle_id_number', sa.String(50), nullable=True, unique=True))


def downgrade():
    # Remove vehicle_id_number column from forklifts table
    op.drop_column('forklifts', 'vehicle_id_number')