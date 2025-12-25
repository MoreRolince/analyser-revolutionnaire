"""
Service de scraping continu pour maintenir les données à jour
Tourne en permanence et scrape les boutiques régulièrement
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ajouter les chemins pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
scraper_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(scraper_dir)
backend_path = os.path.join(project_root, 'backend')

# Ajouter les chemins dans l'ordre correct
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
if scraper_dir not in sys.path:
    sys.path.insert(0, scraper_dir)

# Fonction helper pour importer les modèles du backend
def import_backend_models():
    """Importe les modèles du backend avec gestion d'erreur"""
    # Essayer d'abord l'import normal
    try:
        from app.models import ShopGlobal, ProductGlobal, MarketplaceType
        print("✅ Import réussi via app.models")
        return ShopGlobal, ProductGlobal, MarketplaceType
    except ImportError as e:
        print(f"⚠️ Import normal échoué: {e}")
    
    # Si l'import échoue, utiliser importlib
    import importlib.util
    
    # Chercher models.py dans plusieurs emplacements
    possible_paths = [
        '/backend/app/models.py',  # Docker monté (priorité)
        os.path.join(backend_path, 'app', 'models.py') if backend_path and os.path.exists(backend_path) else None,
        os.path.join(project_root, 'backend', 'app', 'models.py') if os.path.exists(os.path.join(project_root, 'backend')) else None,
    ]
    
    # Filtrer les chemins None
    possible_paths = [p for p in possible_paths if p]
    
    for models_path in possible_paths:
        if os.path.exists(models_path):
            try:
                print(f"📦 Tentative d'import depuis: {models_path}")
                # Charger le module parent 'app' d'abord
                app_dir = os.path.dirname(models_path)
                if app_dir not in sys.path:
                    sys.path.insert(0, app_dir)
                
                # Charger models.py
                spec = importlib.util.spec_from_file_location("app.models", models_path)
                models_module = importlib.util.module_from_spec(spec)
                
                # Exécuter le module
                spec.loader.exec_module(models_module)
                
                print(f"✅ Import réussi depuis {models_path}")
                return models_module.ShopGlobal, models_module.ProductGlobal, models_module.MarketplaceType
            except Exception as e:
                print(f"❌ Erreur import {models_path}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    raise ImportError(f"Impossible de trouver app.models. Chemins testés: {possible_paths}")

from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from services.discovery import MarketplaceDiscovery
from services.winners_crawler import crawl_marketplace_winners
from utils.scoring import calculate_product_score, calculate_shop_score

# Configuration DB - utiliser la même configuration que le backend
# Charger depuis .env du backend si disponible
backend_env_path = os.path.join(project_root, 'backend', '.env')
if os.path.exists(backend_env_path):
    from dotenv import load_dotenv
    load_dotenv(backend_env_path)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"  # Port 5433 pour correspondre au docker-compose.yml
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class ContinuousScraper:
    """Scraper continu qui maintient les données à jour"""
    
    def __init__(self):
        self.discovery = MarketplaceDiscovery()
        self.chariow_scraper = ChariowScraper()
        self.maketou_scraper = MaketouScraper()
        self.scrape_interval_hours = 6  # Scraper toutes les 6 heures
        self.discovery_interval_hours = 24  # Découvrir de nouvelles boutiques toutes les 24h
    
    async def scrape_shop(self, shop_url: str, marketplace: str) -> Dict[str, Any]:
        """Scrape une boutique et met à jour la base de données"""
        db = SessionLocal()
        
        try:
            # Sélectionner le scraper approprié
            if marketplace == "chariow":
                scraper = self.chariow_scraper
            elif marketplace == "maketou":
                scraper = self.maketou_scraper
            else:
                return {"status": "error", "message": f"Marketplace non supporté: {marketplace}"}
            
            print(f"🔄 Scraping boutique: {shop_url}")
            shop_data = await scraper.scrape_async(shop_url)
            
            if not shop_data or shop_data.get('product_count', 0) == 0:
                return {"status": "skipped", "message": "Aucun produit trouvé"}
            
            # Calculer le score
            shop_score = calculate_shop_score(shop_data)
            
            # Importer les modèles
            ShopGlobal, ProductGlobal, MarketplaceType = import_backend_models()
            
            # S'assurer que marketplace est en minuscules pour l'enum
            marketplace_lower = marketplace.lower()
            try:
                marketplace_enum = MarketplaceType(marketplace_lower)
            except ValueError:
                # Si la valeur n'existe pas dans l'enum, utiliser "other"
                marketplace_enum = MarketplaceType.OTHER
            
            # Debug: vérifier la valeur
            print(f"🔍 Debug: marketplace_enum = {marketplace_enum}, value = {marketplace_enum.value}, type = {type(marketplace_enum.value)}")
            
            # Mettre à jour ou créer la boutique
            existing_shop = db.query(ShopGlobal).filter(
                ShopGlobal.shop_url == shop_url
            ).first()
            
            if existing_shop:
                existing_shop.shop_name = shop_data.get('name', existing_shop.shop_name)
                existing_shop.score_global = shop_score
                existing_shop.revenue_est_min = self._extract_revenue_min(shop_data.get('estimated_revenue', ''))
                existing_shop.revenue_est_max = self._extract_revenue_max(shop_data.get('estimated_revenue', ''))
                existing_shop.winners_count = len([p for p in shop_data.get('products', []) if p.get('price', 0) > 0])
                existing_shop.last_scraped_at = datetime.utcnow()
            else:
                # Utiliser la valeur string de l'enum pour éviter les problèmes de conversion SQLAlchemy
                new_shop = ShopGlobal(
                    marketplace=marketplace_enum.value,  # Utiliser .value pour obtenir "maketou" au lieu de l'enum
                    shop_name=shop_data.get('name', 'Boutique'),
                    shop_url=shop_url,
                    score_global=shop_score,
                    revenue_est_min=self._extract_revenue_min(shop_data.get('estimated_revenue', '')),
                    revenue_est_max=self._extract_revenue_max(shop_data.get('estimated_revenue', '')),
                    winners_count=len([p for p in shop_data.get('products', []) if p.get('price', 0) > 0]),
                    last_scraped_at=datetime.utcnow()
                )
                db.add(new_shop)
            
            # Mettre à jour les produits
            products_saved = 0
            for product_raw in shop_data.get('products', []):
                # Vérifier que le produit a un nom, un prix valide ET une URL valide
                product_url = product_raw.get('url', '').strip()
                if not (product_raw.get('name') and product_raw.get('price', 0) > 0 and product_url):
                    continue  # Ignorer les produits sans URL valide
                
                product_score = calculate_product_score({
                    "name": product_raw.get('name'),
                    "url": product_url,
                    "marketplace": marketplace,
                    "estimated_daily_sales": 8,
                    "ideal_price": product_raw.get('price', 0),
                    "competition_level": "Moyen",
                    "trend": "stable"
                })
                
                # Sauvegarder TOUS les produits (pas seulement les winners)
                existing_product = db.query(ProductGlobal).filter(
                    ProductGlobal.product_url == product_url
                ).first()
                
                if existing_product:
                    existing_product.product_name = product_raw.get('name')
                    existing_product.price = product_raw.get('price', 0)
                    existing_product.score_winner = product_score
                    existing_product.sales_est_min = 25
                    existing_product.sales_est_max = 35
                    existing_product.revenue_est_min = product_raw.get('price', 0) * 25 * 0.7
                    existing_product.revenue_est_max = product_raw.get('price', 0) * 35
                    existing_product.last_scraped_at = datetime.utcnow()
                else:
                    # Utiliser la valeur string de l'enum pour éviter les problèmes de conversion SQLAlchemy
                    new_product = ProductGlobal(
                        marketplace=marketplace_enum.value,  # Utiliser .value pour obtenir "maketou" au lieu de l'enum
                        product_name=product_raw.get('name'),
                        shop_name=shop_data.get('name', 'Boutique'),
                        product_url=product_url,
                        product_image=product_raw.get('image', ''),
                        product_description=product_raw.get('description', ''),
                        price=product_raw.get('price', 0),
                        sales_est_min=25,
                        sales_est_max=35,
                        revenue_est_min=product_raw.get('price', 0) * 25 * 0.7,
                        revenue_est_max=product_raw.get('price', 0) * 35,
                        score_winner=product_score,
                        category=None,
                        last_scraped_at=datetime.utcnow()
                    )
                    db.add(new_product)
                products_saved += 1
            
            try:
                db.commit()
                print(f"✅ Boutique mise à jour: {products_saved} produits")
            except Exception as commit_error:
                db.rollback()
                print(f"⚠️ Erreur lors de la sauvegarde des produits: {commit_error}")
                # Réessayer avec une gestion d'erreur plus fine
                raise
            
            return {
                "status": "success",
                "shop_url": shop_url,
                "products_saved": products_saved,
                "shop_score": shop_score
            }
        
        except Exception as e:
            db.rollback()
            print(f"❌ Erreur scraping boutique {shop_url}: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
        finally:
            db.close()
    
    def _extract_revenue_min(self, revenue_str: str) -> float:
        """Extrait le revenu minimum"""
        import re
        if not revenue_str:
            return 0.0
        match = re.search(r'([\d,]+)', revenue_str.replace(' ', ''))
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except:
                return 0.0
        return 0.0
    
    def _extract_revenue_max(self, revenue_str: str) -> float:
        """Extrait le revenu maximum"""
        import re
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
                return float(matches[0].replace(',', '')) * 1.5
            except:
                return 0.0
        return 0.0
    
    async def update_all_shops(self):
        """Met à jour toutes les boutiques existantes"""
        db = SessionLocal()
        
        try:
            ShopGlobal, ProductGlobal, MarketplaceType = import_backend_models()
            
            # S'assurer que les tables existent
            from sqlalchemy import inspect
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            if 'shops_global' not in existing_tables or 'products_global' not in existing_tables:
                # Créer les tables si elles n'existent pas
                from app.database import Base
                Base.metadata.create_all(bind=engine)
                print("✅ Tables créées dans la base de données")
            
            # Vérifier la connexion à la base de données
            try:
                from sqlalchemy import text
                db.execute(text("SELECT 1"))
            except Exception as db_error:
                db.close()
                db_host_port = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else "inconnu"
                raise Exception(f"Impossible de se connecter à la base de données: {db_error}. "
                              f"Assurez-vous que PostgreSQL est démarré (docker-compose up -d postgres) et accessible sur {db_host_port}")
            
            # Récupérer toutes les boutiques qui doivent être mises à jour
            # (scrapées il y a plus de 6 heures)
            cutoff_time = datetime.utcnow() - timedelta(hours=self.scrape_interval_hours)
            
            shops_to_update = db.query(ShopGlobal).filter(
                (ShopGlobal.last_scraped_at < cutoff_time) | (ShopGlobal.last_scraped_at.is_(None))
            ).limit(20).all()  # Limiter à 20 boutiques par cycle
            
            print(f"📊 {len(shops_to_update)} boutiques à mettre à jour")
            
            results = []
            for shop in shops_to_update:
                marketplace = shop.marketplace.value if hasattr(shop.marketplace, 'value') else str(shop.marketplace)
                result = await self.scrape_shop(shop.shop_url, marketplace)
                results.append(result)
                # Attendre un peu entre chaque scraping pour ne pas surcharger
                await asyncio.sleep(2)
            
            return results
        
        finally:
            db.close()
    
    async def discover_and_add_new_shops(self):
        """Découvre de nouvelles boutiques et les ajoute"""
        db = SessionLocal()
        
        try:
            ShopGlobal, _, _ = import_backend_models()
            
            # Découvrir de nouvelles boutiques
            print("🔍 Découverte de nouvelles boutiques...")
            discovered = await self.discovery.discover_all_shops()
            
            new_shops_count = 0
            for marketplace, shop_urls in discovered.items():
                for shop_url in shop_urls:
                    # Vérifier si la boutique existe déjà
                    existing = db.query(ShopGlobal).filter(
                        ShopGlobal.shop_url == shop_url
                    ).first()
                    
                    if not existing:
                        # Scraper la nouvelle boutique
                        result = await self.scrape_shop(shop_url, marketplace)
                        if result.get('status') == 'success':
                            new_shops_count += 1
                        await asyncio.sleep(2)  # Pause entre chaque scraping
            
            print(f"✅ {new_shops_count} nouvelles boutiques ajoutées")
            return new_shops_count
        
        finally:
            db.close()
    
    async def run_cycle(self):
        """Exécute un cycle complet de scraping"""
        print(f"\n{'='*60}")
        print(f"🔄 Cycle de scraping - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # 1. Mettre à jour les boutiques existantes
        print("📊 Mise à jour des boutiques existantes...")
        update_results = await self.update_all_shops()
        
        # 2. Découvrir de nouvelles boutiques (une fois par jour)
        # Vérifier si c'est le moment de découvrir
        db = SessionLocal()
        try:
            ShopGlobal, _, _ = import_backend_models()
            last_discovery = db.query(ShopGlobal).order_by(ShopGlobal.last_scraped_at.desc()).first()
            
            should_discover = True
            if last_discovery and last_discovery.last_scraped_at:
                hours_since_discovery = (datetime.utcnow() - last_discovery.last_scraped_at).total_seconds() / 3600
                should_discover = hours_since_discovery >= self.discovery_interval_hours
            
            if should_discover:
                print("\n🔍 Découverte de nouvelles boutiques...")
                new_shops = await self.discover_and_add_new_shops()
            else:
                print("\n⏭️  Découverte de nouvelles boutiques ignorée (trop récente)")
                new_shops = 0
        finally:
            db.close()
        
        print(f"\n✅ Cycle terminé: {len(update_results)} boutiques mises à jour, {new_shops} nouvelles boutiques")
        
        return {
            "updated": len(update_results),
            "new_shops": new_shops,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def run_continuous(self):
        """Lance le scraping continu (tourne indéfiniment)"""
        print("🚀 Démarrage du scraper continu...")
        print(f"⏰ Intervalle de scraping: {self.scrape_interval_hours} heures")
        print(f"🔍 Intervalle de découverte: {self.discovery_interval_hours} heures\n")
        
        while True:
            try:
                await self.run_cycle()
                
                # Attendre avant le prochain cycle
                wait_seconds = self.scrape_interval_hours * 3600
                print(f"\n⏳ Prochain cycle dans {self.scrape_interval_hours} heures...\n")
                await asyncio.sleep(wait_seconds)
            
            except KeyboardInterrupt:
                print("\n🛑 Arrêt du scraper continu...")
                break
            except Exception as e:
                print(f"\n❌ Erreur dans le cycle: {e}")
                import traceback
                traceback.print_exc()
                # Attendre 1 heure avant de réessayer en cas d'erreur
                await asyncio.sleep(3600)

if __name__ == "__main__":
    scraper = ContinuousScraper()
    asyncio.run(scraper.run_continuous())