"""
Scraper Facebook Ads Library ULTRA OPTIMISÉ - 100 annonces en 10 minutes
Stratégie: Parallélisation + Extraction rapide + Pas de délais inutiles
"""
import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import hashlib

# Configuration DB
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

from app.models import FacebookAdRaw, DigitalProductDetected, DigitalProductScore
from services.winner_scorer import WinnerScorer


class FastFacebookScraper:
    """Scraper ultra-optimisé avec parallélisation"""
    
    BASE_URL = "https://www.facebook.com/ads/library"
    
    # Mots-clés prioritaires (volume élevé)
    KEYWORDS = [
        "formation", "ebook", "coaching", "cours", "guide",
        "make money", "business en ligne", "revenus passifs",
        "formation marketing", "ebook marketing", "formation digitale",
        "cours en ligne", "formation en ligne", "tutoriel",
        "gagner de l'argent", "revenus", "business",
    ]
    
    async def scrape_keyword_parallel(self, keyword: str, page, seen_urls: set) -> list:
        """Scrape un mot-clé de manière optimisée"""
        ads = []
        
        try:
            # URL sans filtre pays pour récupérer globalement
            url = f"{self.BASE_URL}/?active_status=all&ad_type=all&q={keyword.replace(' ', '%20')}&search_type=keyword_unordered"
            
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(1)  # Délai minimal
            
            # Scroll rapide et efficace (5 scrolls max)
            for i in range(5):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(0.5)  # Délai minimal entre scrolls
            
            # Extraction immédiate
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extraction rapide : chercher tous les liens externes directement
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                if not href or 'facebook.com' in href or href in seen_urls:
                    continue
                
                if href.startswith('http'):
                    # Vérifier si c'est un produit digital
                    url_lower = href.lower()
                    if any(domain in url_lower for domain in [
                        'maketou', 'chariow', 'systeme.io', 'gumroad', 
                        'payhip', 'notion.so', 'drive.google'
                    ]) or any(pattern in url_lower for pattern in [
                        '/product', '/produit', '/ebook', '/formation', 
                        '/cours', '/guide', '/coaching'
                    ]):
                        seen_urls.add(href)
                        
                        # Extraction rapide des données
                        img = link.find('img')
                        media_url = img.get('src') if img else None
                        
                        # Texte depuis le parent
                        parent = link.find_parent(['div', 'article', 'section'])
                        ad_text = ""
                        if parent:
                            ad_text = parent.get_text(strip=True)[:300]
                        if not ad_text:
                            ad_text = link.get_text(strip=True)[:300]
                        
                        if len(ad_text) >= 20:  # Validation minimale
                            ads.append({
                                'product_title': keyword,
                                'ad_text': ad_text,
                                'media_url': media_url,
                                'landing_page_url': href,
                                'advertiser_page': '',
                                'active_status': 'active',
                                'country_targeting': 'ALL',
                                'keyword': keyword,
                            })
        
        except Exception as e:
            print(f"  ⚠️  Erreur {keyword}: {e}")
        
        return ads
    
    async def scrape_all_fast(self, target: int = 100) -> list:
        """Scrape tous les mots-clés en parallèle"""
        all_ads = []
        seen_urls = set()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage"]
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            
            # Bloquer les ressources inutiles
            await context.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,css}", lambda route: route.abort())
            
            # Créer plusieurs pages pour parallélisation
            pages = [await context.new_page() for _ in range(3)]  # 3 pages en parallèle
            
            try:
                # Scraper les mots-clés en parallèle par groupes de 3
                for i in range(0, len(self.KEYWORDS), 3):
                    if len(all_ads) >= target:
                        break
                    
                    keywords_batch = self.KEYWORDS[i:i+3]
                    
                    # Scraper en parallèle
                    tasks = [
                        self.scrape_keyword_parallel(kw, pages[j % 3], seen_urls)
                        for j, kw in enumerate(keywords_batch)
                    ]
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results:
                        if isinstance(result, list):
                            all_ads.extend(result)
                            print(f"  ✅ {len(result)} annonces (Total: {len(all_ads)})")
                    
                    if len(all_ads) >= target:
                        break
                    
                    await asyncio.sleep(0.5)  # Délai minimal entre batches
                
            finally:
                await browser.close()
        
        return all_ads[:target]


