"""
Scraper Facebook Ads Library PRO - Stratégie clusters de mots-clés
Focus: Produits digitaux africains (Business + Spiritualité)
"""
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional, Set
import re
import asyncio
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, unquote
from collections import defaultdict


class FacebookAdsScraperPro:
    """Scraper professionnel avec stratégie clusters de mots-clés"""
    
    BASE_URL = "https://www.facebook.com/ads/library"
    
    # CLUSTERS DE MOTS-CLÉS (pas des mots isolés)
    KEYWORD_CLUSTERS = {
        "digital_business": [
            "ebook", "formation en ligne", "gagne argent", "revenus en ligne",
            "business digital", "formation WhatsApp", "tunnel de vente", "systeme.io",
            "make money", "revenus passifs", "affiliation", "dropshipping",
            "formation marketing", "cours en ligne", "tutoriel digital",
        ],
        "spirituality_faith": [
            "prière", "délivrance", "prospérité", "abondance", "destinée",
            "éveil spirituel", "loi de l'attraction", "prières financières",
            "bénédiction", "miracle", "jeûne et prière", "manifestation",
            "spiritualité africaine", "protection spirituelle", "prière puissante",
            "prière efficace", "prière qui marche", "prière pour argent",
        ],
        "african_context": [
            "FCFA", "paiement mobile", "Orange Money", "MTN MoMo",
            "WhatsApp Business", "Afrique", "Bénin", "Côte d'Ivoire",
            "Cameroun", "Sénégal", "Mali", "Burkina Faso",
        ]
    }
    
    def __init__(self):
        self.scraped_ads = []
        self.landing_pages_map = defaultdict(list)  # URL -> [ads]
    
    async def scrape_cluster(self, cluster_name: str, keywords: List[str], limit_per_keyword: int = 30) -> List[Dict[str, Any]]:
        """
        Scrape un cluster de mots-clés en parallèle
        
        Args:
            cluster_name: Nom du cluster (digital_business, spirituality_faith, etc.)
            keywords: Liste des mots-clés du cluster
            limit_per_keyword: Limite d'annonces par mot-clé
        """
        all_ads = []
        seen_urls = set()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage"]
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="fr-FR"
            )
            
            # Bloquer ressources inutiles
            await context.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,css}", lambda route: route.abort())
            
            # Créer pages en parallèle
            pages = [await context.new_page() for _ in range(min(3, len(keywords)))]
            
            try:
                # Scraper les mots-clés en parallèle par groupes
                for i in range(0, len(keywords), len(pages)):
                    if len(all_ads) >= limit_per_keyword * len(keywords):
                        break
                    
                    keywords_batch = keywords[i:i+len(pages)]
                    
                    # Scraper en parallèle
                    tasks = [
                        self._scrape_keyword_fast(
                            kw, 
                            pages[j % len(pages)], 
                            seen_urls,
                            cluster_name
                        )
                        for j, kw in enumerate(keywords_batch)
                    ]
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results:
                        if isinstance(result, list):
                            all_ads.extend(result)
                            # Mapper les landing pages
                            for ad in result:
                                landing_url = ad.get('landing_page_url', '')
                                if landing_url:
                                    self.landing_pages_map[landing_url].append(ad)
                    
                    print(f"  📊 Cluster {cluster_name}: {len(all_ads)} annonces (batch {i//len(pages)+1})")
                    
                    await asyncio.sleep(1)  # Délai minimal
                
            finally:
                await browser.close()
        
        return all_ads
    
    async def _scrape_keyword_fast(self, keyword: str, page, seen_urls: Set[str], cluster: str) -> List[Dict[str, Any]]:
        """Scrape un mot-clé de manière optimisée"""
        ads = []
        
        try:
            # URL sans filtre pays (global)
            url = f"{self.BASE_URL}/?active_status=all&ad_type=all&q={keyword.replace(' ', '%20')}&search_type=keyword_unordered"
            
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(1)
            
            # Scroll rapide (5 scrolls)
            for _ in range(5):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(0.5)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extraction rapide
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                if not href or 'facebook.com' in href or href in seen_urls:
                    continue
                
                if href.startswith('http'):
                    # Résoudre les liens de tracking
                    clean_url = self._resolve_tracking_link(href)
                    
                    # Vérifier si produit digital
                    if self._is_digital_product_url(clean_url):
                        seen_urls.add(clean_url)
                        
                        # Extraction rapide
                        img = link.find('img')
                        media_url = img.get('src') if img else None
                        
                        parent = link.find_parent(['div', 'article', 'section'])
                        ad_text = ""
                        if parent:
                            ad_text = parent.get_text(strip=True)[:500]
                        if not ad_text or len(ad_text) < 20:
                            continue
                        
                        # Extraire CTA
                        cta_text = self._extract_cta_fast(parent or link)
                        
                        # Extraire nom de la page
                        advertiser_page = self._extract_advertiser_page(parent or link)
                        
                        # Détecter signaux africains
                        africa_signals = self._detect_africa_signals(ad_text, clean_url)
                        
                        # Détecter WhatsApp CTA
                        has_whatsapp = self._has_whatsapp_cta(ad_text, clean_url)
                        
                        # Détecter payment proof
                        has_payment_proof = self._has_payment_proof(ad_text)
                        
                        ads.append({
                            'ad_text': ad_text,
                            'media_url': media_url,
                            'landing_page_url': clean_url,
                            'advertiser_page': advertiser_page,
                            'cta_text': cta_text,
                            'keyword': keyword,
                            'cluster': cluster,
                            'country_targeting': 'ALL',
                            'active_status': 'active',
                            'africa_signals': africa_signals,
                            'has_whatsapp_cta': has_whatsapp,
                            'has_payment_proof': has_payment_proof,
                            'scraped_at': datetime.now().isoformat(),
                        })
        
        except Exception as e:
            print(f"    ⚠️  Erreur {keyword}: {e}")
        
        return ads
    
    def _resolve_tracking_link(self, url: str) -> str:
        """Résout les liens de tracking Facebook"""
        try:
            parsed = urlparse(url)
            if 'l.php' in parsed.path or 'u=' in parsed.query:
                params = parse_qs(parsed.query)
                if 'u' in params:
                    return unquote(params['u'][0])
            return url
        except:
            return url
    
    def _is_digital_product_url(self, url: str) -> bool:
        """Vérifie si URL est un produit digital"""
        url_lower = url.lower()
        
        # Domaines connus
        digital_domains = [
            'maketou', 'chariow', 'systeme.io', 'gumroad', 'payhip',
            'notion.so', 'drive.google', 'clickbank', 'jvzoo'
        ]
        
        if any(domain in url_lower for domain in digital_domains):
            return True
        
        # Patterns d'URLs
        digital_patterns = [
            r'/product', r'/produit', r'/ebook', r'/formation',
            r'/cours', r'/guide', r'/coaching', r'/template'
        ]
        
        return any(re.search(pattern, url_lower) for pattern in digital_patterns)
    
    def _extract_cta_fast(self, element) -> str:
        """Extrait le CTA rapidement"""
        if not element:
            return ""
        
        cta_elem = element.find(['button', 'a'], class_=re.compile(r'cta|button|action', re.I))
        if cta_elem:
            return cta_elem.get_text(strip=True)[:50]
        return ""
    
    def _extract_advertiser_page(self, element) -> str:
        """Extrait le nom de la page publicitaire"""
        if not element:
            return ""
        
        page_link = element.find('a', href=re.compile(r'facebook.com/(pages|groups|people)'))
        if page_link:
            return page_link.get('href', '')
        return ""
    
    def _detect_africa_signals(self, text: str, url: str) -> List[str]:
        """Détecte les signaux africains"""
        signals = []
        text_lower = text.lower()
        url_lower = url.lower()
        
        africa_keywords = {
            'FCFA': 'currency_fcfa',
            'Orange Money': 'payment_orange',
            'MTN MoMo': 'payment_mtn',
            'WhatsApp Business': 'whatsapp_business',
            'paiement mobile': 'payment_mobile',
        }
        
        countries = ['bénin', 'côte d\'ivoire', 'cameroun', 'sénégal', 'mali', 'burkina faso', 'afrique']
        
        for keyword, signal in africa_keywords.items():
            if keyword.lower() in text_lower or keyword.lower() in url_lower:
                signals.append(signal)
        
        for country in countries:
            if country in text_lower:
                signals.append(f'country_{country.replace(" ", "_")}')
        
        return signals
    
    def _has_whatsapp_cta(self, text: str, url: str) -> bool:
        """Détecte la présence d'un CTA WhatsApp"""
        text_lower = text.lower()
        url_lower = url.lower()
        
        whatsapp_indicators = [
            'whatsapp', 'wa.me', 'chat whatsapp', 'contactez-nous whatsapp',
            'cliquez pour whatsapp', 'message whatsapp'
        ]
        
        return any(indicator in text_lower or indicator in url_lower for indicator in whatsapp_indicators)
    
    def _has_payment_proof(self, text: str) -> bool:
        """Détecte la présence de preuves de paiement"""
        text_lower = text.lower()
        
        proof_indicators = [
            'retraits', 'captures', 'témoignages', 'preuves de paiement',
            'screenshots', 'paiements reçus', 'revenus générés'
        ]
        
        return any(indicator in text_lower for indicator in proof_indicators)
    
    async def scrape_all_clusters(self, limit_per_cluster: int = 50) -> List[Dict[str, Any]]:
        """Scrape tous les clusters"""
        all_ads = []
        
        print(f"\n📦 Scraping de {len(self.KEYWORD_CLUSTERS)} clusters...")
        
        for cluster_name, keywords in self.KEYWORD_CLUSTERS.items():
            print(f"\n🔍 Cluster: {cluster_name} ({len(keywords)} mots-clés)")
            ads = await self.scrape_cluster(cluster_name, keywords, limit_per_cluster)
            all_ads.extend(ads)
            print(f"  ✅ {len(ads)} annonces du cluster {cluster_name}")
        
        # Déduplication
        seen_urls = set()
        unique_ads = []
        for ad in all_ads:
            url = ad.get('landing_page_url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_ads.append(ad)
        
        print(f"\n✅ {len(unique_ads)} annonces uniques scrapées")
        return unique_ads
    
    def get_landing_pages_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques par landing page (pour scoring)"""
        return {
            url: {
                'ads_count': len(ads),
                'ads': ads,
                'first_seen': min(ad.get('scraped_at', '') for ad in ads),
                'last_seen': max(ad.get('scraped_at', '') for ad in ads),
            }
            for url, ads in self.landing_pages_map.items()
        }

