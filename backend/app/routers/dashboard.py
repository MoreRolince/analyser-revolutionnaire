from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, AnalysisJob, TrackedShop, ProductGlobal, ShopGlobal, JobStatus, PlanType
from app.schemas import DashboardStats
from app.auth import get_current_active_user

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Calculer le score d'opportunité du marché (simplifié)
    # En production, cela devrait être calculé par IA basé sur les données
    market_opportunity_score = 85.0
    
    # Calculer les analyses restantes
    completed_jobs = db.query(AnalysisJob).filter(
        AnalysisJob.user_id == current_user.id,
        AnalysisJob.status == JobStatus.COMPLETED
    ).count()

    # Quotas selon le plan (PlanType enum)
    if current_user.plan == PlanType.THREE_MONTHS:
        max_analyses = 100
    elif current_user.plan == PlanType.SIX_MONTHS:
        max_analyses = 300
    else:
        max_analyses = 10
    
    remaining_analyses = max(0, max_analyses - completed_jobs)
    
    # Nombre de boutiques suivies
    tracked_shops_count = db.query(TrackedShop).filter(
        TrackedShop.user_id == current_user.id
    ).count()
    
    # Produits tendance depuis products_global (top 5 par score) - UNIQUEMENT les produits complets
    trending_products = db.query(ProductGlobal).filter(
        ProductGlobal.id > 3,  # Exclure les IDs 1, 2, 3 (données par défaut)
        ~ProductGlobal.product_name.ilike('%exemple%'),  # Exclure les noms contenant "exemple"
        ProductGlobal.product_url.isnot(None),
        ProductGlobal.product_url != '',
        ProductGlobal.product_name.isnot(None),
        ProductGlobal.product_name != '',
        ProductGlobal.product_image.isnot(None),
        ProductGlobal.product_image != ''
    ).order_by(
        ProductGlobal.score_winner.desc()
    ).limit(5).all()
    
    trending_products_data = [
        {
            "id": p.id,
            "name": p.product_name,
            "score": p.score_winner,
            "marketplace": str(p.marketplace) if p.marketplace else "other"
        }
        for p in trending_products
    ]
    
    # Ne pas créer de données par défaut - afficher seulement les vraies données scrapées
    
    # Recommandation du jour basée sur les statistiques
    if remaining_analyses > 0:
        daily_recommendation = f"Vous avez {remaining_analyses} analyses restantes. Explorez les opportunités du marché africain !"
    else:
        daily_recommendation = "Vous avez atteint votre quota d'analyses. Pensez à mettre à niveau votre plan pour continuer."
    
    # Statistiques globales du marché (SEULEMENT les vraies données scrapées)
    total_market_shops = db.query(ShopGlobal).filter(
        ShopGlobal.id > 3,
        ~ShopGlobal.shop_name.ilike('%exemple%')
    ).count()
    total_market_products = db.query(ProductGlobal).filter(
        ProductGlobal.id > 3,
        ~ProductGlobal.product_name.ilike('%exemple%')
    ).count()
    
    # Top 3 boutiques winners du marché - UNIQUEMENT les boutiques complètes
    top_market_shops = db.query(ShopGlobal).filter(
        ShopGlobal.id > 3,  # Exclure les IDs 1, 2, 3 (données par défaut)
        ~ShopGlobal.shop_name.ilike('%exemple%'),  # Exclure les noms contenant "exemple"
        ShopGlobal.shop_url.isnot(None),
        ShopGlobal.shop_url != '',
        ShopGlobal.shop_name.isnot(None),
        ShopGlobal.shop_name != ''
    ).order_by(
        ShopGlobal.score_global.desc()
    ).limit(3).all()
    
    top_market_shops_data = [
        {
            "id": shop.id,
            "name": shop.shop_name,
            "score": shop.score_global,
            "marketplace": str(shop.marketplace) if shop.marketplace else "other"
        }
        for shop in top_market_shops
    ]
    
    # Top 3 produits winners du marché - UNIQUEMENT les produits complets
    top_market_products = db.query(ProductGlobal).filter(
        ProductGlobal.id > 3,  # Exclure les IDs 1, 2, 3 (données par défaut)
        ~ProductGlobal.product_name.ilike('%exemple%'),  # Exclure les noms contenant "exemple"
        ProductGlobal.product_url.isnot(None),
        ProductGlobal.product_url != '',
        ProductGlobal.product_name.isnot(None),
        ProductGlobal.product_name != '',
        ProductGlobal.product_image.isnot(None),
        ProductGlobal.product_image != ''
    ).order_by(
        ProductGlobal.score_winner.desc()
    ).limit(3).all()
    
    top_market_products_data = [
        {
            "id": product.id,
            "name": product.product_name,
            "score": product.score_winner,
            "marketplace": str(product.marketplace) if product.marketplace else "other"
        }
        for product in top_market_products
    ]
    
    return DashboardStats(
        market_opportunity_score=market_opportunity_score,
        remaining_analyses=remaining_analyses,
        tracked_shops=tracked_shops_count,
        trending_products=trending_products_data,
        daily_recommendation=daily_recommendation,
        market_stats={
            "total_shops": total_market_shops,
            "total_products": total_market_products,
            "top_shops": top_market_shops_data,
            "top_products": top_market_products_data
        }
    )

