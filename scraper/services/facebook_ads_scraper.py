"""
Scraper Facebook Ads Library - Détection de produits digitaux via publicités
"""
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
import re
import asyncio
from datetime import datetime
from urllib.parse import urlparse, parse_qs


class FacebookAdsScraper:
    """Scraper pour Facebook Ads Library"""
    
    BASE_URL = "https://www.facebook.com/ads/library"
    
    # Mots-clés pour produits digitaux - Marché africain (Afrique de l'Ouest)
    DIGITAL_PRODUCT_KEYWORDS = [
        # Produits digitaux généraux
        "formation", "e-book", "ebook", "coaching", "guide", "programme",
        "make money", "digital product", "cours", "pdf", "business en ligne",
        "revenus", "astuces", "marketplace", "Makétou", "Chariow", "Systeme.io",
        "système.io", "gumroad", "payhip", "notion", "template", "logiciel",
        "plugin", "theme", "application", "software", "tutoriel", "formation en ligne",
        "cours en ligne", "ebook pdf", "guide pdf", "formation digitale",
        "revenus passifs", "affiliation", "dropshipping", "business digital",
        # Mots-clés spécifiques Afrique de l'Ouest
        "formation afrique", "ebook afrique", "coaching afrique", "guide afrique",
        "cours afrique", "business afrique", "revenus afrique", "argent afrique",
        "formation cameroun", "formation sénégal", "formation côte d'ivoire",
        "formation mali", "formation burkina faso", "formation bénin", "formation tog",
        "ebook cameroun", "ebook sénégal", "ebook côte d'ivoire",
        "coaching cameroun", "coaching sénégal", "coaching côte d'ivoire",
        "make money afrique", "gagner de l'argent afrique", "revenus passifs afrique",
        "business en ligne afrique", "dropshipping afrique", "affiliation afrique",
        "formation digitale afrique", "cours en ligne afrique", "tutoriel afrique",
        "guide pdf afrique", "template afrique", "logiciel afrique",
        # Mots-clés en français local
        "faire de l'argent", "gagner de l'argent", "argent facile",
        "revenus supplémentaires", "business rentable", "opportunité business",
        "formation rentable", "cours rentable", "guide rentable",
    ]
    
    def __init__(self):
        self.ads_scraped = []
    
    async def search_ads(self, keyword: str, country: str = "SN", limit: int = 200) -> List[Dict[str, Any]]:
        """
        Recherche des publicités Facebook pour un mot-clé donné
        Parcourt TOUTE la bibliothèque avec scroll infini
        
        Args:
            keyword: Mot-clé à rechercher
            country: Code pays (SN, CI, ML, BF, BJ, TG pour Afrique de l'Ouest)
            limit: Nombre maximum d'annonces à scraper
        """
        ads = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()
            
            try:
                # Construire l'URL de recherche Facebook Ads Library
                search_url = f"{self.BASE_URL}/?active_status=all&ad_type=all&country={country}&q={keyword.replace(' ', '%20')}&search_type=keyword_unordered"
                
                print(f"  🔍 Recherche: '{keyword}' (pays: {country})...")
                await page.goto(search_url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(5000)  # Attendre le chargement
                
                # Scroll infini pour charger TOUTES les annonces
                print(f"    📜 Parcours de toute la bibliothèque (scroll infini)...")
                seen_ads_count = 0
                no_new_ads_count = 0
                max_scrolls = 50  # Limite de sécurité
                
                for scroll_attempt in range(max_scrolls):
                    # Scroll vers le bas
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(3000)  # Attendre le chargement
                    
                    # Extraire les annonces de cette page
                    current_ads = await self._extract_ads_from_page(page, keyword, country)
                    
                    # Compter les nouvelles annonces
                    current_count = len(current_ads)
                    if current_count > seen_ads_count:
                        seen_ads_count = current_count
                        no_new_ads_count = 0
                        print(f"    📊 {current_count} annonces trouvées...")
                    else:
                        no_new_ads_count += 1
                        # Si pas de nouvelles annonces depuis 3 scrolls, arrêter
                        if no_new_ads_count >= 3:
                            print(f"    ✅ Fin du scroll ({current_count} annonces totales)")
                            break
                    
                    # Vérifier si on a atteint la limite
                    if current_count >= limit:
                        print(f"    ✅ Limite atteinte ({limit} annonces)")
                        break
                
                # Extraire toutes les annonces finales
                ads = await self._extract_ads_from_page(page, keyword, country)
                
                print(f"  ✅ {len(ads)} annonces trouvées pour '{keyword}' ({country})")
                
            except Exception as e:
                print(f"  ❌ Erreur recherche '{keyword}': {e}")
                import traceback
                traceback.print_exc()
            finally:
                await browser.close()
        
        return ads[:limit]
    
    async def _extract_ads_from_page(self, page, keyword: str, country: str) -> List[Dict[str, Any]]:
        """Extrait les annonces depuis la page Facebook Ads Library avec image, texte et CTA"""
        ads = []
        seen_urls = set()
        
        try:
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Facebook Ads Library structure - chercher les conteneurs d'annonces
            # Les annonces sont dans des divs avec des classes spécifiques
            ad_containers = soup.find_all('div', class_=re.compile(r'x1y1aw1k|x1n2onr6|_99s5', re.I))
            
            # Si pas de résultats avec les classes spécifiques, chercher par structure générale
            if not ad_containers or len(ad_containers) < 5:
                # Chercher tous les divs qui pourraient contenir des annonces
                ad_containers = soup.find_all('div', attrs={'role': 'article'}) or \
                               soup.find_all('div', class_=re.compile(r'card|item|entry', re.I))
            
            # Extraire les annonces depuis les conteneurs
            for container in ad_containers:
                try:
                    ad_data = await self._extract_ad_from_container(container, keyword, country)
                    if ad_data and ad_data.get('landing_page_url') and ad_data['landing_page_url'] not in seen_urls:
                        seen_urls.add(ad_data['landing_page_url'])
                        ads.append(ad_data)
                except Exception:
                    continue
            
            # Méthode alternative: chercher tous les liens avec images
            if len(ads) < 10:
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    if not href or href in seen_urls or 'facebook.com' in href:
                        continue
                    
                    # Vérifier si c'est une URL externe (landing page)
                    if href.startswith('http'):
                        seen_urls.add(href)
                        ad_data = await self._extract_ad_data_from_link(link, href, keyword, country)
                        if ad_data:
                            ads.append(ad_data)
            
            # Chercher dans le texte de la page (pour les URLs dans le JS)
            page_text = str(soup)
            url_pattern = re.compile(r'https?://[^\\s<>\"{}|\\\\^`\\[\\]]+')
            urls_found = url_pattern.findall(page_text)
            
            for url in urls_found:
                if 'facebook.com' in url or url in seen_urls:
                    continue
                
                if self._is_digital_product_url(url):
                    seen_urls.add(url)
                    ad_data = {
                        "product_title": keyword,
                        "ad_text": "",
                        "landing_page_url": url,
                        "cta_url": url,  # CTA URL = landing page
                        "advertiser_page": "",
                        "start_date": None,
                        "active_status": "unknown",
                        "country_targeting": country,
                        "keyword": keyword,
                        "scraped_at": datetime.now().isoformat(),
                        "media_url": None,
                    }
                    ads.append(ad_data)
        
        except Exception as e:
            print(f"    ⚠️  Erreur extraction annonces: {e}")
            import traceback
            traceback.print_exc()
        
        return ads
    
    async def _extract_ad_from_container(self, container, keyword: str, country: str) -> Optional[Dict[str, Any]]:
        """Extrait une annonce complète depuis un conteneur (avec image, texte, CTA)"""
        try:
            # Extraire l'image
            img = container.find('img')
            media_url = None
            if img:
                media_url = (img.get('src', '') or 
                           img.get('data-src', '') or 
                           img.get('data-lazy-src', '') or
                           img.get('data-original', ''))
                if media_url and not media_url.startswith('http'):
                    media_url = None
            
            # Extraire le texte publicitaire
            ad_text = ""
            text_elements = container.find_all(['p', 'span', 'div'], class_=re.compile(r'text|content|message', re.I))
            for elem in text_elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 10:
                    ad_text = text[:500]  # Limiter à 500 caractères
                    break
            
            # Si pas de texte trouvé, prendre tout le texte du conteneur
            if not ad_text:
                ad_text = container.get_text(strip=True)[:500]
            
            # Extraire l'URL du CTA (landing page)
            cta_url = None
            link = container.find('a', href=True)
            if link:
                href = link.get('href', '')
                if href.startswith('http') and 'facebook.com' not in href:
                    cta_url = href
                elif href.startswith('/'):
                    # Lien relatif Facebook, chercher dans les attributs data
                    data_attrs = container.find_all(attrs={'data-href': True})
                    if data_attrs:
                        cta_url = data_attrs[0].get('data-href', '')
            
            # Extraire le titre (première ligne du texte ou h1/h2/h3)
            title = keyword
            title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
            if title_elem:
                title = title_elem.get_text(strip=True)[:200]
            elif ad_text:
                # Prendre les premiers mots du texte comme titre
                title = ad_text.split('\n')[0][:200] if '\n' in ad_text else ad_text[:200]
            
            # Extraire la page publicitaire
            advertiser_page = ""
            page_link = container.find('a', href=re.compile(r'facebook.com/(pages|groups|people)'))
            if page_link:
                advertiser_page = page_link.get('href', '')
            
            if not cta_url:
                return None
            
            return {
                "product_title": title,
                "ad_text": ad_text,  # Texte publicitaire complet
                "landing_page_url": cta_url,  # URL du CTA
                "cta_url": cta_url,  # URL du CTA (alias)
                "advertiser_page": advertiser_page,
                "start_date": None,
                "active_status": "active",
                "country_targeting": country,
                "keyword": keyword,
                "scraped_at": datetime.now().isoformat(),
                "media_url": media_url,  # URL de l'image publicitaire
            }
        except Exception:
            return None
    
    async def _extract_ad_data_from_link(self, link_element, href: str, keyword: str, country: str) -> Optional[Dict[str, Any]]:
        """Extrait les données d'une annonce depuis un élément de lien (avec image, texte, CTA)"""
        try:
            # Chercher le titre dans le texte du lien ou les parents
            title = link_element.get_text(strip=True)
            if not title or len(title) < 5:
                # Chercher dans les parents
                parent = link_element.find_parent(['div', 'article', 'section'])
                if parent:
                    title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'span', 'div'], class_=re.compile(r'title|heading', re.I))
                    if title_elem:
                        title = title_elem.get_text(strip=True)
            
            # Chercher le texte publicitaire (ad_text)
            ad_text = ""
            parent = link_element.find_parent(['div', 'article'])
            if parent:
                desc_elem = parent.find(['p', 'div', 'span'], class_=re.compile(r'description|text|content|message', re.I))
                if desc_elem:
                    ad_text = desc_elem.get_text(strip=True)[:500]
                else:
                    # Prendre tout le texte du parent
                    ad_text = parent.get_text(strip=True)[:500]
            
            # Chercher l'image publicitaire
            media_url = None
            img = link_element.find('img') or (parent.find('img') if parent else None)
            if img:
                media_url = (img.get('src', '') or 
                           img.get('data-src', '') or 
                           img.get('data-lazy-src', '') or
                           img.get('data-original', ''))
                if media_url and not media_url.startswith('http'):
                    media_url = None
            
            # Chercher la page publicitaire
            advertiser_page = ""
            if parent:
                page_link = parent.find('a', href=re.compile(r'facebook.com/(pages|groups|people)'))
                if page_link:
                    advertiser_page = page_link.get('href', '')
            
            return {
                "product_title": title[:200] if title else keyword,
                "ad_text": ad_text,  # Texte publicitaire
                "landing_page_url": href,  # URL du CTA
                "cta_url": href,  # URL du CTA (alias)
                "advertiser_page": advertiser_page,
                "start_date": None,
                "active_status": "active",
                "country_targeting": country,
                "keyword": keyword,
                "scraped_at": datetime.now().isoformat(),
                "media_url": media_url,  # URL de l'image
            }
        except Exception:
            return None
    
    def _is_digital_product_url(self, url: str) -> bool:
        """Vérifie si une URL pourrait être une landing page de produit digital"""
        url_lower = url.lower()
        
        # Vérifier les domaines connus de produits digitaux
        digital_domains = [
            'maketou.com', 'chariow.com', 'systeme.io', 'gumroad.com',
            'payhip.com', 'notion.so', 'drive.google.com', 'clickbank.com',
            'jvzoo.com', 'warriorplus.com', 'udemy.com', 'teachable.com',
        ]
        
        if any(domain in url_lower for domain in digital_domains):
            return True
        
        # Vérifier les patterns d'URLs de produits digitaux
        digital_patterns = [
            r'/product', r'/produit', r'/ebook', r'/formation', r'/cours',
            r'/template', r'/guide', r'/programme', r'/coaching',
        ]
        
        return any(re.search(pattern, url_lower) for pattern in digital_patterns)
    
    async def scrape_all_keywords(self, countries: List[str] = None, limit_per_keyword: int = 200) -> List[Dict[str, Any]]:
        """
        Scrape TOUTES les annonces pour TOUS les mots-clés
        Parcourt toute la bibliothèque Facebook Ads pour chaque combinaison
        
        Args:
            countries: Liste de codes pays (par défaut: Afrique de l'Ouest uniquement)
            limit_per_keyword: Nombre max d'annonces par mot-clé (200 par défaut)
        """
        # Pays Afrique de l'Ouest uniquement
        if countries is None:
            countries = ["SN", "CI", "ML", "BF", "BJ", "TG", "MR", "GW", "GN", "SL"]  # Afrique de l'Ouest
        
        all_ads = []
        total_combinations = len(self.DIGITAL_PRODUCT_KEYWORDS) * len(countries)
        current = 0
        
        print(f"\n📊 Scraping de {total_combinations} combinaisons (mots-clés × pays)")
        print(f"   Mots-clés: {len(self.DIGITAL_PRODUCT_KEYWORDS)}")
        print(f"   Pays: {len(countries)} ({', '.join(countries)})")
        print(f"   Limite par combinaison: {limit_per_keyword} annonces")
        
        for keyword in self.DIGITAL_PRODUCT_KEYWORDS:
            for country in countries:
                current += 1
                try:
                    print(f"\n[{current}/{total_combinations}] '{keyword}' - {country}")
                    ads = await self.search_ads(keyword, country, limit_per_keyword)
                    all_ads.extend(ads)
                    print(f"  ✅ {len(ads)} annonces ajoutées (Total: {len(all_ads)})")
                    await asyncio.sleep(3)  # Pause entre les recherches pour éviter le rate limiting
                except Exception as e:
                    print(f"  ⚠️  Erreur pour '{keyword}' ({country}): {e}")
                    continue
        
        # Déduplication par landing_page_url
        print(f"\n🔄 Déduplication des annonces...")
        seen_urls = set()
        unique_ads = []
        for ad in all_ads:
            url = ad.get('landing_page_url', '') or ad.get('cta_url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_ads.append(ad)
        
        print(f"  ✅ {len(unique_ads)} annonces uniques (sur {len(all_ads)} totales)")
        
        return unique_ads

