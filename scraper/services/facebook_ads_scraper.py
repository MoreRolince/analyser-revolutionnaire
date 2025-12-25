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
                # Augmenter le timeout et ajouter des retries
                max_retries = 3
                retry_count = 0
                success = False
                
                while retry_count < max_retries and not success:
                    try:
                        await page.goto(search_url, wait_until="domcontentloaded", timeout=120000)  # 120 secondes
                        await page.wait_for_timeout(8000)  # Attendre le chargement (augmenté)
                        success = True
                    except Exception as retry_error:
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"    ⚠️  Tentative {retry_count + 1}/{max_retries} après erreur: {str(retry_error)[:50]}")
                            await asyncio.sleep(5 * retry_count)  # Délai exponentiel
                        else:
                            raise retry_error
                
                # Scroll infini pour charger TOUTES les annonces (on arrive ici seulement si success == True)
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
                print(f"  ❌ Erreur recherche '{keyword}' ({country}): {str(e)[:100]}", flush=True)
                # Ne pas imprimer toute la traceback pour éviter de polluer les logs
                # Le code continue avec ads = [] (liste vide)
            finally:
                try:
                    await browser.close()
                except:
                    pass  # Ignorer les erreurs de fermeture
        
        return ads[:limit]
    
    async def _extract_ads_from_page(self, page, keyword: str, country: str) -> List[Dict[str, Any]]:
        """Extrait les annonces depuis la page Facebook Ads Library avec image, texte et CTA"""
        ads = []
        seen_urls = set()
        
        # URLs Facebook/Meta à exclure (pages internes, pas de vraies landing pages)
        excluded_domains = [
            'facebook.com', 'fb.com', 'fb.me', 'instagram.com', 'meta.com',
            'metastatus.com', 'messenger.com', 'whatsapp.com', 'oculus.com',
            'facebook.net', 'fbcdn.net', 'fbsbx.com', 'fbstatic.com',
            'l.facebook.com'
        ]
        
        def is_valid_landing_page(url: str) -> bool:
            """Vérifie si l'URL est une vraie landing page (pas une page Facebook/Meta)"""
            if not url or not url.startswith('http'):
                return False
            url_lower = url.lower()
            return not any(domain in url_lower for domain in excluded_domains)
        
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
                    if not ad_data:
                        continue
                    
                    landing_url = ad_data.get('landing_page_url')
                    if not landing_url:
                        continue  # Pas d'URL, skip
                    
                    if landing_url in seen_urls:
                        continue  # Déjà vu
                    
                    # Vérifier si c'est une vraie landing page
                    if not is_valid_landing_page(landing_url):
                        print(f"    ⚠️  URL filtrée (Facebook/Meta): {landing_url[:60]}...", flush=True)
                        continue
                    
                    seen_urls.add(landing_url)
                    ads.append(ad_data)
                except Exception:
                    continue
            
            # Méthode alternative: chercher tous les liens avec images
            if len(ads) < 10:
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    if not href or href in seen_urls or not is_valid_landing_page(href):
                        continue
                    
                    # Vérifier si c'est une URL externe (landing page)
                    if href.startswith('http'):
                        seen_urls.add(href)
                        ad_data = await self._extract_ad_data_from_link(link, href, keyword, country)
                        if ad_data:
                            ads.append(ad_data)
            
            # Chercher dans le JavaScript de la page (les vraies URLs sont souvent dans le JS)
            try:
                # Exécuter du JavaScript pour extraire les URLs depuis les données JSON cachées
                js_urls = await page.evaluate("""
                    () => {
                        const urls = new Set();
                        const excluded = ['facebook.com', 'fb.com', 'metastatus.com', 'instagram.com', 'meta.com'];
                        
                        // Chercher dans window.__d, window.__r, etc. (structures de données React/Facebook)
                        const searchInObject = (obj, depth = 0) => {
                            if (depth > 5) return;
                            if (!obj || typeof obj !== 'object') return;
                            
                            for (let key in obj) {
                                if (key === 'url' || key === 'link' || key === 'href' || key === 'landingPageUrl' || key === 'cta_url') {
                                    const val = obj[key];
                                    if (typeof val === 'string' && val.startsWith('http')) {
                                        const isExcluded = excluded.some(domain => val.includes(domain));
                                        if (!isExcluded) {
                                            urls.add(val);
                                        }
                                    }
                                }
                                if (typeof obj[key] === 'object') {
                                    searchInObject(obj[key], depth + 1);
                                }
                            }
                        };
                        
                        // Chercher dans les variables globales
                        if (window.__d) searchInObject(window.__d);
                        if (window.__r) searchInObject(window.__r);
                        if (window._csr) searchInObject(window._csr);
                        
                        // Chercher dans le texte de la page
                        const bodyText = document.body.innerText || '';
                        const urlRegex = /https?:\\/\\/[^\\s<>"{}|\\\\^`\\[\\]]+/g;
                        const matches = bodyText.match(urlRegex);
                        if (matches) {
                            matches.forEach(url => {
                                const isExcluded = excluded.some(domain => url.includes(domain));
                                if (!isExcluded) {
                                    urls.add(url);
                                }
                            });
                        }
                        
                        return Array.from(urls);
                    }
                """)
                
                for url in js_urls:
                    if url in seen_urls or not is_valid_landing_page(url):
                        continue
                    
                    if self._is_digital_product_url(url):
                        seen_urls.add(url)
                        ad_data = {
                            "product_title": keyword,
                            "ad_text": "",
                            "landing_page_url": url,
                            "cta_url": url,
                            "advertiser_page": "",
                            "start_date": None,
                            "active_status": "unknown",
                            "country_targeting": country,
                            "keyword": keyword,
                            "scraped_at": datetime.now().isoformat(),
                            "media_url": None,
                        }
                        ads.append(ad_data)
            except Exception as js_error:
                print(f"    ⚠️  Erreur extraction JS: {str(js_error)[:50]}", flush=True)
            
            # Chercher dans le texte HTML aussi (fallback)
            page_text = str(soup)
            url_pattern = re.compile(r'https?://[^\\s<>\"{}|\\\\^`\\[\\]]+')
            urls_found = url_pattern.findall(page_text)
            
            for url in urls_found:
                if url in seen_urls or not is_valid_landing_page(url):
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
            
            # Extraire l'URL du CTA (landing page) - chercher plus agressivement
            cta_url = None
            
            # 1. Chercher dans les liens directs
            link = container.find('a', href=True)
            if link:
                href = link.get('href', '')
                # Décoder les liens de tracking Facebook (l.facebook.com)
                if 'l.facebook.com' in href or 'l.php' in href:
                    try:
                        from urllib.parse import urlparse, parse_qs, unquote
                        parsed = urlparse(href)
                        params = parse_qs(parsed.query)
                        if 'u' in params:
                            cta_url = unquote(params['u'][0])
                    except:
                        pass
                elif href.startswith('http'):
                    cta_url = href
                elif href.startswith('/'):
                    # Lien relatif, chercher dans les attributs data
                    data_attrs = container.find_all(attrs={'data-href': True})
                    if data_attrs:
                        cta_url = data_attrs[0].get('data-href', '')
            
            # 2. Si pas trouvé, chercher dans tous les attributs data-*
            if not cta_url:
                for attr in ['data-href', 'data-url', 'data-link', 'href']:
                    elem = container.find(attrs={attr: True})
                    if elem:
                        url = elem.get(attr, '')
                        if url and url.startswith('http') and not any(d in url.lower() for d in ['facebook.com', 'fb.com', 'metastatus.com']):
                            cta_url = url
                            break
            
            # 3. Chercher dans le texte (URLs dans le contenu)
            if not cta_url and ad_text:
                url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
                urls_in_text = url_pattern.findall(ad_text)
                for url in urls_in_text:
                    if not any(d in url.lower() for d in ['facebook.com', 'fb.com', 'metastatus.com', 'instagram.com']):
                        cta_url = url
                        break
            
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
            
            # Retourner None seulement si vraiment pas d'URL ET pas de texte (annonce invalide)
            if not cta_url and not ad_text:
                return None
            
            # Si pas d'URL mais du texte, créer une annonce quand même (l'URL sera None)
            # Le filtre is_valid_landing_page la filtrera si nécessaire
            
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

