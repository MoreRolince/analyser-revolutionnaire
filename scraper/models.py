# Ce fichier importe les modèles depuis le backend pour éviter la duplication
# En production, vous pourriez créer un package partagé

import sys
import os

# Ajouter le chemin du backend pour les imports
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
sys.path.insert(0, backend_path)

from app.models import (
    User, Payment, Shop, Product, ShopSnapshot,
    TrackedShop, AnalysisJob, AIMessage, AdminLog,
    UserRole, PlanType, PaymentStatus, JobStatus, MarketplaceType
)

__all__ = [
    'User', 'Payment', 'Shop', 'Product', 'ShopSnapshot',
    'TrackedShop', 'AnalysisJob', 'AIMessage', 'AdminLog',
    'UserRole', 'PlanType', 'PaymentStatus', 'JobStatus', 'MarketplaceType'
]

