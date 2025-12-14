"""
Analyseur de landing pages - Détecte et extrait les données des produits digitaux
"""
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List
import re
from urllib.parse import urlparse, urljoin
from datetime import datetime


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
        """
        try:
            if not self._is_digital_product_domain(url):
                return None
            
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
                        "price": self._extract_price(soup),
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
    
    def _extract_price(self, soup: BeautifulSoup) -> float:
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
            r'(\d+[\s,.]?\d*\.?\d*)',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, price_text)
            if matches:
                try:
                    price_str = str(matches[-1]).replace(',', '').replace(' ', '').strip()
                    price_val = float(price_str)
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

