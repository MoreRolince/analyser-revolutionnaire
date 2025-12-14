"""
Script pour découvrir et scraper automatiquement des boutiques sur Chariow et Maketou
et ajouter leurs produits au dashboard
"""
import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

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
from services.discovery import MarketplaceDiscovery
from utils.scoring import calculate_product_score, calculate_shop_score

def normalize_shop_url(url: str, marketplace: str) -> str:
    """
    Normalise une URL de boutique en ne gardant que le domaine racine
    (évite de traiter des pages produit/checkout comme des boutiques).
    """
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        # S'assurer que le domaine correspond au marketplace attendu
        host = parsed.netloc.lower()
        if marketplace == 'chariow' and 'mychariow.shop' not in host:
            return ""
        if marketplace == 'maketou' and 'mymaketou.store' not in host:
            return ""
        # Conserver seulement schéma + netloc
        normalized = urlunparse((parsed.scheme or 'https', host, '', '', '', ''))
        return normalized.rstrip('/')
    except Exception:
        return ""

async def discover_shops_from_search(marketplace: str) -> list:
    """Découvre des boutiques en cherchant sur Google ou directement sur les marketplaces"""
    shop_urls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            if marketplace == 'chariow':
                # Chercher des boutiques Chariow
                search_urls = [
                    "https://www.google.com/search?q=site:mychariow.shop",
                    "https://chariow.com",
                ]
            else:  # maketou
                # Chercher des boutiques Maketou
                search_urls = [
                    "https://www.google.com/search?q=site:mymaketou.store",
                    "https://maketou.com",
                ]
            
            for search_url in search_urls:
                try:
                    print(f"🔍 Exploration: {search_url}")
                    await page.goto(search_url, wait_until="networkidle", timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    content = await page.content()
                    try:
                        soup = BeautifulSoup(content, 'lxml')
                    except:
                        soup = BeautifulSoup(content, 'html.parser')
                    
                    # Chercher tous les liens
                    all_links = soup.find_all('a', href=True)
                    
                    for link in all_links:
                        href = link.get('href', '')
                        if not href:
                            continue
                        
                        # Convertir en URL absolue
                        if not href.startswith('http'):
                            href = urljoin(search_url, href)
                        
                        # Normaliser au domaine racine
                        clean_url = normalize_shop_url(href, marketplace)
                        if not clean_url:
                            continue
                        
                        if clean_url not in shop_urls:
                            shop_urls.append(clean_url)
                            print(f"  ✅ Boutique {marketplace} trouvée: {clean_url}")
                    
                    # Scroll pour charger plus
                    for i in range(2):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(2000)
                        
                        content = await page.content()
                        try:
                            soup = BeautifulSoup(content, 'lxml')
                        except:
                            soup = BeautifulSoup(content, 'html.parser')
                        
                        all_links = soup.find_all('a', href=True)
                        for link in all_links:
                            href = link.get('href', '')
                            if not href:
                                continue
                            if not href.startswith('http'):
                                href = urljoin(search_url, href)
                            
                            clean_url = normalize_shop_url(href, marketplace)
                            if not clean_url:
                                continue
                            
                            if clean_url not in shop_urls:
                                shop_urls.append(clean_url)
                                print(f"  ✅ Boutique {marketplace} trouvée: {clean_url}")
                    
                    await asyncio.sleep(2)
                
                except Exception as e:
                    print(f"  ⚠️ Erreur sur {search_url}: {e}")
                    continue
        
        finally:
            await browser.close()
    
    return shop_urls

async def discover_shops_from_known_shops(marketplace: str, known_shops: list) -> list:
    """Découvre plus de boutiques en explorant les boutiques connues"""
    shop_urls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for shop_url in known_shops:
            try:
                print(f"🔍 Exploration depuis: {shop_url}")
                await page.goto(shop_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)
                
                content = await page.content()
                try:
                    soup = BeautifulSoup(content, 'lxml')
                except:
                    soup = BeautifulSoup(content, 'html.parser')
                
                # Chercher tous les liens
                all_links = soup.find_all('a', href=True)
                
                for link in all_links:
                    href = link.get('href', '')
                    if not href:
                        continue
                    
                    if not href.startswith('http'):
                        href = urljoin(shop_url, href)
                    
                    clean_url = normalize_shop_url(href, marketplace)
                    if not clean_url or clean_url == shop_url.rstrip('/'):
                        continue
                    
                    if clean_url not in shop_urls:
                        shop_urls.append(clean_url)
                        print(f"  ✅ Boutique trouvée: {clean_url}")
                
                await asyncio.sleep(2)
            
            except Exception as e:
                print(f"  ⚠️ Erreur: {e}")
                continue
        
        await browser.close()
    
    return shop_urls

def is_product_complete(product_data: dict) -> bool:
    """Vérifie qu'un produit a toutes les données requises"""
    if not product_data.get('name') or not product_data.get('name').strip():
        return False
    if not product_data.get('url') or not product_data.get('url').startswith('http'):
        return False
    if not product_data.get('image') or not (product_data.get('image').startswith('http') or product_data.get('image').startswith('//')):
        return False
    return True

async def scrape_and_save_shop(shop_url: str, marketplace: str, scraper_instance, db):
    """Scrape une boutique et sauvegarde ses produits"""
    try:
        print(f"\n🏪 Scraping boutique: {shop_url}")
        shop_data = await scraper_instance.scrape_async(shop_url)
        
        if not shop_data:
            print(f"  ⚠️ Aucune donnée récupérée")
            return 0
        
        if not shop_data.get('products'):
            print(f"  ⚠️ Aucun produit trouvé")
            return 0
        
        print(f"  📦 {len(shop_data.get('products', []))} produits trouvés")

        from app.models import ProductGlobal, ShopGlobal
        marketplace_value = marketplace.lower()
        
        # Sauvegarder ou mettre à jour la boutique
        existing_shop = db.query(ShopGlobal).filter(ShopGlobal.shop_url == shop_url).first()
        
        shop_score = calculate_shop_score(shop_data) if shop_data else 70
        
        if existing_shop:
            existing_shop.shop_name = shop_data.get('name', existing_shop.shop_name)
            existing_shop.score_global = shop_score
            existing_shop.last_scraped_at = datetime.now()
        else:
            new_shop = ShopGlobal(
                marketplace=marketplace_value,
                shop_name=shop_data.get('name', 'Boutique'),
                shop_url=shop_url,
                score_global=shop_score,
                revenue_est_min=0,
                revenue_est_max=0,
                winners_count=0,
                last_scraped_at=datetime.now()
            )
            db.add(new_shop)
        
        # Sauvegarder les produits complets
        saved_count = 0
        for product in shop_data.get('products', []):
            if not is_product_complete(product):
                continue
            
            # Vérifier si le produit existe déjà
            existing_product = db.query(ProductGlobal).filter(
                ProductGlobal.product_url == product.get('url')
            ).first()
            
            product_score = calculate_product_score({
                "name": product.get('name'),
                "url": product.get('url'),
                "marketplace": marketplace,
                "estimated_daily_sales": 8,
                "ideal_price": product.get('price', 0),
                "competition_level": "Moyen",
                "trend": "stable"
            })
            
            if existing_product:
                # Mettre à jour
                existing_product.product_name = product.get('name')
                existing_product.product_image = product.get('image')
                existing_product.product_description = product.get('description', '')
                existing_product.price = product.get('price', 0)
                existing_product.score_winner = product_score
                existing_product.last_scraped_at = datetime.now()
            else:
                # Créer nouveau
                new_product = ProductGlobal(
                    marketplace=marketplace_value,
                    product_name=product.get('name'),
                    shop_name=shop_data.get('name', 'Boutique'),
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
                saved_count += 1
        
        db.commit()
        print(f"  ✅ {saved_count} nouveaux produits sauvegardés")
        return saved_count
    
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 0

async def main():
    """Fonction principale - Découvre et scrape TOUTES les boutiques Chariow et Maketou"""
    print("🚀 Découverte et scraping automatique de TOUTES les boutiques Chariow et Maketou")
    print("=" * 70)
    
    db = SessionLocal()
    discovery = MarketplaceDiscovery()
    
    try:
        # Découvrir TOUTES les boutiques Chariow
        print("\n📦 Étape 1: Découverte de TOUTES les boutiques CHARIOW...")
        print("-" * 70)
        chariow_shops = await discovery.discover_chariow_shops()
        print(f"\n✅ {len(chariow_shops)} boutiques Chariow découvertes au total")
        
        # Découvrir TOUTES les boutiques Maketou
        print("\n📦 Étape 2: Découverte de TOUTES les boutiques MAKETOU...")
        print("-" * 70)
        maketou_shops = await discovery.discover_maketou_shops()
        print(f"\n✅ {len(maketou_shops)} boutiques Maketou découvertes au total")
        
        # Scraper les boutiques Chariow
        print(f"\n📦 Étape 3: Scraping des {len(chariow_shops)} boutiques CHARIOW...")
        print("-" * 70)
        chariow_scraper = ChariowScraper()
        total_chariow_products = 0
        
        for i, shop_url in enumerate(chariow_shops, 1):
            print(f"\n[{i}/{len(chariow_shops)}]")
            count = await scrape_and_save_shop(shop_url, 'chariow', chariow_scraper, db)
            total_chariow_products += count
            await asyncio.sleep(3)  # Pause entre les boutiques
        
        # Scraper les boutiques Maketou
        print(f"\n📦 Étape 4: Scraping des {len(maketou_shops)} boutiques MAKETOU...")
        print("-" * 70)
        maketou_scraper = MaketouScraper()
        total_maketou_products = 0
        
        for i, shop_url in enumerate(maketou_shops, 1):
            print(f"\n[{i}/{len(maketou_shops)}]")
            count = await scrape_and_save_shop(shop_url, 'maketou', maketou_scraper, db)
            total_maketou_products += count
            await asyncio.sleep(3)  # Pause entre les boutiques
        
        # Résumé final
        print(f"\n{'='*70}")
        print(f"✅ SCRAPING TERMINÉ!")
        print(f"{'='*70}")
        print(f"Boutiques Chariow scrapées: {len(chariow_shops)}")
        print(f"Produits Chariow ajoutés: {total_chariow_products}")
        print(f"Boutiques Maketou scrapées: {len(maketou_shops)}")
        print(f"Produits Maketou ajoutés: {total_maketou_products}")
        print(f"Total produits ajoutés: {total_chariow_products + total_maketou_products}")
        print(f"{'='*70}")
        print(f"\n🎉 Tous les produits sont maintenant disponibles sur le dashboard!")
    
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())


et ajouter leurs produits au dashboard
"""
import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

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
from services.discovery import MarketplaceDiscovery
from utils.scoring import calculate_product_score, calculate_shop_score

def normalize_shop_url(url: str, marketplace: str) -> str:
    """
    Normalise une URL de boutique en ne gardant que le domaine racine
    (évite de traiter des pages produit/checkout comme des boutiques).
    """
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        # S'assurer que le domaine correspond au marketplace attendu
        host = parsed.netloc.lower()
        if marketplace == 'chariow' and 'mychariow.shop' not in host:
            return ""
        if marketplace == 'maketou' and 'mymaketou.store' not in host:
            return ""
        # Conserver seulement schéma + netloc
        normalized = urlunparse((parsed.scheme or 'https', host, '', '', '', ''))
        return normalized.rstrip('/')
    except Exception:
        return ""

async def discover_shops_from_search(marketplace: str) -> list:
    """Découvre des boutiques en cherchant sur Google ou directement sur les marketplaces"""
    shop_urls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            if marketplace == 'chariow':
                # Chercher des boutiques Chariow
                search_urls = [
                    "https://www.google.com/search?q=site:mychariow.shop",
                    "https://chariow.com",
                ]
            else:  # maketou
                # Chercher des boutiques Maketou
                search_urls = [
                    "https://www.google.com/search?q=site:mymaketou.store",
                    "https://maketou.com",
                ]
            
            for search_url in search_urls:
                try:
                    print(f"🔍 Exploration: {search_url}")
                    await page.goto(search_url, wait_until="networkidle", timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    content = await page.content()
                    try:
                        soup = BeautifulSoup(content, 'lxml')
                    except:
                        soup = BeautifulSoup(content, 'html.parser')
                    
                    # Chercher tous les liens
                    all_links = soup.find_all('a', href=True)
                    
                    for link in all_links:
                        href = link.get('href', '')
                        if not href:
                            continue
                        
                        # Convertir en URL absolue
                        if not href.startswith('http'):
                            href = urljoin(search_url, href)
                        
                        # Normaliser au domaine racine
                        clean_url = normalize_shop_url(href, marketplace)
                        if not clean_url:
                            continue
                        
                        if clean_url not in shop_urls:
                            shop_urls.append(clean_url)
                            print(f"  ✅ Boutique {marketplace} trouvée: {clean_url}")
                    
                    # Scroll pour charger plus
                    for i in range(2):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(2000)
                        
                        content = await page.content()
                        try:
                            soup = BeautifulSoup(content, 'lxml')
                        except:
                            soup = BeautifulSoup(content, 'html.parser')
                        
                        all_links = soup.find_all('a', href=True)
                        for link in all_links:
                            href = link.get('href', '')
                            if not href:
                                continue
                            if not href.startswith('http'):
                                href = urljoin(search_url, href)
                            
                            clean_url = normalize_shop_url(href, marketplace)
                            if not clean_url:
                                continue
                            
                            if clean_url not in shop_urls:
                                shop_urls.append(clean_url)
                                print(f"  ✅ Boutique {marketplace} trouvée: {clean_url}")
                    
                    await asyncio.sleep(2)
                
                except Exception as e:
                    print(f"  ⚠️ Erreur sur {search_url}: {e}")
                    continue
        
        finally:
            await browser.close()
    
    return shop_urls

async def discover_shops_from_known_shops(marketplace: str, known_shops: list) -> list:
    """Découvre plus de boutiques en explorant les boutiques connues"""
    shop_urls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for shop_url in known_shops:
            try:
                print(f"🔍 Exploration depuis: {shop_url}")
                await page.goto(shop_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)
                
                content = await page.content()
                try:
                    soup = BeautifulSoup(content, 'lxml')
                except:
                    soup = BeautifulSoup(content, 'html.parser')
                
                # Chercher tous les liens
                all_links = soup.find_all('a', href=True)
                
                for link in all_links:
                    href = link.get('href', '')
                    if not href:
                        continue
                    
                    if not href.startswith('http'):
                        href = urljoin(shop_url, href)
                    
                    clean_url = normalize_shop_url(href, marketplace)
                    if not clean_url or clean_url == shop_url.rstrip('/'):
                        continue
                    
                    if clean_url not in shop_urls:
                        shop_urls.append(clean_url)
                        print(f"  ✅ Boutique trouvée: {clean_url}")
                
                await asyncio.sleep(2)
            
            except Exception as e:
                print(f"  ⚠️ Erreur: {e}")
                continue
        
        await browser.close()
    
    return shop_urls

def is_product_complete(product_data: dict) -> bool:
    """Vérifie qu'un produit a toutes les données requises"""
    if not product_data.get('name') or not product_data.get('name').strip():
        return False
    if not product_data.get('url') or not product_data.get('url').startswith('http'):
        return False
    if not product_data.get('image') or not (product_data.get('image').startswith('http') or product_data.get('image').startswith('//')):
        return False
    return True

async def scrape_and_save_shop(shop_url: str, marketplace: str, scraper_instance, db):
    """Scrape une boutique et sauvegarde ses produits"""
    try:
        print(f"\n🏪 Scraping boutique: {shop_url}")
        shop_data = await scraper_instance.scrape_async(shop_url)
        
        if not shop_data:
            print(f"  ⚠️ Aucune donnée récupérée")
            return 0
        
        if not shop_data.get('products'):
            print(f"  ⚠️ Aucun produit trouvé")
            return 0
        
        print(f"  📦 {len(shop_data.get('products', []))} produits trouvés")

        from app.models import ProductGlobal, ShopGlobal
        marketplace_value = marketplace.lower()
        
        # Sauvegarder ou mettre à jour la boutique
        existing_shop = db.query(ShopGlobal).filter(ShopGlobal.shop_url == shop_url).first()
        
        shop_score = calculate_shop_score(shop_data) if shop_data else 70
        
        if existing_shop:
            existing_shop.shop_name = shop_data.get('name', existing_shop.shop_name)
            existing_shop.score_global = shop_score
            existing_shop.last_scraped_at = datetime.now()
        else:
            new_shop = ShopGlobal(
                marketplace=marketplace_value,
                shop_name=shop_data.get('name', 'Boutique'),
                shop_url=shop_url,
                score_global=shop_score,
                revenue_est_min=0,
                revenue_est_max=0,
                winners_count=0,
                last_scraped_at=datetime.now()
            )
            db.add(new_shop)
        
        # Sauvegarder les produits complets
        saved_count = 0
        for product in shop_data.get('products', []):
            if not is_product_complete(product):
                continue
            
            # Vérifier si le produit existe déjà
            existing_product = db.query(ProductGlobal).filter(
                ProductGlobal.product_url == product.get('url')
            ).first()
            
            product_score = calculate_product_score({
                "name": product.get('name'),
                "url": product.get('url'),
                "marketplace": marketplace,
                "estimated_daily_sales": 8,
                "ideal_price": product.get('price', 0),
                "competition_level": "Moyen",
                "trend": "stable"
            })
            
            if existing_product:
                # Mettre à jour
                existing_product.product_name = product.get('name')
                existing_product.product_image = product.get('image')
                existing_product.product_description = product.get('description', '')
                existing_product.price = product.get('price', 0)
                existing_product.score_winner = product_score
                existing_product.last_scraped_at = datetime.now()
            else:
                # Créer nouveau
                new_product = ProductGlobal(
                    marketplace=marketplace_value,
                    product_name=product.get('name'),
                    shop_name=shop_data.get('name', 'Boutique'),
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
                saved_count += 1
        
        db.commit()
        print(f"  ✅ {saved_count} nouveaux produits sauvegardés")
        return saved_count
    
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 0

async def main():
    """Fonction principale - Découvre et scrape TOUTES les boutiques Chariow et Maketou"""
    print("🚀 Découverte et scraping automatique de TOUTES les boutiques Chariow et Maketou")
    print("=" * 70)
    
    db = SessionLocal()
    discovery = MarketplaceDiscovery()
    
    try:
        # Découvrir TOUTES les boutiques Chariow
        print("\n📦 Étape 1: Découverte de TOUTES les boutiques CHARIOW...")
        print("-" * 70)
        chariow_shops = await discovery.discover_chariow_shops()
        print(f"\n✅ {len(chariow_shops)} boutiques Chariow découvertes au total")
        
        # Découvrir TOUTES les boutiques Maketou
        print("\n📦 Étape 2: Découverte de TOUTES les boutiques MAKETOU...")
        print("-" * 70)
        maketou_shops = await discovery.discover_maketou_shops()
        print(f"\n✅ {len(maketou_shops)} boutiques Maketou découvertes au total")
        
        # Scraper les boutiques Chariow
        print(f"\n📦 Étape 3: Scraping des {len(chariow_shops)} boutiques CHARIOW...")
        print("-" * 70)
        chariow_scraper = ChariowScraper()
        total_chariow_products = 0
        
        for i, shop_url in enumerate(chariow_shops, 1):
            print(f"\n[{i}/{len(chariow_shops)}]")
            count = await scrape_and_save_shop(shop_url, 'chariow', chariow_scraper, db)
            total_chariow_products += count
            await asyncio.sleep(3)  # Pause entre les boutiques
        
        # Scraper les boutiques Maketou
        print(f"\n📦 Étape 4: Scraping des {len(maketou_shops)} boutiques MAKETOU...")
        print("-" * 70)
        maketou_scraper = MaketouScraper()
        total_maketou_products = 0
        
        for i, shop_url in enumerate(maketou_shops, 1):
            print(f"\n[{i}/{len(maketou_shops)}]")
            count = await scrape_and_save_shop(shop_url, 'maketou', maketou_scraper, db)
            total_maketou_products += count
            await asyncio.sleep(3)  # Pause entre les boutiques
        
        # Résumé final
        print(f"\n{'='*70}")
        print(f"✅ SCRAPING TERMINÉ!")
        print(f"{'='*70}")
        print(f"Boutiques Chariow scrapées: {len(chariow_shops)}")
        print(f"Produits Chariow ajoutés: {total_chariow_products}")
        print(f"Boutiques Maketou scrapées: {len(maketou_shops)}")
        print(f"Produits Maketou ajoutés: {total_maketou_products}")
        print(f"Total produits ajoutés: {total_chariow_products + total_maketou_products}")
        print(f"{'='*70}")
        print(f"\n🎉 Tous les produits sont maintenant disponibles sur le dashboard!")
    
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())

