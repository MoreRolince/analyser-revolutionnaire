"""
Script pour relancer le scraping de tous les produits
et récupérer les vrais noms, liens et images
"""
import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ajouter les chemins pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, 'backend')

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Configuration DB
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Importer les scrapers
from services.chariow import ChariowScraper
from services.maketou import MaketouScraper

async def rescrape_product(product_url: str, marketplace: str):
    """Re-scrape un produit pour obtenir les vraies données"""
    try:
        if marketplace.lower() == 'chariow':
            scraper = ChariowScraper()
        elif marketplace.lower() == 'maketou':
            scraper = MaketouScraper()
        else:
            return None
        
        print(f"🔄 Scraping: {product_url[:60]}...")
        result = await scraper.scrape_async(product_url)
        return result
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

async def main():
    """Fonction principale"""
    db = SessionLocal()
    
    try:
        # Importer les modèles
        from app.models import ProductGlobal, MarketplaceType
        
        # Récupérer tous les produits
        products = db.query(ProductGlobal).all()
        print(f"📦 {len(products)} produits à re-scraper...\n")
        
        updated = 0
        errors = 0
        skipped = 0
        
        for i, product in enumerate(products, 1):
            if not product.product_url:
                print(f"⚠️ [{i}/{len(products)}] Pas d'URL pour le produit ID {product.id}")
                skipped += 1
                continue
            
            try:
                # Déterminer le marketplace
                marketplace = product.marketplace
                if hasattr(marketplace, 'value'):
                    marketplace = marketplace.value
                marketplace = str(marketplace).lower()
                
                # Scraper le produit
                result = await rescrape_product(product.product_url, marketplace)
                
                if result and result.get("name"):
                    # Mettre à jour les données
                    old_name = product.product_name
                    product.product_name = result.get("name", product.product_name)
                    
                    # Mettre à jour l'URL si elle a changé
                    if result.get("url") and result.get("url") != product.product_url:
                        product.product_url = result["url"]
                    
                    # Mettre à jour l'image
                    if result.get("image"):
                        product.product_image = result["image"]
                        print(f"✅ Image trouvée: {result['image'][:60]}...")
                    
                    # Mettre à jour la description
                    if result.get("description"):
                        product.product_description = result["description"][:1000]
                    
                    # Mettre à jour le prix
                    if result.get("price"):
                        product.price = result.get("price")
                    
                    product.last_scraped_at = datetime.now()
                    
                    db.commit()
                    updated += 1
                    print(f"✅ [{i}/{len(products)}] Mis à jour: {product.product_name[:50]}")
                    if old_name != product.product_name:
                        print(f"   Ancien nom: {old_name[:50]}")
                else:
                    print(f"⚠️ [{i}/{len(products)}] Aucune donnée récupérée pour {product.product_url[:60]}")
                    errors += 1
                
                # Pause pour éviter de surcharger
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ [{i}/{len(products)}] Erreur pour {product.product_url[:60]}: {e}")
                errors += 1
                db.rollback()
                continue
        
        print(f"\n{'='*60}")
        print(f"✅ Re-scraping terminé!")
        print(f"   - {updated} produits mis à jour")
        print(f"   - {errors} erreurs")
        print(f"   - {skipped} produits ignorés (pas d'URL)")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Démarrage du re-scraping des produits...")
    print("=" * 60)
    asyncio.run(main())




Script pour relancer le scraping de tous les produits
et récupérer les vrais noms, liens et images
"""
import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ajouter les chemins pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, 'backend')

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Configuration DB
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Importer les scrapers
from services.chariow import ChariowScraper
from services.maketou import MaketouScraper

async def rescrape_product(product_url: str, marketplace: str):
    """Re-scrape un produit pour obtenir les vraies données"""
    try:
        if marketplace.lower() == 'chariow':
            scraper = ChariowScraper()
        elif marketplace.lower() == 'maketou':
            scraper = MaketouScraper()
        else:
            return None
        
        print(f"🔄 Scraping: {product_url[:60]}...")
        result = await scraper.scrape_async(product_url)
        return result
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

async def main():
    """Fonction principale"""
    db = SessionLocal()
    
    try:
        # Importer les modèles
        from app.models import ProductGlobal, MarketplaceType
        
        # Récupérer tous les produits
        products = db.query(ProductGlobal).all()
        print(f"📦 {len(products)} produits à re-scraper...\n")
        
        updated = 0
        errors = 0
        skipped = 0
        
        for i, product in enumerate(products, 1):
            if not product.product_url:
                print(f"⚠️ [{i}/{len(products)}] Pas d'URL pour le produit ID {product.id}")
                skipped += 1
                continue
            
            try:
                # Déterminer le marketplace
                marketplace = product.marketplace
                if hasattr(marketplace, 'value'):
                    marketplace = marketplace.value
                marketplace = str(marketplace).lower()
                
                # Scraper le produit
                result = await rescrape_product(product.product_url, marketplace)
                
                if result and result.get("name"):
                    # Mettre à jour les données
                    old_name = product.product_name
                    product.product_name = result.get("name", product.product_name)
                    
                    # Mettre à jour l'URL si elle a changé
                    if result.get("url") and result.get("url") != product.product_url:
                        product.product_url = result["url"]
                    
                    # Mettre à jour l'image
                    if result.get("image"):
                        product.product_image = result["image"]
                        print(f"✅ Image trouvée: {result['image'][:60]}...")
                    
                    # Mettre à jour la description
                    if result.get("description"):
                        product.product_description = result["description"][:1000]
                    
                    # Mettre à jour le prix
                    if result.get("price"):
                        product.price = result.get("price")
                    
                    product.last_scraped_at = datetime.now()
                    
                    db.commit()
                    updated += 1
                    print(f"✅ [{i}/{len(products)}] Mis à jour: {product.product_name[:50]}")
                    if old_name != product.product_name:
                        print(f"   Ancien nom: {old_name[:50]}")
                else:
                    print(f"⚠️ [{i}/{len(products)}] Aucune donnée récupérée pour {product.product_url[:60]}")
                    errors += 1
                
                # Pause pour éviter de surcharger
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ [{i}/{len(products)}] Erreur pour {product.product_url[:60]}: {e}")
                errors += 1
                db.rollback()
                continue
        
        print(f"\n{'='*60}")
        print(f"✅ Re-scraping terminé!")
        print(f"   - {updated} produits mis à jour")
        print(f"   - {errors} erreurs")
        print(f"   - {skipped} produits ignorés (pas d'URL)")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Démarrage du re-scraping des produits...")
    print("=" * 60)
    asyncio.run(main())



