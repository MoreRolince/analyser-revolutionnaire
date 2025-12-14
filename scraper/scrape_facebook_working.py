"""
Pipeline Facebook Ads - Style Minea
Scraper → Sauvegarder → Afficher sur le site
Mots-clés UNIQUEMENT en français
"""
import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configuration encodage UTF-8 pour Windows
if sys.platform == 'win32':
    try:
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

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
from services.facebook_ads_scraper_working import scrape_ads_library, MOTS_CLES_FRANCAIS
from playwright.async_api import async_playwright


async def save_ads_to_db(db, ads: list) -> int:
    """Sauvegarde les annonces dans la base de données"""
    saved = 0
    
    for ad in ads:
        try:
            # VALIDATION : landing_page_url est OBLIGATOIRE (NOT NULL dans la DB)
            landing_url = ad.get('productUrl') or ad.get('snapshotUrl') or ''
            
            # Si pas d'URL, utiliser une URL par défaut ou skip
            if not landing_url or landing_url.strip() == '':
                # Essayer de construire une URL depuis le texte ou skip
                if ad.get('pageName') and ad.get('pageName') != 'Page Facebook':
                    # Utiliser une URL Facebook par défaut si on a le nom de la page
                    landing_url = f"https://www.facebook.com/{ad.get('pageName', '').replace(' ', '')}"
                else:
                    # Skip cette annonce si pas d'URL valide
                    continue
            
            # Vérifier si l'annonce existe déjà (par landing_page_url)
            from sqlalchemy import text
            existing = db.execute(
                text("SELECT COUNT(*) FROM fb_ads_raw WHERE landing_page_url = :url"),
                {"url": landing_url}
            ).scalar()
            
            if existing > 0:
                continue
            
            # Créer l'annonce
            fb_ad = FacebookAdRaw(
                product_title=ad.get('title') or ad.get('text', '')[:200] or 'Sans titre',
                description=ad.get('text', '') or '',
                media_url=ad.get('imageUrl'),
                landing_page_url=landing_url,  # Toujours défini maintenant
                advertiser_page=ad.get('pageName', '') or 'Page Facebook',
                active_status='active',
                country_targeting='ALL',
                keyword=ad.get('keyword', ''),
            )
            
            db.add(fb_ad)
            saved += 1
            
        except Exception as e:
            print(f"  Erreur sauvegarde annonce: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    try:
        db.commit()
        return saved
    except Exception as e:
        print(f"  Erreur commit: {e}")
        db.rollback()
        return 0


async def create_products_from_ads(db):
    """Crée les produits depuis les annonces"""
    # Utiliser SQL direct pour éviter les problèmes de colonnes manquantes
    from sqlalchemy import text
    ads_result = db.execute(text("SELECT id, landing_page_url, product_title, description, advertiser_page, keyword, scraped_at FROM fb_ads_raw")).fetchall()
    created = 0
    
    for row in ads_result:
        try:
            ad_id, landing_url, product_title, description, advertiser_page, keyword, scraped_at = row
            
            # Vérifier si le produit existe déjà (SQL direct)
            existing = db.execute(
                text("SELECT COUNT(*) FROM digital_products_detected WHERE landing_page_url = :url"),
                {"url": landing_url}
            ).scalar()
            
            if existing > 0:
                continue
            
            # Détecter le marketplace
            url = (landing_url or '').lower()
            marketplace = None
            
            if 'maketou' in url:
                marketplace = 'maketou'
            elif 'chariow' in url:
                marketplace = 'chariow'
            elif 'systeme.io' in url or 'systemeio' in url:
                marketplace = 'systeme.io'
            elif 'gumroad' in url:
                marketplace = 'gumroad'
            elif 'payhip' in url:
                marketplace = 'payhip'
            elif 'notion.so' in url:
                marketplace = 'notion'
            elif 'drive.google' in url:
                marketplace = 'google_drive'
            
            # Détecter le niche
            text = (description or '').lower()
            niche = None
            
            spirituality_keywords = [
                'prière', 'délivrance', 'prospérité', 'abondance', 'destinée',
                'éveil spirituel', 'loi de l\'attraction', 'prières financières',
                'bénédiction', 'miracle', 'jeûne et prière', 'manifestation',
                'spiritualité africaine', 'protection spirituelle', 'guérison', 'foi'
            ]
            
            business_keywords = [
                'formation', 'ebook', 'coaching', 'cours', 'guide', 'programme',
                'gagner de l\'argent', 'revenus passifs', 'business en ligne',
                'marketing digital', 'e-commerce', 'dropshipping', 'affiliation'
            ]
            
            has_spirituality = any(kw in text for kw in spirituality_keywords)
            has_business = any(kw in text for kw in business_keywords)
            
            if has_spirituality and has_business:
                niche = 'mixed'
            elif has_spirituality:
                niche = 'spirituality'
            elif has_business:
                niche = 'business'
            
            # Détecter le type de produit
            product_type = None
            if 'ebook' in text or 'livre' in text or 'pdf' in text:
                product_type = 'ebook'
            elif 'formation' in text or 'cours' in text or 'coaching' in text:
                product_type = 'formation'
            elif 'template' in text or 'modèle' in text:
                product_type = 'template'
            elif 'audio' in text or 'podcast' in text:
                product_type = 'audio'
            elif 'prière' in text or 'spiritualité' in text:
                product_type = 'spiritual_guide'
            
            # Détecter le funnel type
            funnel_type = None
            if 'systeme.io' in url or 'systemeio' in url:
                funnel_type = 'systeme.io'
            elif 'whatsapp' in text.lower() or 'wa.me' in url:
                funnel_type = 'whatsapp'
            elif marketplace:
                funnel_type = 'marketplace'
            else:
                funnel_type = 'custom'
            
            # Extraire le prix depuis le texte
            price = None
            
            import re
            price_patterns = [
                r'(\d+[\s,.]?\d*)\s*(FCFA|F\s*CFA|francs)',
                r'(\d+[\s,.]?\d*)\s*(€|euros?)',
                r'(\d+[\s,.]?\d*)\s*(\$|dollars?)',
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        price_str = match.group(1).replace(' ', '').replace(',', '.')
                        price = float(price_str)
                        break
                    except:
                        pass
            
            # Créer le produit (sans currency qui n'existe pas)
            product = DigitalProductDetected(
                landing_page_url=landing_url,
                product_title=product_title or "Produit digital",
                description=description or '',
                price=price,
                seller_name=advertiser_page or 'Page Facebook',
                images=None,  # Pas d'image pour l'instant
                cta_text=None,
                marketplace=marketplace,
                niche=niche,
                product_type=product_type,
                funnel_type=funnel_type,
                facebook_page_name=advertiser_page or 'Page Facebook',
                first_seen_date=scraped_at or datetime.now(),
                last_seen_date=scraped_at or datetime.now(),
                detected_keywords=[keyword] if keyword else None,
            )
            
            db.add(product)
            created += 1
            
        except Exception as e:
            print(f"  Erreur creation produit: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    try:
        db.commit()
        print(f"  {created} produits crees")
        return created
    except Exception as e:
        print(f"  Erreur commit produits: {e}")
        db.rollback()
        return 0


def calculate_scores(db):
    """Calcule les scores pour tous les produits"""
    # Utiliser SQL direct pour éviter les problèmes de colonnes manquantes
    from sqlalchemy import text
    products_result = db.execute(text("""
        SELECT id, landing_page_url, product_title, price, marketplace, niche
        FROM digital_products_detected
    """)).fetchall()
    scored = 0
    
    for row in products_result:
        product_id, landing_url, product_title, price, marketplace, niche = row
        try:
            # Vérifier si le score existe déjà (SQL direct)
            existing = db.execute(
                text("SELECT COUNT(*) FROM digital_products_scores WHERE product_id = :pid"),
                {"pid": product_id}
            ).scalar()
            
            if existing > 0:
                continue
            
            # Compter les annonces pour ce produit (SQL direct)
            ads_count = db.execute(
                text("SELECT COUNT(*) FROM fb_ads_raw WHERE landing_page_url = :url"),
                {"url": landing_url}
            ).scalar()
            
            if ads_count == 0:
                continue
            
            # Calculer le score winner (simplifié)
            winner_score = 0.0
            
            # Score basé sur le nombre d'annonces
            if ads_count >= 5:
                winner_score += 30
            elif ads_count >= 3:
                winner_score += 20
            elif ads_count >= 2:
                winner_score += 10
            
            # Bonus marketplace
            marketplace_bonus = 0.0
            if marketplace in ['maketou', 'chariow']:
                marketplace_bonus = 15.0
            elif marketplace == 'systeme.io':
                marketplace_bonus = 10.0
            
            winner_score += marketplace_bonus
            
            # Bonus niche
            if niche == 'spirituality':
                winner_score += 10
            elif niche == 'business':
                winner_score += 15
            elif niche == 'mixed':
                winner_score += 20
            
            # Bonus prix attractif
            if price:
                if 5000 <= price <= 50000:
                    winner_score += 10
                elif price < 5000:
                    winner_score += 5
                elif 5 <= price <= 50:
                    winner_score += 10
            
            # Limiter à 100
            winner_score = min(winner_score, 100.0)
            
            # Créer le score
            score = DigitalProductScore(
                product_id=product_id,
                winner_score=winner_score,
                ads_count=ads_count,
                marketplace_bonus=marketplace_bonus,
                scoring_details={
                    'ads_count_score': min(ads_count * 10, 30),
                    'marketplace_bonus': marketplace_bonus,
                    'niche_bonus': 10 if niche == 'spirituality' else (15 if niche == 'business' else (20 if niche == 'mixed' else 0)),
                    'price_bonus': 10 if price and 5000 <= price <= 50000 else 0,
                }
            )
            
            db.add(score)
            scored += 1
            
        except Exception as e:
            print(f"  Erreur calcul score pour produit {product_id}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    try:
        db.commit()
        print(f"  {scored} scores calcules")
        return scored
    except Exception as e:
        print(f"  Erreur commit scores: {e}")
        db.rollback()
        return 0


async def main():
    """Pipeline principal - Style Minea"""
    print("DEBUT DU SCRIPT")
    sys.stdout.flush()
    
    db = SessionLocal()
    print("Connexion a la base de donnees etablie")
    sys.stdout.flush()
    
    try:
        print("SCRAPING FACEBOOK ADS - STYLE MINEA")
        print("=" * 70)
        print(f"{len(MOTS_CLES_FRANCAIS)} mots-cles en francais")
        print("Objectif: 100+ annonces reelles")
        print("=" * 70)
        sys.stdout.flush()
        
        # Vérifier ce qu'on a déjà (utiliser SQL direct pour éviter les problèmes de colonnes manquantes)
        from sqlalchemy import text
        current_ads = db.execute(text("SELECT COUNT(*) FROM fb_ads_raw")).scalar()
        current_products = db.execute(text("SELECT COUNT(*) FROM digital_products_detected")).scalar()
        current_scores = db.execute(text("SELECT COUNT(*) FROM digital_products_scores")).scalar()
        
        print(f"\nEtat actuel:")
        print(f"   Annonces: {current_ads}")
        print(f"   Produits: {current_products}")
        print(f"   Scores: {current_scores}")
        
        target = 100
        needed = max(0, target - current_ads)
        
        if needed == 0:
            print("\nObjectif deja atteint!")
        else:
            print(f"\nBesoin: {needed} nouvelles annonces")
            
            # Scraping
            print(f"\nETAPE 1: Scraping Facebook Ads Library")
            print("-" * 70)
            sys.stdout.flush()
            
            limit_per_keyword = max(5, needed // len(MOTS_CLES_FRANCAIS) + 1)
            print(f"Limite par mot-cle: {limit_per_keyword}")
            sys.stdout.flush()
            
            print("Appel de scrape_all_keywords avec sauvegarde par batch...")
            sys.stdout.flush()
            
            # Scraper avec sauvegarde par batch
            all_ads = []
            seen_ids = set()
            batch_size = 10  # Sauvegarder tous les 10 mots-clés
            total_saved = 0
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled'
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='fr-FR',
                    timezone_id='Europe/Paris'
                )
                
                page = await context.new_page()
                
                try:
                    for i, keyword in enumerate(MOTS_CLES_FRANCAIS, 1):
                        print(f"\n[{i}/{len(MOTS_CLES_FRANCAIS)}] Recherche: {keyword}...")
                        sys.stdout.flush()
                        
                        try:
                            ads = await scrape_ads_library(search_term=keyword, limit=limit_per_keyword)
                            
                            for ad in ads:
                                if ad['id'] not in seen_ids:
                                    seen_ids.add(ad['id'])
                                    all_ads.append(ad)
                            
                            print(f"  {len(ads)} annonces trouvees (Total unique: {len(all_ads)})")
                            sys.stdout.flush()
                            
                            # Sauvegarder par batch tous les 10 mots-clés
                            if i % batch_size == 0 and len(all_ads) > 0:
                                print(f"\n  [BATCH] Sauvegarde de {len(all_ads)} annonces...")
                                sys.stdout.flush()
                                try:
                                    batch_saved = await save_ads_to_db(db, all_ads)
                                    total_saved += batch_saved
                                    print(f"  [BATCH] {batch_saved} nouvelles annonces sauvegardees (Total: {total_saved})")
                                    sys.stdout.flush()
                                    all_ads = []  # Reset pour le prochain batch
                                except Exception as e:
                                    print(f"  [ERREUR BATCH] {e}")
                                    import traceback
                                    traceback.print_exc()
                                    # Continuer même en cas d'erreur
                                    all_ads = []
                            
                            await asyncio.sleep(2)  # Délai entre les recherches
                            
                        except Exception as e:
                            print(f"  ERREUR pour {keyword}: {e}")
                            continue
                    
                    # Sauvegarder les dernières annonces
                    if len(all_ads) > 0:
                        print(f"\n  [FINAL] Sauvegarde des dernieres {len(all_ads)} annonces...")
                        sys.stdout.flush()
                        batch_saved = await save_ads_to_db(db, all_ads)
                        total_saved += batch_saved
                        print(f"  [FINAL] {batch_saved} nouvelles annonces sauvegardees")
                        sys.stdout.flush()
                
                finally:
                    await browser.close()
            
            print(f"\nscrape_all_keywords termine, {total_saved} annonces sauvegardees au total")
            sys.stdout.flush()
        
        # Créer les produits
        print(f"\nETAPE 3: Creation des produits")
        print("-" * 70)
        
        products_created = await create_products_from_ads(db)
        
        # Calculer les scores
        print(f"\nETAPE 4: Calcul des scores Winner")
        print("-" * 70)
        
        scores_calculated = calculate_scores(db)
        
        # Stats finales (utiliser SQL direct)
        from sqlalchemy import text
        final_ads = db.execute(text("SELECT COUNT(*) FROM fb_ads_raw")).scalar()
        final_products = db.execute(text("SELECT COUNT(*) FROM digital_products_detected")).scalar()
        final_scores = db.execute(text("SELECT COUNT(*) FROM digital_products_scores")).scalar()
        
        winners = db.execute(text("SELECT COUNT(*) FROM digital_products_scores WHERE winner_score >= 60.0")).scalar()
        
        print(f"\n{'=' * 70}")
        print(f"RESULTAT FINAL:")
        print(f"   Annonces: {final_ads}")
        print(f"   Produits: {final_products}")
        print(f"   Scores: {final_scores}")
        print(f"   WINNERS (score >= 60): {winners}")
        print(f"{'=' * 70}")
        
        if final_ads >= 100:
            print(f"\nOBJECTIF ATTEINT! ({final_ads} annonces)")
        else:
            print(f"\n{final_ads}/100 annonces")
        
    except Exception as e:
        print(f"\nErreur fatale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

