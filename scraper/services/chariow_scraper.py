"""
Scraper Chariow - Détection exacte des produits via pattern prd_
"""
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
import re
import asyncio
from urllib.parse import urljoin, urlparse
from datetime import datetime


class ChariowScraper:
    """Scraper pour les boutiques et produits Chariow"""
    
    def __init__(self):
        self.marketplace = "chariow"
        self.base_url = "https://chariow.com"
        # Pattern pour détecter les produits Chariow
        self.product_pattern = re.compile(r'/prd_([a-zA-Z0-9]+)')
    
    async def scrape_shop(self, shop_url: str) -> Dict[str, Any]:
        """
        Scrape une boutique Chariow complète
        Pattern boutique: https://<nom>.mychariow.shop/fr
        """
        # Normaliser l'URL de la boutique (exactement comme Maketou)
        shop_url = shop_url.rstrip('/')  # Enlever les slashes finaux
        if not shop_url.endswith('/fr'):
            shop_url = shop_url + '/fr'
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            page = await browser.new_page()
            
            try:
                print(f"  📦 Chargement boutique: {shop_url}")
                await page.goto(shop_url, wait_until="networkidle", timeout=60000)
                
                # Attendre que React/Next.js charge les produits (exactement comme Maketou)
                print(f"  ⏳ Attente du chargement React/Next.js...")
                await page.wait_for_timeout(3000)
                
                # Attendre que les produits soient visibles dans le DOM
                try:
                    await page.wait_for_selector('div[class*="grid"], a[href*="/prd_"], a[href*="/checkout"]', timeout=15000)
                    print(f"  ✅ Produits détectés dans le DOM")
                except:
                    print(f"  ⚠️ Timeout - produits peut-être pas encore chargés, on continue...")
                
                # Scroll multiple pour charger tout le contenu dynamique (COMME MAKETOU)
                for scroll_attempt in range(5):
                    content_before = len(await page.content())
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                    await page.evaluate("window.scrollTo(0, 0)")
                    await page.wait_for_timeout(1000)
                    content_after = len(await page.content())
                    if content_before == content_after:
                        break
                
                # Attendre encore un peu après le scroll pour que tout soit chargé (COMME MAKETOU)
                await page.wait_for_timeout(3000)
                
                content = await page.content()
                try:
                    soup = BeautifulSoup(content, 'lxml')
                except:
                    soup = BeautifulSoup(content, 'html.parser')
                
                # Extraire le nom de la boutique
                shop_name = self._extract_shop_name(soup, shop_url)
                
                # Détecter les produits sur toutes les pages (gestion pagination explicite comme Maketou)
                all_product_urls = set()
                max_pages = 20  # Limite de sécurité
                # Lire le nombre total de pages depuis la nav
                try:
                    pagination_total = await page.evaluate("""
                        () => {
                            const nav = document.querySelector('nav[aria-label*="pagination"], nav[data-slot="base"][aria-label*="pagination"]');
                            if (!nav) return 1;
                            const totalAttr = nav.getAttribute('data-total');
                            const total = totalAttr ? parseInt(totalAttr, 10) : 1;
                            return isNaN(total) ? 1 : total;
                        }
                    """)
                except Exception:
                    pagination_total = 1
                total_pages = max(1, min(pagination_total, max_pages))
                
                base_shop = shop_url.split('?')[0].rstrip('/')
                
                for page_index in range(total_pages):
                    current_page = page_index + 1
                    page_url = base_shop if current_page == 1 else f"{base_shop}?page={current_page}"
                    
                    if current_page > 1:
                        print(f"  📄 Navigation vers la page {current_page}: {page_url}")
                        try:
                            await page.goto(page_url, wait_until="networkidle", timeout=60000)
                            await page.wait_for_timeout(3000)
                        except Exception as e:
                            print(f"  ⚠️ Erreur navigation page {current_page}: {e}")
                            continue
                    
                    print(f"  📄 Page {current_page}...")
                    
                    # Recharger le contenu et le soup
                    content = await page.content()
                    try:
                        soup = BeautifulSoup(content, 'lxml')
                    except:
                        soup = BeautifulSoup(content, 'html.parser')
                    
                    # Détecter les produits sur la page actuelle (JS + HTML) - EXACTEMENT COMME MAKETOU
                    print(f"    🔍 Début détection produits (page {current_page})...")
                    try:
                        product_urls_js = await self._find_product_urls_playwright(page, shop_url)
                        print(f"    🔍 {len(product_urls_js)} produits détectés via JavaScript")
                        if len(product_urls_js) == 0:
                            print(f"    ⚠️ Aucun produit trouvé via JavaScript - vérification en cours...")
                    except Exception as e:
                        print(f"    ⚠️ Erreur lors de la détection JS: {e}")
                        import traceback
                        traceback.print_exc()
                        product_urls_js = []
                    
                    try:
                        product_urls_html = self._find_product_urls(soup, shop_url)
                        print(f"    🔍 {len(product_urls_html)} produits détectés via HTML parsing")
                        if len(product_urls_html) == 0:
                            print(f"    ⚠️ Aucun produit trouvé via HTML - vérification en cours...")
                    except Exception as e:
                        print(f"    ⚠️ Erreur lors de la détection HTML: {e}")
                        import traceback
                        traceback.print_exc()
                        product_urls_html = []
                    
                    # Vérifier les nouveaux produits
                    page_product_urls = set(product_urls_js + product_urls_html)
                    new_products = page_product_urls - all_product_urls
                    
                    if len(new_products) == 0:
                        print(f"    ℹ️ Aucun nouveau produit trouvé sur la page {current_page}")
                    else:
                        all_product_urls.update(page_product_urls)
                        print(f"    ✅ {len(new_products)} nouveaux produits (total: {len(all_product_urls)})")
                
                product_urls = list(all_product_urls)
                print(f"  ✅ {len(product_urls)} produits uniques détectés au total sur {total_pages} page(s)")
                
                # Construction rapide des produits depuis les scripts (COMME MAKETOU)
                page_content = await page.content()
                products = self._extract_products_from_scripts(page_content, shop_url)
                
                # Toujours essayer d'extraire depuis le DOM pour avoir les données les plus complètes (COMME MAKETOU)
                print(f"  🔍 Extraction DOM pour données complètes...")
                dom_products = await self._extract_products_from_dom(page, shop_url, product_urls)
                if dom_products and len(dom_products) > 0:
                    print(f"  ✅ {len(dom_products)} produits extraits depuis le DOM")
                    # Fusionner avec les produits existants (prioriser DOM)
                    if dom_products:
                        products_by_id = {p.get('slug') or p.get('id'): p for p in products if p.get('slug') or p.get('id')}
                        for dp in dom_products:
                            product_id = dp.get('slug') or dp.get('id')
                            if product_id:
                                if product_id in products_by_id:
                                    existing = products_by_id[product_id]
                                    if (dp.get('name') or dp.get('product_title')) and not (existing.get('name') or existing.get('product_title')):
                                        products_by_id[product_id] = {**existing, **dp}
                                    elif dp.get('price') and dp.get('price') > 0 and (not existing.get('price') or existing.get('price') == 0):
                                        products_by_id[product_id] = {**existing, **dp}
                                else:
                                    products_by_id[product_id] = dp
                        products = list(products_by_id.values())
                elif not products or len(products) == 0:
                    print(f"  ⚠️ Aucun produit extrait depuis scripts ni DOM")
                
                if products:
                    print(f"  ✅ {len(products)} produits finaux avec données complètes")
                    return {
                        "shop_name": shop_name,
                        "shop_url": shop_url,
                        "marketplace": self.marketplace,
                        "product_count": len(products),
                        "products": products,
                        "scraped_at": datetime.now().isoformat()
                    }
                
                # Sinon, scraper chaque produit (plus lent) - COMME MAKETOU
                products = []
                for i, product_url in enumerate(product_urls, 1):
                    try:
                        print(f"    [{i}/{len(product_urls)}] Scraping: {product_url[:60]}...")
                        product_data = await self.scrape_product(product_url, shop_name, shop_url)
                        if product_data:
                            products.append(product_data)
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"    ❌ Erreur scraping produit {product_url}: {e}")
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
        # Essayer plusieurs sélecteurs
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
                    return name
        
        # Fallback: extraire depuis l'URL
        parsed = urlparse(shop_url)
        shop_name = parsed.netloc.split('.')[0].replace('-', ' ').title()
        return shop_name
    
    def _find_product_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Trouve TOUS les URLs de produits via le pattern prd_ ou des IDs simples
        Patterns: 
        - https://<boutique>.mychariow.shop/prd_xxxxxx
        - https://<boutique>.mychariow.shop/1688 (ID numérique ou alphanumérique)
        """
        product_urls = set()
        parsed_base = urlparse(base_url)
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
        
        # Pattern pour détecter les IDs de produits (numériques ou alphanumériques courts)
        # Exclure les chemins comme /fr, /checkout, /cart, etc.
        id_pattern = re.compile(r'/([a-zA-Z0-9]{3,20})(?:[/?#]|$)')  # ID de 3 à 20 caractères
        excluded_paths = {'fr', 'checkout', 'cart', 'login', 'register', 'account', 'admin', 'api'}
        # Pages spéciales Chariow à exclure (ne sont pas des produits)
        excluded_product_ids = {
            'contact', 'about', 'terms', 'privacy', 'help', 'faq', 'support', 
            'shipping', 'returns', 'refund', 'policy', 'legal', 'cgv', 'mentions',
            'conditions', 'policies', 'info', 'information', 'blog', 'news'
        }
        
        # Méthode 1: Chercher tous les liens contenant prd_
        all_links = soup.find_all('a', href=True)
        print(f"    🔍 Debug HTML: {len(all_links)} liens trouvés dans le HTML")
        prd_links_found = 0
        filtered_count = 0
        for link in all_links:
            href = link.get('href', '')
            if not href:
                continue
            
            # Convertir en URL absolue
            if not href.startswith('http'):
                if href.startswith('/'):
                    href_abs = base_domain + href
                else:
                    href_abs = urljoin(base_url, href)
            else:
                href_abs = href
            
            # Ignorer les URLs externes
            if not href_abs.startswith(base_domain):
                continue
            
            # Vérifier si le lien contient le pattern prd_
            if '/prd_' in href or 'prd_' in href:
                # Extraire l'URL complète du produit
                match = self.product_pattern.search(href_abs)
                if match:
                    product_id = match.group(1)
                    # Exclure les pages spéciales (contact, about, etc.)
                    prd_links_found += 1
                    if product_id.lower() not in excluded_product_ids:
                        product_url = f"{base_domain}/prd_{product_id}"
                        product_urls.add(product_url)
                    else:
                        filtered_count += 1
                        print(f"    ⚠️ HTML: Produit filtré: prd_{product_id}")
                elif '/prd_' in href_abs:
                    # Même si le pattern ne match pas exactement, extraire l'URL
                    parts = href_abs.split('/prd_')
                    if len(parts) > 1:
                        product_id = parts[1].split('/')[0].split('?')[0]
                        if product_id and product_id.lower() not in excluded_product_ids:
                            product_url = f"{base_domain}/prd_{product_id}"
                            product_urls.add(product_url)
            else:
                # Méthode alternative: Détecter des IDs simples (comme /1688)
                # Mais seulement si le lien semble pointer vers un produit (pas /fr, /checkout, etc.)
                match = id_pattern.search(href_abs.replace(base_domain, ''))
                if match:
                    potential_id = match.group(1)
                    # Exclure les chemins connus, les IDs qui ressemblent à des chemins, et les pages spéciales
                    if (potential_id.lower() not in excluded_paths and 
                        potential_id.lower() not in excluded_product_ids and 
                        not potential_id.startswith('http')):
                        # Construire les deux formats possibles: /prd_ID et /ID
                        # On essaiera les deux, mais prd_ est le format canonique
                        product_url = f"{base_domain}/prd_{potential_id}"
                        product_urls.add(product_url)
        
        print(f"    🔍 Debug HTML: {prd_links_found} liens /prd_ trouvés, {filtered_count} filtrés")
        
        # Méthode 2: Chercher dans le texte de la page (pour les URLs dans le JS)
        page_text = str(soup)
        # Chercher /prd_XXXXX
        prd_matches = re.findall(r'/prd_([a-zA-Z0-9]+)', page_text)
        print(f"    🔍 Debug HTML regex: {len(prd_matches)} matches /prd_ dans le texte")
        for product_id in prd_matches:
            # Exclure les pages spéciales
            if product_id.lower() not in excluded_product_ids:
                product_url = f"{base_domain}/prd_{product_id}"
                product_urls.add(product_url)
            else:
                print(f"    ⚠️ HTML regex: Produit filtré: prd_{product_id}")
        
        # Chercher aussi des patterns comme /1688 dans le texte (mais être prudent)
        # On cherche des patterns qui semblent être des IDs de produits
        id_matches = re.findall(rf'{re.escape(base_domain)}/([a-zA-Z0-9]{{4,15}})(?:[/?#"]|$)', page_text)
        for product_id in id_matches:
            if (product_id.lower() not in excluded_paths and 
                product_id.lower() not in excluded_product_ids and 
                not product_id.startswith('http')):
                product_url = f"{base_domain}/prd_{product_id}"
                product_urls.add(product_url)
        
        # Méthode 3: Chercher dans les attributs data-*
        for elem in soup.find_all(attrs=True):
            for attr, value in elem.attrs.items():
                if isinstance(value, str):
                    if '/prd_' in value:
                        match = self.product_pattern.search(value)
                        if match:
                            product_id = match.group(1)
                            # Exclure les pages spéciales
                            if product_id.lower() not in excluded_product_ids:
                                product_url = f"{base_domain}/prd_{product_id}"
                                product_urls.add(product_url)
                    elif base_domain in value:
                        # Chercher aussi des IDs dans les attributs
                        match = re.search(rf'{re.escape(base_domain)}/([a-zA-Z0-9]{{4,15}})(?:[/?#"]|$)', value)
                        if match:
                            product_id = match.group(1)
                            if product_id.lower() not in excluded_paths and product_id.lower() not in excluded_product_ids:
                                product_url = f"{base_domain}/prd_{product_id}"
                                product_urls.add(product_url)
        
        return sorted(list(product_urls))
    
    async def _go_to_next_page(self, page, current_page: int) -> bool:
        """
        Essaie de naviguer vers la page suivante.
        Utilise des sélecteurs compatibles Playwright (locators) pour trouver
        les boutons/liens de pagination.
        Retourne True si une page suivante a été trouvée et chargée.
        """
        try:
            # Stratégie 1: boutons "Suivant / Next / › / »"
            next_texts = ["Suivant", "Next", "›", "»"]
            for text in next_texts:
                locator = page.locator(f"xpath=//a[contains(., '{text}') or //button[contains(., '{text}')]]")
                count = await locator.count()
                if count > 0:
                    # Cliquer sur le premier bouton non désactivé
                    for i in range(count):
                        btn = locator.nth(i)
                        try:
                            disabled = await btn.get_attribute("disabled")
                            classes = await btn.get_attribute("class") or ""
                            if disabled or "disabled" in classes:
                                continue
                            await btn.click()
                            await page.wait_for_timeout(2000)
                            return True
                        except Exception:
                            continue

            # Stratégie 2: lien vers la page suivante (numéro de page)
            next_page_number = current_page + 1
            page_locator = page.locator(
                f"xpath=//a[contains(@href, 'page={next_page_number}') or "
                f"contains(@href, 'p={next_page_number}') or text()='{next_page_number}']"
            )
            if await page_locator.count() > 0:
                try:
                    await page_locator.first.click()
                    await page.wait_for_timeout(2000)
                    return True
                except Exception:
                    pass

            # Stratégie 3: boutons "Voir plus / Load more / Afficher plus"
            more_texts = ["Voir plus", "Load more", "Afficher plus"]
            for text in more_texts:
                locator = page.locator(f"xpath=//a[contains(., '{text}')] | //button[contains(., '{text}')]")
                count = await locator.count()
                if count > 0:
                    try:
                        await locator.first.click()
                        await page.wait_for_timeout(3000)
                        return True
                    except Exception:
                        continue

            return False

        except Exception as e:
            print(f"    ⚠️ Erreur lors de la recherche de la page suivante: {e}")
            return False
    
    async def _find_product_urls_playwright(self, page, base_url: str) -> List[str]:
        """
        Trouve les URLs de produits via Playwright (DOM live) - EXACTEMENT COMME MAKETOU
        Pour Chariow, les produits sont chargés via React/Next.js, donc on doit attendre le rendu complet.
        """
        product_urls = set()
        parsed_base = urlparse(base_url)
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
        excluded_product_ids = {
            'contact', 'about', 'terms', 'privacy', 'help', 'faq', 'support', 
            'shipping', 'returns', 'refund', 'policy', 'legal', 'cgv', 'mentions',
            'conditions', 'policies', 'info', 'information', 'blog', 'news'
        }
        
        try:
            # Stratégie 1: Extraire les IDs produits depuis les données JSON dans les scripts Next.js (COMME MAKETOU)
            print(f"      🔍 Extraction depuis les scripts Next.js...")
            page_content = await page.content()
            # Chercher les IDs dans les scripts (pattern prd_XXXXX ou juste l'ID)
            # MAIS exclure les IDs de boutique (store_*) et autres IDs non-produits
            product_ids_raw = re.findall(r'"id":"([^"]+)"', page_content)
            product_ids_escaped = re.findall(r'\\"id\\":\\"([^\\"]+)\\"', page_content)
            # Chercher aussi /prd_ dans les scripts (ceux-là sont sûrement des produits)
            prd_ids = re.findall(r'/prd_([a-zA-Z0-9_-]+)', page_content)
            
            # Filtrer : exclure les IDs de boutique (store_*) et autres patterns non-produits
            all_ids = list(set(product_ids_raw + product_ids_escaped + prd_ids))
            product_ids_from_scripts = []
            for pid in all_ids:
                pid_lower = pid.lower()
                # Exclure les IDs de boutique
                if pid_lower.startswith('store_'):
                    continue
                # Exclure les IDs trop courts ou trop longs (probablement pas des produits)
                if len(pid) < 3 or len(pid) > 50:
                    continue
                # Exclure les pages spéciales
                if pid_lower in excluded_product_ids:
                    continue
                product_ids_from_scripts.append(pid)
            
            if product_ids_from_scripts:
                print(f"      ✅ {len(product_ids_from_scripts)} IDs produits trouvés dans les scripts")
                for product_id in product_ids_from_scripts:
                    product_url = f"{base_domain}/prd_{product_id}"
                    product_urls.add(product_url)
                print(f"      📋 Exemples IDs: {product_ids_from_scripts[:3]}")
            else:
                print(f"      ⚠️ Aucun ID produit trouvé dans les scripts (IDs bruts filtrés: {len(all_ids)})")
            
            # Stratégie 2: Chercher les liens dans le DOM (après rendu React) - COMME MAKETOU
            print(f"      🔍 Recherche dans le DOM...")
            total_links = await page.evaluate("() => document.querySelectorAll('a[href]').length")
            print(f"      🔗 Total liens sur la page: {total_links}")
            
            # Chercher les produits avec le pattern /prd_
            links = await page.evaluate(f"""
                () => {{
                    const base = '{base_domain}';
                    const excludedIds = ['contact', 'about', 'terms', 'privacy', 'help', 'faq', 'support', 
                                         'shipping', 'returns', 'refund', 'policy', 'legal', 'cgv', 'mentions',
                                         'conditions', 'policies', 'info', 'information', 'blog', 'news'];
                    const out = [];
                    document.querySelectorAll('a[href]').forEach(a => {{
                        let href = a.getAttribute('href') || a.href || '';
                        if (!href || href.startsWith('#')) return;
                        
                        // Convertir en URL absolue
                        if (!href.startsWith('http')) {{
                            if (href.startsWith('/')) href = base + href;
                            else href = base + '/' + href;
                        }}
                        
                        // Nettoyer
                        href = href.split('#')[0].split('?')[0];
                        
                        // Vérifier si c'est un produit (pattern /prd_)
                        if (href.startsWith(base) && href.includes('/prd_')) {{
                            const match = href.match(/\\/prd_([a-zA-Z0-9]+)/);
                            if (match) {{
                                const productId = match[1].toLowerCase();
                                // Exclure les pages spéciales
                                if (!excludedIds.includes(productId)) {{
                                    out.push(href);
                                }}
                            }}
                        }}
                    }});
                    return Array.from(new Set(out));
                }}
            """)
            
            print(f"      ✅ {len(links)} produits trouvés via DOM")
            if len(links) > 0:
                print(f"      📋 Exemples DOM: {links[:3]}")
            
            for href in links:
                product_urls.add(href)
            
            # Stratégie 3: Chercher les boutons "Acheter" et remonter au produit parent - COMME MAKETOU
            print(f"      🔍 Recherche via boutons 'Acheter'...")
            buy_buttons = await page.evaluate(f"""
                () => {{
                    const base = '{base_domain}';
                    const excludedIds = ['contact', 'about', 'terms', 'privacy', 'help', 'faq', 'support', 
                                         'shipping', 'returns', 'refund', 'policy', 'legal', 'cgv', 'mentions',
                                         'conditions', 'policies', 'info', 'information', 'blog', 'news'];
                    const urls = [];
                    // Chercher tous les boutons avec texte "Acheter" ou "Commander"
                    const buttons = Array.from(document.querySelectorAll('button, a'));
                    buttons.forEach(btn => {{
                        const text = (btn.textContent || '').toLowerCase();
                        if (text.includes('acheter') || text.includes('commander') || text.includes('buy')) {{
                            // Remonter pour trouver le lien produit parent
                            let parent = btn.closest('div[class*="product"], div[class*="card"], article, a');
                            while (parent && parent.tagName !== 'A' && parent !== document.body) {{
                                parent = parent.parentElement;
                            }}
                            if (parent && parent.tagName === 'A' && parent.href) {{
                                let href = parent.href;
                                if (!href.startsWith('http')) {{
                                    if (href.startsWith('/')) href = base + href;
                                    else href = base + '/' + href;
                                }}
                                if (href.includes('/prd_')) {{
                                    const match = href.match(/\\/prd_([a-zA-Z0-9]+)/);
                                    if (match) {{
                                        const productId = match[1].toLowerCase();
                                        if (!excludedIds.includes(productId)) {{
                                            urls.push(href.split('#')[0].split('?')[0]);
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }});
                    return Array.from(new Set(urls));
                }}
            """)
            
            if buy_buttons:
                print(f"      ✅ {len(buy_buttons)} produits trouvés via boutons")
                for href in buy_buttons:
                    product_urls.add(href)
                
        except Exception as e:
            print(f"    ⚠️ Erreur détection JS produits: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"      ✅ Total produits uniques trouvés: {len(product_urls)}")
        return sorted(list(product_urls))
    
    def _extract_products_from_scripts(self, page_content: str, shop_url: str) -> List[dict]:
        """
        Extrait les produits directement depuis le JSON des scripts Next.js - COMME MAKETOU
        Rapide et évite de scraper chaque page produit.
        """
        products = []
        parsed = urlparse(shop_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        # Essayer d'abord de parser le JSON complet depuis les scripts Next.js
        import json
        try:
            # Chercher les scripts qui contiennent les données produits
            script_patterns = [
                r'"products"\s*:\s*\[(.*?)\]',  # Pattern products array
                r'products.*?\[(.*?)\]',  # Pattern plus flexible
            ]
            
            for pattern in script_patterns:
                matches = re.findall(pattern, page_content, re.S | re.I)
                for match in matches:
                    try:
                        json_str = '[' + match + ']'
                        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                        products_data = json.loads(json_str)
                        if isinstance(products_data, list) and len(products_data) > 0:
                            print(f"      ✅ {len(products_data)} produits parsés depuis JSON")
                            for p in products_data:
                                if isinstance(p, dict) and (p.get('id') or p.get('slug')):
                                    product_id = p.get('id') or p.get('slug')
                                    name = p.get('name') or p.get('title') or p.get('product_title') or product_id
                                    price_val = p.get('price') or p.get('original_price')
                                    promo_val = p.get('promotedPrice') or p.get('promo_price') or p.get('promotionalPrice')
                                    image = p.get('featuredImage') or p.get('image') or p.get('product_image')
                                    
                                    url = f"{base}/prd_{product_id}"
                                    products.append({
                                        "product_title": name,
                                        "name": name,
                                        "title": name,
                                        "product_url": url,
                                        "url": url,
                                        "price": promo_val or price_val or 0,
                                        "promotedPrice": promo_val,
                                        "promo_price": promo_val,
                                        "original_price": price_val,
                                        "images": [image] if image else [],
                                        "image": image,
                                        "featuredImage": image,
                                        "description": p.get('description') or p.get('shortDescription'),
                                        "slug": product_id,
                                        "id": product_id,
                                        "marketplace": "chariow",
                                    })
                            if products:
                                seen = set()
                                unique_products = []
                                for p in products:
                                    product_id = p.get('slug') or p.get('id')
                                    if product_id and product_id not in seen:
                                        seen.add(product_id)
                                        unique_products.append(p)
                                return unique_products
                    except (json.JSONDecodeError, ValueError) as e:
                        continue
        except Exception as e:
            print(f"      ⚠️ Erreur parsing JSON complet: {e}")
        
        # Fallback: méthode regex - chercher /prd_ dans les scripts (EXACTEMENT COMME MAKETOU avec slug)
        prd_matches = re.findall(r'/prd_([a-zA-Z0-9_-]+)', page_content)
        unique_ids = list(dict.fromkeys(prd_matches))
        print(f"      🔍 Fallback regex: {len(unique_ids)} IDs trouvés")
        
        excluded_ids = {'contact', 'about', 'terms', 'privacy', 'help', 'faq', 'support'}
        for product_id in unique_ids:
            # Exclure les IDs de boutique (store_*)
            if product_id and product_id.lower().startswith('store_'):
                continue
            if product_id.lower() in excluded_ids:
                continue
            # Ignorer les IDs trop courts ou trop longs
            if len(product_id) < 3 or len(product_id) > 50:
                continue
            # Chercher les données autour de l'ID dans les scripts
            name = None
            price = None
            image = None
            
            # Chercher un bloc JSON autour de l'ID
            block_pattern = r'\{[^}]*"id"\s*:\s*"%s"[^}]*\}' % re.escape(product_id)
            block_match = re.search(block_pattern, page_content, re.S)
            if block_match:
                block = block_match.group(0)
                name_m = re.search(r'"name"\s*:\s*"([^"]+)"', block)
                if name_m:
                    name = name_m.group(1)
                price_m = re.search(r'"price"\s*:\s*(\d+(?:\.\d+)?)', block)
                if price_m:
                    price = float(price_m.group(1))
            
            url = f"{base}/prd_{product_id}"
            products.append({
                "product_title": name or product_id,
                "name": name or product_id,
                "title": name or product_id,
                "product_url": url,
                "url": url,
                "price": price or 0,
                "slug": product_id,
                "id": product_id,
                "marketplace": "chariow",
            })
        
        return products
    
    async def _extract_products_from_dom(self, page, shop_url: str, product_urls: List[str]) -> List[dict]:
        """
        Extrait les produits depuis le DOM directement avec Playwright pour Chariow.
        Pattern: /prd_<id>
        """
        products = []
        parsed = urlparse(shop_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        try:
            # Extraire directement depuis le DOM - SIMPLE comme demandé
            products_data = await page.evaluate(f"""
                () => {{
                    const base = '{base}';
                    const products = [];
                    const seen = new Set();
                    
                    // Chercher tous les boutons "Acheter" qui ont /prd_xxx/checkout
                    const buyButtons = Array.from(document.querySelectorAll('a[href*="/prd_"]'));
                    
                    for (const button of buyButtons) {{
                        const href = button.getAttribute('href') || button.href || '';
                        if (!href) continue;
                        
                        // Extraire l'ID produit depuis /prd_xxx/checkout ou /prd_xxx
                        const prdMatch = href.match(/\\/prd_([a-zA-Z0-9]+)/);
                        if (!prdMatch) continue;
                        
                        const productId = prdMatch[1];
                        if (productId.startsWith('store_') || seen.has(productId)) continue;
                        seen.add(productId);
                        
                        // Trouver le conteneur parent (carte produit)
                        const container = button.closest('div, article');
                        if (!container) continue;
                        
                        // Extraire le titre
                        let title = '';
                        const titleEl = container.querySelector('[class*="Text-root"][class*="text-lg"], [class*="Text-root"][class*="text-u"], h1, h2, h3, h4');
                        if (titleEl) {{
                            title = titleEl.textContent.trim();
                        }}
                        if (!title || title.length < 3) continue;
                        
                        // Extraire l'image
                        let image = null;
                        const img = container.querySelector('img');
                        if (img) image = img.src || img.getAttribute('data-src') || img.getAttribute('src');
                        
                        // Extraire le prix (chercher le prix en rouge - le prix promo)
                        let price = 0;
                        const priceEls = container.querySelectorAll('span[class*="text-red"], span[class*="Text-root"]');
                        for (const priceEl of priceEls) {{
                            const priceText = priceEl.textContent || '';
                            const priceMatch = priceText.match(/([\\d\\s\\u00A0,]+)\\s*(?:F\\s*CFA|FCFA|XOF|€|\\$)/i);
                            if (priceMatch) {{
                                const numStr = priceMatch[1].replace(/[\\s\\u00A0,]/g, '').replace(/\\.(?!\\d)/g, '');
                                const parsed = parseFloat(numStr);
                                if (!isNaN(parsed) && parsed > 0) {{
                                    price = parsed;
                                    break;
                                }}
                            }}
                        }}
                        
                        // Construire l'URL produit canonique
                        const productUrl = base + '/prd_' + productId;
                        
                        products.push({{
                            name: title,
                            title: title,
                            product_title: title,
                            id: productId,
                            product_url: productUrl,
                            url: productUrl,
                            price: price,
                            promotedPrice: price,
                            promo_price: price,
                            image: image,
                            featuredImage: image,
                            images: image ? [image] : [],
                            slug: productId
                        }});
                    }}
                    
                    return products;
                }}
            """)
            
            if products_data and len(products_data) > 0:
                for p in products_data:
                    p['marketplace'] = 'chariow'
                products = products_data
            
        except Exception as e:
            print(f"  ⚠️ Erreur extraction DOM: {e}")
            import traceback
            traceback.print_exc()
        
        return products
    
    async def scrape_product(self, product_url: str, shop_name: str = "", shop_url: str = "") -> Optional[Dict[str, Any]]:
        """
        Scrape un produit Chariow individuel
        Pattern: https://<boutique>.mychariow.shop/prd_<id>
        """
        # Vérifier d'abord si c'est une page spéciale à exclure
        excluded_product_ids = {
            'contact', 'about', 'terms', 'privacy', 'help', 'faq', 'support', 
            'shipping', 'returns', 'refund', 'policy', 'legal', 'cgv', 'mentions',
            'conditions', 'policies', 'info', 'information', 'blog', 'news'
        }
        
        # Extraire l'ID du produit depuis l'URL
        match = self.product_pattern.search(product_url)
        if match:
            product_id = match.group(1).lower()
            # Exclure les IDs de boutique (store_*)
            if product_id.startswith('store_'):
                return None
            if product_id in excluded_product_ids:
                # C'est une page spéciale, pas un produit
                return None
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            page = await browser.new_page()
            
            try:
                # Essayer d'abord avec domcontentloaded (plus rapide)
                try:
                    await page.goto(product_url, wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(2000)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=15000)
                    except:
                        pass  # Continuer même si networkidle timeout
                except Exception as e:
                    # Si domcontentloaded échoue, essayer avec load
                    try:
                        await page.goto(product_url, wait_until="load", timeout=20000)
                        await page.wait_for_timeout(2000)
                    except:
                        # Dernier recours: sans wait_until
                        await page.goto(product_url, timeout=20000)
                        await page.wait_for_timeout(3000)
                
                content = await page.content()
                try:
                    soup = BeautifulSoup(content, 'lxml')
                except:
                    soup = BeautifulSoup(content, 'html.parser')
                
                # Extraire l'ID du produit depuis l'URL
                match = self.product_pattern.search(product_url)
                product_id = match.group(1) if match else product_url.split('/prd_')[-1] if '/prd_' in product_url else None
                
                # Extraire toutes les données
                title = self._extract_title(soup)
                # Essayer d'abord avec Playwright pour une meilleure précision
                price = await self._extract_price_playwright(page)
                if price == 0:
                    # Fallback sur BeautifulSoup
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
    
    async def _extract_price_playwright(self, page) -> float:
        """Extrait le prix en utilisant Playwright pour exécuter du JavaScript"""
        try:
            # Attendre un peu pour le chargement dynamique
            await page.wait_for_timeout(2000)
            
            # Exécuter du JavaScript pour trouver le prix dans le DOM
            # Stratégie: chercher TOUS les textes contenant FCFA, puis extraire le prix
            price = await page.evaluate("""
                () => {
                    // Fonction pour nettoyer et parser un prix
                    function parsePrice(text) {
                        // Chercher un prix avec FCFA (format: "3 605 F CFA" avec espaces insécables)
                        const fcfaMatch = text.match(/([\\d\\s,\\.]+)\\s*F\\s*CFA/i) || 
                                         text.match(/([\\d\\s,\\.]+)\\s*FCFA/i) ||
                                         text.match(/F\\s*CFA\\s*([\\d\\s,\\.]+)/i) ||
                                         text.match(/FCFA\\s*([\\d\\s,\\.]+)/i);
                        
                        if (!fcfaMatch) return null;
                        
                        // Nettoyer: remplacer espaces insécables (\u00A0), espaces normaux, virgules
                        let priceStr = fcfaMatch[1].replace(/[\\u00A0\\s,]/g, '');
                        
                        // Gérer les points: si c'est un séparateur de milliers (ex: 3.605), on le garde
                        // Si c'est un décimal (ex: 3.5), on le convertit
                        if (priceStr.includes('.')) {
                            const parts = priceStr.split('.');
                            if (parts.length === 2 && parts[1].length <= 2) {
                                // C'est un décimal, convertir en entier
                                priceStr = parts[0] + parts[1];
                            } else {
                                // C'est un séparateur de milliers, supprimer le point
                                priceStr = priceStr.replace(/\\./g, '');
                            }
                        }
                        
                        const price = parseFloat(priceStr);
                        // Filtrer les années (2000-2099) et les valeurs trop élevées
                        if (price >= 100 && price <= 1000000 && !(price >= 2000 && price <= 2099 && priceStr.length <= 4)) {
                            return price;
                        }
                        return null;
                    }
                    
                    // 1. Chercher dans tous les éléments avec "raiton-Text-root"
                    const chariowSelectors = [
                        'div[class*="raiton-Text-root"]',
                        'span[class*="raiton-Text-root"]',
                        'p[class*="raiton-Text-root"]',
                    ];
                    
                    for (const selector of chariowSelectors) {
                        try {
                            const elems = document.querySelectorAll(selector);
                            for (const elem of elems) {
                                const text = elem.textContent || elem.innerText || '';
                                const price = parsePrice(text);
                                if (price) return price;
                            }
                        } catch (e) {
                            // Ignorer les erreurs de sélecteur
                        }
                    }
                    
                    // 2. Chercher dans TOUS les éléments contenant "FCFA" ou "F CFA"
                    const allElements = document.querySelectorAll('*');
                    const fcfaTexts = [];
                    for (const elem of allElements) {
                        const text = elem.textContent || elem.innerText || '';
                        if ((text.includes('FCFA') || text.includes('F CFA') || text.includes('franc')) && 
                            elem.children.length === 0) {  // Élément feuille seulement
                            const price = parsePrice(text);
                            if (price) {
                                fcfaTexts.push({price: price, text: text.substring(0, 100)});
                            }
                        }
                    }
                    
                    // Prendre le prix le plus probable (le plus petit qui est dans la plage valide)
                    if (fcfaTexts.length > 0) {
                        // Trier par prix croissant et prendre le premier valide
                        fcfaTexts.sort((a, b) => a.price - b.price);
                        for (const item of fcfaTexts) {
                            if (item.price >= 100 && item.price <= 1000000) {
                                return item.price;
                            }
                        }
                    }
                    
                    // 3. Fallback: chercher dans les attributs data
                    const dataPriceElems = document.querySelectorAll('[data-price]');
                    for (const elem of dataPriceElems) {
                        const price = parseFloat(elem.getAttribute('data-price'));
                        if (price >= 100 && price <= 1000000) {
                            return price;
                        }
                    }
                    
                    // 4. Dernier recours: chercher n'importe quel nombre suivi de FCFA dans tout le body
                    const bodyText = document.body.textContent || '';
                    const price = parsePrice(bodyText);
                    if (price) return price;
                    
                    return null;
                }
            """)
            
            if price and 100 <= price <= 1000000:
                return float(price)
        except Exception as e:
            print(f"      ⚠️  Erreur extraction prix Playwright: {e}")
            import traceback
            traceback.print_exc()
        
        return 0.0
    
    def _extract_price(self, soup: BeautifulSoup) -> float:
        """Extrait le prix en FCFA depuis BeautifulSoup (fallback)"""
        def parse_price_from_text(text: str) -> float:
            """Parse un prix depuis un texte"""
            # Chercher un prix avec FCFA
            fcfa_match = (re.search(r'([\d\s,\.]+)\s*F\s*CFA', text, re.IGNORECASE) or 
                         re.search(r'([\d\s,\.]+)\s*FCFA', text, re.IGNORECASE) or
                         re.search(r'F\s*CFA\s*([\d\s,\.]+)', text, re.IGNORECASE) or
                         re.search(r'FCFA\s*([\d\s,\.]+)', text, re.IGNORECASE))
            
            if not fcfa_match:
                return 0.0
            
            try:
                # Nettoyer: remplacer espaces insécables (\u00A0), espaces, virgules
                price_str = fcfa_match.group(1).replace('\u00A0', '').replace(',', '').replace(' ', '').strip()
                # Gérer les points: séparateur de milliers ou décimal
                if '.' in price_str:
                    parts = price_str.split('.')
                    if len(parts) == 2 and len(parts[1]) <= 2:
                        # Décimal, convertir
                        price_str = parts[0] + parts[1]
                    else:
                        # Séparateur de milliers, supprimer
                        price_str = price_str.replace('.', '')
                price_val = float(price_str)
                # Filtrer les années (2000-2099) et valeurs suspectes
                if 100 <= price_val <= 1000000 and not (2000 <= price_val <= 2099 and len(price_str) <= 4):
                    return price_val
            except (ValueError, AttributeError):
                pass
            return 0.0
        
        # 1. Chercher dans tous les éléments avec "raiton-Text-root"
        chariow_selectors = [
            'div[class*="raiton-Text-root"]',
            'span[class*="raiton-Text-root"]',
            'p[class*="raiton-Text-root"]',
        ]
        
        for selector in chariow_selectors:
            try:
                elems = soup.select(selector)
                for elem in elems:
                    price_text = elem.get_text(strip=True)
                    price = parse_price_from_text(price_text)
                    if price > 0:
                        return price
            except Exception:
                continue
        
        # 2. Chercher dans TOUS les éléments contenant "FCFA" ou "F CFA"
        all_elements = soup.find_all(string=re.compile(r'FCFA|F\s*CFA|franc', re.IGNORECASE))
        prices_found = []
        for text_node in all_elements:
            if text_node.parent:
                price_text = text_node.parent.get_text(strip=True)
                price = parse_price_from_text(price_text)
                if price > 0:
                    prices_found.append(price)
        
        if prices_found:
            # Prendre le prix le plus petit valide
            prices_found.sort()
            for p in prices_found:
                if 100 <= p <= 1000000:
                    return p
        
        # 3. Fallback: chercher dans les attributs data
        data_price_elems = soup.select('[data-price]')
        for elem in data_price_elems:
            try:
                price_val = float(elem.get('data-price', 0))
                if 100 <= price_val <= 1000000:
                    return price_val
            except (ValueError, TypeError):
                continue
        
        # 4. Dernier recours: chercher dans tout le body
        body_text = soup.get_text()
        price = parse_price_from_text(body_text)
        if price > 0:
            return price
        
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
                    # Nettoyer srcset
                    if ' ' in img_src:
                        img_src = img_src.split(' ')[0]
                    
                    # Convertir en URL absolue
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    elif img_src.startswith('/'):
                        img_src = urljoin(base_url, img_src)
                    elif not img_src.startswith('http'):
                        img_src = urljoin(base_url, img_src)
                    
                    # Éviter les doublons et les images de placeholder
                    if img_src not in seen_urls and 'placeholder' not in img_src.lower():
                        images.append(img_src)
                        seen_urls.add(img_src)
        
        return images[:10]  # Limiter à 10 images
    
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
                # Chercher un nombre entre 0 et 5
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

