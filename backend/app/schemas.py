from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class PlanType(str, Enum):
    TRIAL = "trial"
    THREE_MONTHS = "3months"
    SIX_MONTHS = "6months"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class MarketplaceType(str, Enum):
    CHARIOW = "chariow"
    MAKETOU = "maketou"
    SYSTEMIO = "systemio"
    SYSTEMEIO = "systemeio"  # Alias pour compatibilité
    OTHER = "other"

# Auth Schemas
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: UserRole
    status: Optional[UserStatus] = None
    plan: Optional[PlanType]
    quota: Dict[str, int]
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

# Analysis Schemas
class AnalysisRequest(BaseModel):
    url: str

class AnalysisResult(BaseModel):
    type: str  # "shop" or "product"
    score: float
    data: Dict[str, Any]
    ai_insights: Optional[str] = None

# Shop Schemas
class ShopCreate(BaseModel):
    name: str
    url: str
    marketplace: MarketplaceType

class ShopResponse(BaseModel):
    id: int
    name: str
    url: str
    marketplace: MarketplaceType
    score: Optional[float]
    estimated_revenue: Optional[float]
    estimated_sales: Optional[int]
    product_count: Optional[int]
    age_months: Optional[int]
    growth_rate: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True

# Product Schemas
class ProductResponse(BaseModel):
    id: int
    name: str
    url: str
    marketplace: MarketplaceType
    score: Optional[float]
    estimated_daily_sales: Optional[int]
    ideal_price: Optional[float]
    competition_level: Optional[str]
    trend: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Dashboard Schemas
class DashboardStats(BaseModel):
    market_opportunity_score: float
    remaining_analyses: int
    tracked_shops: int
    trending_products: List[Dict[str, Any]]
    daily_recommendation: str
    market_stats: Optional[Dict[str, Any]] = None

# Winners Schemas
class ProductGlobalResponse(BaseModel):
    id: int
    marketplace: str  # String au lieu d'enum pour compatibilité
    product_name: str
    shop_name: str
    product_url: str
    product_image: Optional[str] = None
    product_description: Optional[str] = None
    price: Optional[float]
    sales_est_min: Optional[int]
    sales_est_max: Optional[int]
    revenue_est_min: Optional[float]
    revenue_est_max: Optional[float]
    score_winner: float
    category: Optional[str]
    last_scraped_at: Optional[datetime]
    created_at: datetime

    @validator('marketplace', pre=True)
    def convert_marketplace(cls, v):
        """Convertit l'enum ou string en string"""
        if hasattr(v, 'value'):
            return v.value
        return str(v) if v else 'other'

    class Config:
        from_attributes = True

class ShopGlobalResponse(BaseModel):
    id: int
    marketplace: str  # String au lieu d'enum pour compatibilité
    shop_name: str
    shop_url: str
    score_global: float
    revenue_est_min: Optional[float]
    revenue_est_max: Optional[float]
    winners_count: int
    last_scraped_at: Optional[datetime]
    created_at: datetime

    @validator('marketplace', pre=True)
    def convert_marketplace(cls, v):
        """Convertit l'enum ou string en string"""
        if hasattr(v, 'value'):
            return v.value
        return str(v) if v else 'other'

    class Config:
        from_attributes = True

# Admin Schemas
class PaymentApproval(BaseModel):
    payment_id: int
    approve: bool


    shop_name: str
    product_url: str
    product_image: Optional[str] = None
    product_description: Optional[str] = None
    price: Optional[float]
    sales_est_min: Optional[int]
    sales_est_max: Optional[int]
    revenue_est_min: Optional[float]
    revenue_est_max: Optional[float]
    score_winner: float
    category: Optional[str]
    last_scraped_at: Optional[datetime]
    created_at: datetime

    @validator('marketplace', pre=True)
    def convert_marketplace(cls, v):
        """Convertit l'enum ou string en string"""
        if hasattr(v, 'value'):
            return v.value
        return str(v) if v else 'other'

    class Config:
        from_attributes = True

class ShopGlobalResponse(BaseModel):
    id: int
    marketplace: str  # String au lieu d'enum pour compatibilité
    shop_name: str
    shop_url: str
    score_global: float
    revenue_est_min: Optional[float]
    revenue_est_max: Optional[float]
    winners_count: int
    last_scraped_at: Optional[datetime]
    created_at: datetime

    @validator('marketplace', pre=True)
    def convert_marketplace(cls, v):
        """Convertit l'enum ou string en string"""
        if hasattr(v, 'value'):
            return v.value
        return str(v) if v else 'other'

    class Config:
        from_attributes = True

# Admin Schemas
class PaymentApproval(BaseModel):
    payment_id: int
    approve: bool

