#!/usr/bin/env python3
"""
Script pour mettre à jour les prix des produits existants
"""
import asyncio
import os
import sys
from datetime import datetime

# Ajouter les chemins pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, 'backend')

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Configuration DB
env_path = os.path.join(project_root, 'backend', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

from app.models import DigitalProductDetected
from services.chariow_scraper import ChariowScraper
from services.maketou_scraper import MaketouScraper

async def update_product_price(db, product):
    """Met à jour le prix d'un produit"""
    url = product.landing_page_url
    
    try:
        if 'mychariow.shop' in url or 'chariow.com' in url:
            print(f"  🔍 Scraping Chariow...")
            scraper = ChariowScraper()
            product_data = await scraper.scrape_product(url, "", "")
            if product_data:
                new_price = product_data.get('price', 0)
                print(f"  📊 Prix extrait: {new_price} FCFA")
                if new_price > 0 and 100 <= new_price <= 1000000:
                    old_price = product.price
                    # Mettre à jour seulement si le prix a changé significativement (> 10% de différence)
                    if abs(new_price - old_price) > max(old_price * 0.1, 1000):
                        product.price = new_price
                        product.updated_at = datetime.now()
                        print(f"  ✅ Prix mis à jour: {old_price} → {new_price} FCFA")
                        return True
                    else:
                        print(f"  ℹ️  Prix similaire (différence < 10%): {old_price} vs {new_price}")
                        return False
                else:
                    print(f"  ⚠️  Prix extrait invalide ou hors limites: {new_price}")
            else:
                print(f"  ⚠️  Aucune donnée extraite")
        elif 'mymaketou.store' in url or 'maketou.com' in url:
            print(f"  🔍 Scraping Maketou...")
            scraper = MaketouScraper()
            product_data = await scraper.scrape_product(url, "", "")
            if product_data:
                new_price = product_data.get('price', 0)
                print(f"  📊 Prix extrait: {new_price} FCFA")
                if new_price > 0 and 100 <= new_price <= 1000000:
                    old_price = product.price
                    # Mettre à jour seulement si le prix a changé significativement (> 10% de différence)
                    if abs(new_price - old_price) > max(old_price * 0.1, 1000):
                        product.price = new_price
                        product.updated_at = datetime.now()
                        print(f"  ✅ Prix mis à jour: {old_price} → {new_price} FCFA")
                        return True
                    else:
                        print(f"  ℹ️  Prix similaire (différence < 10%): {old_price} vs {new_price}")
                        return False
                else:
                    print(f"  ⚠️  Prix extrait invalide ou hors limites: {new_price}")
            else:
                print(f"  ⚠️  Aucune donnée extraite")
    except Exception as e:
        print(f"  ❌ Erreur pour {url}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return False

async def main():
    db = SessionLocal()
    try:
        # Récupérer tous les produits avec des prix suspects
        products = db.query(DigitalProductDetected).all()
        
        print(f"📊 {len(products)} produits à vérifier")
        print("-" * 70)
        
        updated_count = 0
        for i, product in enumerate(products, 1):
            print(f"\n[{i}/{len(products)}] {product.product_title[:50]}")
            print(f"  URL: {product.landing_page_url[:60]}...")
            print(f"  Prix actuel: {product.price} FCFA")
            
            # Toujours essayer de mettre à jour le prix (pour corriger les erreurs)
            # Mais on marque comme "suspect" seulement ceux qui sont clairement faux
            is_suspect = product.price < 100 or product.price > 1000000 or (2000 <= product.price <= 2099)
            
            if is_suspect:
                print(f"  ⚠️  Prix suspect détecté")
            
            # Essayer de mettre à jour le prix
            if await update_product_price(db, product):
                updated_count += 1
                db.commit()
            elif not is_suspect:
                print(f"  ℹ️  Prix actuel semble correct (pas de changement)")
            
            await asyncio.sleep(2)  # Pause entre les requêtes
        
        print(f"\n{'='*70}")
        print(f"✅ Mise à jour terminée!")
        print(f"  {updated_count} prix mis à jour")
        print(f"{'='*70}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
