from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re
import asyncio
from urllib.parse import urljoin, urlparse

class ChariowScraper:
    def __init__(self):
        self.marketplace = "chariow"
        self.base_url = "https://chariow.com"
    
    async def scrape_async(self, url: str) -> Dict[str, Any]:
        """
        Scrape une page CHARIOW (boutique ou produit)
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Attendre que la page charge complètement
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(2000)  # Attendre 2 secondes pour le JS
                
                content = await page.content()
                # Utiliser html.parser si lxml n'est pas disponible
                try:
                    soup = BeautifulSoup(content, 'lxml')
                except:
                    soup = BeautifulSoup(content, 'html.parser')
                
                # Détecter si c'est une page boutique ou produit
                if self._is_shop_page(soup, url):
                    return await self._scrape_shop(page, soup, url)
                else:
                    return await self._scrape_product(page, soup, url)
                    
            finally:
                await browser.close()
    
    def scrape(self, url: str) -> Dict[str, Any]:
        """Wrapper synchrone"""
        return asyncio.run(self.scrape_async(url))
    
    def _is_shop_page(self, soup: BeautifulSoup, url: str) -> bool:
        """Détecte si c'est une page boutique"""
        # Les URLs Chariow de boutiques contiennent généralement .mychariow.shop
        if '.mychariow.shop' in url.lower() or '/shop' in url.lower():
            return True
        
        # Chercher des indicateurs dans le HTML
        shop_indicators = [
            soup.find('div', class_=re.compile(r'shop|boutique|store|vendor', re.I)),
            soup.find('h1', string=re.compile(r'boutique|shop|store', re.I)),
            soup.find('div', id=re.compile(r'shop|store|vendor', re.I)),
            soup.find_all('div', class_=re.compile(r'product|item|card', re.I))  # Si plusieurs produits, c'est une boutique
        ]
        return any(shop_indicators)
    
    async def _scrape_shop(self, page, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Scrape les données d'une boutique Chariow"""
        data = {
            "name": "",
            "url": url,
            "marketplace": self.marketplace,
            "estimated_revenue": None,
            "estimated_sales": None,
            "product_count": 0,
            "products": [],
            "age": None,
            "growth_rate": 0,
            "strengths": [],
            "weaknesses": []
        }
        
        # Extraire le nom de la boutique
        name_selectors = [
            'h1',
            '.shop-name',
            '.store-name',
            '[class*="shop"] h1',
            '[class*="store"] h1',
            'title'
        ]
        for selector in name_selectors:
            name_elem = soup.select_one(selector)
            if name_elem:
                data["name"] = name_elem.get_text(strip=True)
                break
        
        if not data["name"]:
            # Extraire depuis l'URL
            parsed = urlparse(url)
            data["name"] = parsed.netloc.split('.')[0].replace('-', ' ').title()
        
        # Scraper les produits de la boutique
        # Chercher les produits sur la page avec plusieurs stratégies
        products_found = []

        # Stratégie 1: Sélecteurs CSS spécifiques
        product_selectors = [
            'div[class*="product"]',
            'article[class*="product"]',
            'div[class*="item"]',
            'div[class*="card"]',
            'a[href*="/product"]',
            'a[href*="/p/"]',
            '[data-product]',
            '.product-item',
            '.product-card',
            '.woocommerce-loop-product__link',
            'li.product',
            'div.product',
            '[class*="grid"] [class*="product"]',
            '[class*="grid"] [class*="card"]'
        ]

        for selector in product_selectors:
            products_found = soup.select(selector)
            if products_found:
                break

        # Stratégie 2: Chercher tous les liens qui pourraient être des produits
        if not products_found:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                # Si le lien contient des mots-clés de produit
                if any(keyword in href.lower() for keyword in ['/product', '/p/', '/item', '/produit']):
                    # Chercher le parent ou le conteneur
                    parent = link.find_parent(['div', 'article', 'li'])
                    if parent and parent not in products_found:
                        products_found.append(parent)

        # Stratégie 3: Scroll et recharger
        if len(products_found) < 5:
            try:
                # Scroll plusieurs fois pour charger le contenu dynamique
                for _ in range(4):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)

                    content = await page.content()
                    try:
                        soup = BeautifulSoup(content, 'lxml')
                    except:
                        soup = BeautifulSoup(content, 'html.parser')

                    for selector in product_selectors:
                        found = soup.select(selector)
                        if found and len(found) > len(products_found):
                            products_found = found
                            break
                    if len(products_found) >= 5:
                        break
            except Exception:
                pass

        data["product_count"] = len(products_found)

        # Extraire les détails des produits (augmenter la limite à 80)
        for product_elem in products_found[:80]:
            try:
                product_data = self._extract_product_from_list(product_elem, url)
                if product_data:
                    data["products"].append(product_data)
            except Exception as e:
                print(f"Erreur extraction produit: {e}")
                continue
        
        # Calculer les estimations basées sur les produits réels
        if data["products"]:
            total_price = sum(p.get("price", 0) for p in data["products"] if p.get("price"))
            avg_price = total_price / len(data["products"]) if data["products"] else 0
            
            # Estimation de ventes (basée sur le nombre de produits)
            estimated_monthly_sales = len(data["products"]) * 8  # ~8 ventes/mois par produit
            data["estimated_sales"] = estimated_monthly_sales
            
            # Estimation de revenus
            if avg_price > 0:
                revenue_min = estimated_monthly_sales * avg_price * 0.6
                revenue_max = estimated_monthly_sales * avg_price * 1.2
                data["estimated_revenue"] = f"{revenue_min:,.0f} - {revenue_max:,.0f} FCFA/mois"
            else:
                data["estimated_revenue"] = f"{estimated_monthly_sales * 5000:,.0f} - {estimated_monthly_sales * 15000:,.0f} FCFA/mois"
        else:
            # Estimations par défaut si pas de produits trouvés
            data["estimated_sales"] = 50
            data["estimated_revenue"] = "250,000 - 750,000 FCFA/mois"
        
        # Analyser les points forts/faibles
        if data["product_count"] > 20:
            data["strengths"].append("Large catalogue de produits")
        if data["product_count"] > 10:
            data["strengths"].append("Bonne diversité")
        if data["product_count"] < 5:
            data["weaknesses"].append("Catalogue limité")
        
        # Estimer l'ancienneté (basé sur l'URL ou autres indicateurs)
        data["age"] = "6-12 mois"  # Estimation par défaut
        
        return data
    
    def _extract_product_from_list(self, product_elem, base_url: str) -> Dict[str, Any]:
        """Extrait les données d'un produit depuis la liste"""
        product_data = {
            "name": "",
            "url": "",
            "price": 0,
            "image": ""
        }
        
        # Nom du produit
        name_elem = product_elem.find('h2') or product_elem.find('h3') or product_elem.find('a')
        if name_elem:
            product_data["name"] = name_elem.get_text(strip=True)
        
        # URL du produit - chercher plusieurs façons
        link_elem = product_elem.find('a', href=True)
        if not link_elem:
            # Chercher dans les parents
            parent = product_elem.find_parent('a', href=True)
            if parent:
                link_elem = parent
        
        if link_elem:
            href = link_elem.get('href', '')
            if href:
                # S'assurer que l'URL est absolue
                if href.startswith('//'):
                    product_data["url"] = 'https:' + href
                elif href.startswith('/'):
                    product_data["url"] = urljoin(base_url, href)
                elif not href.startswith('http'):
                    product_data["url"] = urljoin(base_url, href)
                else:
                    product_data["url"] = href
        
        # Prix
        # Chercher dans tout le texte de l'élément et ses enfants
        price_text = product_elem.get_text()
        
        # Chercher aussi dans les spans et divs avec des classes de prix
        price_elements = product_elem.find_all(['span', 'div', 'p'], class_=re.compile(r'price|amount|cost', re.I))
        for price_elem in price_elements:
            price_text += " " + price_elem.get_text()
        
        price_patterns = [
            r'(\d+[\s,.]?\d*)\s*(?:FCFA|€|\$|XOF)',  # 5000 FCFA
            r'(?:FCFA|€|\$|XOF)\s*(\d+[\s,.]?\d*)',  # FCFA 5000
            r'\$(\d+[\s,.]?\d*)',  # $5.31
            r'(\d+[\s,.]?\d*\.?\d*)',  # 5000 ou 5.31
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, price_text)
            if matches:
                try:
                    # Prendre le dernier match (généralement le prix principal)
                    price_str = matches[-1] if isinstance(matches[-1], str) else str(matches[-1])
                    price_str = price_str.replace(',', '').replace(' ', '').strip()
                    price_val = float(price_str)
                    
                    # Convertir $ en FCFA si nécessaire
                    if '$' in price_text or (price_val < 100 and '.' in price_str):
                        price_val = price_val * 600
                    
                    product_data["price"] = price_val
                    break
                except Exception as e:
                    continue
        
        # Image - chercher plusieurs attributs et convertir en URL absolue
        img_elem = product_elem.find('img')
        if img_elem:
            img_src = (img_elem.get('src', '') or 
                      img_elem.get('data-src', '') or 
                      img_elem.get('data-lazy-src', '') or
                      img_elem.get('data-original', '') or
                      img_elem.get('data-image', ''))
            if img_src:
                # Convertir URL relative en absolue
                if img_src.startswith('//'):
                    product_data["image"] = 'https:' + img_src
                elif img_src.startswith('/'):
                    product_data["image"] = urljoin(base_url, img_src)
                elif not img_src.startswith('http'):
                    product_data["image"] = urljoin(base_url, img_src)
                else:
                    product_data["image"] = img_src
        
        return product_data if product_data["name"] else None
    
    async def _scrape_product(self, page, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Scrape les données d'un produit Chariow"""
        data = {
            "name": "",
            "url": url,
            "marketplace": self.marketplace,
            "estimated_daily_sales": 0,
            "ideal_price": None,
            "price": 0,
            "competition_level": "Moyen",
            "trend": "stable",
            "risks": [],
            "description": "",
            "category": ""
        }
        
        # Nom du produit
        name_elem = soup.find('h1') or soup.find('title')
        if name_elem:
            data["name"] = name_elem.get_text(strip=True)
        
        # Prix
        price_selectors = [
            '.price',
            '[class*="price"]',
            '[class*="amount"]',
            'span:contains("FCFA")',
            'span:contains("€")',
            'span:contains("$")'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text()
                price_match = re.search(r'(\d+[\s,.]?\d*)', price_text.replace(',', '').replace(' ', ''))
                if price_match:
                    try:
                        data["price"] = float(price_match.group(1))
                        data["ideal_price"] = f"{data['price']:,.0f} FCFA"
                        break
                    except:
                        continue
        
        # Image du produit - chercher plusieurs attributs
        img_selectors = [
            'img[src*="product"]',
            'img[class*="product"]',
            '.product-image img',
            '.product img',
            'img[alt*="product"]',
            'main img',
            'article img',
            'img'
        ]
        for selector in img_selectors:
            img_elem = soup.select_one(selector)
            if img_elem:
                img_src = (img_elem.get('src', '') or 
                          img_elem.get('data-src', '') or 
                          img_elem.get('data-lazy-src', '') or
                          img_elem.get('data-original', '') or
                          img_elem.get('data-image', '') or
                          img_elem.get('srcset', '').split(',')[0].strip() if img_elem.get('srcset') else '')
                if img_src:
                    # Nettoyer srcset (prendre la première URL)
                    if ' ' in img_src:
                        img_src = img_src.split(' ')[0]
                    # Convertir URL relative en absolue
                    if img_src.startswith('//'):
                        data["image"] = 'https:' + img_src
                    elif img_src.startswith('/'):
                        data["image"] = urljoin(url, img_src)
                    elif not img_src.startswith('http'):
                        data["image"] = urljoin(url, img_src)
                    else:
                        data["image"] = img_src
                    break
        
        # Description - chercher plusieurs emplacements
        desc_selectors = [
            ('div', {'class': re.compile(r'description|content|detail|info', re.I)}),
            ('p', {'class': re.compile(r'description|content|detail', re.I)}),
            ('div', {'id': re.compile(r'description|content|detail', re.I)}),
            ('section', {'class': re.compile(r'description|content', re.I)}),
            ('meta', {'name': 'description'}),
        ]
        
        for tag, attrs in desc_selectors:
            if tag == 'meta':
                desc_elem = soup.find('meta', attrs)
                if desc_elem:
                    data["description"] = desc_elem.get('content', '')[:1000]
                    break
            else:
                desc_elem = soup.find(tag, attrs)
                if desc_elem:
                    desc_text = desc_elem.get_text(strip=True)
                    if len(desc_text) > 20:  # Ignorer les descriptions trop courtes
                        data["description"] = desc_text[:1000]
                        break
        
        # Catégorie
        category_elem = soup.find('a', class_=re.compile(r'category|tag', re.I))
        if category_elem:
            data["category"] = category_elem.get_text(strip=True)
        
        # Estimer les ventes quotidiennes (heuristique basée sur le prix)
        if data["price"] > 0:
            if data["price"] < 5000:
                data["estimated_daily_sales"] = 15
            elif data["price"] < 20000:
                data["estimated_daily_sales"] = 8
            else:
                data["estimated_daily_sales"] = 3
        else:
            data["estimated_daily_sales"] = 5
        
        return data
    
    def is_shop_page(self, data: Dict[str, Any]) -> bool:
        """Détermine si les données correspondent à une boutique"""
        return "product_count" in data or "products" in data

            if products_found:
                break

        # Stratégie 2: Chercher tous les liens qui pourraient être des produits
        if not products_found:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                # Si le lien contient des mots-clés de produit
                if any(keyword in href.lower() for keyword in ['/product', '/p/', '/item', '/produit']):
                    # Chercher le parent ou le conteneur
                    parent = link.find_parent(['div', 'article', 'li'])
                    if parent and parent not in products_found:
                        products_found.append(parent)

        # Stratégie 3: Scroll et recharger
        if len(products_found) < 5:
            try:
                # Scroll plusieurs fois pour charger le contenu dynamique
                for _ in range(4):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)

                    content = await page.content()
                    try:
                        soup = BeautifulSoup(content, 'lxml')
                    except:
                        soup = BeautifulSoup(content, 'html.parser')

                    for selector in product_selectors:
                        found = soup.select(selector)
                        if found and len(found) > len(products_found):
                            products_found = found
                            break
                    if len(products_found) >= 5:
                        break
            except Exception:
                pass

        data["product_count"] = len(products_found)

        # Extraire les détails des produits (augmenter la limite à 80)
        for product_elem in products_found[:80]:
            try:
                product_data = self._extract_product_from_list(product_elem, url)
                if product_data:
                    data["products"].append(product_data)
            except Exception as e:
                print(f"Erreur extraction produit: {e}")
                continue
        
        # Calculer les estimations basées sur les produits réels
        if data["products"]:
            total_price = sum(p.get("price", 0) for p in data["products"] if p.get("price"))
            avg_price = total_price / len(data["products"]) if data["products"] else 0
            
            # Estimation de ventes (basée sur le nombre de produits)
            estimated_monthly_sales = len(data["products"]) * 8  # ~8 ventes/mois par produit
            data["estimated_sales"] = estimated_monthly_sales
            
            # Estimation de revenus
            if avg_price > 0:
                revenue_min = estimated_monthly_sales * avg_price * 0.6
                revenue_max = estimated_monthly_sales * avg_price * 1.2
                data["estimated_revenue"] = f"{revenue_min:,.0f} - {revenue_max:,.0f} FCFA/mois"
            else:
                data["estimated_revenue"] = f"{estimated_monthly_sales * 5000:,.0f} - {estimated_monthly_sales * 15000:,.0f} FCFA/mois"
        else:
            # Estimations par défaut si pas de produits trouvés
            data["estimated_sales"] = 50
            data["estimated_revenue"] = "250,000 - 750,000 FCFA/mois"
        
        # Analyser les points forts/faibles
        if data["product_count"] > 20:
            data["strengths"].append("Large catalogue de produits")
        if data["product_count"] > 10:
            data["strengths"].append("Bonne diversité")
        if data["product_count"] < 5:
            data["weaknesses"].append("Catalogue limité")
        
        # Estimer l'ancienneté (basé sur l'URL ou autres indicateurs)
        data["age"] = "6-12 mois"  # Estimation par défaut
        
        return data
    
    def _extract_product_from_list(self, product_elem, base_url: str) -> Dict[str, Any]:
        """Extrait les données d'un produit depuis la liste"""
        product_data = {
            "name": "",
            "url": "",
            "price": 0,
            "image": ""
        }
        
        # Nom du produit
        name_elem = product_elem.find('h2') or product_elem.find('h3') or product_elem.find('a')
        if name_elem:
            product_data["name"] = name_elem.get_text(strip=True)
        
        # URL du produit - chercher plusieurs façons
        link_elem = product_elem.find('a', href=True)
        if not link_elem:
            # Chercher dans les parents
            parent = product_elem.find_parent('a', href=True)
            if parent:
                link_elem = parent
        
        if link_elem:
            href = link_elem.get('href', '')
            if href:
                # S'assurer que l'URL est absolue
                if href.startswith('//'):
                    product_data["url"] = 'https:' + href
                elif href.startswith('/'):
                    product_data["url"] = urljoin(base_url, href)
                elif not href.startswith('http'):
                    product_data["url"] = urljoin(base_url, href)
                else:
                    product_data["url"] = href
        
        # Prix
        # Chercher dans tout le texte de l'élément et ses enfants
        price_text = product_elem.get_text()
        
        # Chercher aussi dans les spans et divs avec des classes de prix
        price_elements = product_elem.find_all(['span', 'div', 'p'], class_=re.compile(r'price|amount|cost', re.I))
        for price_elem in price_elements:
            price_text += " " + price_elem.get_text()
        
        price_patterns = [
            r'(\d+[\s,.]?\d*)\s*(?:FCFA|€|\$|XOF)',  # 5000 FCFA
            r'(?:FCFA|€|\$|XOF)\s*(\d+[\s,.]?\d*)',  # FCFA 5000
            r'\$(\d+[\s,.]?\d*)',  # $5.31
            r'(\d+[\s,.]?\d*\.?\d*)',  # 5000 ou 5.31
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, price_text)
            if matches:
                try:
                    # Prendre le dernier match (généralement le prix principal)
                    price_str = matches[-1] if isinstance(matches[-1], str) else str(matches[-1])
                    price_str = price_str.replace(',', '').replace(' ', '').strip()
                    price_val = float(price_str)
                    
                    # Convertir $ en FCFA si nécessaire
                    if '$' in price_text or (price_val < 100 and '.' in price_str):
                        price_val = price_val * 600
                    
                    product_data["price"] = price_val
                    break
                except Exception as e:
                    continue
        
        # Image - chercher plusieurs attributs et convertir en URL absolue
        img_elem = product_elem.find('img')
        if img_elem:
            img_src = (img_elem.get('src', '') or 
                      img_elem.get('data-src', '') or 
                      img_elem.get('data-lazy-src', '') or
                      img_elem.get('data-original', '') or
                      img_elem.get('data-image', ''))
            if img_src:
                # Convertir URL relative en absolue
                if img_src.startswith('//'):
                    product_data["image"] = 'https:' + img_src
                elif img_src.startswith('/'):
                    product_data["image"] = urljoin(base_url, img_src)
                elif not img_src.startswith('http'):
                    product_data["image"] = urljoin(base_url, img_src)
                else:
                    product_data["image"] = img_src
        
        return product_data if product_data["name"] else None
    
    async def _scrape_product(self, page, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Scrape les données d'un produit Chariow"""
        data = {
            "name": "",
            "url": url,
            "marketplace": self.marketplace,
            "estimated_daily_sales": 0,
            "ideal_price": None,
            "price": 0,
            "competition_level": "Moyen",
            "trend": "stable",
            "risks": [],
            "description": "",
            "category": ""
        }
        
        # Nom du produit
        name_elem = soup.find('h1') or soup.find('title')
        if name_elem:
            data["name"] = name_elem.get_text(strip=True)
        
        # Prix
        price_selectors = [
            '.price',
            '[class*="price"]',
            '[class*="amount"]',
            'span:contains("FCFA")',
            'span:contains("€")',
            'span:contains("$")'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text()
                price_match = re.search(r'(\d+[\s,.]?\d*)', price_text.replace(',', '').replace(' ', ''))
                if price_match:
                    try:
                        data["price"] = float(price_match.group(1))
                        data["ideal_price"] = f"{data['price']:,.0f} FCFA"
                        break
                    except:
                        continue
        
        # Image du produit - chercher plusieurs attributs
        img_selectors = [
            'img[src*="product"]',
            'img[class*="product"]',
            '.product-image img',
            '.product img',
            'img[alt*="product"]',
            'main img',
            'article img',
            'img'
        ]
        for selector in img_selectors:
            img_elem = soup.select_one(selector)
            if img_elem:
                img_src = (img_elem.get('src', '') or 
                          img_elem.get('data-src', '') or 
                          img_elem.get('data-lazy-src', '') or
                          img_elem.get('data-original', '') or
                          img_elem.get('data-image', '') or
                          img_elem.get('srcset', '').split(',')[0].strip() if img_elem.get('srcset') else '')
                if img_src:
                    # Nettoyer srcset (prendre la première URL)
                    if ' ' in img_src:
                        img_src = img_src.split(' ')[0]
                    # Convertir URL relative en absolue
                    if img_src.startswith('//'):
                        data["image"] = 'https:' + img_src
                    elif img_src.startswith('/'):
                        data["image"] = urljoin(url, img_src)
                    elif not img_src.startswith('http'):
                        data["image"] = urljoin(url, img_src)
                    else:
                        data["image"] = img_src
                    break
        
        # Description - chercher plusieurs emplacements
        desc_selectors = [
            ('div', {'class': re.compile(r'description|content|detail|info', re.I)}),
            ('p', {'class': re.compile(r'description|content|detail', re.I)}),
            ('div', {'id': re.compile(r'description|content|detail', re.I)}),
            ('section', {'class': re.compile(r'description|content', re.I)}),
            ('meta', {'name': 'description'}),
        ]
        
        for tag, attrs in desc_selectors:
            if tag == 'meta':
                desc_elem = soup.find('meta', attrs)
                if desc_elem:
                    data["description"] = desc_elem.get('content', '')[:1000]
                    break
            else:
                desc_elem = soup.find(tag, attrs)
                if desc_elem:
                    desc_text = desc_elem.get_text(strip=True)
                    if len(desc_text) > 20:  # Ignorer les descriptions trop courtes
                        data["description"] = desc_text[:1000]
                        break
        
        # Catégorie
        category_elem = soup.find('a', class_=re.compile(r'category|tag', re.I))
        if category_elem:
            data["category"] = category_elem.get_text(strip=True)
        
        # Estimer les ventes quotidiennes (heuristique basée sur le prix)
        if data["price"] > 0:
            if data["price"] < 5000:
                data["estimated_daily_sales"] = 15
            elif data["price"] < 20000:
                data["estimated_daily_sales"] = 8
            else:
                data["estimated_daily_sales"] = 3
        else:
            data["estimated_daily_sales"] = 5
        
        return data
    
    def is_shop_page(self, data: Dict[str, Any]) -> bool:
        """Détermine si les données correspondent à une boutique"""
        return "product_count" in data or "products" in data
