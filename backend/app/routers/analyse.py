from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue
import os
import uuid
import re

from app.database import get_db, SessionLocal
from app.models import User, AnalysisJob, JobStatus, ProductGlobal, ShopGlobal, PlanType
from app.schemas import AnalysisRequest, AnalysisResult, AnalysisJobStatus
from app.auth import get_current_active_user
from datetime import datetime as dt
import asyncio
import sys
import os

# Ajouter le chemin du scraper pour les imports
# __file__ = backend/app/routers/analyse.py
# On remonte jusqu'à la racine du projet (3 niveaux: routers -> app -> backend)
# Puis on ajoute le dossier scraper à la racine
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # backend/
project_root = os.path.dirname(backend_dir)  # racine du projet
scraper_path = os.path.join(project_root, 'scraper')
if scraper_path not in sys.path:
    sys.path.insert(0, scraper_path)
print(f"🔍 Chemin du projet (racine): {project_root}")
print(f"🔍 Chemin du scraper: {scraper_path}")

try:
    # Importer les scrapers depuis le dossier scraper/services
    print(f"🔍 Tentative d'import des scrapers depuis: {scraper_path}")
    from services.chariow_scraper import ChariowScraper
    from services.maketou_scraper import MaketouScraper
    from services.systemio_scraper import SystemioScraper
    SCRAPERS_AVAILABLE = True
    print(f"✅ Scrapers importés avec succès: ChariowScraper={ChariowScraper is not None}, MaketouScraper={MaketouScraper is not None}, SystemioScraper={SystemioScraper is not None}")
except ImportError as e:
    # Si les imports échouent, on utilisera les données de la base
    print(f"⚠️ Impossible d'importer les scrapers: {e}")
    import traceback
    traceback.print_exc()
    ChariowScraper = None
    MaketouScraper = None
    SystemioScraper = None
    SCRAPERS_AVAILABLE = False

router = APIRouter()

# Fonction supprimée - utilise la version avec paramètre db ci-dessous

# Initialiser Redis avec gestion d'erreur
redis_conn = None
scraper_queue = None
try:
    redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), socket_connect_timeout=2)
    redis_conn.ping()  # Tester la connexion
    scraper_queue = Queue("scraper", connection=redis_conn)
except Exception as e:
    print(f"⚠️ Redis non disponible: {e}. Mode dégradé activé (analyses directes sans queue).")
    redis_conn = None
    scraper_queue = None

