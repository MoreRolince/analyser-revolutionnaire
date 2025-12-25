"""
Analyseur de landing pages - Détecte et extrait les données des produits digitaux
"""
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List
import re
from urllib.parse import urlparse, urljoin
from datetime import datetime
import sys
import os

# Ajouter le chemin pour importer les scrapers spécifiques
current_dir = os.path.dirname(os.path.abspath(__file__))
scraper_dir = os.path.dirname(current_dir)
if scraper_dir not in sys.path:
    sys.path.insert(0, scraper_dir)

try:
    from services.chariow_scraper import ChariowScraper
    from services.maketou_scraper import MaketouScraper
    SCRAPERS_AVAILABLE = True
except ImportError:
    SCRAPERS_AVAILABLE = False


class LandingPageAnalyzer:
    """Analyse les landing pages pour détecter les produits digitaux"""
    
    # Domaines de produits digitaux
    DIGITAL_PRODUCT_DOMAINS = [
        'maketou.com', 'mymaketou.store',
        'chariow.com', 'mychariow.shop',
        'systeme.io', 'gumroad.com', 'payhip.com',
        'notion.so', 'drive.google.com'
    ]
    
    def __init__(self):
        self.analyzed_pages: List[str] = []
    
    async def analyze_landing_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Analyse une landing page pour détecter si c'est un produit digital
        Utilise les scrapers spécifiques pour Chariow et Maketou si disponibles
        """
        try:
            if not self._is_digital_product_domain(url):
                return None
            
            # Utiliser les scrapers spécifiques pour une meilleure précision
            if SCRAPERS_AVAILABLE:
                if 'mychariow.shop' in url or 'chariow.com' in url:
                    try:
                        scraper = ChariowScraper()
                        product_data = await scraper.scrape_product(url, "", "")
                        if product_data and product_data.get('price', 0) > 0:
                            return {
                                "landing_page_url": url,
                                "product_title": product_data.get('title') or product_data.get('name', ''),
                                "price": product_data.get('price', 0),
                                "seller_name": product_data.get('shop_name', ''),
                                "description": product_data.get('description', ''),
                                "images": product_data.get('images', []) if isinstance(product_data.get('images'), list) else ([product_data.get('image', '')] if product_data.get('image') else []),
                                "bullet_points": [],
                                "cta_text": "",
                                "social_proof": {},
                                "page_structure": {},
                                "marketplace": "chariow",
                                "analyzed_at": datetime.now().isoformat(),
                            }
                    except Exception as e:
                        print(f"    ⚠️  Erreur scraper Chariow {url}: {e}")
                
                elif 'mymaketou.store' in url or 'maketou.com' in url:
                    try:
                        scraper = MaketouScraper()
                        product_data = await scraper.scrape_product(url, "", "")
                        if product_data and product_data.get('price', 0) > 0:
                            return {
                                "landing_page_url": url,
                                "product_title": product_data.get('title') or product_data.get('name', ''),
                                "price": product_data.get('price', 0),
                                "seller_name": product_data.get('shop_name', ''),
                                "description": product_data.get('description', ''),
                                "images": product_data.get('images', []) if isinstance(product_data.get('images'), list) else ([product_data.get('image', '')] if product_data.get('image') else []),
                                "bullet_points": [],
                                "cta_text": "",
                                "social_proof": {},
                                "page_structure": {},
                                "marketplace": "maketou",
                                "analyzed_at": datetime.now().isoformat(),
                            }
                    except Exception as e:
                        print(f"    ⚠️  Erreur scraper Maketou {url}: {e}")
            
            # Fallback sur l'analyseur générique
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                page = await browser.new_page()
                
                try:
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    product_data = {
                        "landing_page_url": url,
                        "product_title": self._extract_title(soup, url),
                        "price": self._extract_price(soup, url),
                        "seller_name": self._extract_seller_name(soup, url),
                        "description": self._extract_description(soup),
                        "images": self._extract_images(soup, url),
                        "bullet_points": self._extract_bullet_points(soup),
                        "cta_text": self._extract_cta(soup),
                        "social_proof": self._extract_social_proof(soup),
                        "page_structure": self._analyze_page_structure(soup),
                        "marketplace": self._detect_marketplace(url),
                        "analyzed_at": datetime.now().isoformat(),
                    }
                    
                    if product_data["product_title"] and product_data["price"] > 0:
                        return product_data
                    return None
                except Exception as e:
                    print(f"    ⚠️  Erreur analyse {url}: {e}")
                    return None
                finally:
                    await browser.close()
        except Exception as e:
            print(f"  ❌ Erreur analyse landing page {url}: {e}")
            return None
    
    def _is_digital_product_domain(self, url: str) -> bool:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(d in domain for d in self.DIGITAL_PRODUCT_DOMAINS)
    
    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        selectors = ['h1', '.product-title', '[class*="title"]', '[class*="heading"]', 'title']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                if title and len(title) > 5:
                    return title[:200]
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            if ' - ' in title:
                title = title.split(' - ')[0]
            return title[:200]
        return ""
    
    def _extract_price(self, soup: BeautifulSoup, url: str = "") -> float:
        """Extrait le prix avec des sélecteurs spécifiques pour chaque marketplace"""
        # Utiliser des scrapers spécifiques si disponibles
        if 'mychariow.shop' in url or 'chariow.com' in url:
            return self._extract_price_chariow(soup)
        elif 'mymaketou.store' in url or 'maketou.com' in url:
            return self._extract_price_maketou(soup)
        else:
            return self._extract_price_generic(soup)
    
    def _extract_price_chariow(self, soup: BeautifulSoup) -> float:
        """Extraction spécifique pour Chariow"""
        # Sélecteurs spécifiques Chariow
        price_selectors = [
            '.product-price',
            '[class*="product-price"]',
            '[class*="price"]',
            '[data-price]',
            'span[class*="price"]',
            'div[class*="price"]',
        ]
        
        for selector in price_selectors:
            elems = soup.select(selector)
            for elem in elems:
                price_text = elem.get_text(strip=True)
                # Patterns pour FCFA
                patterns = [
                    r'(\d+[\s,.]?\d*)\s*(?:FCFA|XOF|francs?)',
                    r'(?:FCFA|XOF|francs?)\s*(\d+[\s,.]?\d*)',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, price_text, re.IGNORECASE)
                    if matches:
                        try:
                            price_str = str(matches[-1]).replace(',', '').replace(' ', '').replace('.', '').strip()
                            price_val = float(price_str)
                            # Filtrer les valeurs suspectes (années, IDs, etc.)
                            if 100 <= price_val <= 1000000:  # Prix raisonnable entre 100 et 1M FCFA
                                return price_val
                        except Exception:
                            continue
        return 0.0
    
    def _extract_price_maketou(self, soup: BeautifulSoup) -> float:
        """Extraction spécifique pour Maketou"""
        # Sélecteurs spécifiques Maketou
        price_selectors = [
            '.product-price',
            '[class*="product-price"]',
            '[class*="price"]',
            '[data-price]',
            'span[class*="price"]',
            'div[class*="price"]',
        ]
        
        for selector in price_selectors:
            elems = soup.select(selector)
            for elem in elems:
                price_text = elem.get_text(strip=True)
                # Patterns pour FCFA
                patterns = [
                    r'(\d+[\s,.]?\d*)\s*(?:FCFA|XOF|francs?)',
                    r'(?:FCFA|XOF|francs?)\s*(\d+[\s,.]?\d*)',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, price_text, re.IGNORECASE)
                    if matches:
                        try:
                            price_str = str(matches[-1]).replace(',', '').replace(' ', '').replace('.', '').strip()
                            price_val = float(price_str)
                            # Filtrer les valeurs suspectes
                            if 100 <= price_val <= 1000000:
                                return price_val
                        except Exception:
                            continue
        return 0.0
    
    def _extract_price_generic(self, soup: BeautifulSoup) -> float:
        """Extraction générique pour les autres marketplaces"""
        price_text = ""
        selectors = ['.price', '[class*="price"]', '[class*="amount"]', '[data-price]', '[data-amount]']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                price_text = elem.get_text()
                break
        if not price_text:
            price_text = soup.get_text()
        patterns = [
            r'(\d+[\s,.]?\d*)\s*(?:FCFA|XOF|€|\$|EUR)',
            r'(?:FCFA|XOF|€|\$|EUR)\s*(\d+[\s,.]?\d*)',
            r'\$(\d+[\s,.]?\d*\.?\d*)',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, price_text)
            if matches:
                try:
                    price_str = str(matches[-1]).replace(',', '').replace(' ', '').strip()
                    price_val = float(price_str)
                    # Filtrer les valeurs suspectes (années, IDs, etc.)
                    if price_val < 100 or price_val > 1000000:
                        continue
                    if '$' in price_text or (price_val < 100 and '.' in price_str):
                        price_val = price_val * 600  # Approx conversion USD->FCFA
                    return price_val
                except Exception:
                    continue
        return 0.0
    
    def _extract_seller_name(self, soup: BeautifulSoup, url: str) -> str:
        selectors = ['.seller', '[class*="seller"]', '[class*="vendor"]', '[class*="author"]', '[class*="creator"]']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                seller = elem.get_text(strip=True)
                if seller:
                    return seller[:100]
        parsed = urlparse(url)
        netloc = parsed.netloc
        if 'mymaketou.store' in netloc or 'mychariow.shop' in netloc:
            seller = netloc.split('.')[0]
            return seller.replace('-', ' ').title()
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        selectors = [
            '.description', '[class*="description"]', '[class*="desc"]',
            '.product-description', '[class*="product-description"]',
            'meta[name="description"]'
        ]
        for selector in selectors:
            if selector.startswith('meta'):
                meta = soup.find('meta', attrs={'name': 'description'})
                if meta and meta.get('content'):
                    return meta['content'][:800]
            elem = soup.select_one(selector)
            if elem:
                desc = elem.get_text(strip=True)
                if desc and len(desc) > 20:
                    return desc[:800]
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 30:
                return text[:800]
        return ""
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        images: List[str] = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if not src:
                continue
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = urljoin(base_url, src)
            if src.startswith('http'):
                images.append(src)
        return list(dict.fromkeys(images))[:10]
    
    def _extract_bullet_points(self, soup: BeautifulSoup) -> List[str]:
        bullet_points: List[str] = []
        for ul in soup.find_all('ul'):
            items = [li.get_text(strip=True) for li in ul.find_all('li')]
            items = [i for i in items if len(i) > 3]
            if len(items) >= 2:
                bullet_points.extend(items)
        return bullet_points[:12]
    
    def _extract_cta(self, soup: BeautifulSoup) -> str:
        selectors = [
            'a[href*="checkout"]',
            'a[href*="buy"]',
            'a[href*="order"]',
            'button',
            '[class*="cta"]',
        ]
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text and len(text) > 2:
                    return text[:60]
        return ""
    
    def _extract_social_proof(self, soup: BeautifulSoup) -> Dict[str, Any]:
        text = soup.get_text(" ", strip=True)
        reviews = re.findall(r'(\d+)\s*(avis|reviews|évaluations)', text, re.I)
        rating = re.findall(r'(\d[\.,]?\d?)\s*/\s*5', text)
        return {
            "reviews_count": int(reviews[0][0]) if reviews else 0,
            "rating": float(rating[0].replace(',', '.')) if rating else None,
        }
    
    def _analyze_page_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        return {
            "images_count": len(self._extract_images(soup, "")),
            "paragraphs_count": len(soup.find_all('p')),
            "headings_count": len(soup.find_all(['h1', 'h2', 'h3'])),
        }
    
    def _detect_marketplace(self, url: str) -> str:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if 'maketou' in domain:
            return 'maketou'
        if 'chariow' in domain:
            return 'chariow'
        if 'systeme.io' in domain:
            return 'systeme.io'
        if 'gumroad' in domain:
            return 'gumroad'
        if 'payhip' in domain:
            return 'payhip'
        return 'other'