async def main():
    """Script principal optimisé"""
    db = SessionLocal()
    
    try:
        print("🚀 SCRAPING ULTRA OPTIMISÉ - OBJECTIF: 100 ANNONCES EN 10 MIN")
        print("=" * 70)
        
        # Vérifier ce qu'on a déjà
        current = db.query(FacebookAdRaw).count()
        print(f"📊 Annonces actuelles: {current}")
        
        target = 100
        needed = max(0, target - current)
        
        if needed == 0:
            print("✅ Objectif déjà atteint!")
            return
        
        print(f"🎯 Objectif: {needed} nouvelles annonces")
        print(f"⏱️  Temps estimé: 5-10 minutes\n")
        
        scraper = FastFacebookScraper()
        
        # Scraping rapide
        print("📦 Scraping en cours...")
        start_time = datetime.now()
        all_ads = await scraper.scrape_all_fast(target=needed)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ {len(all_ads)} annonces scrapées en {elapsed:.1f} secondes")
        
        # Sauvegarde rapide en batch
        print(f"\n💾 Sauvegarde...")
        saved = 0
        
        for ad in all_ads:
            try:
                existing = db.query(FacebookAdRaw).filter(
                    FacebookAdRaw.landing_page_url == ad['landing_page_url']
                ).first()
                
                if not existing:
                    fb_ad = FacebookAdRaw(**ad)
                    db.add(fb_ad)
                    saved += 1
            except:
                continue
        
        db.commit()
        print(f"✅ {saved} annonces sauvegardées")
        
        # Création rapide des produits
        print(f"\n📦 Création des produits...")
        products_created = 0
        
        ads = db.query(FacebookAdRaw).all()
        for ad in ads:
            try:
                existing = db.query(DigitalProductDetected).filter(
                    DigitalProductDetected.landing_page_url == ad.landing_page_url
                ).first()
                
                if not existing:
                    url = (ad.landing_page_url or '').lower()
                    marketplace = None
                    
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
                    
                    if marketplace or any(kw in (ad.description or '').lower() for kw in ['formation', 'ebook', 'cours']):
                        product = DigitalProductDetected(
                            landing_page_url=ad.landing_page_url,
                            product_title=ad.product_title or "Produit digital",
                            description=ad.description,
                            marketplace=marketplace,
                        )
                        db.add(product)
                        products_created += 1
            except:
                continue
        
        db.commit()
        print(f"✅ {products_created} produits créés")
        
        # Calcul rapide des scores
        print(f"\n🏆 Calcul des scores...")
        scores_created = 0
        
        products = db.query(DigitalProductDetected).all()
        for product in products:
            try:
                existing = db.query(DigitalProductScore).filter(
                    DigitalProductScore.product_id == product.id
                ).first()
                
                if existing:
                    continue
                
                ads_for_product = db.query(FacebookAdRaw).filter(
                    FacebookAdRaw.landing_page_url == product.landing_page_url
                ).all()
                
                if not ads_for_product:
                    continue
                
                ads_data = [{
                    'product_title': ad.product_title,
                    'description': ad.description,
                    'landing_page_url': ad.landing_page_url,
                    'country_targeting': ad.country_targeting,
                } for ad in ads_for_product]
                
                product_data = {
                    'product_title': product.product_title,
                    'price': product.price or 0,
                    'description': product.description,
                    'marketplace': product.marketplace,
                }
                
                score_data = WinnerScorer.calculate_winner_score(
                    product_data,
                    ads_data,
                    {'cta_text': '', 'page_structure': {}}
                )
                
                score = DigitalProductScore(
                    product_id=product.id,
                    winner_score=score_data['winner_score'],
                    ads_count=score_data['ads_count'],
                    countries_targeted=score_data.get('countries_targeted', 0),
                    marketplace_bonus=score_data.get('marketplace_bonus', 0),
                    scoring_details=score_data.get('scoring_details'),
                )
                db.add(score)
                scores_created += 1
            except:
                continue
        
        db.commit()
        print(f"✅ {scores_created} scores calculés")
        
        # Stats finales
        final_ads = db.query(FacebookAdRaw).count()
        final_products = db.query(DigitalProductDetected).count()
        final_scores = db.query(DigitalProductScore).count()
        
        print(f"\n{'=' * 70}")
        print(f"📊 STATISTIQUES FINALES:")
        print(f"   Annonces: {final_ads}")
        print(f"   Produits: {final_products}")
        print(f"   Scores: {final_scores}")
        print(f"{'=' * 70}")
        
        if final_ads >= 100:
            print(f"\n🎉 OBJECTIF ATTEINT! ({final_ads} annonces)")
        else:
            print(f"\n⚠️  {final_ads}/100 annonces")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

