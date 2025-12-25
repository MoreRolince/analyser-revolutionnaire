from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import sys

from app.database import get_db
from app.auth import get_current_admin_user
from app.models import User

# Ajouter le chemin du scraper pour les imports
# Le scraper est au même niveau que backend, donc on remonte 4 niveaux depuis app/routers/scraper.py
# app/routers/scraper.py -> app/routers -> app -> backend -> projet_root
projet_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
scraper_path = os.path.join(projet_root, 'scraper')
if scraper_path not in sys.path:
    sys.path.insert(0, scraper_path)

# Imports du scraper
try:
    from services.winners_crawler import crawl_marketplace_winners, crawl_all_marketplaces
    from services.continuous_scraper import ContinuousScraper
except ImportError as e:
    # Si les imports échouent, on définit None pour éviter les erreurs
    crawl_marketplace_winners = None
    crawl_all_marketplaces = None
    ContinuousScraper = None
    print(f"⚠️ Impossible d'importer les modules du scraper: {e}")

router = APIRouter()

# Import pour le pipeline Facebook Ads
try:
    import asyncio
    import subprocess
    from pathlib import Path
except ImportError:
    pass


@router.post("/crawl")
async def trigger_crawl(
    marketplace: Optional[str] = None,
    shop_urls: Optional[List[str]] = None,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Déclenche le crawling d'une marketplace spécifique.
    Seulement accessible aux admins.
    """
    import traceback
    
    if crawl_marketplace_winners is None:
        raise HTTPException(
            status_code=500,
            detail="Module de crawling non disponible. Vérifiez les imports du scraper."
        )

    marketplaces = [marketplace] if marketplace else ["chariow", "maketou"]

    results = []
    for mp in marketplaces:
        try:
            result = await crawl_marketplace_winners(mp, shop_urls=shop_urls)
            if result and isinstance(result, dict):
                results.append(
                    {
                        "marketplace": mp,
                        "status": "success",
                        "products": result.get("products", 0),
                        "shops": result.get("shops", 0),
                    }
                )
            else:
                results.append(
                    {
                        "marketplace": mp,
                        "status": "error",
                        "error": "Résultat invalide retourné par crawl_marketplace_winners",
                    }
                )
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"❌ Erreur lors du crawl de {mp}: {e}")
            print(error_trace)
            results.append(
                {
                    "marketplace": mp,
                    "status": "error",
                    "error": str(e),
                }
            )

    return {"message": "Crawling terminé", "results": results}


@router.post("/crawl-all")
async def trigger_crawl_all(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Déclenche le crawling de toutes les marketplaces.
    """
    if crawl_all_marketplaces is None:
        raise HTTPException(
            status_code=500,
            detail="Module de crawling non disponible. Vérifiez les imports du scraper."
        )

    # URLs de boutiques connues à scraper
    shop_urls = {
        "maketou": ["https://numerik.mymaketou.store/"],
        "chariow": ["https://tuswehnj.mychariow.shop/"],
    }

    try:
        results = crawl_all_marketplaces(shop_urls=shop_urls)
        return {
            "message": "Crawling de toutes les marketplaces terminé",
            "results": results,
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Erreur lors du crawling: {e}")
        print(error_trace)
        raise HTTPException(
            status_code=500, detail=f"Erreur lors du crawling: {str(e)}"
        )


@router.post("/run-cycle")
async def trigger_continuous_cycle(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Déclenche un cycle de scraping continu manuellement.
    """
    if ContinuousScraper is None:
        raise HTTPException(
            status_code=500,
            detail="Module de scraping continu non disponible. Vérifiez les imports du scraper."
        )

    try:
        scraper = ContinuousScraper()
        result = await scraper.run_cycle()
        return {"message": "Cycle de scraping terminé", "result": result}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Erreur lors du cycle: {e}")
        print(error_trace)
        raise HTTPException(
            status_code=500, detail=f"Erreur lors du cycle: {str(e)}"
        )


@router.get("/status")
async def get_scraper_status(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Récupère le statut du scraper (nombre de boutiques, dernière mise à jour, etc.).
    Inclut aussi les statistiques du pipeline Facebook Ads.
    """
    from app.models import ShopGlobal, ProductGlobal, FacebookAdRaw, DigitalProductDetected, DigitalProductScore
    from sqlalchemy import func

    total_shops = db.query(ShopGlobal).count()
    total_products = db.query(ProductGlobal).count()

    # Dernière mise à jour
    last_update = db.query(func.max(ShopGlobal.last_scraped_at)).scalar()

    # Boutiques par marketplace
    shops_by_marketplace = (
        db.query(ShopGlobal.marketplace, func.count(ShopGlobal.id))
        .group_by(ShopGlobal.marketplace)
        .all()
    )

    # Statistiques Facebook Ads Pipeline
    total_fb_ads = db.query(FacebookAdRaw).count()
    total_digital_products = db.query(DigitalProductDetected).count()
    total_scores = db.query(DigitalProductScore).count()
    winners_count = db.query(DigitalProductScore).filter(
        DigitalProductScore.winner_score >= 60.0
    ).count()
    
    # Dernière annonce scrapée
    last_ad = db.query(func.max(FacebookAdRaw.scraped_at)).scalar()
    
    # Dernier produit détecté
    last_product = db.query(func.max(DigitalProductDetected.analyzed_at)).scalar()
    
    # Dernier score calculé
    last_score = db.query(func.max(DigitalProductScore.calculated_at)).scalar()

    return {
        "marketplace_scraping": {
            "total_shops": total_shops,
            "total_products": total_products,
            "last_update": last_update.isoformat() if last_update else None,
            "shops_by_marketplace": {
                str(mp): count for mp, count in shops_by_marketplace
            },
        },
        "facebook_ads_pipeline": {
            "total_ads_scraped": total_fb_ads,
            "total_products_detected": total_digital_products,
            "total_scores_calculated": total_scores,
            "winners_count": winners_count,
            "last_ad_scraped": last_ad.isoformat() if last_ad else None,
            "last_product_detected": last_product.isoformat() if last_product else None,
            "last_score_calculated": last_score.isoformat() if last_score else None,
        }
    }


@router.post("/facebook-ads-pipeline")
async def trigger_facebook_ads_pipeline(
    kill_existing: bool = False,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Lance le pipeline complet de scraping Facebook Ads Library.
    Seulement accessible aux admins.
    
    Args:
        kill_existing: Si True, tue le processus existant avant de lancer un nouveau
    """
    import traceback
    import subprocess
    
    try:
        # Vérifier si un pipeline est déjà en cours (sans psutil)
        import subprocess as sp
        result = sp.run(['pgrep', '-f', 'facebook_ads_pipeline.py'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            existing_pid = int(result.stdout.strip().split('\n')[0])
            
            if kill_existing:
                # Tuer le processus existant
                try:
                    sp.run(['kill', '-9', str(existing_pid)], check=True)
                    import time
                    time.sleep(2)  # Attendre que le processus se termine
                    return {
                        "message": f"Processus {existing_pid} arrêté. Relancez le pipeline.",
                        "killed_pid": existing_pid,
                        "status": "killed",
                        "note": "Relancez le pipeline pour démarrer avec la nouvelle version."
                    }
                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Impossible d'arrêter le processus {existing_pid}: {str(e)}"
                    )
            else:
                return {
                    "message": "Un pipeline Facebook Ads est déjà en cours",
                    "process_id": existing_pid,
                    "status": "already_running",
                    "note": "Utilisez kill_existing=true pour arrêter le processus actuel et relancer."
                }
        
        # Chemin vers le script du pipeline
        pipeline_path = os.path.join(projet_root, 'scraper', 'facebook_ads_pipeline.py')
        
        if not os.path.exists(pipeline_path):
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline Facebook Ads non trouvé: {pipeline_path}"
            )
        
        # Lancer le pipeline en arrière-plan
        # Note: On utilise subprocess pour lancer le script Python
        import sys
        
        # Démarrer le processus en arrière-plan avec redirection des logs
        log_file = os.path.join(projet_root, 'scraper', 'facebook_ads_pipeline.log')
        
        # Ouvrir le fichier en mode append (ne pas fermer immédiatement)
        log_fd = open(log_file, 'a', buffering=1)  # Line buffering
        
        # Utiliser -u pour unbuffered output et PYTHONUNBUFFERED pour forcer le flush
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        
        process = subprocess.Popen(
            [sys.executable, '-u', pipeline_path],  # -u pour unbuffered
            stdout=log_fd,
            stderr=subprocess.STDOUT,
            cwd=os.path.join(projet_root, 'scraper'),
            env=env,
            bufsize=1  # Line buffering
        )
        
        # Ne pas fermer log_fd - le laisser ouvert pendant l'exécution du processus
        # Il sera fermé automatiquement quand le processus se terminera
        
        return {
            "message": "Pipeline Facebook Ads lancé en arrière-plan",
            "process_id": process.pid,
            "status": "running",
            "log_file": log_file,
            "note": "Le pipeline peut prendre plusieurs heures. Utilisez /facebook-ads-pipeline/status pour suivre la progression."
        }
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"❌ Erreur lors du lancement du pipeline Facebook Ads: {e}")
        print(error_trace)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du lancement du pipeline: {str(e)}"
        )


@router.get("/facebook-ads-pipeline/status")
async def get_facebook_ads_pipeline_status(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Récupère le statut du pipeline Facebook Ads en cours.
    """
    import subprocess as sp
    from app.models import FacebookAdRaw, DigitalProductDetected, DigitalProductScore
    from sqlalchemy import func
    from datetime import timedelta
    
    # Chercher le processus en cours (sans psutil)
    running_process = None
    try:
        result = sp.run(['pgrep', '-f', 'facebook_ads_pipeline.py'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            pid = int(result.stdout.strip().split('\n')[0])
            # Essayer d'obtenir des infos sur le processus
            try:
                ps_result = sp.run(['ps', '-p', str(pid), '-o', 'pid,pcpu,rss,etime'], capture_output=True, text=True)
                if ps_result.returncode == 0:
                    lines = ps_result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        parts = lines[1].split()
                        if len(parts) >= 4:
                            running_process = {
                                "pid": pid,
                                "cpu_percent": float(parts[1]) if parts[1] != '-' else None,
                                "memory_mb": int(parts[2]) / 1024 if parts[2].isdigit() else None,
                                "running_time": parts[3] if len(parts) > 3 else None
                            }
            except:
                running_process = {"pid": pid, "status": "running"}
    except:
        pass
    
    # Statistiques de la base de données
    total_ads = db.query(FacebookAdRaw).count()
    total_products = db.query(DigitalProductDetected).count()
    total_scores = db.query(DigitalProductScore).count()
    winners_count = db.query(DigitalProductScore).filter(
        DigitalProductScore.winner_score >= 60.0
    ).count()
    
    # Dernières activités
    last_ad = db.query(func.max(FacebookAdRaw.scraped_at)).scalar()
    last_product = db.query(func.max(DigitalProductDetected.analyzed_at)).scalar()
    last_score = db.query(func.max(DigitalProductScore.calculated_at)).scalar()
    
    # Compter les annonces des dernières heures
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    ads_last_hour = db.query(FacebookAdRaw).filter(
        FacebookAdRaw.scraped_at >= one_hour_ago
    ).count()
    
    # Vérifier si le fichier de log existe
    log_file = os.path.join(projet_root, 'scraper', 'facebook_ads_pipeline.log')
    log_exists = os.path.exists(log_file)
    log_size = os.path.getsize(log_file) if log_exists else 0
    
    # Lire les dernières lignes du log si disponible
    recent_logs = None
    if log_exists and log_size > 0:
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                recent_logs = lines[-20:] if len(lines) > 20 else lines  # Dernières 20 lignes
        except:
            pass
    
    return {
        "process": running_process,
        "status": "running" if running_process else "not_running",
        "statistics": {
            "total_ads_scraped": total_ads,
            "ads_last_hour": ads_last_hour,
            "total_products_detected": total_products,
            "total_scores_calculated": total_scores,
            "winners_count": winners_count,
        },
        "last_activities": {
            "last_ad_scraped": last_ad.isoformat() if last_ad else None,
            "last_product_detected": last_product.isoformat() if last_product else None,
            "last_score_calculated": last_score.isoformat() if last_score else None,
        },
        "log_info": {
            "log_file_exists": log_exists,
            "log_size_bytes": log_size,
            "recent_logs": recent_logs[-10:] if recent_logs else None  # Dernières 10 lignes seulement
        },
        "note": "Le pipeline peut prendre plusieurs heures. Il scrape toutes les annonces Facebook Ads pour tous les mots-clés dans 10 pays d'Afrique de l'Ouest."
    }


@router.get("/facebook-ads-pipeline/logs")
async def get_facebook_ads_pipeline_logs(
    lines: int = 50,
    admin_user: User = Depends(get_current_admin_user),
):
    """
    Récupère les logs du pipeline Facebook Ads.
    """
    log_file = os.path.join(projet_root, 'scraper', 'facebook_ads_pipeline.log')
    
    if not os.path.exists(log_file):
        return {
            "error": "Fichier de log non trouvé",
            "note": "Le pipeline a peut-être été lancé avant l'activation des logs. Relancez-le pour activer les logs."
        }
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "log_file": log_file,
            "total_lines": len(all_lines),
            "showing_last": len(recent_lines),
            "logs": recent_lines
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture logs: {str(e)}")
