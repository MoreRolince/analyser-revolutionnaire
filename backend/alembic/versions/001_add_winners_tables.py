"""Add winners tables

Revision ID: 001_add_winners_tables
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_winners_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Vérifier et créer l'enum MarketplaceType si nécessaire
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'marketplacetype')"))
    enum_exists = result.scalar()
    
    if not enum_exists:
        op.execute("CREATE TYPE marketplacetype AS ENUM ('chariow', 'maketou', 'systemio', 'systemeio', 'other')")
    else:
        # Ajouter 'systemeio' à l'enum s'il n'existe pas déjà
        result = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'systemeio' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'marketplacetype')
            )
        """))
        systemeio_exists = result.scalar()
        if not systemeio_exists:
            op.execute("ALTER TYPE marketplacetype ADD VALUE 'systemeio'")
    
    # Créer la table products_global seulement si elle n'existe pas
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'products_global'
        )
    """))
    table_exists = result.scalar()
    
    if not table_exists:
        op.create_table(
            'products_global',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('marketplace', postgresql.ENUM('chariow', 'maketou', 'systemio', 'systemeio', 'other', name='marketplacetype', create_type=False), nullable=False),
            sa.Column('product_name', sa.String(), nullable=False),
            sa.Column('shop_name', sa.String(), nullable=False),
            sa.Column('product_url', sa.String(), nullable=False),
            sa.Column('price', sa.Float(), nullable=True),
            sa.Column('sales_est_min', sa.Integer(), nullable=True),
            sa.Column('sales_est_max', sa.Integer(), nullable=True),
            sa.Column('revenue_est_min', sa.Float(), nullable=True),
            sa.Column('revenue_est_max', sa.Float(), nullable=True),
            sa.Column('score_winner', sa.Float(), nullable=False),
            sa.Column('category', sa.String(), nullable=True),
            sa.Column('last_scraped_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_products_global_id'), 'products_global', ['id'], unique=False)
        op.create_index(op.f('ix_products_global_marketplace'), 'products_global', ['marketplace'], unique=False)
        op.create_index(op.f('ix_products_global_product_url'), 'products_global', ['product_url'], unique=True)
        op.create_index(op.f('ix_products_global_score_winner'), 'products_global', ['score_winner'], unique=False)
        op.create_index(op.f('ix_products_global_category'), 'products_global', ['category'], unique=False)
    
    # Créer la table shops_global seulement si elle n'existe pas
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'shops_global'
        )
    """))
    shops_table_exists = result.scalar()
    
    if not shops_table_exists:
        op.create_table(
            'shops_global',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('marketplace', postgresql.ENUM('chariow', 'maketou', 'systemio', 'systemeio', 'other', name='marketplacetype', create_type=False), nullable=False),
            sa.Column('shop_name', sa.String(), nullable=False),
            sa.Column('shop_url', sa.String(), nullable=False),
            sa.Column('score_global', sa.Float(), nullable=False),
            sa.Column('revenue_est_min', sa.Float(), nullable=True),
            sa.Column('revenue_est_max', sa.Float(), nullable=True),
            sa.Column('winners_count', sa.Integer(), server_default='0', nullable=True),
            sa.Column('last_scraped_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_shops_global_id'), 'shops_global', ['id'], unique=False)
        op.create_index(op.f('ix_shops_global_marketplace'), 'shops_global', ['marketplace'], unique=False)
        op.create_index(op.f('ix_shops_global_shop_url'), 'shops_global', ['shop_url'], unique=True)
        op.create_index(op.f('ix_shops_global_score_global'), 'shops_global', ['score_global'], unique=False)
    
    # Supprimer la table ai_messages si elle existe
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'ai_messages'
        )
    """))
    ai_messages_exists = result.scalar()
    if ai_messages_exists:
        op.drop_table('ai_messages')


def downgrade() -> None:
    op.drop_index(op.f('ix_shops_global_score_global'), table_name='shops_global')
    op.drop_index(op.f('ix_shops_global_shop_url'), table_name='shops_global')
    op.drop_index(op.f('ix_shops_global_marketplace'), table_name='shops_global')
    op.drop_index(op.f('ix_shops_global_id'), table_name='shops_global')
    op.drop_table('shops_global')
    
    op.drop_index(op.f('ix_products_global_category'), table_name='products_global')
    op.drop_index(op.f('ix_products_global_score_winner'), table_name='products_global')
    op.drop_index(op.f('ix_products_global_product_url'), table_name='products_global')
    op.drop_index(op.f('ix_products_global_marketplace'), table_name='products_global')
    op.drop_index(op.f('ix_products_global_id'), table_name='products_global')
    op.drop_table('products_global')
