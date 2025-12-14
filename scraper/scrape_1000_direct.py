"""
Script pour scraper 1000 produits directement depuis des boutiques connues
Chariow et Maketou avec validation des données
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

# Importer les scrapers
from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from utils.scoring import calculate_product_score

# Liste de boutiques connues à scraper
KNOWN_CHARIOW_SHOPS = [
    # Ajouter d'autres URLs Chariow ici si vous en connaissez
]

KNOWN_MAKETOU_SHOPS = [
    "https://numerik.mymaketou.store/",
    # Ajouter d'autres URLs Maketou ici si vous en connaissez
]

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
        print(f"  🔄 Scraping boutique: {shop_url}")
        shop_data = await scraper_instance.scrape_async(shop_url)
        
        if not shop_data:
            print(f"    ⚠️ Aucune donnée récupérée")
            return []
        
        if not shop_data.get('products'):
            print(f"    ⚠️ Aucun produit trouvé dans cette boutique")
            return []
        
        print(f"    📦 {len(shop_data.get('products', []))} produits trouvés")
        
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
                print(f"    ✅ Produit complet: {product.get('name', '')[:50]}")
            else:
                missing = []
                if not product.get('name'): missing.append('nom')
                if not product.get('url'): missing.append('URL')
                if not product.get('image'): missing.append('image')
                print(f"    ⚠️ Produit incomplet (manque: {', '.join(missing)})")
        
        print(f"    ✅ {len(complete_products)} produits complets sur {len(shop_data.get('products', []))}")
        return complete_products
    
    except Exception as e:
        print(f"  ❌ Erreur scraping boutique {shop_url}: {e}")
        import traceback
        traceback.print_exc()
        return []

async def scrape_marketplace(marketplace: str, shop_urls: list, target_products: int) -> list:
    """Scrape les produits d'une marketplace jusqu'à atteindre le nombre cible"""
    if marketplace == 'chariow':
        scraper = ChariowScraper()
    elif marketplace == 'maketou':
        scraper = MaketouScraper()
    else:
        return []
    
    complete_products = []
    shops_scraped = 0
    
    print(f"\n📦 Scraping {marketplace.upper()} - {len(shop_urls)} boutiques disponibles")
    print("-" * 70)
    
    # Scraper les boutiques jusqu'à avoir assez de produits
    for shop_url in shop_urls:
        if len(complete_products) >= target_products:
            break
        
        print(f"\n🏪 Boutique {shops_scraped + 1}/{len(shop_urls)}: {shop_url}")
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
        updated = 0
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
                updated += 1
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
        print(f"\n💾 Sauvegarde terminée:")
        print(f"   - {saved} nouveaux produits sauvegardés")
        print(f"   - {updated} produits mis à jour")
        return saved + updated
    
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
    print("=" * 70)
    chariow_products = await scrape_marketplace('chariow', KNOWN_CHARIOW_SHOPS, target_per_marketplace)
    all_complete_products.extend(chariow_products)
    print(f"\n✅ {len(chariow_products)} produits complets trouvés sur Chariow")
    
    # Si on n'a pas assez de produits Chariow, on continue avec Maketou
    if len(all_complete_products) < 1000:
        remaining = 1000 - len(all_complete_products)
        target_maketou = min(remaining, target_per_marketplace)
        
        print(f"\n📦 Étape 2: Scraping {target_maketou} produits sur MAKETOU...")
        print("=" * 70)
        maketou_products = await scrape_marketplace('maketou', KNOWN_MAKETOU_SHOPS, target_maketou)
        all_complete_products.extend(maketou_products)
        print(f"\n✅ {len(maketou_products)} produits complets trouvés sur Maketou")
    
    # Afficher le résumé
    print(f"\n{'='*70}")
    print(f"📊 RÉSUMÉ DU SCRAPING")
    print(f"{'='*70}")
    print(f"Total produits complets trouvés: {len(all_complete_products)}")
    chariow_count = len([p for p in all_complete_products if p.get('marketplace') == 'chariow'])
    maketou_count = len([p for p in all_complete_products if p.get('marketplace') == 'maketou'])
    print(f"  - Chariow: {chariow_count}")
    print(f"  - Maketou: {maketou_count}")
    
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
        print(f"\n⚠️ Aucun produit complet trouvé. Vérifiez les scrapers et les URLs des boutiques.")

if __name__ == "__main__":
    asyncio.run(main())




Chariow et Maketou avec validation des données
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

# Importer les scrapers
from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from utils.scoring import calculate_product_score

# Liste de boutiques connues à scraper
KNOWN_CHARIOW_SHOPS = [
    # Ajouter d'autres URLs Chariow ici si vous en connaissez
]

KNOWN_MAKETOU_SHOPS = [
    "https://numerik.mymaketou.store/",
    # Ajouter d'autres URLs Maketou ici si vous en connaissez
]

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
        print(f"  🔄 Scraping boutique: {shop_url}")
        shop_data = await scraper_instance.scrape_async(shop_url)
        
        if not shop_data:
            print(f"    ⚠️ Aucune donnée récupérée")
            return []
        
        if not shop_data.get('products'):
            print(f"    ⚠️ Aucun produit trouvé dans cette boutique")
            return []
        
        print(f"    📦 {len(shop_data.get('products', []))} produits trouvés")
        
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
                print(f"    ✅ Produit complet: {product.get('name', '')[:50]}")
            else:
                missing = []
                if not product.get('name'): missing.append('nom')
                if not product.get('url'): missing.append('URL')
                if not product.get('image'): missing.append('image')
                print(f"    ⚠️ Produit incomplet (manque: {', '.join(missing)})")
        
        print(f"    ✅ {len(complete_products)} produits complets sur {len(shop_data.get('products', []))}")
        return complete_products
    
    except Exception as e:
        print(f"  ❌ Erreur scraping boutique {shop_url}: {e}")
        import traceback
        traceback.print_exc()
        return []

async def scrape_marketplace(marketplace: str, shop_urls: list, target_products: int) -> list:
    """Scrape les produits d'une marketplace jusqu'à atteindre le nombre cible"""
    if marketplace == 'chariow':
        scraper = ChariowScraper()
    elif marketplace == 'maketou':
        scraper = MaketouScraper()
    else:
        return []
    
    complete_products = []
    shops_scraped = 0
    
    print(f"\n📦 Scraping {marketplace.upper()} - {len(shop_urls)} boutiques disponibles")
    print("-" * 70)
    
    # Scraper les boutiques jusqu'à avoir assez de produits
    for shop_url in shop_urls:
        if len(complete_products) >= target_products:
            break
        
        print(f"\n🏪 Boutique {shops_scraped + 1}/{len(shop_urls)}: {shop_url}")
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
        updated = 0
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
                updated += 1
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
        print(f"\n💾 Sauvegarde terminée:")
        print(f"   - {saved} nouveaux produits sauvegardés")
        print(f"   - {updated} produits mis à jour")
        return saved + updated
    
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
    print("=" * 70)
    chariow_products = await scrape_marketplace('chariow', KNOWN_CHARIOW_SHOPS, target_per_marketplace)
    all_complete_products.extend(chariow_products)
    print(f"\n✅ {len(chariow_products)} produits complets trouvés sur Chariow")
    
    # Si on n'a pas assez de produits Chariow, on continue avec Maketou
    if len(all_complete_products) < 1000:
        remaining = 1000 - len(all_complete_products)
        target_maketou = min(remaining, target_per_marketplace)
        
        print(f"\n📦 Étape 2: Scraping {target_maketou} produits sur MAKETOU...")
        print("=" * 70)
        maketou_products = await scrape_marketplace('maketou', KNOWN_MAKETOU_SHOPS, target_maketou)
        all_complete_products.extend(maketou_products)
        print(f"\n✅ {len(maketou_products)} produits complets trouvés sur Maketou")
    
    # Afficher le résumé
    print(f"\n{'='*70}")
    print(f"📊 RÉSUMÉ DU SCRAPING")
    print(f"{'='*70}")
    print(f"Total produits complets trouvés: {len(all_complete_products)}")
    chariow_count = len([p for p in all_complete_products if p.get('marketplace') == 'chariow'])
    maketou_count = len([p for p in all_complete_products if p.get('marketplace') == 'maketou'])
    print(f"  - Chariow: {chariow_count}")
    print(f"  - Maketou: {maketou_count}")
    
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
        print(f"\n⚠️ Aucun produit complet trouvé. Vérifiez les scrapers et les URLs des boutiques.")

if __name__ == "__main__":
    asyncio.run(main())



