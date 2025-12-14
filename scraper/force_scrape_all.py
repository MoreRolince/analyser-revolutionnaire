"""
Script pour forcer le scraping de TOUTES les boutiques existantes
et collecter un maximum de produits
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ajouter les chemins
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_path)

from services.continuous_scraper import ContinuousScraper, import_backend_models

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

async def force_scrape_all():
    """Force le scraping de toutes les boutiques"""
    print("="*70)
    print("🚀 SCRAPING FORCÉ DE TOUTES LES BOUTIQUES")
    print("="*70)
    print()
    
    scraper = ContinuousScraper()
    db = SessionLocal()
    
    try:
        ShopGlobal, _, _ = import_backend_models()
        
        # Récupérer TOUTES les boutiques
        all_shops = db.query(ShopGlobal).all()
        print(f"📦 {len(all_shops)} boutiques trouvées")
        print()
        
        total_products = 0
        successful = 0
        failed = 0
        
        for i, shop in enumerate(all_shops, 1):
            marketplace = shop.marketplace if isinstance(shop.marketplace, str) else shop.marketplace.value
            print(f"[{i}/{len(all_shops)}] 🔄 {shop.shop_name} ({marketplace})")
            
            try:
                result = await scraper.scrape_shop(shop.shop_url, marketplace)
                
                if result.get('status') == 'success':
                    successful += 1
                    products = result.get('products_saved', 0)
                    total_products += products
                    print(f"   ✅ {products} produits sauvegardés")
                else:
                    failed += 1
                    print(f"   ⚠️  {result.get('message', 'Erreur')}")
                
                # Pause entre chaque scraping
                await asyncio.sleep(2)
                
            except Exception as e:
                failed += 1
                print(f"   ❌ Erreur: {e}")
                continue
        
        print("\n" + "="*70)
        print("📊 RÉSUMÉ")
        print("="*70)
        print(f"✅ Boutiques réussies: {successful}")
        print(f"❌ Boutiques échouées: {failed}")
        print(f"📦 Total produits collectés: {total_products}")
        print()
        
        # Afficher les statistiques finales
        stats = db.query(ShopGlobal).all()
        total_shops = len(stats)
        total_winners = sum(s.winners_count for s in stats)
        avg_score = sum(s.score_global for s in stats) / total_shops if total_shops > 0 else 0
        
        print("📈 STATISTIQUES FINALES")
        print(f"   Total boutiques: {total_shops}")
        print(f"   Total winners: {total_winners}")
        print(f"   Score moyen: {avg_score:.1f}/100")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(force_scrape_all())




Script pour forcer le scraping de TOUTES les boutiques existantes
et collecter un maximum de produits
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ajouter les chemins
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_path)

from services.continuous_scraper import ContinuousScraper, import_backend_models

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

async def force_scrape_all():
    """Force le scraping de toutes les boutiques"""
    print("="*70)
    print("🚀 SCRAPING FORCÉ DE TOUTES LES BOUTIQUES")
    print("="*70)
    print()
    
    scraper = ContinuousScraper()
    db = SessionLocal()
    
    try:
        ShopGlobal, _, _ = import_backend_models()
        
        # Récupérer TOUTES les boutiques
        all_shops = db.query(ShopGlobal).all()
        print(f"📦 {len(all_shops)} boutiques trouvées")
        print()
        
        total_products = 0
        successful = 0
        failed = 0
        
        for i, shop in enumerate(all_shops, 1):
            marketplace = shop.marketplace if isinstance(shop.marketplace, str) else shop.marketplace.value
            print(f"[{i}/{len(all_shops)}] 🔄 {shop.shop_name} ({marketplace})")
            
            try:
                result = await scraper.scrape_shop(shop.shop_url, marketplace)
                
                if result.get('status') == 'success':
                    successful += 1
                    products = result.get('products_saved', 0)
                    total_products += products
                    print(f"   ✅ {products} produits sauvegardés")
                else:
                    failed += 1
                    print(f"   ⚠️  {result.get('message', 'Erreur')}")
                
                # Pause entre chaque scraping
                await asyncio.sleep(2)
                
            except Exception as e:
                failed += 1
                print(f"   ❌ Erreur: {e}")
                continue
        
        print("\n" + "="*70)
        print("📊 RÉSUMÉ")
        print("="*70)
        print(f"✅ Boutiques réussies: {successful}")
        print(f"❌ Boutiques échouées: {failed}")
        print(f"📦 Total produits collectés: {total_products}")
        print()
        
        # Afficher les statistiques finales
        stats = db.query(ShopGlobal).all()
        total_shops = len(stats)
        total_winners = sum(s.winners_count for s in stats)
        avg_score = sum(s.score_global for s in stats) / total_shops if total_shops > 0 else 0
        
        print("📈 STATISTIQUES FINALES")
        print(f"   Total boutiques: {total_shops}")
        print(f"   Total winners: {total_winners}")
        print(f"   Score moyen: {avg_score:.1f}/100")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(force_scrape_all())



