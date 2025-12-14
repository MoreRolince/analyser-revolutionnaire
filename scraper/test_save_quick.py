"""
Test rapide : scraper 1 mot-clé et sauvegarder
"""
import asyncio
import sys
import os

# Configuration Windows
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configuration DB
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, 'backend')

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from services.facebook_ads_scraper_working import scrape_ads_library
from app.models import FacebookAdRaw

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

async def test():
    print("=" * 70)
    print("TEST RAPIDE: Scraper et sauvegarder")
    print("=" * 70)
    
    # Scraper 1 mot-clé
    print("\n1. Scraping du mot-cle 'formation'...")
    ads = await scrape_ads_library(search_term="formation", limit=3)
    print(f"   {len(ads)} annonces trouvees")
    
    if not ads:
        print("   ERREUR: Aucune annonce trouvee")
        return
    
    # Afficher les annonces
    for i, ad in enumerate(ads[:3], 1):
        print(f"\n   Annonce {i}:")
        print(f"      Page: {ad.get('pageName', 'N/A')}")
        print(f"      Texte: {ad.get('text', 'N/A')[:80]}...")
        print(f"      Image: {'OUI' if ad.get('imageUrl') else 'NON'}")
        url = ad.get('productUrl') or 'N/A'
        if url != 'N/A':
            print(f"      URL: {url[:60]}...")
        else:
            print(f"      URL: N/A")
    
    # Sauvegarder
    print("\n2. Sauvegarde dans la base de donnees...")
    db = SessionLocal()
    
    try:
        saved = 0
        for ad in ads:
            try:
                # Vérifier si existe déjà
                existing = db.execute(
                    text("SELECT COUNT(*) FROM fb_ads_raw WHERE landing_page_url = :url"),
                    {"url": ad.get('productUrl') or ad.get('snapshotUrl', '')}
                ).scalar()
                
                if existing > 0:
                    print(f"   Annonce deja existante: {ad.get('pageName', 'N/A')}")
                    continue
                
                # Créer l'annonce
                fb_ad = FacebookAdRaw(
                    product_title=ad.get('title') or ad.get('text', '')[:200],
                    description=ad.get('text', ''),
                    media_url=ad.get('imageUrl'),
                    landing_page_url=ad.get('productUrl') or ad.get('snapshotUrl', ''),
                    advertiser_page=ad.get('pageName', ''),
                    active_status='active',
                    country_targeting='ALL',
                    keyword=ad.get('keyword', 'formation'),
                )
                
                db.add(fb_ad)
                saved += 1
                print(f"   Annonce sauvegardee: {ad.get('pageName', 'N/A')}")
                
            except Exception as e:
                print(f"   ERREUR sauvegarde: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        db.commit()
        print(f"\n3. RESULTAT: {saved} nouvelles annonces sauvegardees")
        
        # Vérifier le total
        total = db.execute(text("SELECT COUNT(*) FROM fb_ads_raw")).scalar()
        print(f"   Total annonces en base: {total}")
        
    except Exception as e:
        print(f"   ERREUR commit: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test())

