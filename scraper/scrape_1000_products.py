"""
Script pour scraper 1000 produits complets (URL, nom, description, image)
sur Chariow et Maketou avec validation des données
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

# Importer les scrapers et services
from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from services.discovery import MarketplaceDiscovery
from services.continuous_scraper import ContinuousScraper
from utils.scoring import calculate_product_score

def is_product_complete(product_data: dict) -> bool:
    """Vérifie qu'un produit a toutes les données requises"""
    required_fields = ['name', 'url', 'image']
    
    # Vérifier que tous les champs requis sont présents et non vides
    for field in required_fields:
        if not product_data.get(field):
            return False
        if isinstance(product_data[field], str) and len(product_data[field].strip()) == 0:
            return False
    
    # Vérifier que l'URL est valide (commence par http)
    url = product_data.get('url', '')
    if not url.startswith('http'):
        return False
    
    # Vérifier que l'image est valide (commence par http ou //)
    image = product_data.get('image', '')
    if image and not (image.startswith('http') or image.startswith('//')):
        return False
    
    return True

async def scrape_shop_products(shop_url: str, marketplace: str, scraper_instance) -> list:
    """Scrape tous les produits d'une boutique et retourne uniquement les produits complets"""
    try:
        print(f"  🔄 Scraping boutique: {shop_url[:60]}...")
        shop_data = await scraper_instance.scrape_async(shop_url)
        
        if not shop_data or not shop_data.get('products'):
            return []
        
        complete_products = []
        for product in shop_data.get('products', []):
            # Vérifier que le produit est complet
            if is_product_complete(product):
                # Ajouter la description si disponible
                if not product.get('description'):
                    product['description'] = ''
                
                # Ajouter le prix si disponible
                if not product.get('price'):
                    product['price'] = 0
                
                complete_products.append(product)
            else:
                missing = []
                if not product.get('name'): missing.append('nom')
                if not product.get('url'): missing.append('URL')
                if not product.get('image'): missing.append('image')
                print(f"    ⚠️ Produit incomplet (manque: {', '.join(missing)})")
        
        return complete_products
    
    except Exception as e:
        print(f"  ❌ Erreur scraping boutique {shop_url[:60]}: {e}")
        return []

async def discover_and_scrape_shops(marketplace: str, target_products: int) -> list:
    """Découvre des boutiques et scrape leurs produits jusqu'à atteindre le nombre cible"""
    discovery = MarketplaceDiscovery()
    complete_products = []
    shops_scraped = 0
    
    if marketplace == 'chariow':
        scraper = ChariowScraper()
        shop_urls = await discovery.discover_chariow_shops()
    elif marketplace == 'maketou':
        scraper = MaketouScraper()
        shop_urls = await discovery.discover_maketou_shops()
    else:
        return []
    
    print(f"📦 {len(shop_urls)} boutiques découvertes sur {marketplace.upper()}")
    
    # Scraper les boutiques jusqu'à avoir assez de produits
    for shop_url in shop_urls:
        if len(complete_products) >= target_products:
            break
        
        products = await scrape_shop_products(shop_url, marketplace, scraper)
        
        for product in products:
            if len(complete_products) >= target_products:
                break
            
            # Vérifier que le produit n'existe pas déjà
            existing = any(p.get('url') == product.get('url') for p in complete_products)
            if not existing:
                product['marketplace'] = marketplace
                product['shop_url'] = shop_url
                complete_products.append(product)
                print(f"    ✅ Produit complet ajouté: {product.get('name', '')[:50]}")
        
        shops_scraped += 1
        await asyncio.sleep(2)  # Pause entre les boutiques
    
    return complete_products

