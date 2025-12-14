"""
Script de scraping Facebook Ads amélioré - Version rapide et efficace
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

from services.facebook_ads_scraper_v2 import FacebookAdsScraperV2
from app.models import FacebookAdRaw, DigitalProductDetected


async def scrape_and_save():
    """Scrape et sauvegarde les annonces"""
    db = SessionLocal()
    
    try:
        print("🚀 SCRAPING FACEBOOK ADS - VERSION AMÉLIORÉE")
        print("=" * 60)
        
        scraper = FacebookAdsScraperV2()
        
        # Scraping avec mots-clés prioritaires et pays principaux
        print("\n📦 Démarrage du scraping...")
        all_ads = await scraper.scrape_all_keywords(
            countries=["SN", "CI", "BJ"],  # Sénégal, Côte d'Ivoire, Bénin
            limit_per_keyword=30  # Limite raisonnable pour rapidité
        )
        
        print(f"\n💾 Sauvegarde de {len(all_ads)} annonces...")
        saved = 0
        
        for ad in all_ads:
            try:
                # Vérifier si existe déjà
                existing = db.query(FacebookAdRaw).filter(
                    FacebookAdRaw.landing_page_url == ad.get('landing_page_url', '')
                ).first()
                
                if not existing:
                    fb_ad = FacebookAdRaw(
                        product_title=ad.get('product_title'),
                        description=ad.get('ad_text', ''),
                        media_url=ad.get('media_url'),
                        landing_page_url=ad.get('landing_page_url', ''),
                        advertiser_page=ad.get('advertiser_page'),
                        active_status=ad.get('active_status', 'active'),
                        country_targeting=ad.get('country_targeting'),
                        keyword=ad.get('keyword'),
                    )
                    db.add(fb_ad)
                    saved += 1
            except Exception as e:
                print(f"  ⚠️  Erreur sauvegarde: {e}")
                continue
        
        db.commit()
        print(f"✅ {saved} nouvelles annonces sauvegardées")
        
        # Créer les produits détectés
        print(f"\n📦 Création des produits détectés...")
        products_created = 0
        
        for ad in all_ads:
            try:
                existing = db.query(DigitalProductDetected).filter(
                    DigitalProductDetected.landing_page_url == ad.get('landing_page_url', '')
                ).first()
                
                if not existing:
                    # Détecter le marketplace
                    marketplace = None
                    url = ad.get('landing_page_url', '').lower()
                    if 'maketou' in url:
                        marketplace = 'maketou'
                    elif 'chariow' in url:
                        marketplace = 'chariow'
                    elif 'systeme.io' in url:
                        marketplace = 'systeme.io'
                    elif 'gumroad' in url:
                        marketplace = 'gumroad'
                    elif 'payhip' in url:
                        marketplace = 'payhip'
                    
                    # Extraire le prix depuis les insights
                    price = None
                    insights = ad.get('insights', {})
                    if insights.get('estimated_price'):
                        price = insights['estimated_price']
                    
                    product = DigitalProductDetected(
                        landing_page_url=ad.get('landing_page_url', ''),
                        product_title=ad.get('product_title', 'Produit digital'),
                        description=ad.get('ad_text', ''),
                        price=price,
                        marketplace=marketplace,
                    )
                    db.add(product)
                    products_created += 1
            except Exception as e:
                continue
        
        db.commit()
        print(f"✅ {products_created} produits créés")
        
        print(f"\n🎉 Terminé!")
        print(f"   Annonces: {saved}")
        print(f"   Produits: {products_created}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(scrape_and_save())

