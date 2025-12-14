"""
Script de scraping direct - Scrape les boutiques et produits sans découverte complexe
"""
import asyncio
import os
import sys
import re
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bs4 import BeautifulSoup

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
from services.digital_product_detector import DigitalProductDetector
from services.shop_generator import ShopURLGenerator
from storage.repository import save_shop_with_products


# Aucune boutique en dur - Découverte automatique uniquement


async def scrape_shop_direct(shop_url: str, marketplace: str, db):
    """Scrape une boutique directement"""
    try:
        print(f"\n{'='*70}")
        print(f"🛒 Scraping: {shop_url}")
        print(f"{'='*70}")
        
        # Choisir le scraper
        if marketplace == 'chariow':
            scraper = ChariowScraper()
        elif marketplace == 'maketou':
            scraper = MaketouScraper()
        else:
            print(f"  ❌ Marketplace inconnue: {marketplace}")
            return 0
        
        # Scraper la boutique
        shop_data = await scraper.scrape_shop(shop_url)
        
        if not shop_data:
            print(f"  ⚠️  Aucune donnée récupérée")
            return 0
        
        if not shop_data.get("products"):
            print(f"  ⚠️  Aucun produit trouvé")
            return 0
        
        print(f"  ✅ {len(shop_data['products'])} produits trouvés")
        
        # Préparer les données pour la sauvegarde
        shop_to_save = {
            "marketplace": marketplace,
            "shop_name": shop_data.get("shop_name", ""),
            "shop_url": shop_url,
            "score_global": 70.0
        }
        
        # Filtrer uniquement les produits digitaux
        digital_products = DigitalProductDetector.filter_digital_products(shop_data["products"])
        print(f"  📊 {len(digital_products)} produits digitaux détectés sur {len(shop_data['products'])} produits totaux")
        
        # Identifier les winners (produits digitaux avec bon score)
        winners = DigitalProductDetector.filter_winners(digital_products, min_score=60.0)
        print(f"  🏆 {len(winners)} WINNERS identifiés (score >= 60)")
        
        products_to_save = []
        for product in digital_products:  # Sauvegarder TOUS les produits digitaux, pas seulement les winners
            # Filtrer les produits invalides
            if not product.get("title") or not product.get("url"):
                continue
            
            # Filtrer les produits d'exemple/test/demo
            title_lower = product.get("title", "").lower()
            if any(word in title_lower for word in ["exemple", "test", "demo", "sample", "placeholder"]):
                continue
            
            # Calculer le score winner
            winner_score = DigitalProductDetector.calculate_winner_score(product)
            is_winner = winner_score >= 60.0
            
            product_to_save = {
                "marketplace": marketplace,
                "product_name": product.get("title", ""),
                "shop_name": shop_data.get("shop_name", ""),
                "product_url": product.get("url", ""),
                "product_image": product.get("images", [None])[0] if product.get("images") else None,
                "product_description": product.get("description", ""),
                "price": product.get("price", 0),
                "category": product.get("category"),
                "score_winner": winner_score
            }
            
            products_to_save.append(product_to_save)
            winner_badge = "🏆 WINNER" if is_winner else ""
            print(f"    ✓ {product.get('title', '')[:50]} (Score: {winner_score:.1f}) {winner_badge}")
        
        if not products_to_save:
            print(f"  ⚠️  Aucun produit valide après filtrage")
            return 0
        
        # Sauvegarder
        try:
            saved_count = save_shop_with_products(db, shop_to_save, products_to_save)
            db.commit()
            print(f"\n  ✅ {saved_count} produits sauvegardés en base de données")
            return saved_count
        except Exception as e:
            db.rollback()
            print(f"  ❌ Erreur sauvegarde: {e}")
            import traceback
            traceback.print_exc()
            return 0
        
    except Exception as e:
        print(f"  ❌ Erreur scraping: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def discover_shops_from_marketplace(marketplace: str):
    """
    Découvre automatiquement des boutiques via génération d'URLs + Google dorks
    Méthode hybride pour maximiser la découverte
    """
    all_shops = set()
    
    # Méthode 1: Génération d'URLs possibles (méthode principale)
    print(f"  🔧 Méthode 1: Génération d'URLs possibles...")
    generated_shops = await ShopURLGenerator.discover_shops(marketplace, limit=500)
    all_shops.update(generated_shops)
    print(f"  ✅ {len(generated_shops)} boutiques trouvées via génération")
    
    # Méthode 2: Google dorks (complémentaire)
    print(f"  🔍 Méthode 2: Recherche Google dorks...")
    google_shops = await discover_shops_via_google(marketplace)
    all_shops.update(google_shops)
    print(f"  ✅ {len(google_shops)} boutiques trouvées via Google")
    
    return sorted(list(all_shops))


async def discover_shops_via_google(marketplace: str):
    """Découvre des boutiques via Google dorks (méthode complémentaire)"""
    from playwright.async_api import async_playwright
    
    shops = set()
    
    if marketplace == 'chariow':
        shop_pattern = re.compile(r'https://([a-zA-Z0-9\-]+)\.mychariow\.shop')
        domain_pattern = 'mychariow.shop'
    elif marketplace == 'maketou':
        shop_pattern = re.compile(r'https://([a-zA-Z0-9\-]+)\.mymaketou\.store')
        domain_pattern = 'mymaketou.store'
    else:
        return []
    
    # Google dorks ciblés
    google_queries = [
        f'site:{domain_pattern}',
        f'site:{domain_pattern} produit',
        f'site:{domain_pattern} ebook',
        f'site:{domain_pattern} formation',
        f'site:{domain_pattern} template',
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        page = await browser.new_page()
        
        try:
            for query in google_queries[:3]:  # Limiter à 3 pour ne pas être trop long
                try:
                    google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                    await page.goto(google_url, wait_until="networkidle", timeout=30000)
                    await page.wait_for_timeout(2000)
                    
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extraire les liens
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        if href.startswith('/url?q='):
                            href = href.split('/url?q=')[1].split('&')[0]
                        
                        match = shop_pattern.search(href)
                        if match:
                            shop_name = match.group(1)
                            if marketplace == 'chariow':
                                shop_url = f"https://{shop_name}.mychariow.shop/fr"
                            else:
                                shop_url = f"https://{shop_name}.mymaketou.store/fr"
                            shops.add(shop_url)
                    
                    await asyncio.sleep(2)
                except Exception:
                    continue
        finally:
            await browser.close()
    
    return list(shops)


def _extract_shops_from_soup(soup: BeautifulSoup, base_url: str, shop_pattern, marketplace: str) -> set:
    """Extrait les URLs de boutiques depuis le HTML"""
    shops = set()
    all_links = soup.find_all('a', href=True)
    
    for link in all_links:
        href = link.get('href', '')
        if not href:
            continue
        
        # Convertir en URL absolue
        if not href.startswith('http'):
            href = f"{base_url}{href}" if href.startswith('/') else f"{base_url}/{href}"
        
        # Vérifier si c'est une boutique
        match = shop_pattern.search(href)
        if match:
            shop_name = match.group(1)
            if marketplace == 'chariow':
                shop_url = f"https://{shop_name}.mychariow.shop/fr"
            else:
                shop_url = f"https://{shop_name}.mymaketou.store/fr"
            shops.add(shop_url)
    
    # Chercher aussi dans le texte de la page (pour les URLs dans le JS)
    page_text = str(soup)
    matches = shop_pattern.findall(page_text)
    for shop_name in matches:
        if marketplace == 'chariow':
            shop_url = f"https://{shop_name}.mychariow.shop/fr"
        else:
            shop_url = f"https://{shop_name}.mymaketou.store/fr"
        shops.add(shop_url)
    
    return shops


async def main():
    """Fonction principale"""
    print("🚀 SCRAPING DIRECT - PRODUITS DIGITAUX")
    print("=" * 70)
    
    db = SessionLocal()
    total_products = 0
    
    try:
        # Découverte automatique de boutiques de produits digitaux
        print("\n📦 DÉCOUVERTE AUTOMATIQUE DE BOUTIQUES")
        print("-" * 70)
        
        print("\n🔍 Découverte boutiques Chariow (produits digitaux)...")
        discovered_chariow = await discover_shops_from_marketplace('chariow')
        print(f"  ✅ {len(discovered_chariow)} boutiques découvertes")
        
        if discovered_chariow:
            print(f"\n📋 Boutiques Chariow trouvées:")
            for i, shop_url in enumerate(discovered_chariow[:10], 1):
                print(f"   {i}. {shop_url}")
            if len(discovered_chariow) > 10:
                print(f"   ... et {len(discovered_chariow) - 10} autres")
        
        print("\n🔍 Découverte boutiques Maketou (produits digitaux)...")
        discovered_maketou = await discover_shops_from_marketplace('maketou')
        print(f"  ✅ {len(discovered_maketou)} boutiques découvertes")
        
        if discovered_maketou:
            print(f"\n📋 Boutiques Maketou trouvées:")
            for i, shop_url in enumerate(discovered_maketou[:10], 1):
                print(f"   {i}. {shop_url}")
            if len(discovered_maketou) > 10:
                print(f"   ... et {len(discovered_maketou) - 10} autres")
        
        # Scraper toutes les boutiques découvertes
        if discovered_chariow:
            print(f"\n🛒 Scraping {len(discovered_chariow)} boutiques Chariow...")
            for i, shop_url in enumerate(discovered_chariow, 1):
                print(f"\n[{i}/{len(discovered_chariow)}]")
                count = await scrape_shop_direct(shop_url, 'chariow', db)
                total_products += count
                await asyncio.sleep(2)
        
        if discovered_maketou:
            print(f"\n🛒 Scraping {len(discovered_maketou)} boutiques Maketou...")
            for i, shop_url in enumerate(discovered_maketou, 1):
                print(f"\n[{i}/{len(discovered_maketou)}]")
                count = await scrape_shop_direct(shop_url, 'maketou', db)
                total_products += count
                await asyncio.sleep(2)
        
        # Résumé final avec statistiques des winners
        print(f"\n{'='*70}")
        print(f"✅ SCRAPING TERMINÉ!")
        print(f"{'='*70}")
        print(f"Total produits digitaux sauvegardés: {total_products}")
        
        # Compter les winners dans la base de données
        from app.models import ProductGlobal
        winners_count = db.query(ProductGlobal).filter(
            ProductGlobal.score_winner >= 60.0
        ).count()
        
        total_digital = db.query(ProductGlobal).count()
        
        print(f"Total produits digitaux en base: {total_digital}")
        print(f"🏆 WINNERS identifiés (score >= 60): {winners_count}")
        print(f"{'='*70}")
        print(f"\n🎉 Les produits digitaux africains sont maintenant dans la base de données!")
        print(f"   🏆 {winners_count} WINNERS sont disponibles sur le dashboard!")
        print(f"   📊 Vous pouvez filtrer par score pour voir les meilleurs produits!")
        
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())


"""
import asyncio
import os
import sys
import re
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bs4 import BeautifulSoup

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
from services.digital_product_detector import DigitalProductDetector
from services.shop_generator import ShopURLGenerator
from storage.repository import save_shop_with_products


# Aucune boutique en dur - Découverte automatique uniquement


async def scrape_shop_direct(shop_url: str, marketplace: str, db):
    """Scrape une boutique directement"""
    try:
        print(f"\n{'='*70}")
        print(f"🛒 Scraping: {shop_url}")
        print(f"{'='*70}")
        
        # Choisir le scraper
        if marketplace == 'chariow':
            scraper = ChariowScraper()
        elif marketplace == 'maketou':
            scraper = MaketouScraper()
        else:
            print(f"  ❌ Marketplace inconnue: {marketplace}")
            return 0
        
        # Scraper la boutique
        shop_data = await scraper.scrape_shop(shop_url)
        
        if not shop_data:
            print(f"  ⚠️  Aucune donnée récupérée")
            return 0
        
        if not shop_data.get("products"):
            print(f"  ⚠️  Aucun produit trouvé")
            return 0
        
        print(f"  ✅ {len(shop_data['products'])} produits trouvés")
        
        # Préparer les données pour la sauvegarde
        shop_to_save = {
            "marketplace": marketplace,
            "shop_name": shop_data.get("shop_name", ""),
            "shop_url": shop_url,
            "score_global": 70.0
        }
        
        # Filtrer uniquement les produits digitaux
        digital_products = DigitalProductDetector.filter_digital_products(shop_data["products"])
        print(f"  📊 {len(digital_products)} produits digitaux détectés sur {len(shop_data['products'])} produits totaux")
        
        # Identifier les winners (produits digitaux avec bon score)
        winners = DigitalProductDetector.filter_winners(digital_products, min_score=60.0)
        print(f"  🏆 {len(winners)} WINNERS identifiés (score >= 60)")
        
        products_to_save = []
        for product in digital_products:  # Sauvegarder TOUS les produits digitaux, pas seulement les winners
            # Filtrer les produits invalides
            if not product.get("title") or not product.get("url"):
                continue
            
            # Filtrer les produits d'exemple/test/demo
            title_lower = product.get("title", "").lower()
            if any(word in title_lower for word in ["exemple", "test", "demo", "sample", "placeholder"]):
                continue
            
            # Calculer le score winner
            winner_score = DigitalProductDetector.calculate_winner_score(product)
            is_winner = winner_score >= 60.0
            
            product_to_save = {
                "marketplace": marketplace,
                "product_name": product.get("title", ""),
                "shop_name": shop_data.get("shop_name", ""),
                "product_url": product.get("url", ""),
                "product_image": product.get("images", [None])[0] if product.get("images") else None,
                "product_description": product.get("description", ""),
                "price": product.get("price", 0),
                "category": product.get("category"),
                "score_winner": winner_score
            }
            
            products_to_save.append(product_to_save)
            winner_badge = "🏆 WINNER" if is_winner else ""
            print(f"    ✓ {product.get('title', '')[:50]} (Score: {winner_score:.1f}) {winner_badge}")
        
        if not products_to_save:
            print(f"  ⚠️  Aucun produit valide après filtrage")
            return 0
        
        # Sauvegarder
        try:
            saved_count = save_shop_with_products(db, shop_to_save, products_to_save)
            db.commit()
            print(f"\n  ✅ {saved_count} produits sauvegardés en base de données")
            return saved_count
        except Exception as e:
            db.rollback()
            print(f"  ❌ Erreur sauvegarde: {e}")
            import traceback
            traceback.print_exc()
            return 0
        
    except Exception as e:
        print(f"  ❌ Erreur scraping: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def discover_shops_from_marketplace(marketplace: str):
    """
    Découvre automatiquement des boutiques via génération d'URLs + Google dorks
    Méthode hybride pour maximiser la découverte
    """
    all_shops = set()
    
    # Méthode 1: Génération d'URLs possibles (méthode principale)
    print(f"  🔧 Méthode 1: Génération d'URLs possibles...")
    generated_shops = await ShopURLGenerator.discover_shops(marketplace, limit=500)
    all_shops.update(generated_shops)
    print(f"  ✅ {len(generated_shops)} boutiques trouvées via génération")
    
    # Méthode 2: Google dorks (complémentaire)
    print(f"  🔍 Méthode 2: Recherche Google dorks...")
    google_shops = await discover_shops_via_google(marketplace)
    all_shops.update(google_shops)
    print(f"  ✅ {len(google_shops)} boutiques trouvées via Google")
    
    return sorted(list(all_shops))


async def discover_shops_via_google(marketplace: str):
    """Découvre des boutiques via Google dorks (méthode complémentaire)"""
    from playwright.async_api import async_playwright
    
    shops = set()
    
    if marketplace == 'chariow':
        shop_pattern = re.compile(r'https://([a-zA-Z0-9\-]+)\.mychariow\.shop')
        domain_pattern = 'mychariow.shop'
    elif marketplace == 'maketou':
        shop_pattern = re.compile(r'https://([a-zA-Z0-9\-]+)\.mymaketou\.store')
        domain_pattern = 'mymaketou.store'
    else:
        return []
    
    # Google dorks ciblés
    google_queries = [
        f'site:{domain_pattern}',
        f'site:{domain_pattern} produit',
        f'site:{domain_pattern} ebook',
        f'site:{domain_pattern} formation',
        f'site:{domain_pattern} template',
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        page = await browser.new_page()
        
        try:
            for query in google_queries[:3]:  # Limiter à 3 pour ne pas être trop long
                try:
                    google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                    await page.goto(google_url, wait_until="networkidle", timeout=30000)
                    await page.wait_for_timeout(2000)
                    
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extraire les liens
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        if href.startswith('/url?q='):
                            href = href.split('/url?q=')[1].split('&')[0]
                        
                        match = shop_pattern.search(href)
                        if match:
                            shop_name = match.group(1)
                            if marketplace == 'chariow':
                                shop_url = f"https://{shop_name}.mychariow.shop/fr"
                            else:
                                shop_url = f"https://{shop_name}.mymaketou.store/fr"
                            shops.add(shop_url)
                    
                    await asyncio.sleep(2)
                except Exception:
                    continue
        finally:
            await browser.close()
    
    return list(shops)


def _extract_shops_from_soup(soup: BeautifulSoup, base_url: str, shop_pattern, marketplace: str) -> set:
    """Extrait les URLs de boutiques depuis le HTML"""
    shops = set()
    all_links = soup.find_all('a', href=True)
    
    for link in all_links:
        href = link.get('href', '')
        if not href:
            continue
        
        # Convertir en URL absolue
        if not href.startswith('http'):
            href = f"{base_url}{href}" if href.startswith('/') else f"{base_url}/{href}"
        
        # Vérifier si c'est une boutique
        match = shop_pattern.search(href)
        if match:
            shop_name = match.group(1)
            if marketplace == 'chariow':
                shop_url = f"https://{shop_name}.mychariow.shop/fr"
            else:
                shop_url = f"https://{shop_name}.mymaketou.store/fr"
            shops.add(shop_url)
    
    # Chercher aussi dans le texte de la page (pour les URLs dans le JS)
    page_text = str(soup)
    matches = shop_pattern.findall(page_text)
    for shop_name in matches:
        if marketplace == 'chariow':
            shop_url = f"https://{shop_name}.mychariow.shop/fr"
        else:
            shop_url = f"https://{shop_name}.mymaketou.store/fr"
        shops.add(shop_url)
    
    return shops


async def main():
    """Fonction principale"""
    print("🚀 SCRAPING DIRECT - PRODUITS DIGITAUX")
    print("=" * 70)
    
    db = SessionLocal()
    total_products = 0
    
    try:
        # Découverte automatique de boutiques de produits digitaux
        print("\n📦 DÉCOUVERTE AUTOMATIQUE DE BOUTIQUES")
        print("-" * 70)
        
        print("\n🔍 Découverte boutiques Chariow (produits digitaux)...")
        discovered_chariow = await discover_shops_from_marketplace('chariow')
        print(f"  ✅ {len(discovered_chariow)} boutiques découvertes")
        
        if discovered_chariow:
            print(f"\n📋 Boutiques Chariow trouvées:")
            for i, shop_url in enumerate(discovered_chariow[:10], 1):
                print(f"   {i}. {shop_url}")
            if len(discovered_chariow) > 10:
                print(f"   ... et {len(discovered_chariow) - 10} autres")
        
        print("\n🔍 Découverte boutiques Maketou (produits digitaux)...")
        discovered_maketou = await discover_shops_from_marketplace('maketou')
        print(f"  ✅ {len(discovered_maketou)} boutiques découvertes")
        
        if discovered_maketou:
            print(f"\n📋 Boutiques Maketou trouvées:")
            for i, shop_url in enumerate(discovered_maketou[:10], 1):
                print(f"   {i}. {shop_url}")
            if len(discovered_maketou) > 10:
                print(f"   ... et {len(discovered_maketou) - 10} autres")
        
        # Scraper toutes les boutiques découvertes
        if discovered_chariow:
            print(f"\n🛒 Scraping {len(discovered_chariow)} boutiques Chariow...")
            for i, shop_url in enumerate(discovered_chariow, 1):
                print(f"\n[{i}/{len(discovered_chariow)}]")
                count = await scrape_shop_direct(shop_url, 'chariow', db)
                total_products += count
                await asyncio.sleep(2)
        
        if discovered_maketou:
            print(f"\n🛒 Scraping {len(discovered_maketou)} boutiques Maketou...")
            for i, shop_url in enumerate(discovered_maketou, 1):
                print(f"\n[{i}/{len(discovered_maketou)}]")
                count = await scrape_shop_direct(shop_url, 'maketou', db)
                total_products += count
                await asyncio.sleep(2)
        
        # Résumé final avec statistiques des winners
        print(f"\n{'='*70}")
        print(f"✅ SCRAPING TERMINÉ!")
        print(f"{'='*70}")
        print(f"Total produits digitaux sauvegardés: {total_products}")
        
        # Compter les winners dans la base de données
        from app.models import ProductGlobal
        winners_count = db.query(ProductGlobal).filter(
            ProductGlobal.score_winner >= 60.0
        ).count()
        
        total_digital = db.query(ProductGlobal).count()
        
        print(f"Total produits digitaux en base: {total_digital}")
        print(f"🏆 WINNERS identifiés (score >= 60): {winners_count}")
        print(f"{'='*70}")
        print(f"\n🎉 Les produits digitaux africains sont maintenant dans la base de données!")
        print(f"   🏆 {winners_count} WINNERS sont disponibles sur le dashboard!")
        print(f"   📊 Vous pouvez filtrer par score pour voir les meilleurs produits!")
        
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