async def save_products_to_db(products: list, marketplace: str):
    """Sauvegarde les produits complets dans la base de données"""
    db = SessionLocal()
    
    try:
        from app.models import ProductGlobal, ShopGlobal, MarketplaceType
        
        # Convertir le marketplace en enum
        marketplace_enum = MarketplaceType(marketplace.upper()) if hasattr(MarketplaceType, marketplace.upper()) else MarketplaceType.OTHER
        
        saved = 0
        skipped = 0
        
        for product in products:
            # Vérifier que le produit n'existe pas déjà
            existing = db.query(ProductGlobal).filter(
                ProductGlobal.product_url == product.get('url')
            ).first()
            
            if existing:
                # Mettre à jour le produit existant
                existing.product_name = product.get('name', existing.product_name)
                existing.product_image = product.get('image', existing.product_image)
                existing.product_description = product.get('description', existing.product_description)
                existing.price = product.get('price', existing.price)
                existing.last_scraped_at = datetime.now()
                saved += 1
            else:
                # Calculer le score
                product_score = calculate_product_score({
                    "name": product.get('name'),
                    "url": product.get('url'),
                    "marketplace": marketplace,
                    "estimated_daily_sales": 8,
                    "ideal_price": product.get('price', 0),
                    "competition_level": "Moyen",
                    "trend": "stable"
                })
                
                # Créer un nouveau produit
                new_product = ProductGlobal(
                    marketplace=marketplace_enum.value,
                    product_name=product.get('name'),
                    shop_name=product.get('shop_name', 'Boutique'),
                    product_url=product.get('url'),
                    product_image=product.get('image'),
                    product_description=product.get('description', ''),
                    price=product.get('price', 0),
                    sales_est_min=25,
                    sales_est_max=35,
                    revenue_est_min=product.get('price', 0) * 25 * 0.7,
                    revenue_est_max=product.get('price', 0) * 35,
                    score_winner=product_score,
                    category=None,
                    last_scraped_at=datetime.now()
                )
                db.add(new_product)
                saved += 1
        
        db.commit()
        print(f"✅ {saved} produits sauvegardés en base de données")
        return saved
    
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        db.close()

async def main():
    """Fonction principale"""
    print("🚀 Démarrage du scraping de 1000 produits complets...")
    print("=" * 70)
    
    target_per_marketplace = 500  # 500 produits par marketplace = 1000 total
    
    all_complete_products = []
    
    # Scraper Chariow
    print(f"\n📦 Étape 1: Scraping {target_per_marketplace} produits sur CHARIOW...")
    print("-" * 70)
    chariow_products = await discover_and_scrape_shops('chariow', target_per_marketplace)
    all_complete_products.extend(chariow_products)
    print(f"✅ {len(chariow_products)} produits complets trouvés sur Chariow")
    
    # Scraper Maketou
    print(f"\n📦 Étape 2: Scraping {target_per_marketplace} produits sur MAKETOU...")
    print("-" * 70)
    maketou_products = await discover_and_scrape_shops('maketou', target_per_marketplace)
    all_complete_products.extend(maketou_products)
    print(f"✅ {len(maketou_products)} produits complets trouvés sur Maketou")
    
    # Afficher le résumé
    print(f"\n{'='*70}")
    print(f"📊 RÉSUMÉ DU SCRAPING")
    print(f"{'='*70}")
    print(f"Total produits complets trouvés: {len(all_complete_products)}")
    print(f"  - Chariow: {len(chariow_products)}")
    print(f"  - Maketou: {len(maketou_products)}")
    
    # Vérifier la qualité des produits
    print(f"\n🔍 Vérification de la qualité des produits...")
    products_with_all = 0
    products_without_desc = 0
    
    for product in all_complete_products:
        if product.get('description') and len(product.get('description', '').strip()) > 0:
            products_with_all += 1
        else:
            products_without_desc += 1
    
    print(f"  - Produits avec nom + URL + image + description: {products_with_all}")
    print(f"  - Produits avec nom + URL + image (sans description): {products_without_desc}")
    
    # Sauvegarder en base de données
    if all_complete_products:
        print(f"\n💾 Sauvegarde en base de données...")
        print("-" * 70)
        
        # Séparer par marketplace pour la sauvegarde
        chariow_to_save = [p for p in all_complete_products if p.get('marketplace') == 'chariow']
        maketou_to_save = [p for p in all_complete_products if p.get('marketplace') == 'maketou']
        
        total_saved = 0
        if chariow_to_save:
            saved = await save_products_to_db(chariow_to_save, 'chariow')
            total_saved += saved
        
        if maketou_to_save:
            saved = await save_products_to_db(maketou_to_save, 'maketou')
            total_saved += saved
        
        print(f"\n{'='*70}")
        print(f"✅ SCRAPING TERMINÉ!")
        print(f"{'='*70}")
        print(f"Total produits sauvegardés: {total_saved}")
        print(f"Tous les produits ont: URL ✅ | Nom ✅ | Image ✅")
        print(f"{'='*70}")
    else:
        print(f"\n⚠️ Aucun produit complet trouvé. Vérifiez les scrapers.")

if __name__ == "__main__":
    asyncio.run(main())




