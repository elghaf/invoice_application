"""add invoice sequence and client type

Revision ID: xxxx
Revises: previous_revision_id
Create Date: 2024-xx-xx
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create sequence for invoice IDs
    op.execute('CREATE SEQUENCE IF NOT EXISTS invoice_id_seq START 1')
    
    # Add client_type column if not exists
    op.add_column('invoices', sa.Column('client_type', sa.String(10), nullable=True))
    
    # Make invoice_number unique
    op.create_unique_constraint('uq_invoice_number', 'invoices', ['invoice_number'])

def downgrade():
    # Remove unique constraint
    op.drop_constraint('uq_invoice_number', 'invoices')
    
    # Drop client_type column
    op.drop_column('invoices', 'client_type')
    
    # Drop sequence
    op.execute('DROP SEQUENCE IF EXISTS invoice_id_seq') 