"""Create missing tables

Revision ID: 003
Revises: acbca60fe487
Create Date: 2023-04-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '003'
down_revision = 'acbca60fe487'
branch_labels = None
depends_on = None


def upgrade():
    # Create operators table if it doesn't exist
    op.create_table(
        'operators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('department', sa.String(100)),
        sa.Column('license_number', sa.String(50)),
        sa.Column('license_expiry', sa.Date()),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('updated_by', sa.String(100)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_id')
    )

    # Create inspection_reports table if it doesn't exist
    op.create_table(
        'inspection_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('forklift_id', sa.Integer(), nullable=False),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('inspection_date', sa.Date(), nullable=False),
        sa.Column('inspection_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('findings', sa.Text()),
        sa.Column('recommendations', sa.Text()),
        sa.Column('next_inspection_date', sa.Date()),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('updated_by', sa.String(100)),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['forklift_id'], ['forklifts.id']),
        sa.ForeignKeyConstraint(['operator_id'], ['operators.id'])
    )


def downgrade():
    # Drop inspection_reports table
    op.drop_table('inspection_reports')
    
    # Drop operators table
    op.drop_table('operators')