Script pour scraper 1000 produits complets (URL, nom, description, image)
sur Chariow et Maketou avec validation des données
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

# Importer les scrapers et services
from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from services.discovery import MarketplaceDiscovery
from services.continuous_scraper import ContinuousScraper
from utils.scoring import calculate_product_score

def is_product_complete(product_data: dict) -> bool:
    """Vérifie qu'un produit a toutes les données requises"""
    required_fields = ['name', 'url', 'image']
    
    # Vérifier que tous les champs requis sont présents et non vides
    for field in required_fields:
        if not product_data.get(field):
            return False
        if isinstance(product_data[field], str) and len(product_data[field].strip()) == 0:
            return False
    
    # Vérifier que l'URL est valide (commence par http)
    url = product_data.get('url', '')
    if not url.startswith('http'):
        return False
    
    # Vérifier que l'image est valide (commence par http ou //)
    image = product_data.get('image', '')
    if image and not (image.startswith('http') or image.startswith('//')):
        return False
    
    return True

async def scrape_shop_products(shop_url: str, marketplace: str, scraper_instance) -> list:
    """Scrape tous les produits d'une boutique et retourne uniquement les produits complets"""
    try:
        print(f"  🔄 Scraping boutique: {shop_url[:60]}...")
        shop_data = await scraper_instance.scrape_async(shop_url)
        
        if not shop_data or not shop_data.get('products'):
            return []
        
        complete_products = []
        for product in shop_data.get('products', []):
            # Vérifier que le produit est complet
            if is_product_complete(product):
                # Ajouter la description si disponible
                if not product.get('description'):
                    product['description'] = ''
                
                # Ajouter le prix si disponible
                if not product.get('price'):
                    product['price'] = 0
                
                complete_products.append(product)
            else:
                missing = []
                if not product.get('name'): missing.append('nom')
                if not product.get('url'): missing.append('URL')
                if not product.get('image'): missing.append('image')
                print(f"    ⚠️ Produit incomplet (manque: {', '.join(missing)})")
        
        return complete_products
    
    except Exception as e:
        print(f"  ❌ Erreur scraping boutique {shop_url[:60]}: {e}")
        return []

async def discover_and_scrape_shops(marketplace: str, target_products: int) -> list:
    """Découvre des boutiques et scrape leurs produits jusqu'à atteindre le nombre cible"""
    discovery = MarketplaceDiscovery()
    complete_products = []
    shops_scraped = 0
    
    if marketplace == 'chariow':
        scraper = ChariowScraper()
        shop_urls = await discovery.discover_chariow_shops()
    elif marketplace == 'maketou':
        scraper = MaketouScraper()
        shop_urls = await discovery.discover_maketou_shops()
    else:
        return []
    
    print(f"📦 {len(shop_urls)} boutiques découvertes sur {marketplace.upper()}")
    
    # Scraper les boutiques jusqu'à avoir assez de produits
    for shop_url in shop_urls:
        if len(complete_products) >= target_products:
            break
        
        products = await scrape_shop_products(shop_url, marketplace, scraper)
        
        for product in products:
            if len(complete_products) >= target_products:
                break
            
            # Vérifier que le produit n'existe pas déjà
            existing = any(p.get('url') == product.get('url') for p in complete_products)
            if not existing:
                product['marketplace'] = marketplace
                product['shop_url'] = shop_url
                complete_products.append(product)
                print(f"    ✅ Produit complet ajouté: {product.get('name', '')[:50]}")
        
        shops_scraped += 1
        await asyncio.sleep(2)  # Pause entre les boutiques
    
    return complete_products

