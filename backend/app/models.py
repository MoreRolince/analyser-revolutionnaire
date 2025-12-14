from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database import Base

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class UserStatus(str, enum.Enum):
    PENDING = "pending"  # En attente de validation
    APPROVED = "approved"  # Approuvé par l'admin
    REJECTED = "rejected"  # Rejeté par l'admin

class PlanType(str, enum.Enum):
    TRIAL = "trial"
    THREE_MONTHS = "3months"
    SIX_MONTHS = "6months"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class MarketplaceType(str, enum.Enum):
    CHARIOW = "chariow"
    MAKETOU = "maketou"
    SYSTEMIO = "systemio"
    SYSTEMEIO = "systemeio"  # Alias pour compatibilité
    GUMROAD = "gumroad"
    PAYHIP = "payhip"
    OTHER = "other"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    status = Column(String, default=UserStatus.PENDING.value)  # Statut de validation
    plan = Column(SQLEnum(PlanType), nullable=True)
    plan_start_date = Column(DateTime, nullable=True)
    plan_end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    payments = relationship("Payment", foreign_keys="Payment.user_id", back_populates="user")
    tracked_shops = relationship("TrackedShop", back_populates="user")
    analysis_jobs = relationship("AnalysisJob", back_populates="user")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan = Column(SQLEnum(PlanType), nullable=False)
    amount = Column(Float, nullable=False)
    proof_url = Column(String, nullable=True)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", foreign_keys=[user_id], back_populates="payments")

class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, unique=True, index=True, nullable=False)
    marketplace = Column(SQLEnum(MarketplaceType), nullable=False)
    score = Column(Float, nullable=True)
    estimated_revenue = Column(Float, nullable=True)
    estimated_sales = Column(Integer, nullable=True)
    product_count = Column(Integer, nullable=True)
    age_months = Column(Integer, nullable=True)
    growth_rate = Column(Float, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    last_scraped_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    products = relationship("Product", back_populates="shop")
    snapshots = relationship("ShopSnapshot", back_populates="shop")
    tracked_by = relationship("TrackedShop", back_populates="shop")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True)
    name = Column(String, nullable=False)
    url = Column(String, unique=True, index=True, nullable=False)
    marketplace = Column(SQLEnum(MarketplaceType), nullable=False)
    score = Column(Float, nullable=True)
    estimated_daily_sales = Column(Integer, nullable=True)
    ideal_price = Column(Float, nullable=True)
    competition_level = Column(String, nullable=True)
    trend = Column(String, nullable=True)  # "rising", "falling", "stable"
    metadata_json = Column(JSON, nullable=True)
    last_scraped_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    shop = relationship("Shop", back_populates="products")

class ShopSnapshot(Base):
    __tablename__ = "shop_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    score = Column(Float, nullable=True)
    estimated_revenue = Column(Float, nullable=True)
    product_count = Column(Integer, nullable=True)
    snapshot_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    shop = relationship("Shop", back_populates="snapshots")

class TrackedShop(Base):
    __tablename__ = "tracked_shops"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    alerts_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="tracked_shops")
    shop = relationship("Shop", back_populates="tracked_by")

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    url = Column(String, nullable=False)
    job_id = Column(String, unique=True, index=True, nullable=False)  # Redis job ID
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="analysis_jobs")

class ProductGlobal(Base):
    __tablename__ = "products_global"

    id = Column(Integer, primary_key=True, index=True)
    marketplace = Column(String, nullable=False, index=True)  # String au lieu d'enum pour éviter les problèmes de conversion
    product_name = Column(String, nullable=False)
    shop_name = Column(String, nullable=False)
    product_url = Column(String, nullable=False, unique=True, index=True)
    product_image = Column(String, nullable=True)  # URL de l'image du produit
    product_description = Column(Text, nullable=True)  # Description du produit
    price = Column(Float, nullable=True)
    sales_est_min = Column(Integer, nullable=True)
    sales_est_max = Column(Integer, nullable=True)
    revenue_est_min = Column(Float, nullable=True)
    revenue_est_max = Column(Float, nullable=True)
    score_winner = Column(Float, nullable=False, index=True)
    category = Column(String, nullable=True, index=True)
    last_scraped_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ShopGlobal(Base):
    __tablename__ = "shops_global"

    id = Column(Integer, primary_key=True, index=True)
    marketplace = Column(String, nullable=False, index=True)  # String au lieu d'enum pour éviter les problèmes de conversion
    shop_name = Column(String, nullable=False)
    shop_url = Column(String, nullable=False, unique=True, index=True)
    score_global = Column(Float, nullable=False, index=True)
    revenue_est_min = Column(Float, nullable=True)
    revenue_est_max = Column(Float, nullable=True)
    winners_count = Column(Integer, default=0)
    last_scraped_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class AdminLog(Base):
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    target_type = Column(String, nullable=True)  # "user", "payment", "shop", etc.
    target_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


