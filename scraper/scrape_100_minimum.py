"""
Script de scraping agressif pour obtenir MINIMUM 100 annonces réelles
Continue jusqu'à atteindre l'objectif
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
from app.models import FacebookAdRaw, DigitalProductDetected, DigitalProductScore
from services.winner_scorer import WinnerScorer


async def scrape_until_100():
    """Scrape jusqu'à obtenir minimum 100 annonces réelles"""
    db = SessionLocal()
    
    try:
        print("🚀 SCRAPING AGRESSIF - OBJECTIF: 100+ ANNONCES RÉELLES")
        print("=" * 70)
        
        # Vérifier combien on a déjà
        current_count = db.query(FacebookAdRaw).count()
        print(f"📊 Annonces actuelles: {current_count}")
        
        target = 100
        if current_count >= target:
            print(f"✅ Objectif déjà atteint! ({current_count} annonces)")
            return
        
        needed = target - current_count
        print(f"🎯 Objectif: {needed} nouvelles annonces minimum")
        
        scraper = FacebookAdsScraperV2()
        
        # Mots-clés étendus pour maximiser les résultats
        ALL_KEYWORDS = [
            # Digital & Marketing (priorité haute)
            "formation marketing digital", "cours développement web", "formation e-commerce",
            "ebook marketing", "formation facebook ads", "cours instagram marketing",
            "formation youtube", "cours seo", "formation wordpress",
            "cours photoshop", "formation canva", "cours figma",
            "formation google ads", "cours tiktok", "formation linkedin",
            "cours email marketing", "formation automation", "cours data analysis",
            "ebook business", "formation dropshipping", "formation copywriting",
            "cours design graphique", "formation vidéo", "cours community management",
            # Spiritualité & Bien-être
            "formation spiritualité", "cours méditation", "formation développement personnel",
            "ebook spiritualité", "formation yoga", "cours reiki",
            "formation astrologie", "cours numérologie", "formation tarot",
            "cours bien-être", "formation énergétique", "ebook développement personnel",
            # Finance & Trading
            "formation trading", "cours forex", "formation cryptomonnaie",
            "ebook trading", "formation investissement",
            # Mots-clés généraux (volume élevé)
            "formation", "ebook", "coaching", "cours", "guide", "programme",
            "make money", "revenus passifs", "business en ligne",
            "gagner de l'argent", "argent facile", "revenus supplémentaires",
            "formation en ligne", "cours en ligne", "tutoriel",
            "formation digitale", "ebook pdf", "guide pdf",
            # Spécifiques Afrique
            "formation afrique", "ebook afrique", "coaching afrique",
            "formation sénégal", "formation côte d'ivoire", "formation bénin",
            "formation mali", "formation burkina faso", "formation tog",
            "business afrique", "revenus afrique", "argent afrique",
        ]
        
        # Scraping global - pas de filtrage par pays
        print(f"\n📦 Configuration:")
        print(f"   Mots-clés: {len(ALL_KEYWORDS)}")
        print(f"   Mode: GLOBAL (tous les pays)")
        print(f"   Limite par mot-clé: 100 annonces")
        
        all_ads = []
        current = 0
        
        # Scraping progressif jusqu'à atteindre l'objectif
        for keyword in ALL_KEYWORDS:
            if len(all_ads) >= needed:
                break
            
            current += 1
            try:
                print(f"\n[{current}/{len(ALL_KEYWORDS)}] '{keyword}'")
                print(f"   Objectif: {needed - len(all_ads)} annonces restantes")
                
                # Scraper globalement (pays = "ALL" ou utiliser un pays principal comme base)
                ads = await scraper.scrape_ads(keyword, country="SN", limit=100)  # SN comme base mais récupère globalement
                all_ads.extend(ads)
                
                print(f"   ✅ {len(ads)} annonces trouvées (Total: {len(all_ads)})")
                
                # Sauvegarder par batch pour ne pas perdre de données
                if len(all_ads) >= 20:
                    saved = await save_batch(db, all_ads)
                    print(f"   💾 {saved} annonces sauvegardées")
                    all_ads = []  # Reset après sauvegarde
                
                await asyncio.sleep(2)  # Délai anti-détection
                
            except Exception as e:
                print(f"   ⚠️  Erreur: {e}")
                continue
        
        # Sauvegarder les dernières annonces
        if all_ads:
            saved = await save_batch(db, all_ads)
            print(f"\n💾 Dernier batch: {saved} annonces sauvegardées")
        
        # Vérifier le total final
        final_count = db.query(FacebookAdRaw).count()
        print(f"\n✅ Total final: {final_count} annonces")
        
        if final_count >= target:
            print(f"🎉 OBJECTIF ATTEINT! ({final_count} annonces)")
        else:
            print(f"⚠️  Objectif non atteint ({final_count}/{target})")
        
        # Créer les produits détectés
        print(f"\n📦 Création des produits détectés...")
        await create_products(db)
        
        # Calculer les scores
        print(f"\n🏆 Calcul des scores...")
        await calculate_scores(db)
        
        # Statistiques finales
        products_count = db.query(DigitalProductDetected).count()
        scores_count = db.query(DigitalProductScore).count()
        
        print(f"\n{'=' * 70}")
        print(f"📊 STATISTIQUES FINALES:")
        print(f"   Annonces: {final_count}")
        print(f"   Produits: {products_count}")
        print(f"   Scores: {scores_count}")
        print(f"{'=' * 70}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


async def save_batch(db, ads: list) -> int:
    """Sauvegarde un batch d'annonces"""
    saved = 0
    
    for ad in ads:
        try:
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
        except Exception:
            continue
    
    try:
        db.commit()
        return saved
    except Exception:
        db.rollback()
        return 0


async def create_products(db):
    """Crée les produits détectés depuis les annonces"""
    # Récupérer toutes les annonces sans produit associé
    ads = db.query(FacebookAdRaw).all()
    created = 0
    
    for ad in ads:
        try:
            existing = db.query(DigitalProductDetected).filter(
                DigitalProductDetected.landing_page_url == ad.landing_page_url
            ).first()
            
            if not existing:
                # Détecter le marketplace
                marketplace = None
                url = ad.landing_page_url.lower() if ad.landing_page_url else ''
                
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
                elif any(domain in url for domain in ['notion.so', 'drive.google.com']):
                    marketplace = 'other'
                
                # Vérifier si c'est un produit digital (doit avoir un marketplace connu)
                if marketplace or any(keyword in (ad.description or '').lower() for keyword in ['formation', 'ebook', 'cours', 'guide', 'coaching']):
                    product = DigitalProductDetected(
                        landing_page_url=ad.landing_page_url,
                        product_title=ad.product_title or "Produit digital",
                        description=ad.description,
                        marketplace=marketplace,
                    )
                    db.add(product)
                    created += 1
        except Exception:
            continue
    
    try:
        db.commit()
        print(f"   ✅ {created} produits créés")
    except Exception:
        db.rollback()


async def calculate_scores(db):
    """Calcule les scores pour tous les produits"""
    products = db.query(DigitalProductDetected).all()
    scored = 0
    
    for product in products:
        try:
            # Vérifier si score existe déjà
            existing_score = db.query(DigitalProductScore).filter(
                DigitalProductScore.product_id == product.id
            ).first()
            
            if existing_score:
                continue
            
            # Récupérer les annonces pour ce produit
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
                'country_targeting': ad.country_targeting,
            } for ad in ads]
            
            # Données du produit
            product_data = {
                'product_title': product.product_title,
                'price': product.price or 0,
                'description': product.description,
                'marketplace': product.marketplace,
            }
            
            # Données de la landing page
            landing_page_data = {
                'cta_text': '',
                'page_structure': {},
            }
            
            # Calculer le score
            score_data = WinnerScorer.calculate_winner_score(
                product_data,
                ads_data,
                landing_page_data
            )
            
            # Créer le score
            product_score = DigitalProductScore(
                product_id=product.id,
                winner_score=score_data['winner_score'],
                ads_count=score_data['ads_count'],
                countries_targeted=score_data['countries_targeted'],
                ad_longevity_days=score_data.get('ad_longevity_days', 0),
                advertiser_pages_count=score_data.get('advertiser_pages_count', 0),
                price_attractiveness=score_data.get('price_attractiveness', 0),
                offer_clarity=score_data.get('offer_clarity', 0),
                has_bonuses=score_data.get('has_bonuses', False),
                cta_strength=score_data.get('cta_strength', 0),
                positioning_niche=score_data.get('positioning_niche'),
                marketplace_bonus=score_data.get('marketplace_bonus', 0),
                scoring_details=score_data.get('scoring_details'),
            )
            db.add(product_score)
            scored += 1
            
        except Exception as e:
            continue
    
    try:
        db.commit()
        print(f"   ✅ {scored} scores calculés")
    except Exception:
        db.rollback()


if __name__ == "__main__":
    print("🔥 SCRAPING AGRESSIF - GARANTIE 100+ ANNONCES RÉELLES")
    print("⏱️  Cela peut prendre 30-60 minutes...")
    print("")
    asyncio.run(scrape_until_100())

