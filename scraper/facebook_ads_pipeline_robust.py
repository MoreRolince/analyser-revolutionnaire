"""
Pipeline robuste et scalable de scraping Facebook Ads Library
Version améliorée pour gérer de grandes quantités de données
"""
import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from collections import defaultdict
import time

# Ajouter les chemins pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, 'backend')

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Configuration DB
from dotenv import load_dotenv
env_path = os.path.join(project_root, 'backend', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(bind=engine)

# Importer les modules
from services.facebook_ads_scraper_working import scrape_ads_library
from services.landing_page_analyzer import LandingPageAnalyzer
from services.product_deduplicator import ProductDeduplicator
from services.winner_scorer import WinnerScorer
from app.models import FacebookAdRaw, DigitalProductDetected, DigitalProductScore


# ============================================================================
# CONFIGURATION SCALABLE
# ============================================================================
class PipelineConfig:
    """Configuration pour le pipeline scalable"""
    # Batch sizes
    SCRAPING_BATCH_SIZE = 50  # Sauvegarder toutes les 50 annonces
    DB_QUERY_BATCH_SIZE = 1000  # Traiter 1000 annonces à la fois depuis la DB
    
    # Timeouts et retries
    LANDING_PAGE_TIMEOUT = 60000  # 60 secondes
    LANDING_PAGE_MAX_RETRIES = 3
    SCRAPING_MAX_RETRIES = 3
    
    # Rate limiting
    DELAY_BETWEEN_KEYWORDS = 3  # Secondes entre chaque mot-clé
    DELAY_BETWEEN_LANDING_PAGES = 1  # Secondes entre chaque landing page
    DELAY_ON_ERROR = 5  # Secondes à attendre après une erreur
    
    # Limites
    MAX_ADS_PER_KEYWORD = 200  # Maximum d'annonces par mot-clé
    MAX_LANDING_PAGES_PER_BATCH = 50  # Analyser 50 landing pages à la fois


# ============================================================================
# FONCTIONS UTILITAIRES ROBUSTES
# ============================================================================
async def retry_with_backoff(func, max_retries=3, delay=5, *args):
    """Exécute une fonction avec retry et backoff exponentiel"""
    for attempt in range(max_retries):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args)
            else:
                return func(*args)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = delay * (2 ** attempt)  # Backoff exponentiel
            print(f"    ⚠️  Tentative {attempt + 1}/{max_retries} échouée: {e}")
            print(f"    ⏳ Nouvelle tentative dans {wait_time}s...")
            await asyncio.sleep(wait_time)
    return None


def get_db_session():
    """Crée une nouvelle session DB (pour éviter les problèmes de connexion)"""
    return SessionLocal()


# ============================================================================
# SAUVEGARDE OPTIMISÉE
# ============================================================================
async def save_ads_to_db_batch(db, ads: list, batch_num: int = 0):
    """Sauvegarde les annonces par batch avec gestion d'erreurs"""
    if not ads:
        return 0
    
    saved_count = 0
    errors = []
    
    for ad in ads:
        try:
            # Vérifier si l'annonce existe déjà
            existing = db.query(FacebookAdRaw).filter(
                FacebookAdRaw.landing_page_url == ad.get('landing_page_url', '')
            ).first()
            
            if not existing:
                fb_ad = FacebookAdRaw(
                    product_title=ad.get('product_title'),
                    description=ad.get('ad_text') or ad.get('description'),
                    media_url=ad.get('media_url'),
                    landing_page_url=ad.get('landing_page_url') or ad.get('cta_url', ''),
                    advertiser_page=ad.get('advertiser_page'),
                    start_date=ad.get('start_date'),
                    active_status=ad.get('active_status'),
                    country_targeting=ad.get('country_targeting'),
                    keyword=ad.get('keyword'),
                )
                db.add(fb_ad)
                saved_count += 1
        except Exception as e:
            errors.append(str(e))
            continue
    
    try:
        db.commit()
        if errors:
            print(f"    ⚠️  {len(errors)} erreurs lors de la sauvegarde (ignorées)")
        return saved_count
    except Exception as e:
        db.rollback()
        print(f"  ❌ Erreur commit batch {batch_num}: {e}")
        return 0


