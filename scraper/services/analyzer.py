import os
import sys
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from services.systemio import SystemioScraper
from services.generic import GenericScraper
from utils.scoring import calculate_shop_score, calculate_product_score
from utils.detector import detect_marketplace

# Configuration de la base de données
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5432/marketpulse"
)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def analyze_url(job_id: str, url: str, user_id: int) -> Dict[str, Any]:
    """
    Fonction principale appelée par le worker Redis Queue
    """
    db = SessionLocal()
    
    try:
        # Détecter le marketplace
        marketplace_type = detect_marketplace(url)
        
        # Sélectionner le scraper approprié
        if marketplace_type == "chariow":
            scraper = ChariowScraper()
        elif marketplace_type == "maketou":
            scraper = MaketouScraper()
        elif marketplace_type == "systemio":
            scraper = SystemioScraper()
        else:
            scraper = GenericScraper()
        
        # Scraper la page
        data = scraper.scrape(url)
        
        # Déterminer si c'est une boutique ou un produit
        is_shop = scraper.is_shop_page(data)
        
        if is_shop:
            # Analyser comme une boutique
            score = calculate_shop_score(data)
            result = {
                "type": "shop",
                "score": score,
                "data": {
                    "name": data.get("name", "Boutique"),
                    "url": url,
                    "marketplace": marketplace_type,
                    "estimatedRevenue": data.get("estimated_revenue", "N/A"),
                    "estimatedSales": data.get("estimated_sales", 0),
                    "productCount": data.get("product_count", 0),
                    "age": data.get("age", "N/A"),
                    "growthRate": data.get("growth_rate", 0),
                    "strengths": data.get("strengths", []),
                    "weaknesses": data.get("weaknesses", []),
                },
                "ai_insights": generate_ai_insights(data, "shop")
            }
        else:
            # Analyser comme un produit
            score = calculate_product_score(data)
            result = {
                "type": "product",
                "score": score,
                "data": {
                    "name": data.get("name", "Produit"),
                    "url": url,
                    "marketplace": marketplace_type,
                    "estimatedDailySales": data.get("estimated_daily_sales", 0),
                    "idealPrice": data.get("ideal_price", "N/A"),
                    "competitionLevel": data.get("competition_level", "Moyen"),
                    "trend": data.get("trend", "stable"),
                    "risks": data.get("risks", []),
                },
                "ai_insights": generate_ai_insights(data, "product")
            }
        
        # Mettre à jour le job dans la base de données
        from models import AnalysisJob, JobStatus
        job = db.query(AnalysisJob).filter(AnalysisJob.job_id == job_id).first()
        if job:
            job.status = JobStatus.COMPLETED
            job.result = result
            db.commit()
        
        # Notifier le backend (optionnel)
        try:
            httpx.post(
                f"{BACKEND_URL}/api/v1/analyse/jobs/{job_id}/complete",
                json=result,
                timeout=5.0
            )
        except:
            pass  # Ignorer les erreurs de notification
        
        return result
        
    except Exception as e:
        # Gérer les erreurs
        error_msg = str(e)
        
        # Mettre à jour le job avec l'erreur
        from models import AnalysisJob, JobStatus
        job = db.query(AnalysisJob).filter(AnalysisJob.job_id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.error = error_msg
            db.commit()
        
        raise e
    finally:
        db.close()

def generate_ai_insights(data: Dict[str, Any], analysis_type: str) -> str:
    """
    Génère des insights IA basés sur les données scrappées
    """
    if analysis_type == "shop":
        score = data.get("score", 0)
        if score >= 80:
            return (
                f"Cette boutique présente un excellent potentiel avec un score de {score}/100. "
                "Les points forts incluent une bonne diversité de produits et une croissance régulière. "
                "Recommandation: Surveiller de près cette boutique pour identifier les opportunités."
            )
        elif score >= 60:
            return (
                f"Avec un score de {score}/100, cette boutique montre un potentiel modéré. "
                "Il y a des opportunités d'amélioration, notamment dans la stratégie de prix et le marketing."
            )
        else:
            return (
                f"Score de {score}/100. Cette boutique nécessite des améliorations significatives "
                "pour être compétitive sur le marché."
            )
    else:  # product
        score = data.get("score", 0)
        trend = data.get("trend", "stable")
        
        if trend == "rising" and score >= 70:
            return (
                f"Ce produit présente un excellent potentiel avec une tendance à la hausse "
                f"et un score de {score}/100. C'est le moment idéal pour investir dans cette niche."
            )
        elif trend == "falling":
            return (
                f"Attention: Ce produit montre une tendance à la baisse. "
                "Il serait prudent d'attendre avant d'investir ou de chercher des alternatives."
            )
        else:
            return (
                f"Produit stable avec un score de {score}/100. "
                "Potentiel modéré, nécessite une analyse plus approfondie avant investissement."
            )

