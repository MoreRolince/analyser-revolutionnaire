"""
Scraper Facebook Ads Library amélioré - Inspiré du modèle Minea
Extraction complète avec métriques, CTA, et validation stricte
"""
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
import re
import asyncio
import hashlib
from datetime import datetime
from urllib.parse import urlparse, parse_qs, unquote


class FacebookAdsScraperV2:
    """Scraper amélioré pour Facebook Ads Library avec extraction complète"""
    
    BASE_URL = "https://www.facebook.com/ads/library"
    
    # Mots-clés produits digitaux - Afrique de l'Ouest
    DIGITAL_PRODUCT_KEYWORDS = [
        # Digital & Marketing
        "formation marketing digital", "cours développement web", "formation e-commerce",
        "ebook marketing", "formation facebook ads", "cours instagram marketing",
        "formation youtube", "cours seo digital", "formation wordpress",
        "cours photoshop", "formation canva", "cours figma",
        "formation google ads", "cours tiktok marketing", "formation linkedin",
        "cours email marketing", "formation automation", "cours data analysis",
        "ebook business", "formation dropshipping", "formation copywriting",
        "cours design graphique", "formation vidéo marketing", "cours community management",
        # Spiritualité & Bien-être
        "formation spiritualité", "cours méditation", "formation développement personnel",
        "ebook spiritualité", "formation yoga", "cours reiki",
        "formation astrologie", "cours numérologie", "formation tarot",
        "cours bien-être", "formation énergétique", "ebook développement personnel",
        # Finance & Trading
        "formation trading", "cours forex", "formation cryptomonnaie",
        "ebook trading", "formation investissement",
        # Mots-clés généraux
        "formation", "ebook", "coaching", "cours", "guide", "programme",
        "make money", "revenus passifs", "business en ligne",
    ]
    
    def __init__(self):
        self.scraped_ads = []
    
    async def scrape_ads(self, keyword: str, country: str = "SN", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Scrape les publicités Facebook avec extraction complète
        
        Args:
            keyword: Mot-clé à rechercher
            country: Code pays (SN, CI, BJ, etc.)
            limit: Nombre maximum d'annonces à scraper
        """
        ads = []
        
        async with async_playwright() as p:
            # 1. Initialisation avec user-agent réaliste
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox"
                ]
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="fr-FR",
                timezone_id="Africa/Dakar"
            )
            
            # Bloquer les ressources inutiles pour accélérer
            await context.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2}", lambda route: route.abort())
            
            page = await context.new_page()
            
            try:
                # 2. Navigation vers Facebook Ads Library - Mode global (pas de filtre pays)
                # Utiliser "ALL" ou ne pas spécifier de pays pour récupérer globalement
                search_url = f"{self.BASE_URL}/?active_status=all&ad_type=all&q={keyword.replace(' ', '%20')}&search_type=keyword_unordered"
                
                print(f"  🔍 Recherche: '{keyword}' ({country})...")
                await page.goto(search_url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(3)  # Délai anti-détection
                
                # 3. Scroll pour charger les publicités
                print(f"    📜 Chargement des annonces...")
                seen_count = 0
                no_new_count = 0
                max_scrolls = 10  # Limité pour rapidité
                
                for scroll_attempt in range(max_scrolls):
                    # Scroll progressif
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2)  # Délai entre scrolls
                    
                    # 4. Extraction des annonces
                    current_ads = await self._extract_ads_from_page(page, keyword, country)
                    
                    if len(current_ads) > seen_count:
                        seen_count = len(current_ads)
                        no_new_count = 0
                        print(f"    📊 {seen_count} annonces trouvées...")
                    else:
                        no_new_count += 1
                        if no_new_count >= 2:  # Arrêt si pas de nouvelles annonces
                            break
                    
                    if seen_count >= limit:
                        break
                
                # Extraction finale
                ads = await self._extract_ads_from_page(page, keyword, country)
                ads = ads[:limit]
                
                print(f"  ✅ {len(ads)} annonces extraites")
                
            except Exception as e:
                print(f"  ❌ Erreur: {e}")
                import traceback
                traceback.print_exc()
            finally:
                await browser.close()
        
        return ads
    
    async def _extract_ads_from_page(self, page, keyword: str, country: str) -> List[Dict[str, Any]]:
        """Extrait les annonces depuis la page avec validation stricte"""
        ads = []
        seen_ids = set()
        
        try:
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # 4. Recherche des conteneurs d'annonces (plusieurs sélecteurs en fallback)
            ad_containers = (
                soup.find_all('div', class_=re.compile(r'x1y1aw1k|x1n2onr6|_99s5', re.I)) or
                soup.find_all('div', attrs={'role': 'article'}) or
                soup.find_all('div', class_=re.compile(r'card|item|entry|ad', re.I))
            )
            
            for container in ad_containers:
                try:
                    ad_data = await self._extract_ad_data(container, keyword, country)
                    
                    if ad_data:
                        # 6. Validation stricte : texte + image + landing page requis
                        if self._validate_ad(ad_data):
                            # 8. Génération d'ID unique
                            ad_id = self._generate_ad_id(ad_data)
                            
                            if ad_id not in seen_ids:
                                seen_ids.add(ad_id)
                                ad_data['ad_id'] = ad_id
                                ads.append(ad_data)
                except Exception:
                    continue
            
            # Fallback : chercher les liens externes
            if len(ads) < 5:
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    if href.startswith('http') and 'facebook.com' not in href:
                        ad_data = await self._extract_ad_from_link(link, href, keyword, country)
                        if ad_data and self._validate_ad(ad_data):
                            ad_id = self._generate_ad_id(ad_data)
                            if ad_id not in seen_ids:
                                seen_ids.add(ad_id)
                                ad_data['ad_id'] = ad_id
                                ads.append(ad_data)
        
        except Exception as e:
            print(f"    ⚠️  Erreur extraction: {e}")
        
        return ads
    
    async def _extract_ad_data(self, container, keyword: str, country: str) -> Optional[Dict[str, Any]]:
        """5. Extraction complète des données d'une annonce"""
        try:
            # Texte publicitaire (minimum 20 caractères)
            ad_text = ""
            text_elements = container.find_all(['p', 'span', 'div'], class_=re.compile(r'text|content|message', re.I))
            for elem in text_elements:
                text = elem.get_text(strip=True)
                if text and len(text) >= 20:
                    ad_text = text[:500]
                    break
            
            if not ad_text:
                ad_text = container.get_text(strip=True)[:500]
            
            if len(ad_text) < 20:
                return None
            
            # Image créative (priorité CDN Facebook)
            media_url = None
            img = container.find('img')
            if img:
                media_url = (
                    img.get('src', '') or
                    img.get('data-src', '') or
                    img.get('data-lazy-src', '') or
                    img.get('data-original', '')
                )
                if media_url and not media_url.startswith('http'):
                    media_url = None
            
            # Nom de la page publicitaire
            advertiser_page = ""
            page_link = container.find('a', href=re.compile(r'facebook.com/(pages|groups|people)'))
            if page_link:
                advertiser_page = page_link.get('href', '')
            
            # Lien produit (landing page) - décodage des liens de tracking
            landing_page_url = None
            link = container.find('a', href=True)
            if link:
                href = link.get('href', '')
                if href.startswith('http') and 'facebook.com' not in href:
                    landing_page_url = self._resolve_tracking_link(href)
                elif href.startswith('/'):
                    # Chercher dans les attributs data
                    data_attrs = container.find_all(attrs={'data-href': True})
                    if data_attrs:
                        landing_page_url = self._resolve_tracking_link(data_attrs[0].get('data-href', ''))
            
            if not landing_page_url:
                return None
            
            # Titre du produit
            title = keyword
            title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
            if title_elem:
                title = title_elem.get_text(strip=True)[:200]
            elif ad_text:
                title = ad_text.split('\n')[0][:200] if '\n' in ad_text else ad_text[:200]
            
            # CTA (Call To Action)
            cta_text = self._extract_cta(container)
            
            # Métriques (si disponibles dans le snapshot)
            metrics = self._extract_metrics(container)
            
            # Insights automatiques
            insights = self._generate_insights(ad_text, landing_page_url)
            
            return {
                "product_title": title,
                "ad_text": ad_text,
                "media_url": media_url,
                "landing_page_url": landing_page_url,
                "advertiser_page": advertiser_page,
                "cta_text": cta_text,
                "country_targeting": country,
                "keyword": keyword,
                "metrics": metrics,
                "insights": insights,
                "scraped_at": datetime.now().isoformat(),
                "active_status": "active",
            }
        except Exception:
            return None
    
    async def _extract_ad_from_link(self, link_element, href: str, keyword: str, country: str) -> Optional[Dict[str, Any]]:
        """Extraction depuis un lien direct"""
        try:
            parent = link_element.find_parent(['div', 'article'])
            
            ad_text = link_element.get_text(strip=True)
            if not ad_text and parent:
                ad_text = parent.get_text(strip=True)[:500]
            
            if len(ad_text) < 20:
                return None
            
            img = link_element.find('img') or (parent.find('img') if parent else None)
            media_url = None
            if img:
                media_url = img.get('src') or img.get('data-src')
            
            landing_page_url = self._resolve_tracking_link(href)
            
            return {
                "product_title": keyword,
                "ad_text": ad_text[:500],
                "media_url": media_url,
                "landing_page_url": landing_page_url,
                "advertiser_page": "",
                "cta_text": "",
                "country_targeting": country,
                "keyword": keyword,
                "metrics": {},
                "insights": {},
                "scraped_at": datetime.now().isoformat(),
                "active_status": "active",
            }
        except Exception:
            return None
    
    def _validate_ad(self, ad_data: Dict[str, Any]) -> bool:
        """6. Validation stricte : texte + landing page requis"""
        return (
            ad_data.get('ad_text', '') and len(ad_data['ad_text']) >= 20 and
            ad_data.get('landing_page_url', '') and
            ad_data['landing_page_url'].startswith('http')
        )
    
    def _resolve_tracking_link(self, url: str) -> str:
        """Résout les liens de tracking Facebook"""
        if not url:
            return ""
        
        try:
            parsed = urlparse(url)
            
            # Décoder les paramètres de tracking
            if 'l.php' in parsed.path or 'u=' in parsed.query:
                params = parse_qs(parsed.query)
                if 'u' in params:
                    return unquote(params['u'][0])
            
            return url
        except Exception:
            return url
    
    def _extract_cta(self, container) -> str:
        """Extrait le texte du CTA"""
        cta_selectors = [
            'button',
            '[class*="cta"]',
            '[class*="button"]',
            '[class*="action"]',
        ]
        
        for selector in cta_selectors:
            elem = container.select_one(selector)
            if elem:
                cta = elem.get_text(strip=True)
                if cta and len(cta) > 3:
                    return cta[:50]
        
        return ""
    
    def _extract_metrics(self, container) -> Dict[str, Any]:
        """Extrait les métriques si disponibles"""
        metrics = {}
        
        # Chercher les métriques dans le texte
        text = container.get_text()
        
        patterns = {
            'impressions': r'(\d+[\s,.]?\d*)\s*(?:impressions|vues)',
            'reach': r'(\d+[\s,.]?\d*)\s*(?:personnes|reach)',
            'ctr': r'(\d+\.?\d*)\s*%',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    metrics[key] = float(match.group(1).replace(',', '').replace(' ', ''))
                except:
                    pass
        
        return metrics
    
    def _generate_insights(self, ad_text: str, landing_url: str) -> Dict[str, Any]:
        """Génère des insights automatiques"""
        insights = {
            "estimated_price": None,
            "main_hook": "",
            "product_type": "unknown",
        }
        
        # Détecter le prix dans le texte
        price_patterns = [
            r'(\d+[\s,.]?\d*)\s*(?:FCFA|XOF|€|\$|EUR)',
            r'(?:FCFA|XOF|€|\$|EUR)\s*(\d+[\s,.]?\d*)',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, ad_text)
            if match:
                try:
                    price = float(match.group(1).replace(',', '').replace(' ', ''))
                    insights["estimated_price"] = price
                    break
                except:
                    pass
        
        # Détecter le hook principal (première phrase accrocheuse)
        sentences = ad_text.split('.')[:3]
        if sentences:
            insights["main_hook"] = sentences[0].strip()[:100]
        
        # Détecter le type de produit depuis l'URL
        url_lower = landing_url.lower()
        if 'maketou' in url_lower or 'chariow' in url_lower:
            insights["product_type"] = "digital_product"
        elif 'systeme.io' in url_lower:
            insights["product_type"] = "digital_product"
        elif 'gumroad' in url_lower or 'payhip' in url_lower:
            insights["product_type"] = "digital_product"
        
        return insights
    
    def _generate_ad_id(self, ad_data: Dict[str, Any]) -> str:
        """8. Génère un ID unique basé sur le contenu"""
        content = f"{ad_data.get('landing_page_url', '')}{ad_data.get('ad_text', '')[:100]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def scrape_all_keywords(self, countries: List[str] = None, limit_per_keyword: int = 50) -> List[Dict[str, Any]]:
        """Scrape tous les mots-clés"""
        if countries is None:
            countries = ["SN", "CI", "BJ"]  # Pays principaux Afrique de l'Ouest
        
        all_ads = []
        total = len(self.DIGITAL_PRODUCT_KEYWORDS) * len(countries)
        current = 0
        
        print(f"\n📊 Scraping de {total} combinaisons")
        print(f"   Mots-clés: {len(self.DIGITAL_PRODUCT_KEYWORDS)}")
        print(f"   Pays: {len(countries)} ({', '.join(countries)})")
        
        for keyword in self.DIGITAL_PRODUCT_KEYWORDS:
            for country in countries:
                current += 1
                try:
                    print(f"\n[{current}/{total}] '{keyword}' - {country}")
                    ads = await self.scrape_ads(keyword, country, limit_per_keyword)
                    all_ads.extend(ads)
                    await asyncio.sleep(2)  # Délai anti-détection
                except Exception as e:
                    print(f"  ⚠️  Erreur: {e}")
                    continue
        
        # Déduplication par ID
        seen_ids = set()
        unique_ads = []
        for ad in all_ads:
            ad_id = ad.get('ad_id') or self._generate_ad_id(ad)
            if ad_id not in seen_ids:
                seen_ids.add(ad_id)
                unique_ads.append(ad)
        
        print(f"\n✅ {len(unique_ads)} annonces uniques scrapées")
        return unique_ads