async def _scrape_shop_progressively(
    job_id: str,
    url: str,
    user_id: int,
    analysis_type: str,
    marketplace_name: str,
    db: Session
):
    """
    Fonction de scraping qui met à jour le job progressivement
    """
    try:
        # Récupérer le job
        job = db.query(AnalysisJob).filter(AnalysisJob.job_id == job_id).first()
        if not job:
            return
        
        job.status = JobStatus.PROCESSING
        db.commit()
        
        # Initialiser les données partielles
        partial_data = {
            "products": [],
            "shop_name": None,
            "marketplace": marketplace_name,
            "url": url
        }
        
        if analysis_type == "shop":
            # Détecter la marketplace
            url_lower = url.lower()
            is_maketou = 'mymaketou' in url_lower or 'maketou' in url_lower
            is_chariow = 'mychariow' in url_lower or 'chariow' in url_lower
            is_systemio = 'systeme.io' in url_lower or 'systemio' in url_lower
            
            # Normaliser l'URL de la boutique avant de scraper (éviter /fr/fr)
            normalized_url = url.rstrip('/')  # Enlever les slashes finaux
            if is_chariow:
                if not normalized_url.endswith('/fr'):
                    normalized_url = normalized_url + '/fr'
            elif is_maketou:
                if not normalized_url.endswith('/fr'):
                    normalized_url = normalized_url + '/fr'
            # Pour systeme.io, pas de normalisation nécessaire (URL déjà correcte)
            
            scraped_data = None
            try:
                if is_chariow and ChariowScraper:
                    scraper = ChariowScraper()
                    scraped_data = await scraper.scrape_shop(normalized_url)
                elif is_maketou and MaketouScraper:
                    scraper = MaketouScraper()
                    scraped_data = await scraper.scrape_shop(normalized_url)
                elif is_systemio and SystemioScraper:
                    scraper = SystemioScraper()
                    scraped_data = await scraper.scrape_shop(normalized_url)
            except Exception as scrape_error:
                import traceback
                error_msg = str(scrape_error)
                print(f"  ❌ Erreur lors du scraping de la boutique: {error_msg}")
                traceback.print_exc()
                
                # Vérifier si c'est un timeout
                if "timeout" in error_msg.lower() or "Timeout" in str(type(scrape_error)):
                    job.status = JobStatus.COMPLETED
                    job.result = {
                        "type": "shop",
                        "status": "error",
                        "error": "Le chargement de la boutique a pris trop de temps. Veuillez réessayer ou vérifier que l'URL est accessible.",
                        "marketplace": marketplace_name,
                        "url": url
                    }
                    job.completed_at = dt.now()
                    db.commit()
                    print(f"  ⚠️ Job {job_id}: Timeout lors du scraping")
                    return
                else:
                    # Autre erreur
                    job.status = JobStatus.COMPLETED
                    job.result = {
                        "type": "shop",
                        "status": "error",
                        "error": f"Erreur lors du scraping: {error_msg}",
                        "marketplace": marketplace_name,
                        "url": url
                    }
                    job.completed_at = dt.now()
                    db.commit()
                    print(f"  ⚠️ Job {job_id}: Erreur scraping - {error_msg}")
                    return
            
            if scraped_data:
                products = scraped_data.get('products', [])
                shop_name = scraped_data.get('shop_name', 'Boutique')
                
                # Mettre à jour progressivement
                for i, product in enumerate(products):
                    partial_data["products"].append(product)
                    partial_data["shop_name"] = shop_name
                    
                    # Mettre à jour le job toutes les 5 produits ou à la fin
                    if (i + 1) % 5 == 0 or i == len(products) - 1:
                        job.result = {
                            "type": "shop",
                            "status": "processing",
                            "products_found": len(partial_data["products"]),
                            "total_products": len(products),
                            "progress": int(((i + 1) / len(products)) * 100) if products else 0,
                            "partial_data": partial_data
                        }
                        db.commit()
                        print(f"  📊 Job {job_id}: {len(partial_data['products'])}/{len(products)} produits trouvés")
                
                # Calculer les stats finales
                product_count = len(products)
                total_price = sum(p.get('price', 0) or 0 for p in products if p.get('price'))
                avg_price = total_price / product_count if product_count > 0 else 0
                estimated_monthly_sales = product_count * 8
                
                if avg_price > 0:
                    revenue_min = estimated_monthly_sales * avg_price * 0.6
                    revenue_max = estimated_monthly_sales * avg_price * 1.2
                else:
                    revenue_min = estimated_monthly_sales * 5000 * 0.6
                    revenue_max = estimated_monthly_sales * 15000 * 1.2
                
                score = 70.0
                if product_count > 20:
                    score += 10
                elif product_count > 10:
                    score += 5
                if avg_price >= 5000 and avg_price <= 30000:
                    score += 10
                if marketplace_name in ["Maketou", "Chariow"]:
                    score += 5
                
                strengths = []
                weaknesses = []
                if product_count > 20:
                    strengths.append("Grand catalogue de produits")
                elif product_count > 10:
                    strengths.append("Bonne diversité de produits")
                else:
                    weaknesses.append("Catalogue limité")
                
                if not strengths:
                    strengths.append(f"Présence sur {marketplace_name}")
                
                # Résultat final
                job.status = JobStatus.COMPLETED
                job.result = {
                    "type": "shop",
                    "score": float(score),
                    "marketplace": marketplace_name,
                    "url": url,
                    "shopName": shop_name,
                    "estimatedRevenue": f"{int(revenue_min):,} - {int(revenue_max):,} FCFA/mois",
                    "estimatedSales": estimated_monthly_sales,
                    "productCount": product_count,
                    "products": products,
                    "age": "6-12 mois",
                    "strengths": strengths,
                    "weaknesses": weaknesses,
                    "progress": 100
                }
                job.completed_at = dt.now()
                db.commit()
                print(f"  ✅ Job {job_id} terminé: {product_count} produits trouvés")
            else:
                # Pas de données scrapées - erreur générique
                job.status = JobStatus.COMPLETED
                job.result = {
                    "type": analysis_type,
                    "status": "error",
                    "error": "Aucune donnée trouvée ou marketplace non supportée"
                }
                db.commit()
                print(f"  ⚠️ Job {job_id}: Aucune donnée trouvée")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        job = db.query(AnalysisJob).filter(AnalysisJob.job_id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.error = str(e)
            db.commit()

@router.post("", response_model=AnalysisResult)
async def create_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    print(f"🔍 Analyse demandée par utilisateur: {current_user.email if current_user else 'N/A'} (plan: {current_user.plan if current_user else 'N/A'})")
    
    # Vérifier les quotas
    completed_jobs = db.query(AnalysisJob).filter(
        AnalysisJob.user_id == current_user.id,
        AnalysisJob.status == JobStatus.COMPLETED
    ).count()
    
    print(f"📊 Jobs complétés: {completed_jobs}")

    # Quotas selon le plan (PlanType enum)
    if current_user.plan == PlanType.THREE_MONTHS:
        max_analyses = 100
    elif current_user.plan == PlanType.SIX_MONTHS:
        max_analyses = 300
    else:
        # Pour le développement/testing: quota plus élevé par défaut
        # En production, on pourrait mettre 10 ou utiliser PlanType.TRIAL
        max_analyses = 1000  # Quota élevé pour développement
    
    print(f"📊 Quota maximum: {max_analyses}")
    
    if completed_jobs >= max_analyses:
        print(f"❌ Quota atteint: {completed_jobs}/{max_analyses}")
        raise HTTPException(
            status_code=403,
            detail="Quota d'analyses atteint. Veuillez mettre à niveau votre plan."
        )
    
    print(f"✅ Quota OK: {completed_jobs}/{max_analyses}")
    
    # Créer un job d'analyse
    job_id = str(uuid.uuid4())
    db_job = AnalysisJob(
        user_id=current_user.id,
        url=request.url,
        job_id=job_id,
        status=JobStatus.PENDING
    )
    db.add(db_job)
    db.commit()
    
    # Détecter le type d'URL et la marketplace
    url_lower = request.url.lower()
    
    # Détection marketplace
    is_maketou = 'mymaketou' in url_lower or 'maketou' in url_lower
    is_chariow = 'mychariow' in url_lower or 'chariow' in url_lower
    is_systemio = 'systeme.io' in url_lower or 'systemio' in url_lower
    
    # Détection type (boutique ou produit)
    # Pour Chariow: 
    #   - Boutiques: se terminent par /fr ou sont juste le domaine ou se terminent par /
    #   - Produits: contiennent /prd_ ou ont un chemin après le domaine (ex: /1688, /abc123)
    # Pour Maketou: 
    #   - Boutiques: se terminent par /fr ou sont juste le domaine
    #   - Produits: contiennent /products/
    
    is_shop = False
    if is_chariow:
        # URLs Chariow de boutique: se terminent par /fr, /fr/, /, ou sont juste le domaine
        if (url_lower.endswith('/fr') or url_lower.endswith('/fr/') or 
            url_lower.endswith('.mychariow.shop/') or url_lower.endswith('.mychariow.shop')):
            is_shop = True
        # URLs Chariow de produit: contiennent /prd_ ou ont un chemin avec ID après le domaine (ex: /1688, /abc123)
        elif '/prd_' in url_lower or re.search(r'\.mychariow\.shop/[^/]+$', url_lower):
            is_shop = False  # C'est un produit
        else:
            # Par défaut, si ça se termine par / c'est une boutique
            is_shop = url_lower.endswith('/')
    elif is_maketou:
        # URLs Maketou de boutique: se terminent par /fr, /fr/, ou sont juste le domaine
        is_shop = (url_lower.endswith('/fr') or url_lower.endswith('/fr/') or 
                   url_lower.endswith('.mymaketou.store') or url_lower.endswith('.mymaketou.store/'))
        # URLs Maketou de produit: contiennent /products/
        if '/products/' in url_lower:
            is_shop = False  # C'est un produit
    elif is_systemio:
        # URLs Systeme.io: Si c'est juste le domaine ou se termine par /, c'est une boutique
        # Si il y a un chemin après le domaine (ex: /nom-produit), c'est un produit
        from urllib.parse import urlparse
        parsed = urlparse(request.url)
        # Si le path est vide ou juste "/", c'est une boutique
        is_shop = not parsed.path or parsed.path == '/'
        # Si le path contient des segments non vides (ex: /nom-produit), c'est un produit
        if parsed.path and parsed.path != '/':
            path_segments = [s for s in parsed.path.strip('/').split('/') if s]
            # Si il y a au moins un segment de chemin, c'est probablement un produit
            if len(path_segments) >= 1:
                is_shop = False  # C'est probablement un produit
    else:
        # Fallback pour autres marketplaces
        is_shop = any(keyword in url_lower for keyword in [
            'boutique', 'shop', 'store', 'vendor', 'seller', 'merchant'
        ]) and not any(keyword in url_lower for keyword in ['/product/', '/p/', '/item/', '/produit/'])
    
    analysis_type = "shop" if is_shop else "product"
    print(f"🔍 Debug: URL={request.url}, is_chariow={is_chariow}, is_maketou={is_maketou}, is_shop={is_shop}, analysis_type={analysis_type}")
    
    # Générer des données d'analyse simulées mais réalistes
    # En production, cela viendrait du scraper
    import random
    
    # Déterminer la marketplace
    marketplace_name = "Inconnue"
    if is_maketou:
        marketplace_name = "Maketou"
    elif is_chariow:
        marketplace_name = "Chariow"
    elif is_systemio:
        marketplace_name = "Systeme.io"
    
    # Pour les boutiques, lancer le scraping en background avec mise à jour progressive
    if analysis_type == "shop":
        # Lancer le scraping en background
        background_tasks.add_task(
            _scrape_shop_progressively,
            job_id=job_id,
            url=request.url,
            user_id=current_user.id,
            analysis_type=analysis_type,
            marketplace_name=marketplace_name,
            db=SessionLocal()  # session dédiée pour le background task
        )
        
        # Retourner immédiatement avec le job_id
        return AnalysisResult(
            type="shop",
            score=0.0,
            data={
                "marketplace": marketplace_name,
                "url": request.url,
                "status": "processing",
                "job_id": job_id,
                "message": "Analyse en cours, les produits seront affichés progressivement"
            },
            ai_insights="Analyse en cours...",
            job_id=job_id
        )
    
    # Pour les produits, traitement synchrone (rapide)
    else:
        # Analyse de produit - SCRAPER RÉELLEMENT
        scraped_data = None
        try:
            print(f"🔍 Debug: is_chariow={is_chariow}, ChariowScraper={ChariowScraper is not None}, SCRAPERS_AVAILABLE={SCRAPERS_AVAILABLE}")
            print(f"🔍 Debug: is_maketou={is_maketou}, MaketouScraper={MaketouScraper is not None}")
            
            if is_chariow and ChariowScraper:
                print(f"🔍 Scraping réel du produit Chariow: {request.url}")
                scraper = ChariowScraper()
                scraped_data = await scraper.scrape_product(request.url, "", "")
            elif is_maketou and MaketouScraper:
                print(f"🔍 Scraping réel du produit Maketou: {request.url}")
                scraper = MaketouScraper()
                scraped_data = await scraper.scrape_product(request.url, "", "")
            else:
                print(f"⚠️ Marketplace non supportée ou scraper non disponible pour: {request.url}")
                print(f"   is_chariow={is_chariow}, ChariowScraper={ChariowScraper is not None if ChariowScraper else None}")
                print(f"   is_maketou={is_maketou}, MaketouScraper={MaketouScraper is not None if MaketouScraper else None}")
                print(f"   SCRAPERS_AVAILABLE={SCRAPERS_AVAILABLE if 'SCRAPERS_AVAILABLE' in globals() else 'undefined'}")
                scraped_data = None
        except Exception as e:
            print(f"❌ Erreur lors du scraping produit: {e}")
            import traceback
            traceback.print_exc()
            scraped_data = None
        
        # Utiliser les données scrapées si disponibles
        if scraped_data:
            product_name = scraped_data.get('title') or scraped_data.get('product_title') or 'Produit'
            product_image = scraped_data.get('images', [None])[0] if scraped_data.get('images') else scraped_data.get('image')
            product_description = scraped_data.get('description', '')
            ideal_price = scraped_data.get('price', 0) or 0
            category = scraped_data.get('category', '')
            
            # Estimer les ventes quotidiennes basées sur le prix
            if ideal_price > 0:
                if ideal_price < 10000:
                    daily_sales = 10  # Produits accessibles = plus de ventes
                elif ideal_price < 25000:
                    daily_sales = 5
                else:
                    daily_sales = 2
            else:
                daily_sales = 3
            
            # Calculer un score basique
            score = 70.0
            if ideal_price >= 5000 and ideal_price <= 30000:
                score += 10
            if product_description and len(product_description) > 100:
                score += 5
            if product_image:
                score += 5
            if marketplace_name in ["Maketou", "Chariow"]:
                score += 5
        else:
            # Fallback: chercher dans la base de données
            product_in_db = db.query(ProductGlobal).filter(
                ProductGlobal.product_url == request.url
            ).first()
            
            if product_in_db:
                product_name = product_in_db.product_name
                product_image = product_in_db.product_image
                product_description = product_in_db.product_description or ""
                ideal_price = product_in_db.price or 15000
                daily_sales = (product_in_db.sales_est_min or 25) // 30  # Ventes quotidiennes estimées
                category = product_in_db.category or ""
                score = float(product_in_db.score_winner) if product_in_db.score_winner else 70.0
            else:
                # Dernier recours: données par défaut
                product_name = "Produit analysé"
                product_image = None
                product_description = ""
                ideal_price = 15000
                daily_sales = 3
                category = ""
                score = 70.0
        
        # Mettre à jour le statut du job
        db_job.status = JobStatus.COMPLETED
        db_job.result = {
            "type": "product",
            "score": float(score),
            "marketplace": marketplace_name,
            "url": request.url
        }
        db.commit()
        
        return AnalysisResult(
            type="product",
            score=float(score),
            data={
                "marketplace": marketplace_name,
                "url": request.url,
                "productName": product_name,
                "productImage": product_image,
                "productDescription": product_description,
                "estimatedDailySales": daily_sales,
                "idealPrice": f"{ideal_price:,} FCFA",
                "competitionLevel": random.choice(["Faible", "Moyenne", "Élevée"]),
                "trend": random.choice(["Montée", "Stable", "Chute"]),
                "risks": [
                    "Concurrence accrue possible",
                    "Saisonnalité du produit",
                    f"Dépendance à {marketplace_name}"
                ]
            },
            ai_insights=(
                f"Ce produit sur {marketplace_name} présente un score de {score}/100. "
                f"Avec {daily_sales} ventes estimées par jour et un prix idéal de {ideal_price:,} FCFA, "
                f"ce produit montre un bon potentiel commercial sur {marketplace_name}. "
                "Il est recommandé de surveiller la concurrence et d'optimiser les descriptions pour "
                "maximiser la visibilité."
            )
        )

@router.get("/jobs/{job_id}", response_model=AnalysisJobStatus)
async def get_analysis_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    job = db.query(AnalysisJob).filter(
        AnalysisJob.job_id == job_id,
        AnalysisJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status_str = job.status.value if hasattr(job.status, "value") else str(job.status)
    
    # Extraire les informations du résultat
    result = job.result or {}
    progress = result.get("progress", None)
    products_found = result.get("products_found", None)
    total_products = result.get("total_products", None)
    partial_data = result.get("partial_data", None)
    
    # Si en cours, retourner les données partielles avec les produits trouvés jusqu'ici
    if status_str == "processing" and partial_data:
        return AnalysisJobStatus(
            job_id=job.job_id,
            status=status_str,
            progress=progress,
            products_found=products_found,
            total_products=total_products,
            partial_result={
                "products": partial_data.get("products", []),
                "shop_name": partial_data.get("shop_name"),
                "marketplace": partial_data.get("marketplace"),
                "url": partial_data.get("url")
            },
            result=None,
            error=job.error
        )
    
    # Si terminé, retourner le résultat final
    return AnalysisJobStatus(
        job_id=job.job_id,
        status=status_str,
        progress=100 if status_str == "completed" else progress,
        products_found=products_found,
        total_products=total_products,
        partial_result=partial_data,
        result=result if status_str == "completed" else None,
        error=job.error
    )

