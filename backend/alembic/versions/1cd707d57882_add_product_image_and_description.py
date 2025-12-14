"""add_product_image_and_description

Revision ID: 1cd707d57882
Revises: 7fcee902115d
Create Date: 2025-12-10 00:33:20.045627

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1cd707d57882'
down_revision = '7fcee902115d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('products_global', sa.Column('product_image', sa.String(), nullable=True))
    op.add_column('products_global', sa.Column('product_description', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('products_global', 'product_description')
    op.drop_column('products_global', 'product_image')



