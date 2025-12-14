"""
Script de vérification des statistiques du scraping Facebook Ads
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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


def main():
    """Affiche les statistiques du scraping"""
    db = SessionLocal()
    
    try:
        print("📊 STATISTIQUES DU SCRAPING FACEBOOK ADS")
        print("=" * 70)
        
        # Annonces
        total_ads = db.query(FacebookAdRaw).count()
        ads_with_image = db.query(FacebookAdRaw).filter(
            FacebookAdRaw.media_url.isnot(None),
            FacebookAdRaw.media_url != ''
        ).count()
        ads_with_url = db.query(FacebookAdRaw).filter(
            FacebookAdRaw.landing_page_url.isnot(None),
            FacebookAdRaw.landing_page_url != ''
        ).count()
        
        print(f"\n📦 ANNONCES:")
        print(f"   Total: {total_ads}")
        print(f"   Avec image: {ads_with_image}")
        print(f"   Avec URL: {ads_with_url}")
        
        # Produits (utiliser SQL direct pour éviter les problèmes de colonnes manquantes)
        from sqlalchemy import text
        total_products = db.execute(text("SELECT COUNT(*) FROM digital_products_detected")).scalar()
        products_by_niche = {}
        products_by_marketplace = {}
        
        # Récupérer les produits avec SQL direct (vérifier d'abord les colonnes disponibles)
        try:
            # Essayer avec marketplace seulement (colonne qui existe probablement)
            products_result = db.execute(text("SELECT marketplace FROM digital_products_detected"))
            products = products_result.fetchall()
            
            for row in products:
                # Par marketplace
                marketplace = row[0] if row[0] else 'unknown'
                products_by_marketplace[marketplace] = products_by_marketplace.get(marketplace, 0) + 1
        except Exception as e:
            # Si les colonnes n'existent pas, juste compter
            print(f"  Note: Impossible de recuperer les details (colonnes manquantes)")
        
        print(f"\nPRODUITS:")
        print(f"   Total: {total_products}")
        if products_by_marketplace:
            print(f"   Par marketplace:")
            for marketplace, count in products_by_marketplace.items():
                print(f"      {marketplace}: {count}")
        
        # Scores (utiliser SQL direct)
        total_scores = db.execute(text("SELECT COUNT(*) FROM digital_products_scores")).scalar()
        winners = db.execute(text("SELECT COUNT(*) FROM digital_products_scores WHERE winner_score >= 60.0")).scalar()
        high_winners = db.execute(text("SELECT COUNT(*) FROM digital_products_scores WHERE winner_score >= 80.0")).scalar()
        
        print(f"\nSCORES:")
        print(f"   Total: {total_scores}")
        print(f"   Winners (>= 60): {winners}")
        print(f"   High Winners (>= 80): {high_winners}")
        
        # Top 10 produits par score (utiliser SQL direct)
        try:
            top_scores = db.execute(text("""
                SELECT s.winner_score, s.ads_count, p.product_title, p.marketplace
                FROM digital_products_scores s
                JOIN digital_products_detected p ON s.product_id = p.id
                ORDER BY s.winner_score DESC
                LIMIT 10
            """)).fetchall()
            
            if top_scores:
                print(f"\nTOP 10 PRODUITS:")
                for i, row in enumerate(top_scores, 1):
                    score_val, ads_count, title, marketplace = row
                    title_display = (title[:50] + '...') if title and len(title) > 50 else (title or 'N/A')
                    print(f"   {i}. Score: {score_val:.1f} | {title_display}")
                    print(f"      Marketplace: {marketplace or 'N/A'} | Ads: {ads_count}")
        except Exception as e:
            print(f"  Note: Impossible d'afficher le top 10 ({e})")
        
        print(f"\n{'=' * 70}")
        
        # Objectifs
        print(f"\nOBJECTIFS:")
        print(f"   Annonces: {total_ads}/100 {'OK' if total_ads >= 100 else 'EN COURS'}")
        print(f"   Produits: {total_products}/100 {'OK' if total_products >= 100 else 'EN COURS'}")
        print(f"   Scores: {total_scores}/100 {'OK' if total_scores >= 100 else 'EN COURS'}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()

