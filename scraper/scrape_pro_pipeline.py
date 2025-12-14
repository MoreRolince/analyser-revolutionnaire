"""
Pipeline PRO complet - Scraping Facebook Ads + Analyse + Scoring
Architecture modulaire optimisée
"""
import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from collections import defaultdict

# Configuration
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

from services.facebook_ads_scraper_pro import FacebookAdsScraperPro
from services.landing_page_analyzer_pro import LandingPageAnalyzerPro
from services.winner_scorer_pro import WinnerScorerPro
from app.models import FacebookAdRaw, DigitalProductDetected, DigitalProductScore


async def main():
    """Pipeline principal PRO"""
    db = SessionLocal()
    
    try:
        print("🚀 PIPELINE PRO - SCRAPING FACEBOOK ADS LIBRARY")
        print("=" * 70)
        print("Stratégie: Clusters de mots-clés + Scoring intelligent")
        print("Focus: Produits digitaux africains (Business + Spiritualité)")
        print("=" * 70)
        
        # ÉTAPE 1: Scraping Facebook Ads
        print("\n📦 ÉTAPE 1: Scraping Facebook Ads Library")
        print("-" * 70)
        
        scraper = FacebookAdsScraperPro()
        all_ads = await scraper.scrape_all_clusters(limit_per_cluster=50)
        
        print(f"✅ {len(all_ads)} annonces scrapées")
        
        # Sauvegarder les ads
        print(f"\n💾 Sauvegarde des annonces...")
        saved_ads = 0
        for ad in all_ads:
            try:
                existing = db.query(FacebookAdRaw).filter(
                    FacebookAdRaw.landing_page_url == ad['landing_page_url']
                ).first()
                
                if not existing:
                    fb_ad = FacebookAdRaw(
                        product_title=ad.get('keyword', ''),
                        description=ad.get('ad_text', ''),
                        media_url=ad.get('media_url'),
                        landing_page_url=ad['landing_page_url'],
                        advertiser_page=ad.get('advertiser_page', ''),
                        active_status=ad.get('active_status', 'active'),
                        country_targeting=ad.get('country_targeting', 'ALL'),
                        keyword=ad.get('keyword', ''),
                    )
                    db.add(fb_ad)
                    saved_ads += 1
            except:
                continue
        
        db.commit()
        print(f"✅ {saved_ads} annonces sauvegardées")
        
        # ÉTAPE 2: Analyse des landing pages
        print(f"\n📦 ÉTAPE 2: Analyse des landing pages")
        print("-" * 70)
        
        analyzer = LandingPageAnalyzerPro()
        landing_pages_stats = scraper.get_landing_pages_stats()
        
        products_created = 0
        
        for landing_url, stats in landing_pages_stats.items():
            try:
                # Vérifier si produit existe déjà
                existing = db.query(DigitalProductDetected).filter(
                    DigitalProductDetected.landing_page_url == landing_url
                ).first()
                
                if existing:
                    continue
                
                # Analyser la landing page
                analysis = await analyzer.analyze_landing_page(landing_url)
                
                if not analysis:
                    continue
                
                # Récupérer le premier ad pour le texte
                first_ad = stats['ads'][0] if stats['ads'] else {}
                ad_text = first_ad.get('ad_text', '')
                
                # Évaluer template ready et resell potential
                analysis['template_ready'] = analyzer.assess_template_ready(analysis, ad_text)
                analysis['resell_potential'] = analyzer.assess_resell_potential(
                    analysis,
                    stats['ads_count'],
                    14  # Estimation durée
                )
                
                # Créer le produit
                product = DigitalProductDetected(
                    landing_page_url=landing_url,
                    product_title=first_ad.get('keyword', 'Produit digital'),
                    description=ad_text[:500],
                    price=analysis.get('price', 0),
                    marketplace=analysis.get('funnel_type'),
                )
                db.add(product)
                products_created += 1
                
                if products_created % 10 == 0:
                    print(f"  ✅ {products_created} produits analysés...")
                
            except Exception as e:
                continue
        
        db.commit()
        print(f"✅ {products_created} produits créés")
        
        # ÉTAPE 3: Calcul des scores WINNER
        print(f"\n📦 ÉTAPE 3: Calcul des scores WINNER")
        print("-" * 70)
        
        scorer = WinnerScorerPro()
        scores_created = 0
        
        products = db.query(DigitalProductDetected).all()
        
        for product in products:
            try:
                # Vérifier si score existe
                existing_score = db.query(DigitalProductScore).filter(
                    DigitalProductScore.product_id == product.id
                ).first()
                
                if existing_score:
                    continue
                
                # Récupérer les ads pour ce produit
                ads = db.query(FacebookAdRaw).filter(
                    FacebookAdRaw.landing_page_url == product.landing_page_url
                ).all()
                
                if not ads:
                    continue
                
                # Convertir en dicts
                ads_data = [{
                    'ad_text': ad.description or '',
                    'landing_page_url': ad.landing_page_url,
                    'has_whatsapp_cta': False,  # À améliorer avec champ DB
                    'has_payment_proof': False,  # À améliorer avec champ DB
                } for ad in ads]
                
                product_data = {
                    'product_title': product.product_title,
                    'price': product.price or 0,
                    'description': product.description,
                    'landing_page_url': product.landing_page_url,
                }
                
                landing_page_data = {
                    'has_whatsapp_funnel': False,  # À améliorer
                }
                
                # Calculer le score
                score_data = scorer.calculate_winner_score(
                    product_data,
                    ads_data,
                    landing_page_data
                )
                
                # Créer le score
                product_score = DigitalProductScore(
                    product_id=product.id,
                    winner_score=score_data['winner_score'],
                    ads_count=score_data['ads_count'],
                    scoring_details=score_data.get('scoring_details'),
                )
                db.add(product_score)
                scores_created += 1
                
            except Exception as e:
                continue
        
        db.commit()
        print(f"✅ {scores_created} scores calculés")
        
        # STATISTIQUES FINALES
        final_ads = db.query(FacebookAdRaw).count()
        final_products = db.query(DigitalProductDetected).count()
        final_scores = db.query(DigitalProductScore).count()
        winners = db.query(DigitalProductScore).filter(
            DigitalProductScore.winner_score >= 60.0
        ).count()
        
        print(f"\n{'=' * 70}")
        print(f"📊 STATISTIQUES FINALES:")
        print(f"   Annonces: {final_ads}")
        print(f"   Produits: {final_products}")
        print(f"   Scores: {final_scores}")
        print(f"   Winners (score >= 60): {winners}")
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

