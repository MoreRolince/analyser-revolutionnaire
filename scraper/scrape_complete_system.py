"""
Script principal de scraping complet
Intègre: détection automatique, scraping, mise à jour, sauvegarde
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

# Importer les modules
from services.chariow_scraper import ChariowScraper
from services.maketou_scraper import MaketouScraper
from services.shop_detector import ShopDetector
from services.product_updater import ProductUpdater
from services.discovery import MarketplaceDiscovery
from storage.repository import save_shop_with_products


async def scrape_shop_complete(shop_url: str, marketplace: str, db, detector: ShopDetector, updater: ProductUpdater):
    """
    Scrape une boutique complète avec détection de changements
    """
    try:
        # Valider que la boutique existe
        is_valid = await detector.validate_shop(shop_url, marketplace)
        if not is_valid:
            print(f"  ⚠️  Boutique invalide ou inaccessible: {shop_url}")
            return 0
        
        # Choisir le scraper approprié
        if marketplace == 'chariow':
            scraper = ChariowScraper()
        elif marketplace == 'maketou':
            scraper = MaketouScraper()
        else:
            print(f"  ❌ Marketplace inconnue: {marketplace}")
            return 0
        
        # Scraper la boutique
        shop_data = await scraper.scrape_shop(shop_url)
        
        if not shop_data or not shop_data.get("products"):
            print(f"  ⚠️  Aucun produit trouvé dans {shop_url}")
            return 0
        
        # Récupérer les produits existants de cette boutique depuis la DB
        from app.models import ProductGlobal
        existing_products = db.query(ProductGlobal).filter(
            ProductGlobal.shop_name == shop_data["shop_name"],
            ProductGlobal.marketplace == marketplace
        ).all()
        
        existing_products_dict = {p.product_url: {
            "id": p.id,
            "url": p.product_url,
            "title": p.product_name,
            "price": p.price,
            "description": p.product_description,
            "images": [p.product_image] if p.product_image else [],
            "category": p.category,
            "rating": None,  # À ajouter si disponible dans le modèle
            "reviews_count": None,
            "date_added": None
        } for p in existing_products}
        
        # Détecter les changements et nouveaux produits
        new_products_count = 0
        updated_products_count = 0
        
        products_to_save = []
        for new_product in shop_data["products"]:
            product_url = new_product.get("url")
            if not product_url:
                continue
            
            existing_product = existing_products_dict.get(product_url)
            
            # Détecter les changements
            changes = updater.detect_changes(existing_product, new_product)
            
            if changes["new_product"]:
                new_products_count += 1
                print(f"    ✨ Nouveau produit: {new_product.get('title', '')[:50]}")
            elif changes["has_changes"]:
                updated_products_count += 1
                change_types = []
                if changes["price_changed"]:
                    change_types.append(f"prix {changes['price_old']}→{changes['price_new']}")
                if changes["reviews_increased"]:
                    change_types.append(f"avis +{changes['reviews_new'] - changes['reviews_old']}")
                if changes["images_changed"]:
                    change_types.append(f"+{len(changes['images_added'])} images")
                print(f"    🔄 Produit mis à jour: {new_product.get('title', '')[:50]} ({', '.join(change_types)})")
            
            # Préparer le produit pour la sauvegarde
            product_to_save = {
                "marketplace": marketplace,
                "product_name": new_product.get("title", ""),
                "shop_name": shop_data["shop_name"],
                "product_url": product_url,
                "product_image": new_product.get("images", [None])[0] if new_product.get("images") else None,
                "product_description": new_product.get("description", ""),
                "price": new_product.get("price", 0),
                "category": new_product.get("category"),
                "score_winner": updater.calculate_growth_score(new_product, changes) if changes["has_changes"] else 50.0
            }
            
            products_to_save.append(product_to_save)
        
        # Sauvegarder la boutique et ses produits
        shop_to_save = {
            "marketplace": marketplace,
            "shop_name": shop_data["shop_name"],
            "shop_url": shop_url,
            "score_global": 70.0  # Score par défaut
        }
        
        try:
            saved_count = save_shop_with_products(db, shop_to_save, products_to_save)
            db.commit()
            
            print(f"  ✅ Boutique sauvegardée: {new_products_count} nouveaux, {updated_products_count} mis à jour, {saved_count} produits en DB")
            return saved_count
        except Exception as e:
            db.rollback()
            print(f"  ❌ Erreur sauvegarde: {e}")
            import traceback
            traceback.print_exc()
            return 0
        
    except Exception as e:
        print(f"  ❌ Erreur scraping boutique {shop_url}: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def main():
    """Fonction principale - Processus complet de scraping"""
    print("🚀 SYSTÈME COMPLET DE SCRAPING CHARIOW & MAKETOU")
    print("=" * 70)
    print("📋 Processus:")
    print("  1. Découverte automatique des boutiques")
    print("  2. Validation des boutiques (HTTP 200)")
    print("  3. Scraping des produits (patterns prd_ et /products/)")
    print("  4. Détection de changements (nouveaux, prix, avis, images)")
    print("  5. Sauvegarde en base de données")
    print("=" * 70)
    
    db = SessionLocal()
    detector = ShopDetector()
    updater = ProductUpdater()
    discovery = MarketplaceDiscovery()
    
    try:
        # Étape 1: Découvrir TOUTES les boutiques
        print("\n📦 ÉTAPE 1: Découverte automatique des boutiques")
        print("-" * 70)
        
        print("\n🔍 Découverte Chariow...")
        chariow_shops_data = await discovery.discover_chariow_shops()
        chariow_shops = [s["shop_url"] if isinstance(s, dict) else s for s in chariow_shops_data]
        
        print("\n🔍 Découverte Maketou...")
        maketou_shops_data = await discovery.discover_maketou_shops()
        maketou_shops = [s["shop_url"] if isinstance(s, dict) else s for s in maketou_shops_data]
        
        print(f"\n✅ {len(chariow_shops)} boutiques Chariow découvertes")
        print(f"✅ {len(maketou_shops)} boutiques Maketou découvertes")
        
        # Étape 2: Valider les boutiques
        print("\n📦 ÉTAPE 2: Validation des boutiques")
        print("-" * 70)
        
        print("🔍 Validation Chariow...")
        valid_chariow = []
        for shop_url in chariow_shops[:100]:  # Limiter pour les tests
            if await detector.validate_shop(shop_url, 'chariow'):
                valid_chariow.append(shop_url)
                print(f"  ✅ {shop_url}")
        
        print("🔍 Validation Maketou...")
        valid_maketou = []
        for shop_url in maketou_shops[:100]:  # Limiter pour les tests
            if await detector.validate_shop(shop_url, 'maketou'):
                valid_maketou.append(shop_url)
                print(f"  ✅ {shop_url}")
        
        print(f"\n✅ {len(valid_chariow)} boutiques Chariow valides")
        print(f"✅ {len(valid_maketou)} boutiques Maketou valides")
        
        # Étape 3: Scraper toutes les boutiques
        print("\n📦 ÉTAPE 3: Scraping des boutiques et produits")
        print("-" * 70)
        
        total_products = 0
        
        # Scraper Chariow
        print(f"\n🛒 Scraping {len(valid_chariow)} boutiques Chariow...")
        for i, shop_url in enumerate(valid_chariow, 1):
            print(f"\n[{i}/{len(valid_chariow)}] {shop_url}")
            count = await scrape_shop_complete(shop_url, 'chariow', db, detector, updater)
            total_products += count
            await asyncio.sleep(2)  # Pause entre les boutiques
        
        # Scraper Maketou
        print(f"\n🛒 Scraping {len(valid_maketou)} boutiques Maketou...")
        for i, shop_url in enumerate(valid_maketou, 1):
            print(f"\n[{i}/{len(valid_maketou)}] {shop_url}")
            count = await scrape_shop_complete(shop_url, 'maketou', db, detector, updater)
            total_products += count
            await asyncio.sleep(2)  # Pause entre les boutiques
        
        # Résumé final
        print(f"\n{'='*70}")
        print(f"✅ SCRAPING TERMINÉ!")
        print(f"{'='*70}")
        print(f"Boutiques Chariow scrapées: {len(valid_chariow)}")
        print(f"Boutiques Maketou scrapées: {len(valid_maketou)}")
        print(f"Total produits traités: {total_products}")
        print(f"{'='*70}")
        print(f"\n🎉 Tous les produits sont maintenant dans la base de données!")
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())


Intègre: détection automatique, scraping, mise à jour, sauvegarde
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

# Importer les modules
from services.chariow_scraper import ChariowScraper
from services.maketou_scraper import MaketouScraper
from services.shop_detector import ShopDetector
from services.product_updater import ProductUpdater
from services.discovery import MarketplaceDiscovery
from storage.repository import save_shop_with_products


async def scrape_shop_complete(shop_url: str, marketplace: str, db, detector: ShopDetector, updater: ProductUpdater):
    """
    Scrape une boutique complète avec détection de changements
    """
    try:
        # Valider que la boutique existe
        is_valid = await detector.validate_shop(shop_url, marketplace)
        if not is_valid:
            print(f"  ⚠️  Boutique invalide ou inaccessible: {shop_url}")
            return 0
        
        # Choisir le scraper approprié
        if marketplace == 'chariow':
            scraper = ChariowScraper()
        elif marketplace == 'maketou':
            scraper = MaketouScraper()
        else:
            print(f"  ❌ Marketplace inconnue: {marketplace}")
            return 0
        
        # Scraper la boutique
        shop_data = await scraper.scrape_shop(shop_url)
        
        if not shop_data or not shop_data.get("products"):
            print(f"  ⚠️  Aucun produit trouvé dans {shop_url}")
            return 0
        
        # Récupérer les produits existants de cette boutique depuis la DB
        from app.models import ProductGlobal
        existing_products = db.query(ProductGlobal).filter(
            ProductGlobal.shop_name == shop_data["shop_name"],
            ProductGlobal.marketplace == marketplace
        ).all()
        
        existing_products_dict = {p.product_url: {
            "id": p.id,
            "url": p.product_url,
            "title": p.product_name,
            "price": p.price,
            "description": p.product_description,
            "images": [p.product_image] if p.product_image else [],
            "category": p.category,
            "rating": None,  # À ajouter si disponible dans le modèle
            "reviews_count": None,
            "date_added": None
        } for p in existing_products}
        
        # Détecter les changements et nouveaux produits
        new_products_count = 0
        updated_products_count = 0
        
        products_to_save = []
        for new_product in shop_data["products"]:
            product_url = new_product.get("url")
            if not product_url:
                continue
            
            existing_product = existing_products_dict.get(product_url)
            
            # Détecter les changements
            changes = updater.detect_changes(existing_product, new_product)
            
            if changes["new_product"]:
                new_products_count += 1
                print(f"    ✨ Nouveau produit: {new_product.get('title', '')[:50]}")
            elif changes["has_changes"]:
                updated_products_count += 1
                change_types = []
                if changes["price_changed"]:
                    change_types.append(f"prix {changes['price_old']}→{changes['price_new']}")
                if changes["reviews_increased"]:
                    change_types.append(f"avis +{changes['reviews_new'] - changes['reviews_old']}")
                if changes["images_changed"]:
                    change_types.append(f"+{len(changes['images_added'])} images")
                print(f"    🔄 Produit mis à jour: {new_product.get('title', '')[:50]} ({', '.join(change_types)})")
            
            # Préparer le produit pour la sauvegarde
            product_to_save = {
                "marketplace": marketplace,
                "product_name": new_product.get("title", ""),
                "shop_name": shop_data["shop_name"],
                "product_url": product_url,
                "product_image": new_product.get("images", [None])[0] if new_product.get("images") else None,
                "product_description": new_product.get("description", ""),
                "price": new_product.get("price", 0),
                "category": new_product.get("category"),
                "score_winner": updater.calculate_growth_score(new_product, changes) if changes["has_changes"] else 50.0
            }
            
            products_to_save.append(product_to_save)
        
        # Sauvegarder la boutique et ses produits
        shop_to_save = {
            "marketplace": marketplace,
            "shop_name": shop_data["shop_name"],
            "shop_url": shop_url,
            "score_global": 70.0  # Score par défaut
        }
        
        try:
            saved_count = save_shop_with_products(db, shop_to_save, products_to_save)
            db.commit()
            
            print(f"  ✅ Boutique sauvegardée: {new_products_count} nouveaux, {updated_products_count} mis à jour, {saved_count} produits en DB")
            return saved_count
        except Exception as e:
            db.rollback()
            print(f"  ❌ Erreur sauvegarde: {e}")
            import traceback
            traceback.print_exc()
            return 0
        
    except Exception as e:
        print(f"  ❌ Erreur scraping boutique {shop_url}: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def main():
    """Fonction principale - Processus complet de scraping"""
    print("🚀 SYSTÈME COMPLET DE SCRAPING CHARIOW & MAKETOU")
    print("=" * 70)
    print("📋 Processus:")
    print("  1. Découverte automatique des boutiques")
    print("  2. Validation des boutiques (HTTP 200)")
    print("  3. Scraping des produits (patterns prd_ et /products/)")
    print("  4. Détection de changements (nouveaux, prix, avis, images)")
    print("  5. Sauvegarde en base de données")
    print("=" * 70)
    
    db = SessionLocal()
    detector = ShopDetector()
    updater = ProductUpdater()
    discovery = MarketplaceDiscovery()
    
    try:
        # Étape 1: Découvrir TOUTES les boutiques
        print("\n📦 ÉTAPE 1: Découverte automatique des boutiques")
        print("-" * 70)
        
        print("\n🔍 Découverte Chariow...")
        chariow_shops_data = await discovery.discover_chariow_shops()
        chariow_shops = [s["shop_url"] if isinstance(s, dict) else s for s in chariow_shops_data]
        
        print("\n🔍 Découverte Maketou...")
        maketou_shops_data = await discovery.discover_maketou_shops()
        maketou_shops = [s["shop_url"] if isinstance(s, dict) else s for s in maketou_shops_data]
        
        print(f"\n✅ {len(chariow_shops)} boutiques Chariow découvertes")
        print(f"✅ {len(maketou_shops)} boutiques Maketou découvertes")
        
        # Étape 2: Valider les boutiques
        print("\n📦 ÉTAPE 2: Validation des boutiques")
        print("-" * 70)
        
        print("🔍 Validation Chariow...")
        valid_chariow = []
        for shop_url in chariow_shops[:100]:  # Limiter pour les tests
            if await detector.validate_shop(shop_url, 'chariow'):
                valid_chariow.append(shop_url)
                print(f"  ✅ {shop_url}")
        
        print("🔍 Validation Maketou...")
        valid_maketou = []
        for shop_url in maketou_shops[:100]:  # Limiter pour les tests
            if await detector.validate_shop(shop_url, 'maketou'):
                valid_maketou.append(shop_url)
                print(f"  ✅ {shop_url}")
        
        print(f"\n✅ {len(valid_chariow)} boutiques Chariow valides")
        print(f"✅ {len(valid_maketou)} boutiques Maketou valides")
        
        # Étape 3: Scraper toutes les boutiques
        print("\n📦 ÉTAPE 3: Scraping des boutiques et produits")
        print("-" * 70)
        
        total_products = 0
        
        # Scraper Chariow
        print(f"\n🛒 Scraping {len(valid_chariow)} boutiques Chariow...")
        for i, shop_url in enumerate(valid_chariow, 1):
            print(f"\n[{i}/{len(valid_chariow)}] {shop_url}")
            count = await scrape_shop_complete(shop_url, 'chariow', db, detector, updater)
            total_products += count
            await asyncio.sleep(2)  # Pause entre les boutiques
        
        # Scraper Maketou
        print(f"\n🛒 Scraping {len(valid_maketou)} boutiques Maketou...")
        for i, shop_url in enumerate(valid_maketou, 1):
            print(f"\n[{i}/{len(valid_maketou)}] {shop_url}")
            count = await scrape_shop_complete(shop_url, 'maketou', db, detector, updater)
            total_products += count
            await asyncio.sleep(2)  # Pause entre les boutiques
        
        # Résumé final
        print(f"\n{'='*70}")
        print(f"✅ SCRAPING TERMINÉ!")
        print(f"{'='*70}")
        print(f"Boutiques Chariow scrapées: {len(valid_chariow)}")
        print(f"Boutiques Maketou scrapées: {len(valid_maketou)}")
        print(f"Total produits traités: {total_products}")
        print(f"{'='*70}")
        print(f"\n🎉 Tous les produits sont maintenant dans la base de données!")
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

