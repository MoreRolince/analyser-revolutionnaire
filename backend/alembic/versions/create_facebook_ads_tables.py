"""Create Facebook Ads tables

Revision ID: create_fb_ads_tables
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_fb_ads_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Créer la table fb_ads_raw
    op.create_table(
        'fb_ads_raw',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_title', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('media_url', sa.String(), nullable=True),
        sa.Column('landing_page_url', sa.String(), nullable=False),
        sa.Column('advertiser_page', sa.String(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('active_status', sa.String(), nullable=True),
        sa.Column('country_targeting', sa.String(), nullable=True),
        sa.Column('keyword', sa.String(), nullable=True),
        sa.Column('scraped_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fb_ads_raw_landing_page_url'), 'fb_ads_raw', ['landing_page_url'], unique=False)
    op.create_index(op.f('ix_fb_ads_raw_keyword'), 'fb_ads_raw', ['keyword'], unique=False)
    op.create_index(op.f('ix_fb_ads_raw_scraped_at'), 'fb_ads_raw', ['scraped_at'], unique=False)
    
    # Créer la table digital_products_detected
    op.create_table(
        'digital_products_detected',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('landing_page_url', sa.String(), nullable=False),
        sa.Column('product_title', sa.String(), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('seller_name', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('images', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('bullet_points', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('cta_text', sa.String(), nullable=True),
        sa.Column('social_proof', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('page_structure', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('marketplace', sa.String(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('landing_page_url')
    )
    op.create_index(op.f('ix_digital_products_detected_landing_page_url'), 'digital_products_detected', ['landing_page_url'], unique=True)
    op.create_index(op.f('ix_digital_products_detected_marketplace'), 'digital_products_detected', ['marketplace'], unique=False)
    op.create_index(op.f('ix_digital_products_detected_analyzed_at'), 'digital_products_detected', ['analyzed_at'], unique=False)
    
    # Créer la table digital_products_scores
    op.create_table(
        'digital_products_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('winner_score', sa.Float(), nullable=False),
        sa.Column('ads_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('countries_targeted', sa.Integer(), server_default='0', nullable=False),
        sa.Column('ad_longevity_days', sa.Integer(), server_default='0', nullable=False),
        sa.Column('advertiser_pages_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('price_attractiveness', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('offer_clarity', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('has_bonuses', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('cta_strength', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('positioning_niche', sa.String(), nullable=True),
        sa.Column('marketplace_bonus', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('scoring_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['digital_products_detected.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id')
    )
    op.create_index(op.f('ix_digital_products_scores_product_id'), 'digital_products_scores', ['product_id'], unique=True)
    op.create_index(op.f('ix_digital_products_scores_winner_score'), 'digital_products_scores', ['winner_score'], unique=False)
    op.create_index(op.f('ix_digital_products_scores_calculated_at'), 'digital_products_scores', ['calculated_at'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_digital_products_scores_calculated_at'), table_name='digital_products_scores')
    op.drop_index(op.f('ix_digital_products_scores_winner_score'), table_name='digital_products_scores')
    op.drop_index(op.f('ix_digital_products_scores_product_id'), table_name='digital_products_scores')
    op.drop_table('digital_products_scores')
    op.drop_index(op.f('ix_digital_products_detected_analyzed_at'), table_name='digital_products_detected')
    op.drop_index(op.f('ix_digital_products_detected_marketplace'), table_name='digital_products_detected')
    op.drop_index(op.f('ix_digital_products_detected_landing_page_url'), table_name='digital_products_detected')
    op.drop_table('digital_products_detected')
    op.drop_index(op.f('ix_fb_ads_raw_scraped_at'), table_name='fb_ads_raw')
    op.drop_index(op.f('ix_fb_ads_raw_keyword'), table_name='fb_ads_raw')
    op.drop_index(op.f('ix_fb_ads_raw_landing_page_url'), table_name='fb_ads_raw')
    op.drop_table('fb_ads_raw')


