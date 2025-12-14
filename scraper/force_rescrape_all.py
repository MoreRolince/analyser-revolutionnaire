"""
Script pour forcer le re-scraping de tous les produits et boutiques
pour récupérer les vraies URLs et images
"""
import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ajouter les chemins pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
scraper_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(scraper_dir)
backend_path = os.path.join(project_root, 'backend')

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.models import ShopGlobal, ProductGlobal, MarketplaceType
from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from services.continuous_scraper import ContinuousScraper

# Configuration DB
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

async def rescrape_all_products():
    """Re-scrape tous les produits pour mettre à jour URLs et images"""
    db = SessionLocal()
    scraper = ContinuousScraper()
    
    try:
        # Récupérer tous les produits
        products = db.query(ProductGlobal).all()
        print(f"📦 {len(products)} produits à re-scraper...")
        
        updated = 0
        errors = 0
        
        for i, product in enumerate(products, 1):
            if not product.product_url:
                print(f"⚠️ Produit {i}/{len(products)}: Pas d'URL, ignoré")
                continue
            
            try:
                print(f"🔄 [{i}/{len(products)}] Scraping: {product.product_name[:50]}...")
                
                # Déterminer le scraper à utiliser
                marketplace_enum = MarketplaceType[product.marketplace.upper()] if hasattr(MarketplaceType, product.marketplace.upper()) else MarketplaceType.OTHER
                
                if marketplace_enum == MarketplaceType.CHARIOW:
                    scraper_instance = ChariowScraper()
                elif marketplace_enum == MarketplaceType.MAKETOU:
                    scraper_instance = MaketouScraper()
                else:
                    print(f"⚠️ Marketplace non supporté: {product.marketplace}")
                    continue
                
                # Scraper le produit
                result = await scraper_instance.scrape_async(product.product_url)
                
                if result and result.get("name"):
                    # Mettre à jour les données
                    product.product_name = result.get("name", product.product_name)
                    product.price = result.get("price", product.price)
                    
                    # Mettre à jour l'image si disponible
                    if result.get("image"):
                        product.product_image = result["image"]
                    
                    # Mettre à jour la description si disponible
                    if result.get("description"):
                        product.product_description = result["description"]
                    
                    # S'assurer que l'URL est correcte
                    if result.get("url"):
                        product.product_url = result["url"]
                    
                    product.last_scraped_at = datetime.now()
                    
                    db.commit()
                    updated += 1
                    print(f"✅ Mis à jour: {product.product_name[:50]}")
                else:
                    print(f"⚠️ Aucune donnée récupérée pour {product.product_url}")
                    errors += 1
                
                # Pause pour éviter de surcharger
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Erreur pour {product.product_url}: {e}")
                errors += 1
                db.rollback()
                continue
        
        print(f"\n✅ Re-scraping terminé: {updated} produits mis à jour, {errors} erreurs")
        
    finally:
        db.close()

async def rescrape_all_shops():
    """Re-scrape toutes les boutiques pour mettre à jour les données"""
    db = SessionLocal()
    scraper = ContinuousScraper()
    
    try:
        # Récupérer toutes les boutiques
        shops = db.query(ShopGlobal).all()
        print(f"🏪 {len(shops)} boutiques à re-scraper...")
        
        updated = 0
        errors = 0
        
        for i, shop in enumerate(shops, 1):
            if not shop.shop_url:
                print(f"⚠️ Boutique {i}/{len(shops)}: Pas d'URL, ignoré")
                continue
            
            try:
                print(f"🔄 [{i}/{len(shops)}] Scraping: {shop.shop_name[:50]}...")
                
                # Scraper la boutique
                result = await scraper.scrape_shop(shop.shop_url, shop.marketplace)
                
                if result:
                    # Mettre à jour les données
                    shop.shop_name = result.get("name", shop.shop_name)
                    shop.revenue_est_min = result.get("estimated_revenue", shop.revenue_est_min)
                    shop.revenue_est_max = result.get("estimated_revenue", shop.revenue_est_max)
                    shop.score_global = result.get("score", shop.score_global)
                    shop.last_scraped_at = datetime.now()
                    
                    db.commit()
                    updated += 1
                    print(f"✅ Boutique mise à jour: {shop.shop_name[:50]}")
                else:
                    print(f"⚠️ Aucune donnée récupérée pour {shop.shop_url}")
                    errors += 1
                
                # Pause pour éviter de surcharger
                await asyncio.sleep(3)
                
            except Exception as e:
                print(f"❌ Erreur pour {shop.shop_url}: {e}")
                errors += 1
                db.rollback()
                continue
        
        print(f"\n✅ Re-scraping terminé: {updated} boutiques mises à jour, {errors} erreurs")
        
    finally:
        db.close()

async def main():
    """Fonction principale"""
    print("🚀 Démarrage du re-scraping complet...")
    print("=" * 60)
    
    # Re-scraper les boutiques d'abord (pour avoir les URLs de produits)
    print("\n📦 Étape 1: Re-scraping des boutiques...")
    await rescrape_all_shops()
    
    # Puis re-scraper les produits
    print("\n📦 Étape 2: Re-scraping des produits...")
    await rescrape_all_products()
    
    print("\n" + "=" * 60)
    print("✅ Re-scraping complet terminé !")

