"""
Endpoints pour les statistiques globales du marché
Basées sur toutes les boutiques scrapées
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, Any
from datetime import datetime, timedelta

from app.database import get_db
from app.models import ShopGlobal, ProductGlobal, MarketplaceType
from app.auth import get_current_active_user
from app.models import User

router = APIRouter()

@router.get("/overview")
async def get_market_overview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Vue d'ensemble du marché avec toutes les statistiques
    """
    # Total boutiques et produits
    total_shops = db.query(ShopGlobal).count()
    total_products = db.query(ProductGlobal).count()
    
    # Boutiques par marketplace
    shops_by_marketplace = db.query(
        ShopGlobal.marketplace,
        func.count(ShopGlobal.id).label('count')
    ).group_by(ShopGlobal.marketplace).all()
    
    shops_by_marketplace_dict = {
        str(mp.value if hasattr(mp, 'value') else mp): count 
        for mp, count in shops_by_marketplace
    }
    
    # Produits par marketplace
    products_by_marketplace = db.query(
        ProductGlobal.marketplace,
        func.count(ProductGlobal.id).label('count')
    ).group_by(ProductGlobal.marketplace).all()
    
    products_by_marketplace_dict = {
        str(mp.value if hasattr(mp, 'value') else mp): count 
        for mp, count in products_by_marketplace
    }
    
    # Top 10 boutiques par score
    top_shops = db.query(ShopGlobal).order_by(
        ShopGlobal.score_global.desc()
    ).limit(10).all()
    
    top_shops_data = [
        {
            "id": shop.id,
            "name": shop.shop_name,
            "marketplace": str(shop.marketplace.value if hasattr(shop.marketplace, 'value') else shop.marketplace),
            "score": shop.score_global,
            "revenue_min": shop.revenue_est_min,
            "revenue_max": shop.revenue_est_max,
            "winners_count": shop.winners_count
        }
        for shop in top_shops
    ]
    
    # Top 10 produits par score
    top_products = db.query(ProductGlobal).order_by(
        ProductGlobal.score_winner.desc()
    ).limit(10).all()
    
    top_products_data = [
        {
            "id": product.id,
            "name": product.product_name,
            "shop_name": product.shop_name,
            "marketplace": str(product.marketplace.value if hasattr(product.marketplace, 'value') else product.marketplace),
            "score": product.score_winner,
            "price": product.price,
            "revenue_min": product.revenue_est_min,
            "revenue_max": product.revenue_est_max
        }
        for product in top_products
    ]
    
    # Statistiques de revenus
    total_revenue_min = db.query(func.sum(ShopGlobal.revenue_est_min)).scalar() or 0
    total_revenue_max = db.query(func.sum(ShopGlobal.revenue_est_max)).scalar() or 0
    
    # Prix moyen des produits
    avg_price = db.query(func.avg(ProductGlobal.price)).filter(
        ProductGlobal.price > 0
    ).scalar() or 0
    
    # Score moyen des boutiques
    avg_shop_score = db.query(func.avg(ShopGlobal.score_global)).scalar() or 0
    
    # Score moyen des produits
    avg_product_score = db.query(func.avg(ProductGlobal.score_winner)).scalar() or 0
    
    # Boutiques mises à jour récemment (dernières 24h)
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    recently_updated = db.query(ShopGlobal).filter(
        ShopGlobal.last_scraped_at >= recent_cutoff
    ).count()
    
    # Tendances : produits en hausse (score > 80)
    trending_products = db.query(ProductGlobal).filter(
        ProductGlobal.score_winner >= 80
    ).order_by(ProductGlobal.score_winner.desc()).limit(5).all()
    
    trending_data = [
        {
            "id": p.id,
            "name": p.product_name,
            "score": p.score_winner,
            "marketplace": str(p.marketplace.value if hasattr(p.marketplace, 'value') else p.marketplace)
        }
        for p in trending_products
    ]
    
    return {
        "total_shops": total_shops,
        "total_products": total_products,
        "shops_by_marketplace": shops_by_marketplace_dict,
        "products_by_marketplace": products_by_marketplace_dict,
        "top_shops": top_shops_data,
        "top_products": top_products_data,
        "market_stats": {
            "total_revenue_min": float(total_revenue_min),
            "total_revenue_max": float(total_revenue_max),
            "avg_price": float(avg_price),
            "avg_shop_score": float(avg_shop_score),
            "avg_product_score": float(avg_product_score),
            "recently_updated_shops": recently_updated
        },
        "trending_products": trending_data,
        "last_update": datetime.utcnow().isoformat()
    }

@router.get("/winners")
async def get_market_winners(
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les winners du marché (boutiques et produits)
    """
    # Top boutiques winners (score >= 75)
    winner_shops = db.query(ShopGlobal).filter(
        ShopGlobal.score_global >= 75
    ).order_by(ShopGlobal.score_global.desc()).limit(limit).all()
    
    # Top produits winners (score >= 80)
    winner_products = db.query(ProductGlobal).filter(
        ProductGlobal.score_winner >= 80
    ).order_by(ProductGlobal.score_winner.desc()).limit(limit).all()
    
    return {
        "shops": [
            {
                "id": shop.id,
                "name": shop.shop_name,
                "marketplace": str(shop.marketplace.value if hasattr(shop.marketplace, 'value') else shop.marketplace),
                "score": shop.score_global,
                "revenue_min": shop.revenue_est_min,
                "revenue_max": shop.revenue_est_max,
                "winners_count": shop.winners_count,
                "url": shop.shop_url
            }
            for shop in winner_shops
        ],
        "products": [
            {
                "id": product.id,
                "name": product.product_name,
                "shop_name": product.shop_name,
                "marketplace": str(product.marketplace.value if hasattr(product.marketplace, 'value') else product.marketplace),
                "score": product.score_winner,
                "price": product.price,
                "revenue_min": product.revenue_est_min,
                "revenue_max": product.revenue_est_max,
                "url": product.product_url
            }
            for product in winner_products
        ]
    }

@router.get("/trends")
async def get_market_trends(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Tendances du marché
    """
    # Produits en forte hausse (score élevé, prix moyen)
    rising_products = db.query(ProductGlobal).filter(
        and_(
            ProductGlobal.score_winner >= 85,
            ProductGlobal.price > 0
        )
    ).order_by(ProductGlobal.score_winner.desc()).limit(10).all()
    
    # Boutiques en croissance (beaucoup de winners)
    growing_shops = db.query(ShopGlobal).filter(
        ShopGlobal.winners_count >= 5
    ).order_by(ShopGlobal.winners_count.desc()).limit(10).all()
    
    # Catégories les plus performantes (si disponible)
    # Pour l'instant, on retourne les produits par marketplace
    
    return {
        "rising_products": [
            {
                "id": p.id,
                "name": p.product_name,
                "score": p.score_winner,
                "price": p.price,
                "marketplace": str(p.marketplace.value if hasattr(p.marketplace, 'value') else p.marketplace)
            }
            for p in rising_products
        ],
        "growing_shops": [
            {
                "id": s.id,
                "name": s.shop_name,
                "winners_count": s.winners_count,
                "score": s.score_global,
                "marketplace": str(s.marketplace.value if hasattr(s.marketplace, 'value') else s.marketplace)
            }
            for s in growing_shops
        ]
    }
