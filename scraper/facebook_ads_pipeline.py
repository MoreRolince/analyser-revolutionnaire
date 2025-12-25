"""
Pipeline complet de scraping Facebook Ads Library pour détecter les produits digitaux winners
"""
import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from collections import defaultdict

# Ajouter les chemins pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, 'backend')

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Configuration DB - Utiliser la même config que le backend
from dotenv import load_dotenv
env_path = os.path.join(project_root, 'backend', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Le port 5433 est mappé depuis 5432 dans docker-compose
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Importer les modules
# Utiliser le scraper "working" qui extrait mieux les vraies URLs
from services.facebook_ads_scraper_working import scrape_ads_library
from services.landing_page_analyzer import LandingPageAnalyzer
from services.product_deduplicator import ProductDeduplicator
from services.winner_scorer import WinnerScorer
from app.models import FacebookAdRaw, DigitalProductDetected, DigitalProductScore


async def save_ads_to_db(db, ads: list):
    """Sauvegarde les annonces Facebook dans fb_ads_raw"""
    saved_count = 0
    
    for ad in ads:
        try:
            # Vérifier si l'annonce existe déjà
            existing = db.query(FacebookAdRaw).filter(
                FacebookAdRaw.landing_page_url == ad.get('landing_page_url', '')
            ).first()
            
            if not existing:
                fb_ad = FacebookAdRaw(
                    product_title=ad.get('product_title'),
                    description=ad.get('ad_text') or ad.get('description'),  # Texte publicitaire
                    media_url=ad.get('media_url'),  # Image publicitaire
                    landing_page_url=ad.get('landing_page_url') or ad.get('cta_url', ''),  # URL du CTA
                    advertiser_page=ad.get('advertiser_page'),
                    start_date=ad.get('start_date'),
                    active_status=ad.get('active_status'),
                    country_targeting=ad.get('country_targeting'),
                    keyword=ad.get('keyword'),
                )
                db.add(fb_ad)
                saved_count += 1
        except Exception as e:
            print(f"    ⚠️  Erreur sauvegarde annonce: {e}")
            continue
    
    try:
        db.commit()
        return saved_count
    except Exception as e:
        db.rollback()
        print(f"  ❌ Erreur commit annonces: {e}")
        return 0


async def analyze_landing_pages(db, ads: list, analyzer: LandingPageAnalyzer):
    """Analyse les landing pages et sauvegarde les produits digitaux détectés"""
    products_detected = []
    
    print(f"\n📄 Analyse de {len(ads)} landing pages...")
    
    for i, ad in enumerate(ads, 1):
        landing_url = ad.get('landing_page_url', '')
        if not landing_url:
            continue
        
        print(f"  [{i}/{len(ads)}] Analyse: {landing_url[:60]}...")
        
        try:
            # Analyser la landing page
            product_data = await analyzer.analyze_landing_page(landing_url)
            
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
                    print(f"    ✅ Produit digital détecté: {product_data.get('product_title', '')[:50]}")
                else:
                    # Mettre à jour le produit existant (toujours mettre à jour le prix pour corriger les erreurs)
                    existing.product_title = product_data.get('product_title', existing.product_title)
                    # Toujours mettre à jour le prix pour corriger les erreurs d'extraction
                    new_price = product_data.get('price', 0)
                    if new_price > 0:  # Seulement si un nouveau prix valide est trouvé
                        existing.price = new_price
                    existing.description = product_data.get('description', existing.description)
                    existing.images = product_data.get('images', existing.images)
                    existing.updated_at = datetime.now()
                    products_detected.append(product_data)
            
            await asyncio.sleep(1)  # Pause entre les analyses
            
        except Exception as e:
            print(f"    ⚠️  Erreur analyse: {e}")
            continue
    
    try:
        db.commit()
        print(f"  ✅ {len(products_detected)} produits digitaux sauvegardés")
        return products_detected
    except Exception as e:
        db.rollback()
        print(f"  ❌ Erreur commit produits: {e}")
        return []


def deduplicate_products(db, products: list):
    """Déduplique les produits et met à jour la base de données"""
    print(f"\n🔄 Déduplication de {len(products)} produits...")
    
    # Trouver les doublons
    duplicates = ProductDeduplicator.find_duplicates(products)
    
    if duplicates:
        print(f"  📊 {len(duplicates)} groupes de produits dupliqués trouvés")
        
        for hash_key, product_group in duplicates.items():
            if len(product_group) > 1:
                # Fusionner les produits
                merged = ProductDeduplicator.merge_products(product_group)
                print(f"    🔗 Fusionné {len(product_group)} versions du produit: {merged.get('product_title', '')[:50]}")
    
    # Détecter les changements de prix
    price_changes = ProductDeduplicator.detect_price_changes(products)
    if price_changes:
        print(f"  💰 {len(price_changes)} changements de prix détectés")
        for change in price_changes[:5]:  # Afficher les 5 premiers
            print(f"    {change['product_title'][:40]}: {change['previous_price']} → {change['current_price']} FCFA")
    
    return len(duplicates), len(price_changes)


def calculate_winner_scores(db):
    """Calcule les scores Winner pour tous les produits"""
    print(f"\n🏆 Calcul des scores Winner...")
    
    # Récupérer tous les produits détectés
    products = db.query(DigitalProductDetected).all()
    
    print(f"  📊 {len(products)} produits à scorer")
    
    scored_count = 0
    
    for product in products:
        try:
            # Récupérer toutes les annonces pour ce produit
            ads = db.query(FacebookAdRaw).filter(
                FacebookAdRaw.landing_page_url == product.landing_page_url
            ).all()
            
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
            
            if scored_count % 10 == 0:
                print(f"    ✅ {scored_count} produits scorés...")
        
        except Exception as e:
            print(f"    ⚠️  Erreur scoring produit {product.id}: {e}")
            continue
    
    try:
        db.commit()
        print(f"  ✅ {scored_count} scores Winner calculés")
        return scored_count
    except Exception as e:
        db.rollback()
        print(f"  ❌ Erreur commit scores: {e}")
        return 0


async def main():
    """Pipeline principal"""
    import sys
    sys.stdout.reconfigure(line_buffering=True)  # Force line buffering
    sys.stderr.reconfigure(line_buffering=True)
    
    print("🚀 PIPELINE FACEBOOK ADS - DÉTECTION DE PRODUITS DIGITAUX WINNERS", flush=True)
    print("=" * 70, flush=True)
    
    db = SessionLocal()
    
    try:
        # Étape 1: Scraper Facebook Ads Library - TOUTE la bibliothèque
        print("\n📦 ÉTAPE 1: Scraping Facebook Ads Library - Afrique de l'Ouest", flush=True)
        print("-" * 70, flush=True)
        print("🌍 Pays ciblés: Sénégal, Côte d'Ivoire, Mali, Burkina Faso, Bénin, Togo, etc.", flush=True)
        print("📝 Mots-clés: Tous les mots-clés produits digitaux", flush=True)
        print("🔄 Parcourt TOUTE la bibliothèque avec scroll infini", flush=True)
        print("💾 Sauvegarde par batch toutes les 50 annonces", flush=True)
        print("-" * 70, flush=True)
        
        # Liste étendue de mots-clés pour trouver plus de produits winners
        # Focus sur les produits digitaux africains (business + formation + spiritualité)
        important_keywords = [
            # Mots-clés généraux produits digitaux
            "formation",
            "ebook",
            "coaching",
            "business en ligne",
            "make money",
            "revenus passifs",
            "formation en ligne",
            "cours en ligne",
            "guide pdf",
            "programme",
            # Mots-clés marketplaces
            "maketou",
            "chariow",
            "systeme.io",
            # Mots-clés business digital
            "dropshipping",
            "affiliation",
            "marketing digital",
            "facebook ads",
            "e-commerce",
            # Mots-clés formation spécialisée
            "formation marketing",
            "formation e-commerce",
            "formation dropshipping",
            "formation copywriting",
            # Mots-clés développement personnel / spiritualité
            "développement personnel",
            "spiritualité",
            "loi de l'attraction",
            "prière",
            # Mots-clés finance / trading
            "trading",
            "forex",
            "investissement",
        ]
        
        all_ads = []
        total_keywords = len(important_keywords)
        current = 0
        batch_size = 10  # Sauvegarder tous les 10 annonces
        total_saved = 0
        
        print(f"\n📊 Configuration PIPELINE ÉTENDU:")
        print(f"   Mots-clés: {len(important_keywords)} (liste complète)")
        print(f"   Scraper: facebook_ads_scraper_working (meilleure extraction URLs)")
        print(f"   Total mots-clés: {total_keywords}")
        print(f"   Batch size: {batch_size} annonces", flush=True)
        
        for keyword in important_keywords:
            current += 1
            try:
                print(f"\n[{current}/{total_keywords}] '{keyword}'", flush=True)
                # Utiliser scrape_ads_library qui extrait mieux les vraies URLs
                # Augmenter la limite à 50 annonces par mot-clé pour avoir plus de résultats
                scraped_ads = await scrape_ads_library(search_term=keyword, limit=50)
                
                # Convertir le format ScrapedAd vers le format attendu
                converted_ads = []
                for ad in scraped_ads:
                    # Utiliser productUrl ou snapshotUrl comme landing page
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
                            "country_targeting": "SN",  # Par défaut Sénégal
                            "keyword": keyword,
                            "scraped_at": datetime.now().isoformat(),
                            "media_url": ad.get('imageUrl'),
                        })
                
                all_ads.extend(converted_ads)
                print(f"  ✅ {len(converted_ads)} annonces ajoutées (Total: {len(all_ads)})", flush=True)
                
                # Sauvegarder par batch
                if len(all_ads) >= batch_size:
                    print(f"  💾 Sauvegarde batch de {len(all_ads)} annonces...", flush=True)
                    batch_saved = await save_ads_to_db(db, all_ads)
                    total_saved += batch_saved
                    print(f"  ✅ {batch_saved} nouvelles annonces sauvegardées (Total: {total_saved})", flush=True)
                    all_ads = []  # Réinitialiser pour le prochain batch
                
                await asyncio.sleep(3)  # Pause entre les recherches
            except Exception as e:
                print(f"  ⚠️  Erreur pour '{keyword}': {e}", flush=True)
                import traceback
                traceback.print_exc()
                continue
        
        # Sauvegarder les annonces restantes
        if all_ads:
            print(f"\n💾 Sauvegarde finale de {len(all_ads)} annonces...")
            batch_saved = await save_ads_to_db(db, all_ads)
            total_saved += batch_saved
            print(f"  ✅ {batch_saved} nouvelles annonces sauvegardées")
        
        print(f"\n✅ {total_saved} nouvelles annonces sauvegardées au total", flush=True)
        
        # Récupérer toutes les annonces de la DB pour les étapes suivantes
        print(f"\n📥 Récupération des annonces depuis la base de données...", flush=True)
        all_ads_from_db = db.query(FacebookAdRaw).all()
        print(f"  ✅ {len(all_ads_from_db)} annonces récupérées", flush=True)
        
        # Convertir en format dict pour l'analyse
        ads_for_analysis = []
        for ad in all_ads_from_db:
            ads_for_analysis.append({
                'landing_page_url': ad.landing_page_url,
                'product_title': ad.product_title,
                'description': ad.description,
                'media_url': ad.media_url,
                'advertiser_page': ad.advertiser_page,
                'keyword': ad.keyword,
            })
        
        # Déduplication finale
        print(f"\n🔄 Déduplication finale...")
        seen_urls = set()
        unique_ads = []
        for ad in ads_for_analysis:
            url = ad.get('landing_page_url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_ads.append(ad)
        
        print(f"\n✅ {len(unique_ads)} annonces uniques scrapées", flush=True)
        
        # Étape 2: Analyser les landing pages
        print("\n📦 ÉTAPE 2: Analyse des landing pages", flush=True)
        print("-" * 70, flush=True)
        
        analyzer = LandingPageAnalyzer()
        products_detected = await analyze_landing_pages(db, unique_ads, analyzer)
        
        # Étape 3: Déduplication
        print("\n📦 ÉTAPE 3: Déduplication des produits")
        print("-" * 70)
        
        duplicates_count, price_changes_count = deduplicate_products(db, products_detected)
        
        # Étape 4: Calcul des scores Winner
        print("\n📦 ÉTAPE 4: Calcul des scores Winner")
        print("-" * 70)
        
        scores_count = calculate_winner_scores(db)
        
        # Résumé final
        print(f"\n{'='*70}")
        print(f"✅ PIPELINE TERMINÉ!")
        print(f"{'='*70}")
        print(f"Annonces sauvegardées: {total_saved}")
        print(f"Produits digitaux détectés: {len(products_detected)}")
        print(f"Produits dupliqués fusionnés: {duplicates_count}")
        print(f"Changements de prix détectés: {price_changes_count}")
        print(f"Scores Winner calculés: {scores_count}")
        
        # Statistiques des winners
        winners = db.query(DigitalProductScore).filter(
            DigitalProductScore.winner_score >= 50.0
        ).count()
        
        print(f"\n🏆 WINNERS (score >= 60): {winners}")
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

