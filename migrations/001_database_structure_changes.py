"""Database structure changes for Issue #1

This migration script implements the following changes:
1. Creates new table 'operators'
2. Creates new table 'inspection_reports'
3. Adds annual inspection fields to forklift_predictions
4. Adds updated_by field to all relevant tables
"""

from app.models import db
from datetime import datetime
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create operators table
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

    # Create inspection_reports table
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

    # Add annual inspection fields to forklift_predictions
    op.add_column('forklift_predictions', sa.Column('annual_inspection_status', sa.String(20)))
    op.add_column('forklift_predictions', sa.Column('annual_inspection_notes', sa.Text()))

    # Add updated_by field to existing tables
    tables = ['forklifts', 'forklift_repairs', 'forklift_predictions']
    for table in tables:
        op.add_column(table, sa.Column('updated_by', sa.String(100)))

def downgrade():
    # Remove updated_by field from existing tables
    tables = ['forklifts', 'forklift_repairs', 'forklift_predictions']
    for table in tables:
        op.drop_column(table, 'updated_by')

    # Remove annual inspection fields from forklift_predictions
    op.drop_column('forklift_predictions', 'annual_inspection_notes')
    op.drop_column('forklift_predictions', 'annual_inspection_status')

    # Drop inspection_reports table
    op.drop_table('inspection_reports')

    # Drop operators table
    op.drop_table('operators')