if __name__ == "__main__":
    asyncio.run(main())




Script pour forcer le re-scraping de tous les produits et boutiques
pour récupérer les vraies URLs et images
"""
import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ajouter les chemins pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
scraper_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(scraper_dir)
backend_path = os.path.join(project_root, 'backend')

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.models import ShopGlobal, ProductGlobal, MarketplaceType
from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from services.continuous_scraper import ContinuousScraper

# Configuration DB
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

async def rescrape_all_products():
    """Re-scrape tous les produits pour mettre à jour URLs et images"""
    db = SessionLocal()
    scraper = ContinuousScraper()
    
    try:
        # Récupérer tous les produits
        products = db.query(ProductGlobal).all()
        print(f"📦 {len(products)} produits à re-scraper...")
        
        updated = 0
        errors = 0
        
        for i, product in enumerate(products, 1):
            if not product.product_url:
                print(f"⚠️ Produit {i}/{len(products)}: Pas d'URL, ignoré")
                continue
            
            try:
                print(f"🔄 [{i}/{len(products)}] Scraping: {product.product_name[:50]}...")
                
                # Déterminer le scraper à utiliser
                marketplace_enum = MarketplaceType[product.marketplace.upper()] if hasattr(MarketplaceType, product.marketplace.upper()) else MarketplaceType.OTHER
                
                if marketplace_enum == MarketplaceType.CHARIOW:
                    scraper_instance = ChariowScraper()
                elif marketplace_enum == MarketplaceType.MAKETOU:
                    scraper_instance = MaketouScraper()
                else:
                    print(f"⚠️ Marketplace non supporté: {product.marketplace}")
                    continue
                
                # Scraper le produit
                result = await scraper_instance.scrape_async(product.product_url)
                
                if result and result.get("name"):
                    # Mettre à jour les données
                    product.product_name = result.get("name", product.product_name)
                    product.price = result.get("price", product.price)
                    
                    # Mettre à jour l'image si disponible
                    if result.get("image"):
                        product.product_image = result["image"]
                    
                    # Mettre à jour la description si disponible
                    if result.get("description"):
                        product.product_description = result["description"]
                    
                    # S'assurer que l'URL est correcte
                    if result.get("url"):
                        product.product_url = result["url"]
                    
                    product.last_scraped_at = datetime.now()
                    
                    db.commit()
                    updated += 1
                    print(f"✅ Mis à jour: {product.product_name[:50]}")
                else:
                    print(f"⚠️ Aucune donnée récupérée pour {product.product_url}")
                    errors += 1
                
                # Pause pour éviter de surcharger
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Erreur pour {product.product_url}: {e}")
                errors += 1
                db.rollback()
                continue
        
        print(f"\n✅ Re-scraping terminé: {updated} produits mis à jour, {errors} erreurs")
        
    finally:
        db.close()

async def rescrape_all_shops():
    """Re-scrape toutes les boutiques pour mettre à jour les données"""
    db = SessionLocal()
    scraper = ContinuousScraper()
    
    try:
        # Récupérer toutes les boutiques
        shops = db.query(ShopGlobal).all()
        print(f"🏪 {len(shops)} boutiques à re-scraper...")
        
        updated = 0
        errors = 0
        
        for i, shop in enumerate(shops, 1):
            if not shop.shop_url:
                print(f"⚠️ Boutique {i}/{len(shops)}: Pas d'URL, ignoré")
                continue
            
            try:
                print(f"🔄 [{i}/{len(shops)}] Scraping: {shop.shop_name[:50]}...")
                
                # Scraper la boutique
                result = await scraper.scrape_shop(shop.shop_url, shop.marketplace)
                
                if result:
                    # Mettre à jour les données
                    shop.shop_name = result.get("name", shop.shop_name)
                    shop.revenue_est_min = result.get("estimated_revenue", shop.revenue_est_min)
                    shop.revenue_est_max = result.get("estimated_revenue", shop.revenue_est_max)
                    shop.score_global = result.get("score", shop.score_global)
                    shop.last_scraped_at = datetime.now()
                    
                    db.commit()
                    updated += 1
                    print(f"✅ Boutique mise à jour: {shop.shop_name[:50]}")
                else:
                    print(f"⚠️ Aucune donnée récupérée pour {shop.shop_url}")
                    errors += 1
                
                # Pause pour éviter de surcharger
                await asyncio.sleep(3)
                
            except Exception as e:
                print(f"❌ Erreur pour {shop.shop_url}: {e}")
                errors += 1
                db.rollback()
                continue
        
        print(f"\n✅ Re-scraping terminé: {updated} boutiques mises à jour, {errors} erreurs")
        
    finally:
        db.close()

async def main():
    """Fonction principale"""
    print("🚀 Démarrage du re-scraping complet...")
    print("=" * 60)
    
    # Re-scraper les boutiques d'abord (pour avoir les URLs de produits)
    print("\n📦 Étape 1: Re-scraping des boutiques...")
    await rescrape_all_shops()
    
    # Puis re-scraper les produits
    print("\n📦 Étape 2: Re-scraping des produits...")
    await rescrape_all_products()
    
    print("\n" + "=" * 60)
    print("✅ Re-scraping complet terminé !")

if __name__ == "__main__":
    asyncio.run(main())



