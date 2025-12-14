"""
Script pour vérifier les statistiques de scraping
"""
import os
import sys
from sqlalchemy import create_engine, func
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

from app.models import FacebookAdRaw, DigitalProductDetected, DigitalProductScore


def check_stats():
    """Vérifie les statistiques de scraping"""
    db = SessionLocal()
    
    try:
        print("📊 STATISTIQUES DE SCRAPING")
        print("=" * 50)
        
        # Compter les annonces Facebook
        ads_count = db.query(FacebookAdRaw).count()
        print(f"\n📢 Annonces Facebook scrapées: {ads_count}")
        
        # Compter par pays
        if ads_count > 0:
            print("\n📍 Par pays:")
            countries = db.query(
                FacebookAdRaw.country_targeting,
                func.count(FacebookAdRaw.id).label('count')
            ).group_by(FacebookAdRaw.country_targeting).all()
            
            for country, count in countries:
                print(f"   {country or 'N/A'}: {count}")
        
        # Compter par mot-clé
        if ads_count > 0:
            print("\n🔑 Par mot-clé:")
            keywords = db.query(
                FacebookAdRaw.keyword,
                func.count(FacebookAdRaw.id).label('count')
            ).group_by(FacebookAdRaw.keyword).limit(10).all()
            
            for keyword, count in keywords:
                print(f"   {keyword or 'N/A'}: {count}")
        
        # Compter les produits détectés
        products_count = db.query(DigitalProductDetected).count()
        print(f"\n📦 Produits digitaux détectés: {products_count}")
        
        # Compter par marketplace
        if products_count > 0:
            print("\n🏪 Par marketplace:")
            marketplaces = db.query(
                DigitalProductDetected.marketplace,
                func.count(DigitalProductDetected.id).label('count')
            ).group_by(DigitalProductDetected.marketplace).all()
            
            for marketplace, count in marketplaces:
                print(f"   {marketplace or 'N/A'}: {count}")
        
        # Compter les scores
        scores_count = db.query(DigitalProductScore).count()
        print(f"\n🏆 Scores calculés: {scores_count}")
        
        if scores_count > 0:
            winners_count = db.query(DigitalProductScore).filter(
                DigitalProductScore.winner_score >= 60.0
            ).count()
            print(f"   Winners (score >= 60): {winners_count}")
        
        # Résumé
        print(f"\n{'=' * 50}")
        print(f"✅ RÉSUMÉ:")
        print(f"   Annonces: {ads_count}")
        print(f"   Produits: {products_count}")
        print(f"   Scores: {scores_count}")
        
        if ads_count > 0 or products_count > 0:
            print(f"\n🎉 La plateforme peut être lancée avec ces données!")
        else:
            print(f"\n⚠️  Aucune donnée disponible. Lancez le scraping d'abord.")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_stats()