# ============================================================================
# ANALYSE OPTIMISÉE DES LANDING PAGES
# ============================================================================
async def analyze_landing_pages_batch(db, ads: list, analyzer: LandingPageAnalyzer, start_idx: int = 0):
    """Analyse les landing pages par batch avec gestion d'erreurs robuste"""
    products_detected = []
    errors_count = 0
    
    total = len(ads)
    print(f"\n📄 Analyse de {total} landing pages (batch {start_idx // PipelineConfig.MAX_LANDING_PAGES_PER_BATCH + 1})...")
    
    for i, ad in enumerate(ads, 1):
        landing_url = ad.get('landing_page_url', '')
        if not landing_url:
            continue
        
        global_idx = start_idx + i
        print(f"  [{global_idx}/{total}] Analyse: {landing_url[:60]}...", flush=True)
        
        try:
            # Analyser avec retry
            product_data = await retry_with_backoff(
                analyzer.analyze_landing_page,
                PipelineConfig.LANDING_PAGE_MAX_RETRIES,
                PipelineConfig.DELAY_ON_ERROR,
                landing_url
            )
            
            if product_data:
                # Vérifier si le produit existe déjà
                existing = db.query(DigitalProductDetected).filter(
                    DigitalProductDetected.landing_page_url == landing_url
                ).first()
                
                if not existing:
                    product = DigitalProductDetected(
                        landing_page_url=landing_url,
                        product_title=product_data.get('product_title', ''),
                        price=product_data.get('price', 0),
                        seller_name=product_data.get('seller_name'),
                        description=product_data.get('description'),
                        images=product_data.get('images', []),
                        bullet_points=product_data.get('bullet_points', []),
                        cta_text=product_data.get('cta_text'),
                        social_proof=product_data.get('social_proof', {}),
                        page_structure=product_data.get('page_structure', {}),
                        marketplace=product_data.get('marketplace'),
                    )
                    db.add(product)
                    products_detected.append(product_data)
                    print(f"    ✅ Produit détecté: {product_data.get('product_title', '')[:50]}")
                else:
                    # Mettre à jour le produit existant
                    existing.product_title = product_data.get('product_title', existing.product_title)
                    new_price = product_data.get('price', 0)
                    if new_price > 0:
                        existing.price = new_price
                    existing.description = product_data.get('description', existing.description)
                    existing.images = product_data.get('images', existing.images)
                    existing.updated_at = datetime.now()
                    products_detected.append(product_data)
            
            # Commit périodique pour éviter les pertes
            if i % 10 == 0:
                try:
                    db.commit()
                except Exception as e:
                    db.rollback()
                    print(f"    ⚠️  Erreur commit périodique: {e}")
            
            await asyncio.sleep(PipelineConfig.DELAY_BETWEEN_LANDING_PAGES)
            
        except Exception as e:
            errors_count += 1
            print(f"    ❌ Erreur analyse (ignorée): {e}")
            if errors_count > 10:
                print(f"    ⚠️  Trop d'erreurs ({errors_count}), pause de {PipelineConfig.DELAY_ON_ERROR}s...")
                await asyncio.sleep(PipelineConfig.DELAY_ON_ERROR)
                errors_count = 0
            continue
    
    try:
        db.commit()
        print(f"  ✅ {len(products_detected)} produits digitaux sauvegardés")
        return products_detected
    except Exception as e:
        db.rollback()
        print(f"  ❌ Erreur commit produits: {e}")
        return []


