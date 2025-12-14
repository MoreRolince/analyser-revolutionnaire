"""
Scraper style Minea - Simple et efficace
Logique: Scraper Facebook Ads → Sauvegarder → Afficher sur le site
Mots-clés UNIQUEMENT en français
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


# MOTS-CLÉS UNIQUEMENT EN FRANÇAIS
MOTS_CLES = [
    # Business & Marketing
    "formation", "ebook", "coaching", "cours", "guide", "programme",
    "gagner de l'argent", "revenus passifs", "business en ligne",
    "formation marketing", "formation digitale", "cours en ligne",
    "formation en ligne", "tutoriel", "make money",
    
    # Spiritualité
    "prière", "prières", "délivrance", "prospérité", "abondance",
    "bénédiction", "miracle", "éveil spirituel", "loi de l'attraction",
    "prières financières", "jeûne et prière", "manifestation",
    "spiritualité africaine", "protection spirituelle",
    
    # Contexte Africain
    "FCFA", "Orange Money", "MTN MoMo", "paiement mobile",
    "WhatsApp Business", "Afrique", "Bénin", "Côte d'Ivoire",
    "Cameroun", "Sénégal", "Mali", "Burkina Faso",
]


async def scraper_facebook_ads(mot_cle: str, page, seen_urls: set) -> list:
    """Scrape les publicités Facebook pour un mot-clé"""
    ads = []
    
    try:
        # URL Facebook Ads Library (sans filtre pays = global)
        url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&q={mot_cle.replace(' ', '%20')}&search_type=keyword_unordered"
        
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(1)
        
        # Scroll pour charger les annonces (5 scrolls rapides)
        for _ in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.5)
        
        # Extraire le HTML
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Chercher tous les liens externes (landing pages)
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            
            # Filtrer: uniquement les liens externes (pas Facebook)
            if not href or 'facebook.com' in href or href in seen_urls:
                continue
            
            if href.startswith('http'):
                # Résoudre les liens de tracking Facebook
                if 'l.php' in href or 'u=' in href:
                    try:
                        from urllib.parse import urlparse, parse_qs, unquote
                        parsed = urlparse(href)
                        params = parse_qs(parsed.query)
                        if 'u' in params:
                            href = unquote(params['u'][0])
                    except:
                        pass
                
                seen_urls.add(href)
                
                # Vérifier si c'est un produit digital
                url_lower = href.lower()
                is_digital = any(domain in url_lower for domain in [
                    'maketou', 'chariow', 'systeme.io', 'gumroad', 'payhip',
                    'notion.so', 'drive.google'
                ]) or any(pattern in url_lower for pattern in [
                    '/product', '/produit', '/ebook', '/formation',
                    '/cours', '/guide', '/coaching', '/template'
                ])
                
                if is_digital:
                    # Extraire l'image
                    img = link.find('img')
                    media_url = None
                    if img:
                        media_url = img.get('src') or img.get('data-src')
                    
                    # Extraire le texte publicitaire
                    parent = link.find_parent(['div', 'article', 'section'])
                    ad_text = ""
                    if parent:
                        ad_text = parent.get_text(strip=True)[:500]
                    if not ad_text:
                        ad_text = link.get_text(strip=True)[:300]
                    
                    if len(ad_text) >= 20:  # Validation minimale
                        ads.append({
                            'product_title': mot_cle,
                            'description': ad_text,
                            'media_url': media_url,
                            'landing_page_url': href,
                            'advertiser_page': '',
                            'active_status': 'active',
                            'country_targeting': 'ALL',
                            'keyword': mot_cle,
                        })
    
    except Exception as e:
        print(f"  ⚠️  Erreur {mot_cle}: {e}")
    
    return ads


async def main():
    """Pipeline principal - Style Minea"""
    db = SessionLocal()
    
    try:
        print("🚀 SCRAPING FACEBOOK ADS - STYLE MINEA")
        print("=" * 60)
        print(f"📝 {len(MOTS_CLES)} mots-clés en français")
        print("🎯 Objectif: 100+ annonces réelles")
        print("=" * 60)
        
        # Vérifier ce qu'on a déjà
        current = db.query(FacebookAdRaw).count()
        print(f"\n📊 Annonces actuelles: {current}")
        
        target = 100
        needed = max(0, target - current)
        
        if needed == 0:
            print("✅ Objectif déjà atteint!")
            return
        
        print(f"🎯 Besoin: {needed} nouvelles annonces\n")
        
        # Scraping
        all_ads = []
        seen_urls = set()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            
            # Bloquer images/fonts pour accélérer
            await context.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,css}", lambda route: route.abort())
            
            page = await context.new_page()
            
            try:
                for i, mot_cle in enumerate(MOTS_CLES, 1):
                    if len(all_ads) >= needed:
                        break
                    
                    print(f"[{i}/{len(MOTS_CLES)}] {mot_cle}...")
                    
                    ads = await scraper_facebook_ads(mot_cle, page, seen_urls)
                    all_ads.extend(ads)
                    
                    print(f"  ✅ {len(ads)} annonces (Total: {len(all_ads)})")
                    
                    # Sauvegarder par batch de 20
                    if len(all_ads) >= 20:
                        saved = await sauvegarder_batch(db, all_ads)
                        print(f"  💾 {saved} sauvegardées")
                        all_ads = []  # Reset
                    
                    await asyncio.sleep(1)  # Délai minimal
                
            finally:
                await browser.close()
        
        # Sauvegarder les dernières
        if all_ads:
            saved = await sauvegarder_batch(db, all_ads)
            print(f"\n💾 Dernier batch: {saved} sauvegardées")
        
        # Créer les produits
        print(f"\n📦 Création des produits...")
        await creer_produits(db)
        
        # Calculer les scores
        print(f"\n🏆 Calcul des scores...")
        await calculer_scores(db)
        
        # Stats finales
        final_ads = db.query(FacebookAdRaw).count()
        final_products = db.query(DigitalProductDetected).count()
        final_scores = db.query(DigitalProductScore).count()
        
        print(f"\n{'=' * 60}")
        print(f"📊 RÉSULTAT FINAL:")
        print(f"   Annonces: {final_ads}")
        print(f"   Produits: {final_products}")
        print(f"   Scores: {final_scores}")
        print(f"{'=' * 60}")
        
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


async def sauvegarder_batch(db, ads: list) -> int:
    """Sauvegarde un batch d'annonces"""
    saved = 0
    
    for ad in ads:
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
    
    try:
        db.commit()
        return saved
    except:
        db.rollback()
        return 0