async def save_products_to_db(products: list, marketplace: str):
    """Sauvegarde les produits complets dans la base de données"""
    db = SessionLocal()
    
    try:
        from app.models import ProductGlobal, ShopGlobal, MarketplaceType
        
        # Convertir le marketplace en enum
        marketplace_enum = MarketplaceType(marketplace.upper()) if hasattr(MarketplaceType, marketplace.upper()) else MarketplaceType.OTHER
        
        saved = 0
        skipped = 0
        
        for product in products:
            # Vérifier que le produit n'existe pas déjà
            existing = db.query(ProductGlobal).filter(
                ProductGlobal.product_url == product.get('url')
            ).first()
            
            if existing:
                # Mettre à jour le produit existant
                existing.product_name = product.get('name', existing.product_name)
                existing.product_image = product.get('image', existing.product_image)
                existing.product_description = product.get('description', existing.product_description)
                existing.price = product.get('price', existing.price)
                existing.last_scraped_at = datetime.now()
                saved += 1
            else:
                # Calculer le score
                product_score = calculate_product_score({
                    "name": product.get('name'),
                    "url": product.get('url'),
                    "marketplace": marketplace,
                    "estimated_daily_sales": 8,
                    "ideal_price": product.get('price', 0),
                    "competition_level": "Moyen",
                    "trend": "stable"
                })
                
                # Créer un nouveau produit
                new_product = ProductGlobal(
                    marketplace=marketplace_enum.value,
                    product_name=product.get('name'),
                    shop_name=product.get('shop_name', 'Boutique'),
                    product_url=product.get('url'),
                    product_image=product.get('image'),
                    product_description=product.get('description', ''),
                    price=product.get('price', 0),
                    sales_est_min=25,
                    sales_est_max=35,
                    revenue_est_min=product.get('price', 0) * 25 * 0.7,
                    revenue_est_max=product.get('price', 0) * 35,
                    score_winner=product_score,
                    category=None,
                    last_scraped_at=datetime.now()
                )
                db.add(new_product)
                saved += 1
        
        db.commit()
        print(f"✅ {saved} produits sauvegardés en base de données")
        return saved
    
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        db.close()

async def main():
    """Fonction principale"""
    print("🚀 Démarrage du scraping de 1000 produits complets...")
    print("=" * 70)
    
    target_per_marketplace = 500  # 500 produits par marketplace = 1000 total
    
    all_complete_products = []
    
    # Scraper Chariow
    print(f"\n📦 Étape 1: Scraping {target_per_marketplace} produits sur CHARIOW...")
    print("-" * 70)
    chariow_products = await discover_and_scrape_shops('chariow', target_per_marketplace)
    all_complete_products.extend(chariow_products)
    print(f"✅ {len(chariow_products)} produits complets trouvés sur Chariow")
    
    # Scraper Maketou
    print(f"\n📦 Étape 2: Scraping {target_per_marketplace} produits sur MAKETOU...")
    print("-" * 70)
    maketou_products = await discover_and_scrape_shops('maketou', target_per_marketplace)
    all_complete_products.extend(maketou_products)
    print(f"✅ {len(maketou_products)} produits complets trouvés sur Maketou")
    
    # Afficher le résumé
    print(f"\n{'='*70}")
    print(f"📊 RÉSUMÉ DU SCRAPING")
    print(f"{'='*70}")
    print(f"Total produits complets trouvés: {len(all_complete_products)}")
    print(f"  - Chariow: {len(chariow_products)}")
    print(f"  - Maketou: {len(maketou_products)}")
    
    # Vérifier la qualité des produits
    print(f"\n🔍 Vérification de la qualité des produits...")
    products_with_all = 0
    products_without_desc = 0
    
    for product in all_complete_products:
        if product.get('description') and len(product.get('description', '').strip()) > 0:
            products_with_all += 1
        else:
            products_without_desc += 1
    
    print(f"  - Produits avec nom + URL + image + description: {products_with_all}")
    print(f"  - Produits avec nom + URL + image (sans description): {products_without_desc}")
    
    # Sauvegarder en base de données
    if all_complete_products:
        print(f"\n💾 Sauvegarde en base de données...")
        print("-" * 70)
        
        # Séparer par marketplace pour la sauvegarde
        chariow_to_save = [p for p in all_complete_products if p.get('marketplace') == 'chariow']
        maketou_to_save = [p for p in all_complete_products if p.get('marketplace') == 'maketou']
        
        total_saved = 0
        if chariow_to_save:
            saved = await save_products_to_db(chariow_to_save, 'chariow')
            total_saved += saved
        
        if maketou_to_save:
            saved = await save_products_to_db(maketou_to_save, 'maketou')
            total_saved += saved
        
        print(f"\n{'='*70}")
        print(f"✅ SCRAPING TERMINÉ!")
        print(f"{'='*70}")
        print(f"Total produits sauvegardés: {total_saved}")
        print(f"Tous les produits ont: URL ✅ | Nom ✅ | Image ✅")
        print(f"{'='*70}")
    else:
        print(f"\n⚠️ Aucun produit complet trouvé. Vérifiez les scrapers.")

if __name__ == "__main__":
    asyncio.run(main())



