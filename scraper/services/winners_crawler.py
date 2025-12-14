import os
import sys
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import re

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from services.systemio import SystemioScraper
from utils.scoring import calculate_product_score, calculate_shop_score

# Configuration de la base de données
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def _extract_revenue_min(revenue_str: str) -> float:
    """Extrait le revenu minimum depuis une chaîne comme '250,000 - 750,000 FCFA/mois'"""
    if not revenue_str:
        return 0.0
    match = re.search(r'([\d,]+)', revenue_str.replace(' ', ''))
    if match:
        try:
            return float(match.group(1).replace(',', ''))
        except:
            return 0.0
    return 0.0

def _extract_revenue_max(revenue_str: str) -> float:
    """Extrait le revenu maximum depuis une chaîne comme '250,000 - 750,000 FCFA/mois'"""
    if not revenue_str:
        return 0.0
    matches = re.findall(r'([\d,]+)', revenue_str.replace(' ', ''))
    if len(matches) > 1:
        try:
            return float(matches[1].replace(',', ''))
        except:
            return 0.0
    elif len(matches) == 1:
        try:
            return float(matches[0].replace(',', '')) * 1.5  # Estimation
        except:
            return 0.0
    return 0.0

async def crawl_marketplace_winners(marketplace: str, shop_urls: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Crawl les winners d'une marketplace spécifique
    Retourne un dict avec 'products' et 'shops'
    
    Args:
        marketplace: Nom de la marketplace (chariow, maketou, systemio)
        shop_urls: Liste optionnelle d'URLs de boutiques à scraper directement
    """
    db = SessionLocal()
    
    try:
        if marketplace == "chariow":
            scraper = ChariowScraper()
            # URLs de boutiques connues à scraper
            if not shop_urls:
                shop_urls = [
                    # Ajouter d'autres URLs de boutiques Chariow ici
                ]
        elif marketplace == "maketou":
            scraper = MaketouScraper()
            if not shop_urls:
                shop_urls = [
                    "https://numerik.mymaketou.store/",
                    # Ajouter d'autres URLs de boutiques Maketou ici
                ]
        elif marketplace == "systemio":
            scraper = SystemioScraper()
            if not shop_urls:
                shop_urls = []
        else:
            return {"products": [], "shops": []}
        
        products = []
        shops = []
        
        # Scraper directement les boutiques fournies
        for shop_url in shop_urls:
            try:
                print(f"🔄 Scraping boutique: {shop_url}")
                shop_data_raw = await scraper.scrape_async(shop_url)
                
                if shop_data_raw and shop_data_raw.get('product_count', 0) > 0:
                    # Convertir les données de la boutique en format ShopGlobal
                    shop_score = calculate_shop_score(shop_data_raw)
                    
                    if shop_score >= 70:  # Seulement les winners
                        shop_data = {
                            "shop_name": shop_data_raw.get('name', 'Boutique'),
                            "shop_url": shop_url,
                            "score_global": shop_score,
                            "revenue_est_min": _extract_revenue_min(shop_data_raw.get('estimated_revenue', '')),
                            "revenue_est_max": _extract_revenue_max(shop_data_raw.get('estimated_revenue', '')),
                            "winners_count": len([p for p in shop_data_raw.get('products', []) if p.get('price', 0) > 0])
                        }
                        shops.append(shop_data)
                    
                    # Extraire les produits de la boutique
                    for product_raw in shop_data_raw.get('products', []):
                        if product_raw.get('name') and product_raw.get('price', 0) > 0:
                            product_score = calculate_product_score({
                                "name": product_raw.get('name'),
                                "url": product_raw.get('url', ''),
                                "marketplace": marketplace,
                                "estimated_daily_sales": 8,  # Estimation
                                "ideal_price": product_raw.get('price', 0),
                                "competition_level": "Moyen",
                                "trend": "stable"
                            })
                            
                            if product_score >= 70:  # Seulement les winners
                                product_data = {
                                    "product_name": product_raw.get('name'),
                                    "shop_name": shop_data_raw.get('name', 'Boutique'),
                                    "product_url": product_raw.get('url', ''),
                                    "product_image": product_raw.get('image', ''),
                                    "product_description": product_raw.get('description', ''),
                                    "price": product_raw.get('price', 0),
                                    "sales_est_min": 25,  # Estimation mensuelle min
                                    "sales_est_max": 35,  # Estimation mensuelle max
                                    "revenue_est_min": product_raw.get('price', 0) * 25 * 0.7,
                                    "revenue_est_max": product_raw.get('price', 0) * 35,
                                    "score_winner": product_score,
                                    "category": None
                                }
                                products.append(product_data)
                
            except Exception as e:
                print(f"❌ Erreur scraping boutique {shop_url}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Sauvegarder en base de données
        backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backend')
        sys.path.insert(0, backend_path)
        from app.models import ProductGlobal, ShopGlobal, MarketplaceType
        
        marketplace_enum = MarketplaceType(marketplace.lower())
        
        # Sauvegarder les produits
        products_saved = 0
        for product_data in products:
            try:
                existing = db.query(ProductGlobal).filter(
                    ProductGlobal.product_url == product_data.get('product_url', '')
                ).first()
                
                if existing:
                    # Mettre à jour
                    for key, value in product_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.last_scraped_at = datetime.utcnow()
                else:
                    # Créer nouveau
                    product = ProductGlobal(
                        marketplace=marketplace_enum,
                        **product_data,
                        last_scraped_at=datetime.utcnow()
                    )
                    db.add(product)
                products_saved += 1
            except Exception as e:
                print(f"Erreur sauvegarde produit: {e}")
                continue
        
        # Sauvegarder les boutiques
        shops_saved = 0
        for shop_data in shops:
            try:
                existing = db.query(ShopGlobal).filter(
                    ShopGlobal.shop_url == shop_data.get('shop_url', '')
                ).first()
                
                if existing:
                    # Mettre à jour
                    for key, value in shop_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.last_scraped_at = datetime.utcnow()
                else:
                    # Créer nouveau
                    shop = ShopGlobal(
                        marketplace=marketplace_enum,
                        **shop_data,
                        last_scraped_at=datetime.utcnow()
                    )
                    db.add(shop)
                shops_saved += 1
            except Exception as e:
                print(f"Erreur sauvegarde boutique: {e}")
                continue
        
        db.commit()
        print(f"✅ Sauvegardé: {products_saved} produits, {shops_saved} boutiques")
        
        return {
            "products": len(products),
            "shops": len(shops),
            "marketplace": marketplace
        }
        
    except Exception as e:
        db.rollback()
        print(f"Erreur lors du crawl: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        db.close()

def crawl_all_marketplaces(shop_urls: Optional[Dict[str, List[str]]] = None):
    """
    Fonction principale pour crawler toutes les marketplaces
    
    Args:
        shop_urls: Dict avec marketplace -> liste d'URLs de boutiques à scraper
    """
    marketplaces = ["chariow", "maketou", "systemio"]
    
    if shop_urls is None:
        shop_urls = {}
    
    results = []
    for marketplace in marketplaces:
        try:
            urls = shop_urls.get(marketplace, None)
            result = asyncio.run(crawl_marketplace_winners(marketplace, shop_urls=urls))
            results.append(result)
            print(f"✅ {marketplace}: {result.get('products', 0)} produits, {result.get('shops', 0)} boutiques")
        except Exception as e:
            print(f"❌ Erreur {marketplace}: {e}")
            import traceback
            traceback.print_exc()
            results.append({"marketplace": marketplace, "error": str(e)})
    
    return results

if __name__ == "__main__":
    # URLs de test
    shop_urls = {
        "maketou": [],  # Boutiques à découvrir automatiquement
        "chariow": []  # Boutiques à découvrir automatiquement
    }
    crawl_all_marketplaces(shop_urls=shop_urls)

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import re

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from services.systemio import SystemioScraper
from utils.scoring import calculate_product_score, calculate_shop_score

# Configuration de la base de données
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def _extract_revenue_min(revenue_str: str) -> float:
    """Extrait le revenu minimum depuis une chaîne comme '250,000 - 750,000 FCFA/mois'"""
    if not revenue_str:
        return 0.0
    match = re.search(r'([\d,]+)', revenue_str.replace(' ', ''))
    if match:
        try:
            return float(match.group(1).replace(',', ''))
        except:
            return 0.0
    return 0.0

def _extract_revenue_max(revenue_str: str) -> float:
    """Extrait le revenu maximum depuis une chaîne comme '250,000 - 750,000 FCFA/mois'"""
    if not revenue_str:
        return 0.0
    matches = re.findall(r'([\d,]+)', revenue_str.replace(' ', ''))
    if len(matches) > 1:
        try:
            return float(matches[1].replace(',', ''))
        except:
            return 0.0
    elif len(matches) == 1:
        try:
            return float(matches[0].replace(',', '')) * 1.5  # Estimation
        except:
            return 0.0
    return 0.0

async def crawl_marketplace_winners(marketplace: str, shop_urls: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Crawl les winners d'une marketplace spécifique
    Retourne un dict avec 'products' et 'shops'
    
    Args:
        marketplace: Nom de la marketplace (chariow, maketou, systemio)
        shop_urls: Liste optionnelle d'URLs de boutiques à scraper directement
    """
    db = SessionLocal()
    
    try:
        if marketplace == "chariow":
            scraper = ChariowScraper()
            # URLs de boutiques connues à scraper
            if not shop_urls:
                shop_urls = [
                    # Ajouter d'autres URLs de boutiques Chariow ici
                ]
        elif marketplace == "maketou":
            scraper = MaketouScraper()
            if not shop_urls:
                shop_urls = [
                    "https://numerik.mymaketou.store/",
                    # Ajouter d'autres URLs de boutiques Maketou ici
                ]
        elif marketplace == "systemio":
            scraper = SystemioScraper()
            if not shop_urls:
                shop_urls = []
        else:
            return {"products": [], "shops": []}
        
        products = []
        shops = []
        
        # Scraper directement les boutiques fournies
        for shop_url in shop_urls:
            try:
                print(f"🔄 Scraping boutique: {shop_url}")
                shop_data_raw = await scraper.scrape_async(shop_url)
                
                if shop_data_raw and shop_data_raw.get('product_count', 0) > 0:
                    # Convertir les données de la boutique en format ShopGlobal
                    shop_score = calculate_shop_score(shop_data_raw)
                    
                    if shop_score >= 70:  # Seulement les winners
                        shop_data = {
                            "shop_name": shop_data_raw.get('name', 'Boutique'),
                            "shop_url": shop_url,
                            "score_global": shop_score,
                            "revenue_est_min": _extract_revenue_min(shop_data_raw.get('estimated_revenue', '')),
                            "revenue_est_max": _extract_revenue_max(shop_data_raw.get('estimated_revenue', '')),
                            "winners_count": len([p for p in shop_data_raw.get('products', []) if p.get('price', 0) > 0])
                        }
                        shops.append(shop_data)
                    
                    # Extraire les produits de la boutique
                    for product_raw in shop_data_raw.get('products', []):
                        if product_raw.get('name') and product_raw.get('price', 0) > 0:
                            product_score = calculate_product_score({
                                "name": product_raw.get('name'),
                                "url": product_raw.get('url', ''),
                                "marketplace": marketplace,
                                "estimated_daily_sales": 8,  # Estimation
                                "ideal_price": product_raw.get('price', 0),
                                "competition_level": "Moyen",
                                "trend": "stable"
                            })
                            
                            if product_score >= 70:  # Seulement les winners
                                product_data = {
                                    "product_name": product_raw.get('name'),
                                    "shop_name": shop_data_raw.get('name', 'Boutique'),
                                    "product_url": product_raw.get('url', ''),
                                    "product_image": product_raw.get('image', ''),
                                    "product_description": product_raw.get('description', ''),
                                    "price": product_raw.get('price', 0),
                                    "sales_est_min": 25,  # Estimation mensuelle min
                                    "sales_est_max": 35,  # Estimation mensuelle max
                                    "revenue_est_min": product_raw.get('price', 0) * 25 * 0.7,
                                    "revenue_est_max": product_raw.get('price', 0) * 35,
                                    "score_winner": product_score,
                                    "category": None
                                }
                                products.append(product_data)
                
            except Exception as e:
                print(f"❌ Erreur scraping boutique {shop_url}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Sauvegarder en base de données
        backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backend')
        sys.path.insert(0, backend_path)
        from app.models import ProductGlobal, ShopGlobal, MarketplaceType
        
        marketplace_enum = MarketplaceType(marketplace.lower())
        
        # Sauvegarder les produits
        products_saved = 0
        for product_data in products:
            try:
                existing = db.query(ProductGlobal).filter(
                    ProductGlobal.product_url == product_data.get('product_url', '')
                ).first()
                
                if existing:
                    # Mettre à jour
                    for key, value in product_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.last_scraped_at = datetime.utcnow()
                else:
                    # Créer nouveau
                    product = ProductGlobal(
                        marketplace=marketplace_enum,
                        **product_data,
                        last_scraped_at=datetime.utcnow()
                    )
                    db.add(product)
                products_saved += 1
            except Exception as e:
                print(f"Erreur sauvegarde produit: {e}")
                continue
        
        # Sauvegarder les boutiques
        shops_saved = 0
        for shop_data in shops:
            try:
                existing = db.query(ShopGlobal).filter(
                    ShopGlobal.shop_url == shop_data.get('shop_url', '')
                ).first()
                
                if existing:
                    # Mettre à jour
                    for key, value in shop_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.last_scraped_at = datetime.utcnow()
                else:
                    # Créer nouveau
                    shop = ShopGlobal(
                        marketplace=marketplace_enum,
                        **shop_data,
                        last_scraped_at=datetime.utcnow()
                    )
                    db.add(shop)
                shops_saved += 1
            except Exception as e:
                print(f"Erreur sauvegarde boutique: {e}")
                continue
        
        db.commit()
        print(f"✅ Sauvegardé: {products_saved} produits, {shops_saved} boutiques")
        
        return {
            "products": len(products),
            "shops": len(shops),
            "marketplace": marketplace
        }
        
    except Exception as e:
        db.rollback()
        print(f"Erreur lors du crawl: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        db.close()

def crawl_all_marketplaces(shop_urls: Optional[Dict[str, List[str]]] = None):
    """
    Fonction principale pour crawler toutes les marketplaces
    
    Args:
        shop_urls: Dict avec marketplace -> liste d'URLs de boutiques à scraper
    """
    marketplaces = ["chariow", "maketou", "systemio"]
    
    if shop_urls is None:
        shop_urls = {}
    
    results = []
    for marketplace in marketplaces:
        try:
            urls = shop_urls.get(marketplace, None)
            result = asyncio.run(crawl_marketplace_winners(marketplace, shop_urls=urls))
            results.append(result)
            print(f"✅ {marketplace}: {result.get('products', 0)} produits, {result.get('shops', 0)} boutiques")
        except Exception as e:
            print(f"❌ Erreur {marketplace}: {e}")
            import traceback
            traceback.print_exc()
            results.append({"marketplace": marketplace, "error": str(e)})
    
    return results

if __name__ == "__main__":
    # URLs de test
    shop_urls = {
        "maketou": [],  # Boutiques à découvrir automatiquement
        "chariow": []  # Boutiques à découvrir automatiquement
    }
    crawl_all_marketplaces(shop_urls=shop_urls)