async def creer_produits(db):
    """Crée les produits depuis les annonces"""
    ads = db.query(FacebookAdRaw).all()
    created = 0
    
    for ad in ads:
        try:
            existing = db.query(DigitalProductDetected).filter(
                DigitalProductDetected.landing_page_url == ad.landing_page_url
            ).first()
            
            if not existing:
                # Détecter marketplace
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
                
                product = DigitalProductDetected(
                    landing_page_url=ad.landing_page_url,
                    product_title=ad.product_title or "Produit digital",
                    description=ad.description,
                    marketplace=marketplace,
                )
                db.add(product)
                created += 1
        except:
            continue
    
    try:
        db.commit()
        print(f"  ✅ {created} produits créés")
    except:
        db.rollback()


async def calculer_scores(db):
    """Calcule les scores pour tous les produits"""
    products = db.query(DigitalProductDetected).all()
    scored = 0
    
    for product in products:
        try:
            existing = db.query(DigitalProductScore).filter(
                DigitalProductScore.product_id == product.id
            ).first()
            
            if existing:
                continue
            
            ads = db.query(FacebookAdRaw).filter(
                FacebookAdRaw.landing_page_url == product.landing_page_url
            ).all()
            
            if not ads:
                continue
            
            ads_data = [{
                'product_title': ad.product_title,
                'description': ad.description,
                'landing_page_url': ad.landing_page_url,
            } for ad in ads]
            
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
                scoring_details=score_data.get('scoring_details'),
            )
            db.add(score)
            scored += 1
        except:
            continue
    
    try:
        db.commit()
        print(f"  ✅ {scored} scores calculés")
    except:
        db.rollback()


if __name__ == "__main__":
    asyncio.run(main())

