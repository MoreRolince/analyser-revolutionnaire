"""
Endpoint pour déclencher manuellement le crawling des marketplaces
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import sys
import asyncio

from app.database import get_db
from app.auth import get_current_admin_user
from app.models import User

router = APIRouter()

@router.post("/crawl")
async def trigger_crawl(
    marketplace: Optional[str] = None,
    shop_urls: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Déclenche le crawling d'une marketplace spécifique
    Seulement accessible aux admins
    """
    # Ajouter le chemin du scraper
    scraper_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scraper')
    sys.path.insert(0, scraper_path)
    
    from services.winners_crawler import crawl_marketplace_winners
    
    if marketplace:
        marketplaces = [marketplace]
    else:
        marketplaces = ["chariow", "maketou"]
    
    results = []
    for mp in marketplaces:
        try:
            result = await crawl_marketplace_winners(mp, shop_urls=shop_urls)
            results.append({
                "marketplace": mp,
                "status": "success",
                "products": result.get("products", 0),
                "shops": result.get("shops", 0)
            })
        except Exception as e:
            results.append({
                "marketplace": mp,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "message": "Crawling terminé",
        "results": results
    }

@router.post("/crawl-all")
async def trigger_crawl_all(
    background_tasks: BackgroundTasks = BackgroundTasks(),
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Déclenche le crawling de toutes les marketplaces
    """
    scraper_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scraper')
    sys.path.insert(0, scraper_path)
    
    from services.winners_crawler import crawl_all_marketplaces
    
    # URLs de boutiques connues à scraper
    shop_urls = {
        "maketou": ["https://numerik.mymaketou.store/"],
        "chariow": ["https://tuswehnj.mychariow.shop/"]
    }
    
    try:
        results = crawl_all_marketplaces(shop_urls=shop_urls)
        return {
            "message": "Crawling de toutes les marketplaces terminé",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du crawling: {str(e)}")

@router.post("/run-cycle")
async def trigger_continuous_cycle(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Déclenche un cycle de scraping continu manuellement
    """
    scraper_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scraper')
    sys.path.insert(0, scraper_path)
    
    from services.continuous_scraper import ContinuousScraper
    
    try:
        scraper = ContinuousScraper()
        result = await scraper.run_cycle()
        return {
            "message": "Cycle de scraping terminé",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du cycle: {str(e)}")

@router.get("/status")
async def get_scraper_status(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Récupère le statut du scraper (nombre de boutiques, dernière mise à jour, etc.)
    """
    from app.models import ShopGlobal, ProductGlobal
    from sqlalchemy import func
    
    total_shops = db.query(ShopGlobal).count()
    total_products = db.query(ProductGlobal).count()
    
    # Dernière mise à jour
    last_update = db.query(func.max(ShopGlobal.last_scraped_at)).scalar()
    
    # Boutiques par marketplace
    shops_by_marketplace = db.query(
        ShopGlobal.marketplace,
        func.count(ShopGlobal.id)
    ).group_by(ShopGlobal.marketplace).all()
    
    return {
        "total_shops": total_shops,
        "total_products": total_products,
        "last_update": last_update.isoformat() if last_update else None,
        "shops_by_marketplace": {
            str(mp): count for mp, count in shops_by_marketplace
        }
    }


"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import sys
import asyncio

from app.database import get_db
from app.auth import get_current_admin_user
from app.models import User

router = APIRouter()

@router.post("/crawl")
async def trigger_crawl(
    marketplace: Optional[str] = None,
    shop_urls: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Déclenche le crawling d'une marketplace spécifique
    Seulement accessible aux admins
    """
    # Ajouter le chemin du scraper
    scraper_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scraper')
    sys.path.insert(0, scraper_path)
    
    from services.winners_crawler import crawl_marketplace_winners
    
    if marketplace:
        marketplaces = [marketplace]
    else:
        marketplaces = ["chariow", "maketou"]
    
    results = []
    for mp in marketplaces:
        try:
            result = await crawl_marketplace_winners(mp, shop_urls=shop_urls)
            results.append({
                "marketplace": mp,
                "status": "success",
                "products": result.get("products", 0),
                "shops": result.get("shops", 0)
            })
        except Exception as e:
            results.append({
                "marketplace": mp,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "message": "Crawling terminé",
        "results": results
    }

@router.post("/crawl-all")
async def trigger_crawl_all(
    background_tasks: BackgroundTasks = BackgroundTasks(),
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Déclenche le crawling de toutes les marketplaces
    """
    scraper_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scraper')
    sys.path.insert(0, scraper_path)
    
    from services.winners_crawler import crawl_all_marketplaces
    
    # URLs de boutiques connues à scraper
    shop_urls = {
        "maketou": ["https://numerik.mymaketou.store/"],
        "chariow": ["https://tuswehnj.mychariow.shop/"]
    }
    
    try:
        results = crawl_all_marketplaces(shop_urls=shop_urls)
        return {
            "message": "Crawling de toutes les marketplaces terminé",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du crawling: {str(e)}")

@router.post("/run-cycle")
async def trigger_continuous_cycle(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Déclenche un cycle de scraping continu manuellement
    """
    scraper_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scraper')
    sys.path.insert(0, scraper_path)
    
    from services.continuous_scraper import ContinuousScraper
    
    try:
        scraper = ContinuousScraper()
        result = await scraper.run_cycle()
        return {
            "message": "Cycle de scraping terminé",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du cycle: {str(e)}")

@router.get("/status")
async def get_scraper_status(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Récupère le statut du scraper (nombre de boutiques, dernière mise à jour, etc.)
    """
    from app.models import ShopGlobal, ProductGlobal
    from sqlalchemy import func
    
    total_shops = db.query(ShopGlobal).count()
    total_products = db.query(ProductGlobal).count()
    
    # Dernière mise à jour
    last_update = db.query(func.max(ShopGlobal.last_scraped_at)).scalar()
    
    # Boutiques par marketplace
    shops_by_marketplace = db.query(
        ShopGlobal.marketplace,
        func.count(ShopGlobal.id)
    ).group_by(ShopGlobal.marketplace).all()
    
    return {
        "total_shops": total_shops,
        "total_products": total_products,
        "last_update": last_update.isoformat() if last_update else None,
        "shops_by_marketplace": {
            str(mp): count for mp, count in shops_by_marketplace
        }
    }