# ============================================================================
# CALCUL DES SCORES OPTIMISÉ
# ============================================================================
def calculate_winner_scores_batch(db, batch_size=100):
    """Calcule les scores Winner par batch pour éviter les problèmes de mémoire"""
    print(f"\n🏆 Calcul des scores Winner (par batch de {batch_size})...")
    
    # Compter le total
    total_products = db.query(DigitalProductDetected).count()
    print(f"  📊 {total_products} produits à scorer")
    
    scored_count = 0
    offset = 0
    
    while offset < total_products:
        # Récupérer un batch de produits
        products = db.query(DigitalProductDetected).offset(offset).limit(batch_size).all()
        
        if not products:
            break
        
        for product in products:
            try:
                # Récupérer toutes les annonces pour ce produit
                ads = db.query(FacebookAdRaw).filter(
                    FacebookAdRaw.landing_page_url == product.landing_page_url
                ).all()
                
                if not ads:
                    continue
                
                # Convertir en dicts
                ads_data = [{
                    'product_title': ad.product_title,
                    'description': ad.description,
                    'landing_page_url': ad.landing_page_url,
                    'advertiser_page': ad.advertiser_page,
                    'start_date': ad.start_date.isoformat() if ad.start_date else None,
                    'active_status': ad.active_status,
                    'country_targeting': ad.country_targeting,
                } for ad in ads]
                
                # Données de la landing page
                landing_page_data = {
                    'cta_text': product.cta_text,
                    'page_structure': product.page_structure or {},
                }
                
                # Données du produit
                product_data = {
                    'product_title': product.product_title,
                    'price': product.price,
                    'description': product.description,
                    'bullet_points': product.bullet_points or [],
                    'marketplace': product.marketplace,
                }
                
                # Calculer le score
                score_data = WinnerScorer.calculate_winner_score(
                    product_data,
                    ads_data,
                    landing_page_data
                )
                
                # Vérifier si le score existe déjà
                existing_score = db.query(DigitalProductScore).filter(
                    DigitalProductScore.product_id == product.id
                ).first()
                
                if existing_score:
                    # Mettre à jour
                    existing_score.winner_score = score_data['winner_score']
                    existing_score.ads_count = score_data['ads_count']
                    existing_score.countries_targeted = score_data['countries_targeted']
                    existing_score.ad_longevity_days = score_data['ad_longevity_days']
                    existing_score.advertiser_pages_count = score_data['advertiser_pages_count']
                    existing_score.price_attractiveness = score_data['price_attractiveness']
                    existing_score.offer_clarity = score_data['offer_clarity']
                    existing_score.has_bonuses = score_data['has_bonuses']
                    existing_score.cta_strength = score_data['cta_strength']
                    existing_score.positioning_niche = score_data['positioning_niche']
                    existing_score.marketplace_bonus = score_data['marketplace_bonus']
                    existing_score.scoring_details = score_data['scoring_details']
                    existing_score.updated_at = datetime.now()
                else:
                    # Créer nouveau score
                    product_score = DigitalProductScore(
                        product_id=product.id,
                        winner_score=score_data['winner_score'],
                        ads_count=score_data['ads_count'],
                        countries_targeted=score_data['countries_targeted'],
                        ad_longevity_days=score_data['ad_longevity_days'],
                        advertiser_pages_count=score_data['advertiser_pages_count'],
                        price_attractiveness=score_data['price_attractiveness'],
                        offer_clarity=score_data['offer_clarity'],
                        has_bonuses=score_data['has_bonuses'],
                        cta_strength=score_data['cta_strength'],
                        positioning_niche=score_data['positioning_niche'],
                        marketplace_bonus=score_data['marketplace_bonus'],
                        scoring_details=score_data['scoring_details'],
                    )
                    db.add(product_score)
                
                scored_count += 1
                
            except Exception as e:
                print(f"    ⚠️  Erreur scoring produit {product.id}: {e}")
                continue
        
        # Commit après chaque batch
        try:
            db.commit()
            print(f"    ✅ Batch {offset // batch_size + 1}: {scored_count} produits scorés...")
        except Exception as e:
            db.rollback()
            print(f"    ❌ Erreur commit batch: {e}")
        
        offset += batch_size
    
    print(f"  ✅ {scored_count} scores Winner calculés au total")
    return scored_count


