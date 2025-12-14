"""
Scraper Maketou - Détection exacte des produits via pattern /products/
"""
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
import re
import asyncio
from urllib.parse import urljoin, urlparse
from datetime import datetime


class MaketouScraper:
    """Scraper pour les boutiques et produits Maketou"""
    
    def __init__(self):
        self.marketplace = "maketou"
        self.base_url = "https://maketou.com"
        # Pattern pour détecter les produits Maketou
        self.product_pattern = re.compile(r'/products/([a-zA-Z0-9\-]+)')
    
    async def scrape_shop(self, shop_url: str) -> Dict[str, Any]:
        """
        Scrape une boutique Maketou complète
        Pattern boutique: https://<nom>.mymaketou.store/fr
        """
        # Normaliser l'URL de la boutique
        if not shop_url.endswith('/fr'):
            if shop_url.endswith('/'):
                shop_url = shop_url + 'fr'
            else:
                shop_url = shop_url + '/fr'
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            page = await browser.new_page()
            
            try:
                print(f"  📦 Chargement boutique: {shop_url}")
                await page.goto(shop_url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(3000)  # Attendre le chargement JS
                
                # Scroll multiple pour charger tout le contenu dynamique
                for scroll_attempt in range(5):
                    content_before = len(await page.content())
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                    await page.evaluate("window.scrollTo(0, 0)")
                    await page.wait_for_timeout(1000)
                    content_after = len(await page.content())
                    if content_before == content_after:
                        break
                
                content = await page.content()
                try:
                    soup = BeautifulSoup(content, 'lxml')
                except:
                    soup = BeautifulSoup(content, 'html.parser')
                
                # Extraire le nom de la boutique
                shop_name = self._extract_shop_name(soup, shop_url)
                
                # Détecter TOUS les produits via le pattern /products/
                product_urls = self._find_product_urls(soup, shop_url)
                
                print(f"  ✅ {len(product_urls)} produits détectés")
                
                # Scraper chaque produit
                products = []
                for i, product_url in enumerate(product_urls, 1):
                    try:
                        print(f"    [{i}/{len(product_urls)}] Scraping: {product_url[:60]}...")
                        product_data = await self.scrape_product(product_url, shop_name, shop_url)
                        if product_data:
                            products.append(product_data)
                        await asyncio.sleep(1)  # Pause entre les produits
                    except Exception as e:
                        print(f"    ❌ Erreur produit {product_url}: {e}")
                        continue
                
                return {
                    "shop_name": shop_name,
                    "shop_url": shop_url,
                    "marketplace": self.marketplace,
                    "product_count": len(products),
                    "products": products,
                    "scraped_at": datetime.now().isoformat()
                }
                
            finally:
                await browser.close()
    
    def _extract_shop_name(self, soup: BeautifulSoup, shop_url: str) -> str:
        """Extrait le nom de la boutique"""
        name_selectors = [
            'h1',
            '.shop-name',
            '.store-name',
            'title',
            '[class*="shop"] h1',
            '[class*="store"] h1'
        ]
        
        for selector in name_selectors:
            elem = soup.select_one(selector)
            if elem:
                name = elem.get_text(strip=True)
                if name and len(name) > 2:
                    # Nettoyer le nom (enlever " - Ma boutique" etc.)
                    if ' - ' in name:
                        name = name.split(' - ')[0].strip()
                    return name
        
        # Fallback: extraire depuis l'URL
        parsed = urlparse(shop_url)
        shop_name = parsed.netloc.split('.')[0].replace('-', ' ').title()
        return shop_name
    
    def _find_product_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Trouve TOUS les URLs de produits via le pattern /products/
        Pattern: https://<boutique>.mymaketou.store/products/<slug>
        """
        product_urls = set()
        parsed_base = urlparse(base_url)
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
        
        # Méthode 1: Chercher tous les liens contenant /products/
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            if not href:
                continue
            
            # Vérifier si le lien contient le pattern /products/
            if '/products/' in href:
                # Convertir en URL absolue
                if not href.startswith('http'):
                    if href.startswith('/'):
                        href = base_domain + href
                    else:
                        href = urljoin(base_url, href)
                
                # Nettoyer l'URL (enlever les paramètres de requête et fragments)
                href = href.split('?')[0].split('#')[0]
                
                # Vérifier que c'est bien un produit (pas /products/ seul)
                if '/products/' in href and href != f"{base_domain}/products/":
                    product_urls.add(href)
        
        # Méthode 2: Chercher dans le texte de la page (pour les URLs dans le JS)
        page_text = str(soup)
        products_matches = re.findall(r'/products/([a-zA-Z0-9\-]+)', page_text)
        for product_slug in products_matches:
            product_url = f"{base_domain}/products/{product_slug}"
            product_urls.add(product_url)
        
        # Méthode 3: Chercher dans les attributs data-*
        for elem in soup.find_all(attrs=True):
            for attr, value in elem.attrs.items():
                if isinstance(value, str) and '/products/' in value:
                    if not value.startswith('http'):
                        if value.startswith('/'):
                            value = base_domain + value
                        else:
                            value = urljoin(base_url, value)
                    value = value.split('?')[0].split('#')[0]
                    if '/products/' in value and value != f"{base_domain}/products/":
                        product_urls.add(value)
        
        return sorted(list(product_urls))
    
    async def scrape_product(self, product_url: str, shop_name: str = "", shop_url: str = "") -> Optional[Dict[str, Any]]:
        """
        Scrape un produit Maketou individuel
        Pattern: https://<boutique>.mymaketou.store/products/<slug>
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            page = await browser.new_page()
            
            try:
                await page.goto(product_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)
                
                content = await page.content()
                try:
                    soup = BeautifulSoup(content, 'lxml')
                except:
                    soup = BeautifulSoup(content, 'html.parser')
                
                # Extraire le slug du produit depuis l'URL
                match = self.product_pattern.search(product_url)
                product_id = match.group(1) if match else product_url.split('/products/')[-1] if '/products/' in product_url else None
                
                # Extraire toutes les données
                title = self._extract_title(soup)
                price = self._extract_price(soup)
                description = self._extract_description(soup)
                images = self._extract_images(soup, product_url)
                category = self._extract_category(soup)
                rating = self._extract_rating(soup)
                reviews_count = self._extract_reviews_count(soup)
                date_added = self._extract_date_added(soup)
                
                # Si pas de titre, le produit n'est pas valide
                if not title:
                    return None
                
                return {
                    "id": product_id or product_url,
                    "url": product_url,
                    "title": title,
                    "price": price,
                    "description": description,
                    "images": images,
                    "category": category,
                    "rating": rating,
                    "reviews_count": reviews_count,
                    "date_added": date_added,
                    "shop_name": shop_name or self._extract_shop_name_from_url(product_url),
                    "shop_url": shop_url or self._get_shop_url_from_product(product_url),
                    "marketplace": self.marketplace,
                    "scraped_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                print(f"      ❌ Erreur scraping produit {product_url}: {e}")
                return None
            finally:
                await browser.close()
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrait le titre du produit"""
        selectors = ['h1', '.product-title', '[class*="title"]', 'title']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                if title and len(title) > 2:
                    return title
        return ""
    
    def _extract_price(self, soup: BeautifulSoup) -> float:
        """Extrait le prix en FCFA"""
        price_text = ""
        price_selectors = [
            '.price',
            '[class*="price"]',
            '[class*="amount"]',
            '[data-price]'
        ]
        
        for selector in price_selectors:
            elem = soup.select_one(selector)
            if elem:
                price_text = elem.get_text()
                break
        
        if not price_text:
            price_text = soup.get_text()
        
        # Patterns de prix (Maketou utilise souvent $)
        patterns = [
            r'\$(\d+[\s,.]?\d*\.?\d*)',
            r'(\d+[\s,.]?\d*)\s*(?:FCFA|XOF)',
            r'(?:FCFA|XOF)\s*(\d+[\s,.]?\d*)',
            r'(\d+[\s,.]?\d*\.?\d*)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, price_text)
            if matches:
                try:
                    price_str = str(matches[-1]).replace(',', '').replace(' ', '').strip()
                    price_val = float(price_str)
                    # Convertir $ en FCFA (1$ ≈ 600 FCFA)
                    if '$' in price_text or (price_val < 100 and '.' in price_str):
                        price_val = price_val * 600
                    return price_val
                except:
                    continue
        
        return 0.0
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extrait la description du produit"""
        desc_selectors = [
            ('div', {'class': re.compile(r'description|content|detail', re.I)}),
            ('p', {'class': re.compile(r'description|content', re.I)}),
            ('div', {'id': re.compile(r'description|content', re.I)}),
            ('meta', {'name': 'description'}),
        ]
        
        for tag, attrs in desc_selectors:
            if tag == 'meta':
                elem = soup.find('meta', attrs)
                if elem:
                    return elem.get('content', '')[:2000]
            else:
                elem = soup.find(tag, attrs)
                if elem:
                    desc = elem.get_text(strip=True)
                    if len(desc) > 20:
                        return desc[:2000]
        
        return ""
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extrait toutes les images du produit"""
        images = []
        img_selectors = [
            'img[src*="product"]',
            '.product-image img',
            '.product-gallery img',
            '[class*="product"] img',
            'img'
        ]
        
        seen_urls = set()
        for selector in img_selectors:
            imgs = soup.select(selector)
            for img in imgs:
                img_src = (img.get('src', '') or 
                          img.get('data-src', '') or 
                          img.get('data-lazy-src', '') or
                          img.get('data-original', ''))
                
                if img_src:
                    if ' ' in img_src:
                        img_src = img_src.split(' ')[0]
                    
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    elif img_src.startswith('/'):
                        img_src = urljoin(base_url, img_src)
                    elif not img_src.startswith('http'):
                        img_src = urljoin(base_url, img_src)
                    
                    if img_src not in seen_urls and 'placeholder' not in img_src.lower():
                        images.append(img_src)
                        seen_urls.add(img_src)
        
        return images[:10]
    
    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait la catégorie du produit"""
        category_selectors = [
            'a[class*="category"]',
            '[class*="category"]',
            '.breadcrumb a',
            'nav a'
        ]
        
        for selector in category_selectors:
            elem = soup.select_one(selector)
            if elem:
                category = elem.get_text(strip=True)
                if category and len(category) > 2 and category.lower() not in ['home', 'accueil', 'shop', 'boutique']:
                    return category
        
        return None
    
    def _extract_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """Extrait la note/rating du produit"""
        rating_selectors = [
            '[class*="rating"]',
            '[class*="star"]',
            '[data-rating]',
            '.review-rating'
        ]
        
        for selector in rating_selectors:
            elem = soup.select_one(selector)
            if elem:
                rating_text = elem.get_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1))
                        if 0 <= rating <= 5:
                            return rating
                    except:
                        pass
        
        return None
    
    def _extract_reviews_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Extrait le nombre d'avis"""
        review_selectors = [
            '[class*="review"]',
            '[class*="comment"]',
            '[data-reviews]'
        ]
        
        for selector in review_selectors:
            elem = soup.select_one(selector)
            if elem:
                review_text = elem.get_text()
                review_match = re.search(r'(\d+)', review_text)
                if review_match:
                    try:
                        return int(review_match.group(1))
                    except:
                        pass
        
        return None
    
    def _extract_date_added(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait la date d'ajout du produit"""
        date_selectors = [
            '[class*="date"]',
            '[class*="created"]',
            'time'
        ]
        
        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                date_text = elem.get_text() or elem.get('datetime', '')
                if date_text:
                    return date_text
        
        return None
    
    def _extract_shop_name_from_url(self, product_url: str) -> str:
        """Extrait le nom de la boutique depuis l'URL du produit"""
        parsed = urlparse(product_url)
        shop_name = parsed.netloc.split('.')[0].replace('-', ' ').title()
        return shop_name
    
    def _get_shop_url_from_product(self, product_url: str) -> str:
        """Construit l'URL de la boutique depuis l'URL du produit"""
        parsed = urlparse(product_url)
        shop_url = f"{parsed.scheme}://{parsed.netloc}/fr"
        return shop_url


"""
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
import re
import asyncio
from urllib.parse import urljoin, urlparse
from datetime import datetime


class MaketouScraper:
    """Scraper pour les boutiques et produits Maketou"""
    
    def __init__(self):
        self.marketplace = "maketou"
        self.base_url = "https://maketou.com"
        # Pattern pour détecter les produits Maketou
        self.product_pattern = re.compile(r'/products/([a-zA-Z0-9\-]+)')
    
    async def scrape_shop(self, shop_url: str) -> Dict[str, Any]:
        """
        Scrape une boutique Maketou complète
        Pattern boutique: https://<nom>.mymaketou.store/fr
        """
        # Normaliser l'URL de la boutique
        if not shop_url.endswith('/fr'):
            if shop_url.endswith('/'):
                shop_url = shop_url + 'fr'
            else:
                shop_url = shop_url + '/fr'
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            page = await browser.new_page()
            
            try:
                print(f"  📦 Chargement boutique: {shop_url}")
                await page.goto(shop_url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(3000)  # Attendre le chargement JS
                
                # Scroll multiple pour charger tout le contenu dynamique
                for scroll_attempt in range(5):
                    content_before = len(await page.content())
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                    await page.evaluate("window.scrollTo(0, 0)")
                    await page.wait_for_timeout(1000)
                    content_after = len(await page.content())
                    if content_before == content_after:
                        break
                
                content = await page.content()
                try:
                    soup = BeautifulSoup(content, 'lxml')
                except:
                    soup = BeautifulSoup(content, 'html.parser')
                
                # Extraire le nom de la boutique
                shop_name = self._extract_shop_name(soup, shop_url)
                
                # Détecter TOUS les produits via le pattern /products/
                product_urls = self._find_product_urls(soup, shop_url)
                
                print(f"  ✅ {len(product_urls)} produits détectés")
                
                # Scraper chaque produit
                products = []
                for i, product_url in enumerate(product_urls, 1):
                    try:
                        print(f"    [{i}/{len(product_urls)}] Scraping: {product_url[:60]}...")
                        product_data = await self.scrape_product(product_url, shop_name, shop_url)
                        if product_data:
                            products.append(product_data)
                        await asyncio.sleep(1)  # Pause entre les produits
                    except Exception as e:
                        print(f"    ❌ Erreur produit {product_url}: {e}")
                        continue
                
                return {
                    "shop_name": shop_name,
                    "shop_url": shop_url,
                    "marketplace": self.marketplace,
                    "product_count": len(products),
                    "products": products,
                    "scraped_at": datetime.now().isoformat()
                }
                
            finally:
                await browser.close()
    
    def _extract_shop_name(self, soup: BeautifulSoup, shop_url: str) -> str:
        """Extrait le nom de la boutique"""
        name_selectors = [
            'h1',
            '.shop-name',
            '.store-name',
            'title',
            '[class*="shop"] h1',
            '[class*="store"] h1'
        ]
        
        for selector in name_selectors:
            elem = soup.select_one(selector)
            if elem:
                name = elem.get_text(strip=True)
                if name and len(name) > 2:
                    # Nettoyer le nom (enlever " - Ma boutique" etc.)
                    if ' - ' in name:
                        name = name.split(' - ')[0].strip()
                    return name
        
        # Fallback: extraire depuis l'URL
        parsed = urlparse(shop_url)
        shop_name = parsed.netloc.split('.')[0].replace('-', ' ').title()
        return shop_name
    
    def _find_product_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Trouve TOUS les URLs de produits via le pattern /products/
        Pattern: https://<boutique>.mymaketou.store/products/<slug>
        """
        product_urls = set()
        parsed_base = urlparse(base_url)
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
        
        # Méthode 1: Chercher tous les liens contenant /products/
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            if not href:
                continue
            
            # Vérifier si le lien contient le pattern /products/
            if '/products/' in href:
                # Convertir en URL absolue
                if not href.startswith('http'):
                    if href.startswith('/'):
                        href = base_domain + href
                    else:
                        href = urljoin(base_url, href)
                
                # Nettoyer l'URL (enlever les paramètres de requête et fragments)
                href = href.split('?')[0].split('#')[0]
                
                # Vérifier que c'est bien un produit (pas /products/ seul)
                if '/products/' in href and href != f"{base_domain}/products/":
                    product_urls.add(href)
        
        # Méthode 2: Chercher dans le texte de la page (pour les URLs dans le JS)
        page_text = str(soup)
        products_matches = re.findall(r'/products/([a-zA-Z0-9\-]+)', page_text)
        for product_slug in products_matches:
            product_url = f"{base_domain}/products/{product_slug}"
            product_urls.add(product_url)
        
        # Méthode 3: Chercher dans les attributs data-*
        for elem in soup.find_all(attrs=True):
            for attr, value in elem.attrs.items():
                if isinstance(value, str) and '/products/' in value:
                    if not value.startswith('http'):
                        if value.startswith('/'):
                            value = base_domain + value
                        else:
                            value = urljoin(base_url, value)
                    value = value.split('?')[0].split('#')[0]
                    if '/products/' in value and value != f"{base_domain}/products/":
                        product_urls.add(value)
        
        return sorted(list(product_urls))
    
    async def scrape_product(self, product_url: str, shop_name: str = "", shop_url: str = "") -> Optional[Dict[str, Any]]:
        """
        Scrape un produit Maketou individuel
        Pattern: https://<boutique>.mymaketou.store/products/<slug>
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            page = await browser.new_page()
            
            try:
                await page.goto(product_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)
                
                content = await page.content()
                try:
                    soup = BeautifulSoup(content, 'lxml')
                except:
                    soup = BeautifulSoup(content, 'html.parser')
                
                # Extraire le slug du produit depuis l'URL
                match = self.product_pattern.search(product_url)
                product_id = match.group(1) if match else product_url.split('/products/')[-1] if '/products/' in product_url else None
                
                # Extraire toutes les données
                title = self._extract_title(soup)
                price = self._extract_price(soup)
                description = self._extract_description(soup)
                images = self._extract_images(soup, product_url)
                category = self._extract_category(soup)
                rating = self._extract_rating(soup)
                reviews_count = self._extract_reviews_count(soup)
                date_added = self._extract_date_added(soup)
                
                # Si pas de titre, le produit n'est pas valide
                if not title:
                    return None
                
                return {
                    "id": product_id or product_url,
                    "url": product_url,
                    "title": title,
                    "price": price,
                    "description": description,
                    "images": images,
                    "category": category,
                    "rating": rating,
                    "reviews_count": reviews_count,
                    "date_added": date_added,
                    "shop_name": shop_name or self._extract_shop_name_from_url(product_url),
                    "shop_url": shop_url or self._get_shop_url_from_product(product_url),
                    "marketplace": self.marketplace,
                    "scraped_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                print(f"      ❌ Erreur scraping produit {product_url}: {e}")
                return None
            finally:
                await browser.close()
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrait le titre du produit"""
        selectors = ['h1', '.product-title', '[class*="title"]', 'title']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                if title and len(title) > 2:
                    return title
        return ""
    
    def _extract_price(self, soup: BeautifulSoup) -> float:
        """Extrait le prix en FCFA"""
        price_text = ""
        price_selectors = [
            '.price',
            '[class*="price"]',
            '[class*="amount"]',
            '[data-price]'
        ]
        
        for selector in price_selectors:
            elem = soup.select_one(selector)
            if elem:
                price_text = elem.get_text()
                break
        
        if not price_text:
            price_text = soup.get_text()
        
        # Patterns de prix (Maketou utilise souvent $)
        patterns = [
            r'\$(\d+[\s,.]?\d*\.?\d*)',
            r'(\d+[\s,.]?\d*)\s*(?:FCFA|XOF)',
            r'(?:FCFA|XOF)\s*(\d+[\s,.]?\d*)',
            r'(\d+[\s,.]?\d*\.?\d*)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, price_text)
            if matches:
                try:
                    price_str = str(matches[-1]).replace(',', '').replace(' ', '').strip()
                    price_val = float(price_str)
                    # Convertir $ en FCFA (1$ ≈ 600 FCFA)
                    if '$' in price_text or (price_val < 100 and '.' in price_str):
                        price_val = price_val * 600
                    return price_val
                except:
                    continue
        
        return 0.0
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extrait la description du produit"""
        desc_selectors = [
            ('div', {'class': re.compile(r'description|content|detail', re.I)}),
            ('p', {'class': re.compile(r'description|content', re.I)}),
            ('div', {'id': re.compile(r'description|content', re.I)}),
            ('meta', {'name': 'description'}),
        ]
        
        for tag, attrs in desc_selectors:
            if tag == 'meta':
                elem = soup.find('meta', attrs)
                if elem:
                    return elem.get('content', '')[:2000]
            else:
                elem = soup.find(tag, attrs)
                if elem:
                    desc = elem.get_text(strip=True)
                    if len(desc) > 20:
                        return desc[:2000]
        
        return ""
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extrait toutes les images du produit"""
        images = []
        img_selectors = [
            'img[src*="product"]',
            '.product-image img',
            '.product-gallery img',
            '[class*="product"] img',
            'img'
        ]
        
        seen_urls = set()
        for selector in img_selectors:
            imgs = soup.select(selector)
            for img in imgs:
                img_src = (img.get('src', '') or 
                          img.get('data-src', '') or 
                          img.get('data-lazy-src', '') or
                          img.get('data-original', ''))
                
                if img_src:
                    if ' ' in img_src:
                        img_src = img_src.split(' ')[0]
                    
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    elif img_src.startswith('/'):
                        img_src = urljoin(base_url, img_src)
                    elif not img_src.startswith('http'):
                        img_src = urljoin(base_url, img_src)
                    
                    if img_src not in seen_urls and 'placeholder' not in img_src.lower():
                        images.append(img_src)
                        seen_urls.add(img_src)
        
        return images[:10]
    
    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait la catégorie du produit"""
        category_selectors = [
            'a[class*="category"]',
            '[class*="category"]',
            '.breadcrumb a',
            'nav a'
        ]
        
        for selector in category_selectors:
            elem = soup.select_one(selector)
            if elem:
                category = elem.get_text(strip=True)
                if category and len(category) > 2 and category.lower() not in ['home', 'accueil', 'shop', 'boutique']:
                    return category
        
        return None
    
    def _extract_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """Extrait la note/rating du produit"""
        rating_selectors = [
            '[class*="rating"]',
            '[class*="star"]',
            '[data-rating]',
            '.review-rating'
        ]
        
        for selector in rating_selectors:
            elem = soup.select_one(selector)
            if elem:
                rating_text = elem.get_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1))
                        if 0 <= rating <= 5:
                            return rating
                    except:
                        pass
        
        return None
    
    def _extract_reviews_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Extrait le nombre d'avis"""
        review_selectors = [
            '[class*="review"]',
            '[class*="comment"]',
            '[data-reviews]'
        ]
        
        for selector in review_selectors:
            elem = soup.select_one(selector)
            if elem:
                review_text = elem.get_text()
                review_match = re.search(r'(\d+)', review_text)
                if review_match:
                    try:
                        return int(review_match.group(1))
                    except:
                        pass
        
        return None
    
    def _extract_date_added(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait la date d'ajout du produit"""
        date_selectors = [
            '[class*="date"]',
            '[class*="created"]',
            'time'
        ]
        
        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                date_text = elem.get_text() or elem.get('datetime', '')
                if date_text:
                    return date_text
        
        return None
    
    def _extract_shop_name_from_url(self, product_url: str) -> str:
        """Extrait le nom de la boutique depuis l'URL du produit"""
        parsed = urlparse(product_url)
        shop_name = parsed.netloc.split('.')[0].replace('-', ' ').title()
        return shop_name
    
    def _get_shop_url_from_product(self, product_url: str) -> str:
        """Construit l'URL de la boutique depuis l'URL du produit"""
        parsed = urlparse(product_url)
        shop_url = f"{parsed.scheme}://{parsed.netloc}/fr"
        return shop_url