# Nouveaux modèles pour le pipeline Facebook Ads
class FacebookAdRaw(Base):
    __tablename__ = "fb_ads_raw"

    id = Column(Integer, primary_key=True, index=True)
    product_title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    media_url = Column(String, nullable=True)  # URL de l'image/vidéo
    landing_page_url = Column(String, nullable=False, index=True)
    advertiser_page = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    active_status = Column(String, nullable=True)  # "active", "inactive", "unknown"
    country_targeting = Column(String, nullable=True)
    keyword = Column(String, nullable=True, index=True)
    scraped_at = Column(DateTime, server_default=func.now(), index=True)
    created_at = Column(DateTime, server_default=func.now())


class DigitalProductDetected(Base):
    __tablename__ = "digital_products_detected"

    id = Column(Integer, primary_key=True, index=True)
    landing_page_url = Column(String, nullable=False, unique=True, index=True)
    product_title = Column(String, nullable=False)
    price = Column(Float, nullable=True)
    currency = Column(String, default="FCFA")  # FCFA, EUR, USD
    seller_name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    images = Column(JSON, nullable=True)  # Liste d'URLs d'images
    bullet_points = Column(JSON, nullable=True)  # Liste de points clés
    cta_text = Column(String, nullable=True)
    social_proof = Column(JSON, nullable=True)  # {reviews_count, rating, testimonials}
    page_structure = Column(JSON, nullable=True)  # Structure de la page
    marketplace = Column(String, nullable=True, index=True)
    
    # Nouveaux champs PRO
    niche = Column(String, nullable=True, index=True)  # business, spirituality, mixed
    product_type = Column(String, nullable=True)  # ebook, formation, template, audio, spiritual_guide, subscription
    funnel_type = Column(String, nullable=True)  # systeme.io, whatsapp, marketplace, custom
    has_whatsapp_funnel = Column(Boolean, default=False)
    template_ready = Column(Boolean, default=False)  # Prêt à être utilisé comme template
    resell_potential = Column(Boolean, default=False)  # Potentiel de revente
    facebook_page_name = Column(String, nullable=True)
    ads_count = Column(Integer, default=0)  # Nombre d'ads pour ce produit
    first_seen_date = Column(DateTime, nullable=True)
    last_seen_date = Column(DateTime, nullable=True)
    detected_keywords = Column(JSON, nullable=True)  # Liste des mots-clés détectés
    africa_relevance_score = Column(Float, default=0.0)  # Score de pertinence africaine
    
    analyzed_at = Column(DateTime, server_default=func.now(), index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DigitalProductScore(Base):
    __tablename__ = "digital_products_scores"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("digital_products_detected.id"), nullable=False, unique=True, index=True)
    winner_score = Column(Float, nullable=False, index=True)  # Score 0-100
    
    # Métriques au niveau des annonces
    ads_count = Column(Integer, default=0)  # Nombre d'annonces pour ce produit
    countries_targeted = Column(Integer, default=0)  # Nombre de pays ciblés
    ad_longevity_days = Column(Integer, default=0)  # Durée de vie des annonces (jours)
    advertiser_pages_count = Column(Integer, default=0)  # Nombre de pages publicitaires
    
    # Métriques au niveau de la landing page
    price_attractiveness = Column(Float, default=0.0)  # Score 0-10
    offer_clarity = Column(Float, default=0.0)  # Score 0-10
    has_bonuses = Column(Boolean, default=False)
    cta_strength = Column(Float, default=0.0)  # Score 0-10
    positioning_niche = Column(String, nullable=True)  # finance, IA, formation, relation, santé, etc.
    
    # Bonus marketplace
    marketplace_bonus = Column(Float, default=0.0)  # +15 pour Maketou/Chariow, +10 pour Systeme.io
    
    # Détails du scoring
    scoring_details = Column(JSON, nullable=True)  # Détails du calcul du score
    
    calculated_at = Column(DateTime, server_default=func.now(), index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    product = relationship("DigitalProductDetected", foreign_keys=[product_id])