# ============================================================================
# PIPELINE PRINCIPAL ROBUSTE
# ============================================================================
async def main():
    """Pipeline principal avec gestion robuste des erreurs"""
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    print("🚀 PIPELINE FACEBOOK ADS - VERSION ROBUSTE ET SCALABLE", flush=True)
    print("=" * 70, flush=True)
    print(f"📊 Configuration:", flush=True)
    print(f"   - Batch size scraping: {PipelineConfig.SCRAPING_BATCH_SIZE}", flush=True)
    print(f"   - Batch size DB: {PipelineConfig.DB_QUERY_BATCH_SIZE}", flush=True)
    print(f"   - Timeout landing pages: {PipelineConfig.LANDING_PAGE_TIMEOUT}ms", flush=True)
    print(f"   - Max retries: {PipelineConfig.LANDING_PAGE_MAX_RETRIES}", flush=True)
    print("=" * 70, flush=True)
    
    db = get_db_session()
    start_time = time.time()
    
    try:
        # Étape 1: Scraping Facebook Ads Library
        print("\n📦 ÉTAPE 1: Scraping Facebook Ads Library", flush=True)
        print("-" * 70, flush=True)
        
        # Configuration des mots-clés (à adapter selon vos besoins)
        keywords = [
            "formation",
            "coaching",
            "business en ligne",
            "ebook",
            "formation en ligne",
            "cours en ligne",
            "produit digital",
            "affiliation",
            "dropshipping",
            "e-commerce",
        ]
        
        all_ads = []
        total_keywords = len(keywords)
        batch_num = 0
        total_saved = 0
        
        print(f"\n📊 Configuration:")
        print(f"   Mots-clés: {len(keywords)}")
        print(f"   Batch size: {PipelineConfig.SCRAPING_BATCH_SIZE} annonces", flush=True)
        
        for idx, keyword in enumerate(keywords, 1):
            try:
                print(f"\n[{idx}/{total_keywords}] '{keyword}'", flush=True)
                
                # Scraper avec retry
                scraped_ads = await retry_with_backoff(
                    scrape_ads_library,
                    max_retries=PipelineConfig.SCRAPING_MAX_RETRIES,
                    delay=PipelineConfig.DELAY_ON_ERROR,
                    search_term=keyword,
                    limit=PipelineConfig.MAX_ADS_PER_KEYWORD
                )
                
                # Convertir le format
                converted_ads = []
                for ad in scraped_ads:
                    landing_url = ad.get('productUrl') or ad.get('snapshotUrl') or ''
                    if landing_url and landing_url.startswith('http'):
                        converted_ads.append({
                            "product_title": ad.get('title') or keyword,
                            "ad_text": ad.get('text') or '',
                            "landing_page_url": landing_url,
                            "cta_url": landing_url,
                            "advertiser_page": ad.get('pageName') or '',
                            "start_date": None,
                            "active_status": "active",
                            "country_targeting": "SN",
                            "keyword": keyword,
                            "scraped_at": datetime.now().isoformat(),
                            "media_url": ad.get('imageUrl'),
                        })
                
                all_ads.extend(converted_ads)
                print(f"  ✅ {len(converted_ads)} annonces ajoutées (Total: {len(all_ads)})", flush=True)
                
                # Sauvegarder par batch
                if len(all_ads) >= PipelineConfig.SCRAPING_BATCH_SIZE:
                    batch_num += 1
                    print(f"  💾 Sauvegarde batch #{batch_num} ({len(all_ads)} annonces)...", flush=True)
                    batch_saved = await save_ads_to_db_batch(db, all_ads, batch_num)
                    total_saved += batch_saved
                    print(f"  ✅ {batch_saved} nouvelles annonces sauvegardées (Total: {total_saved})", flush=True)
                    all_ads = []
                
                await asyncio.sleep(PipelineConfig.DELAY_BETWEEN_KEYWORDS)
                
            except Exception as e:
                print(f"  ❌ Erreur pour '{keyword}': {e}", flush=True)
                import traceback
                traceback.print_exc()
                continue
        
        # Sauvegarder les annonces restantes
        if all_ads:
            batch_num += 1
            print(f"\n💾 Sauvegarde finale batch #{batch_num} ({len(all_ads)} annonces)...", flush=True)
            batch_saved = await save_ads_to_db_batch(db, all_ads, batch_num)
            total_saved += batch_saved
            print(f"  ✅ {batch_saved} nouvelles annonces sauvegardées", flush=True)
        
        print(f"\n✅ {total_saved} nouvelles annonces sauvegardées au total", flush=True)
        
        # Étape 2: Analyser les landing pages (par batch pour éviter les problèmes de mémoire)
        print("\n📦 ÉTAPE 2: Analyse des landing pages", flush=True)
        print("-" * 70, flush=True)
        
        # Récupérer les annonces par batch
        offset = 0
        total_ads = db.query(FacebookAdRaw).count()
        print(f"📥 {total_ads} annonces à analyser (par batch de {PipelineConfig.DB_QUERY_BATCH_SIZE})", flush=True)
        
        all_products_detected = []
        analyzer = LandingPageAnalyzer()
        
        while offset < total_ads:
            batch_ads = db.query(FacebookAdRaw).offset(offset).limit(PipelineConfig.DB_QUERY_BATCH_SIZE).all()
            
            if not batch_ads:
                break
            
            # Convertir en format dict
            ads_for_analysis = []
            seen_urls = set()
            for ad in batch_ads:
                url = ad.landing_page_url
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    ads_for_analysis.append({
                        'landing_page_url': url,
                        'product_title': ad.product_title,
                        'description': ad.description,
                        'media_url': ad.media_url,
                        'advertiser_page': ad.advertiser_page,
                        'keyword': ad.keyword,
                    })
            
            # Analyser ce batch
            products = await analyze_landing_pages_batch(db, ads_for_analysis, analyzer, offset)
            all_products_detected.extend(products)
            
            offset += PipelineConfig.DB_QUERY_BATCH_SIZE
            print(f"  📊 Progression: {min(offset, total_ads)}/{total_ads} annonces traitées", flush=True)
        
        # Étape 3: Déduplication
        print("\n📦 ÉTAPE 3: Déduplication des produits", flush=True)
        print("-" * 70)
        
        # Récupérer tous les produits pour la déduplication
        all_products_for_dedup = db.query(DigitalProductDetected).all()
        products_dict_list = [{
            'product_title': p.product_title,
            'price': p.price,
            'landing_page_url': p.landing_page_url,
            'description': p.description,
        } for p in all_products_for_dedup]
        
        duplicates = ProductDeduplicator.find_duplicates(products_dict_list)
        duplicates_count = len(duplicates) if duplicates else 0
        if duplicates_count:
            print(f"  📊 {duplicates_count} groupes de produits dupliqués trouvés")
        
        price_changes = ProductDeduplicator.detect_price_changes(products_dict_list)
        price_changes_count = len(price_changes) if price_changes else 0
        if price_changes_count:
            print(f"  💰 {price_changes_count} changements de prix détectés")
        
        # Étape 4: Calcul des scores Winner
        print("\n📦 ÉTAPE 4: Calcul des scores Winner", flush=True)
        print("-" * 70)
        
        scores_count = calculate_winner_scores_batch(db, batch_size=100)
        
        # Résumé final
        elapsed_time = time.time() - start_time
        print(f"\n{'='*70}")
        print(f"✅ PIPELINE TERMINÉ!")
        print(f"{'='*70}")
        print(f"⏱️  Temps total: {elapsed_time / 60:.1f} minutes")
        print(f"Annonces sauvegardées: {total_saved}")
        print(f"Produits digitaux détectés: {len(all_products_detected)}")
        print(f"Produits dupliqués fusionnés: {duplicates_count}")
        print(f"Changements de prix détectés: {price_changes_count}")
        print(f"Scores Winner calculés: {scores_count}")
        
        # Statistiques des winners
        winners = db.query(DigitalProductScore).filter(
            DigitalProductScore.winner_score >= 50.0
        ).count()
        
        print(f"\n🏆 WINNERS (score >= 50): {winners}")
        print(f"{'='*70}")
        print(f"\n🎉 Les produits digitaux winners sont maintenant dans la base de données!")
        
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
