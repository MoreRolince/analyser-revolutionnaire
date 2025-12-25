"""
Scraper pour les boutiques et produits Systeme.io
"""
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re
import asyncio
from urllib.parse import urlparse, urljoin

class SystemioScraper:
    """Scraper pour les boutiques et produits Systeme.io"""
    
    def __init__(self):
        self.marketplace = "systeme.io"
        self.base_url = "https://systeme.io"
    
    async def scrape_shop(self, shop_url: str) -> Dict[str, Any]:
        """
        Scrape une boutique Systeme.io complète
        Pattern boutique: https://<nom>.systeme.io
        """
        # Normaliser l'URL (enlever les slashes finaux)
        shop_url = shop_url.rstrip('/')
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            page = await browser.new_page()
            
            try:
                print(f"  📦 Chargement boutique: {shop_url}")
                await page.goto(shop_url, wait_until="networkidle", timeout=60000)
                
                # Attendre que le contenu charge
                print(f"  ⏳ Attente du chargement...")
                await page.wait_for_timeout(3000)
                
                # Scroll pour charger le contenu dynamique
                for scroll_attempt in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                    await page.evaluate("window.scrollTo(0, 0)")
                    await page.wait_for_timeout(1000)
                
                # Récupérer le contenu
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extraire le nom de la boutique
                shop_name = "Boutique Systeme.io"
                title_elem = soup.find('title')
                if title_elem:
                    shop_name = title_elem.get_text(strip=True).split('|')[0].strip()
                
                # Chercher les produits
                products = []
                
                # Méthode 1: Chercher dans les liens produits (structure Systeme.io)
                product_links = soup.find_all('a', href=True)
                seen_urls = set()
                
                for link in product_links:
                    href = link.get('href', '')
                    if not href:
                        continue
                    
                    # Convertir en URL absolue
                    if href.startswith('/'):
                        href = urljoin(shop_url, href)
                    elif not href.startswith('http'):
                        continue
                    
                    # Détecter les liens de produits (pas de /fr, /about, etc.)
                    parsed_link = urlparse(href)
                    if parsed_link.netloc == urlparse(shop_url).netloc:
                        path = parsed_link.path.strip('/')
                        # Ignorer les pages spéciales
                        if path and path not in ['fr', 'en', 'about', 'contact', 'cgv', 'mentions-legales', '']:
                            # Probablement un produit ou une page produit
                            if href not in seen_urls:
                                seen_urls.add(href)
                                
                                # Essayer de scraper le produit depuis la carte
                                product_data = self._extract_product_from_link(link, href, shop_url)
                                if product_data:
                                    products.append(product_data)
                
                # Méthode 2: Chercher dans les cartes produits
                product_cards = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'product|card|item', re.I))
                
                for card in product_cards:
                    # Chercher le lien produit dans la carte
                    card_link = card.find('a', href=True)
                    if card_link:
                        href = card_link.get('href', '')
                        if href.startswith('/'):
                            href = urljoin(shop_url, href)
                        
                        if href and href not in seen_urls:
                            seen_urls.add(href)
                            product_data = self._extract_product_from_card(card, href, shop_url)
                            if product_data:
                                products.append(product_data)
                
                # Déduplication finale
                unique_products = []
                seen = set()
                for p in products:
                    url = p.get('product_url') or p.get('url')
                    if url and url not in seen:
                        seen.add(url)
                        unique_products.append(p)
                
                print(f"  ✅ {len(unique_products)} produits trouvés")
                
                return {
                    "shop_name": shop_name,
                    "products": unique_products,
                    "product_count": len(unique_products)
                }
                
            except Exception as e:
                print(f"  ❌ Erreur scraping boutique Systeme.io: {e}")
                import traceback
                traceback.print_exc()
                return {
                    "shop_name": "Boutique Systeme.io",
                    "products": [],
                    "product_count": 0
                }
            finally:
                await browser.close()
    
    def _extract_product_from_link(self, link, href: str, shop_url: str) -> Dict[str, Any]:
        """Extrait les données d'un produit depuis un lien"""
        try:
            # Chercher le titre dans le lien ou ses parents
            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                # Chercher dans les éléments enfants
                title_elem = link.find(['h2', 'h3', 'h4', 'span', 'div'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
            
            # Chercher l'image
            img = link.find('img')
            image_url = None
            if img:
                image_url = img.get('src') or img.get('data-src')
                if image_url and image_url.startswith('/'):
                    image_url = urljoin(shop_url, image_url)
            
            if not title or len(title) < 3:
                return None
            
            return {
                "product_title": title,
                "product_name": title,
                "title": title,
                "product_url": href,
                "url": href,
                "product_image": image_url,
                "image": image_url,
                "price": None,  # À extraire lors du scraping du produit individuel
                "slug": href.split('/')[-1] if href else None
            }
        except:
            return None
    
    def _extract_product_from_card(self, card, href: str, shop_url: str) -> Dict[str, Any]:
        """Extrait les données d'un produit depuis une carte"""
        try:
            # Titre
            title = None
            for tag in ['h1', 'h2', 'h3', 'h4', 'h5']:
                title_elem = card.find(tag)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                title = card.get_text(strip=True)[:100]
            
            # Image
            img = card.find('img')
            image_url = None
            if img:
                image_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if image_url and image_url.startswith('/'):
                    image_url = urljoin(shop_url, image_url)
            
            # Prix (chercher des patterns comme €, $, FCFA)
            price = None
            price_text = card.get_text()
            price_match = re.search(r'([\d\s,]+)\s*(?:€|\$|FCFA|F\s*CFA)', price_text, re.I)
            if price_match:
                price_str = price_match.group(1).replace(',', '').replace(' ', '')
                try:
                    price = float(price_str)
                except:
                    pass
            
            if not title or len(title) < 3:
                return None
            
            return {
                "product_title": title,
                "product_name": title,
                "title": title,
                "product_url": href,
                "url": href,
                "product_image": image_url,
                "image": image_url,
                "price": price,
                "slug": href.split('/')[-1] if href else None
            }
        except:
            return None
    
    async def scrape_product(self, product_url: str, shop_url: str = "", marketplace: str = "") -> Dict[str, Any]:
        """
        Scrape un produit Systeme.io individuel
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            page = await browser.new_page()
            
            try:
                await page.goto(product_url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(2000)
                
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Titre
                title = None
                for tag in ['h1', 'h2']:
                    title_elem = soup.find(tag)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        break
                
                if not title:
                    title_elem = soup.find('title')
                    if title_elem:
                        title = title_elem.get_text(strip=True).split('|')[0].strip()
                
                # Image
                image_url = None
                img = soup.find('img')
                if img:
                    image_url = img.get('src') or img.get('data-src')
                
                # Prix
                price = None
                price_elem = soup.find(string=re.compile(r'€|\$|FCFA|F\s*CFA', re.I))
                if price_elem:
                    price_match = re.search(r'([\d\s,]+)', str(price_elem))
                    if price_match:
                        try:
                            price = float(price_match.group(1).replace(',', '').replace(' ', ''))
                        except:
                            pass
                
                # Description
                description = None
                desc_elem = soup.find('meta', attrs={'name': 'description'})
                if desc_elem:
                    description = desc_elem.get('content', '')
                else:
                    # Chercher dans le contenu
                    desc_elem = soup.find(['div', 'p'], class_=re.compile(r'description|content', re.I))
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)[:500]
                
                return {
                    "title": title or "Produit Systeme.io",
                    "product_title": title or "Produit Systeme.io",
                    "product_name": title or "Produit Systeme.io",
                    "product_url": product_url,
                    "url": product_url,
                    "product_image": image_url,
                    "image": image_url,
                    "price": price,
                    "description": description
                }
                
            except Exception as e:
                print(f"  ❌ Erreur scraping produit Systeme.io: {e}")
                return {
                    "title": "Produit Systeme.io",
                    "product_url": product_url,
                    "price": None
                }
            finally:
                await browser.close()
