"""
Script simple et rapide pour scraper Facebook Ads Library
Version simplifiée pour avoir des données rapidement
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

from app.models import FacebookAdRaw, DigitalProductDetected


async def scrape_simple():
    """Scrape simple et rapide - quelques mots-clés prioritaires"""
    from playwright.async_api import async_playwright
    from bs4 import BeautifulSoup
    import re
    
    # Mots-clés prioritaires uniquement
    KEYWORDS = [
        "formation", "ebook", "coaching", "make money", 
        "business en ligne", "revenus passifs"
    ]
    
    # Pays principaux Afrique de l'Ouest
    COUNTRIES = ["SN", "CI", "BJ"]  # Sénégal, Côte d'Ivoire, Bénin
    
    db = SessionLocal()
    ads_scraped = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            for keyword in KEYWORDS:
                for country in COUNTRIES:
                    try:
                        page = await context.new_page()
                        
                        # URL de recherche
                        search_url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country={country}&q={keyword.replace(' ', '%20')}&search_type=keyword_unordered"
                        
                        print(f"🔍 {keyword} - {country}...")
                        await page.goto(search_url, wait_until="networkidle", timeout=30000)
                        await page.wait_for_timeout(3000)
                        
                        # Scroll rapide (3 fois seulement)
                        for _ in range(3):
                            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            await page.wait_for_timeout(2000)
                        
                        # Extraire les annonces
                        content = await page.content()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Chercher tous les liens externes
                        all_links = soup.find_all('a', href=True)
                        seen_urls = set()
                        
                        for link in all_links:
                            href = link.get('href', '')
                            if not href or 'facebook.com' in href or href in seen_urls:
                                continue
                            
                            if href.startswith('http'):
                                seen_urls.add(href)
                                
                                # Extraire image
                                img = link.find('img')
                                media_url = None
                                if img:
                                    media_url = img.get('src') or img.get('data-src')
                                
                                # Extraire texte
                                ad_text = link.get_text(strip=True)[:300]
                                if not ad_text:
                                    parent = link.find_parent(['div', 'article'])
                                    if parent:
                                        ad_text = parent.get_text(strip=True)[:300]
                                
                                # Vérifier si c'est un produit digital
                                if any(domain in href.lower() for domain in ['maketou', 'chariow', 'systeme.io', 'gumroad', 'payhip']):
                                    ad_data = {
                                        "product_title": keyword,
                                        "description": ad_text,
                                        "media_url": media_url,
                                        "landing_page_url": href,
                                        "advertiser_page": "",
                                        "active_status": "active",
                                        "country_targeting": country,
                                        "keyword": keyword,
                                    }
                                    ads_scraped.append(ad_data)
                                    print(f"  ✅ {href[:60]}...")
                        
                        await page.close()
                        await asyncio.sleep(2)  # Pause courte
                        
                    except Exception as e:
                        print(f"  ⚠️  Erreur {keyword}/{country}: {e}")
                        continue
            
            await browser.close()
        
        # Sauvegarder dans la DB
        print(f"\n💾 Sauvegarde de {len(ads_scraped)} annonces...")
        saved = 0
        
        for ad in ads_scraped:
            try:
                # Vérifier si existe déjà
                existing = db.query(FacebookAdRaw).filter(
                    FacebookAdRaw.landing_page_url == ad['landing_page_url']
                ).first()
                
                if not existing:
                    fb_ad = FacebookAdRaw(**ad)
                    db.add(fb_ad)
                    saved += 1
            except Exception as e:
                print(f"  ⚠️  Erreur sauvegarde: {e}")
                continue
        
        db.commit()
        print(f"✅ {saved} nouvelles annonces sauvegardées")
        
        # Créer des produits détectés simples
        print(f"\n📦 Création des produits détectés...")
        products_created = 0
        
        for ad in ads_scraped:
            try:
                existing = db.query(DigitalProductDetected).filter(
                    DigitalProductDetected.landing_page_url == ad['landing_page_url']
                ).first()
                
                if not existing:
                    product = DigitalProductDetected(
                        landing_page_url=ad['landing_page_url'],
                        product_title=ad['product_title'] or "Produit digital",
                        description=ad['description'],
                        marketplace=ad['landing_page_url'].split('/')[2] if '/' in ad['landing_page_url'] else None,
                    )
                    db.add(product)
                    products_created += 1
            except Exception as e:
                continue
        
        db.commit()
        print(f"✅ {products_created} produits créés")
        
        print(f"\n🎉 Terminé! {saved} annonces et {products_created} produits disponibles")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 SCRAPING FACEBOOK ADS - VERSION SIMPLE")
    print("=" * 50)
    asyncio.run(scrape_simple())

