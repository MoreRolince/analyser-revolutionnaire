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
        shop_url = shop_url.rstrip('/')  # Enlever les slashes finaux
        if not shop_url.endswith('/fr'):
            shop_url = shop_url + '/fr'
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            page = await browser.new_page()
            
            try:
                print(f"  📦 Chargement boutique: {shop_url}")
                await page.goto(shop_url, wait_until="networkidle", timeout=60000)
                
                # Attendre que React/Next.js charge les produits (plus long pour les SPAs)
                print(f"  ⏳ Attente du chargement React/Next.js...")
                await page.wait_for_timeout(3000)  # Attendre 3 secondes pour React (réduit pour gagner du temps)
                
                # Attendre que les produits soient visibles dans le DOM
                try:
                    # Chercher des éléments de produits (cartes, grilles, etc.)
                    await page.wait_for_selector('div[class*="grid"], div[class*="product"], a[href*="/products/"]', timeout=10000)
                    print(f"  ✅ Produits détectés dans le DOM")
                except:
                    print(f"  ⚠️ Timeout - produits peut-être pas encore chargés, on continue...")
                
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
                
                # Attendre encore un peu après le scroll pour que tout soit chargé
                await page.wait_for_timeout(2000)
                
                content = await page.content()
                try:
                    soup = BeautifulSoup(content, 'lxml')
                except:
                    soup = BeautifulSoup(content, 'html.parser')
                
                # Extraire le nom de la boutique
                shop_name = self._extract_shop_name(soup, shop_url)
                
                # Détecter les produits sur toutes les pages (gestion pagination explicite)
                all_product_urls = set()
                max_pages = 20  # Limite de sécurité
                # Lire le nombre total de pages depuis la nav (data-total)
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
                    
                    # Détecter les produits sur la page actuelle (JS + HTML)
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
                
                # Construction rapide des produits depuis les scripts (nom, prix, image, slug)
                page_content = await page.content()
                products = self._extract_products_from_scripts(page_content, shop_url)
                
                # Toujours essayer d'extraire depuis le DOM pour avoir les données les plus complètes
                print(f"  🔍 Extraction DOM pour données complètes...")
                dom_products = await self._extract_products_from_dom(page, shop_url)
                if dom_products and len(dom_products) > 0:
                    print(f"  ✅ {len(dom_products)} produits extraits depuis le DOM")
                    # Fusionner avec les produits existants (prioriser DOM car plus fiable)
                    if dom_products:
                        # Créer un dict par slug pour fusionner
                        products_by_slug = {p.get('slug'): p for p in products if p.get('slug')}
                        for dp in dom_products:
                            slug = dp.get('slug')
                            if slug:
                                # Prioriser DOM si il a des données complètes
                                if slug in products_by_slug:
                                    existing = products_by_slug[slug]
                                    # Remplacer si DOM a plus d'infos (titre ou prix)
                                    if (dp.get('name') or dp.get('product_title')) and not (existing.get('name') or existing.get('product_title')):
                                        products_by_slug[slug] = {**existing, **dp}
                                    elif dp.get('price') and dp.get('price') > 0 and (not existing.get('price') or existing.get('price') == 0):
                                        products_by_slug[slug] = {**existing, **dp}
                                    # Sinon garder l'existant
                                else:
                                    products_by_slug[slug] = dp
                        products = list(products_by_slug.values())
                elif not products or len(products) == 0:
                    print(f"  ⚠️ Aucun produit extrait depuis scripts ni DOM")
                
                if products:
                    print(f"  ✅ {len(products)} produits finaux avec données complètes")
                    print(f"  📋 Exemples produits: {[{'name': p.get('name') or p.get('product_title'), 'price': p.get('price'), 'slug': p.get('slug')} for p in products[:3]]}")
                    return {
                        "shop_name": shop_name,
                        "shop_url": shop_url,
                        "marketplace": self.marketplace,
                        "product_count": len(products),
                        "products": products,
                        "scraped_at": datetime.now().isoformat()
                    }
                
                # Sinon, scraper chaque produit (plus lent)
                products = []
                for i, product_url in enumerate(product_urls, 1):
                    try:
                        print(f"    [{i}/{len(product_urls)}] Scraping: {product_url[:60]}...")
                        product_data = await self.scrape_product(product_url, shop_name, shop_url)
                        if product_data:
                            products.append(product_data)
                        await asyncio.sleep(0.02)  # Pause minimale entre produits
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
        
        # DEBUG: Compter les liens
        all_links = soup.find_all('a', href=True)
        print(f"      🔗 Total liens HTML: {len(all_links)}")
        
        # Méthode 1: Chercher tous les liens contenant /products/
        products_found_html = []
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
                    products_found_html.append(href)
        
        print(f"      🔗 Liens avec /products/ trouvés: {len(products_found_html)}")
        if len(products_found_html) > 0:
            print(f"      📋 Exemples HTML: {products_found_html[:3]}")
        
        # Méthode 2: Chercher dans le texte de la page (pour les URLs dans le JS)
        page_text = str(soup)
        products_matches = re.findall(r'/products/([a-zA-Z0-9\-]+)', page_text)
        print(f"      🔗 Pattern /products/ trouvés dans le texte: {len(products_matches)}")
        for product_slug in products_matches:
            product_url = f"{base_domain}/products/{product_slug}"
            product_urls.add(product_url)
        
        # Méthode 3: Chercher dans les attributs data-*
        data_products = []
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
                        data_products.append(value)
        
        print(f"      🔗 Produits trouvés dans data-*: {len(data_products)}")
        
        return sorted(list(product_urls))
    
    async def _find_product_urls_playwright(self, page, base_url: str) -> List[str]:
        """
        Trouve les URLs de produits via Playwright (DOM live), utile si le contenu est chargé dynamiquement.
        Pour Maketou, les produits sont chargés via React/Next.js, donc on doit attendre le rendu complet.
        """
        product_urls = set()
        parsed_base = urlparse(base_url)
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
        try:
            # Stratégie 1: Extraire les slugs depuis les données JSON dans les scripts Next.js
            print(f"      🔍 Extraction depuis les scripts Next.js...")
            page_content = await page.content()
            # Deux patterns: brut et échappé
            slugs_raw = re.findall(r'"slug":"([^"]+)"', page_content)
            slugs_escaped = re.findall(r'\\"slug\\":\\"([^\\"]+)\\"', page_content)
            product_slugs_from_scripts = list(set(slugs_raw + slugs_escaped))
            
            if product_slugs_from_scripts:
                print(f"      ✅ {len(product_slugs_from_scripts)} slugs trouvés dans les scripts")
                for slug in product_slugs_from_scripts:
                    product_url = f"{base_domain}/fr/products/{slug}"
                    product_urls.add(product_url)
                print(f"      📋 Exemples slugs: {product_slugs_from_scripts[:3]}")
            
            # Stratégie 2: Chercher les liens dans le DOM (après rendu React)
            print(f"      🔍 Recherche dans le DOM...")
            total_links = await page.evaluate("() => document.querySelectorAll('a[href]').length")
            print(f"      🔗 Total liens sur la page: {total_links}")
            
            # Chercher les produits avec le pattern /products/
            links = await page.evaluate(f"""
                () => {{
                    const base = '{base_domain}';
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
                        
                        // Vérifier si c'est un produit (pattern /fr/products/ ou /products/)
                        if (href.startsWith(base) && (href.includes('/products/') || href.includes('/fr/products/')) && href !== base + '/products/' && href !== base + '/fr/products/') {{
                            out.push(href);
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
            
            # Stratégie 3: Chercher les boutons "Acheter" et remonter au produit parent
            print(f"      🔍 Recherche via boutons 'Acheter'...")
            buy_buttons = await page.evaluate(f"""
                () => {{
                    const base = '{base_domain}';
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
                                if (href.includes('/products/') || href.includes('/fr/products/')) {{
                                    urls.push(href.split('#')[0].split('?')[0]);
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
        Extrait les produits directement depuis le JSON des scripts Next.js.
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
                    # Essayer de parser le JSON complet
                    try:
                        # Nettoyer le match et essayer de parser
                        json_str = '[' + match + ']'
                        # Remplacer les valeurs non échappées problématiques
                        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)  # Enlever trailing commas
                        products_data = json.loads(json_str)
                        if isinstance(products_data, list) and len(products_data) > 0:
                            print(f"      ✅ {len(products_data)} produits parsés depuis JSON")
                            for p in products_data:
                                if isinstance(p, dict) and p.get('slug'):
                                    name = p.get('name') or p.get('title') or p.get('product_title') or p.get('slug')
                                    price_val = p.get('price') or p.get('original_price')
                                    promo_val = p.get('promotedPrice') or p.get('promo_price') or p.get('promotionalPrice')
                                    image = p.get('featuredImage') or p.get('image') or p.get('product_image')
                                    slug = p.get('slug')
                                    
                                    url = f"{base}/fr/products/{slug}"
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
                                        "slug": slug,
                                        "marketplace": "maketou",
                                    })
                            if products:
                                # Déduplication par slug
                                seen = set()
                                unique_products = []
                                for p in products:
                                    if p['slug'] not in seen:
                                        seen.add(p['slug'])
                                        unique_products.append(p)
                                return unique_products
                    except (json.JSONDecodeError, ValueError) as e:
                        continue
        except Exception as e:
            print(f"      ⚠️ Erreur parsing JSON complet: {e}")
        
        # Fallback: méthode regex (méthode originale)
        slug_matches = re.findall(r'"slug":"([^"]+)"', page_content)
        unique_slugs = list(dict.fromkeys(slug_matches))  # dédup
        print(f"      🔍 Fallback regex: {len(unique_slugs)} slugs trouvés")
        for slug in unique_slugs:
            # Chercher un bloc autour du slug
            # Chercher name, featuredImage, price, promotedPrice à partir du slug
            # Essayer plusieurs patterns pour le nom (name peut être échappé ou non)
            name_patterns = [
                r'"slug":"%s"[^}]*?"name":"([^"]+)"' % re.escape(slug),  # Pattern standard
                r'"slug":"%s"[^}]*?"name":\s*"([^"]+)"' % re.escape(slug),  # Avec espaces
                r'"slug":\s*"%s"[^}]*?"name":\s*"([^"]+)"' % re.escape(slug),  # Avec espaces partout
            ]
            name = None
            for pattern in name_patterns:
                name_match = re.search(pattern, page_content, re.S)
                if name_match:
                    name = name_match.group(1)
                    break
            
            # Si pas trouvé, chercher dans un bloc JSON complet autour du slug
            if not name:
                # Chercher un bloc JSON complet contenant le slug
                block_pattern = r'\{[^}]*"slug"\s*:\s*"%s"[^}]*\}' % re.escape(slug)
                block_match = re.search(block_pattern, page_content, re.S)
                if block_match:
                    block = block_match.group(0)
                    name_m = re.search(r'"name"\s*:\s*"([^"]+)"', block)
                    if name_m:
                        name = name_m.group(1)
            
            # Si toujours pas trouvé, utiliser le slug comme fallback
            if not name:
                name = slug.replace('-', ' ').title()
            
            image_match = re.search(r'"slug":"%s"[^}]*?"featuredImage":"([^"]+)"' % re.escape(slug), page_content, re.S)
            price_match = re.search(r'"slug":"%s"[^}]*?"price"\s*:\s*([^,}]+)' % re.escape(slug), page_content, re.S)
            promo_match = re.search(r'"slug":"%s"[^}]*?"promotedPrice"\s*:\s*([^,}]+)' % re.escape(slug), page_content, re.S)
            
            image = image_match.group(1) if image_match else None
            price_raw = price_match.group(1).strip() if price_match else None
            promo_raw = promo_match.group(1).strip() if promo_match else None
            try:
                price_val = float(price_raw) if price_raw and price_raw not in ['null', 'None'] else None
            except:
                price_val = None
            try:
                promo_val = float(promo_raw) if promo_raw and promo_raw not in ['null', 'None'] else None
            except:
                promo_val = None
            
            url = f"{base}/fr/products/{slug}"
            products.append({
                "product_title": name,
                "name": name,  # Ajouter aussi 'name' pour compatibilité
                "title": name,  # Et 'title' aussi
                "product_url": url,
                "url": url,  # Ajouter aussi 'url' pour compatibilité
                "price": promo_val or price_val,
                "promotedPrice": promo_val,  # Ajouter aussi promotedPrice
                "promo_price": promo_val,  # Et promo_price
                "original_price": price_val,
                "images": [image] if image else [],
                "image": image,  # Ajouter aussi 'image' pour compatibilité
                "featuredImage": image,  # Et featuredImage
                "description": None,
                "slug": slug,
                "marketplace": "maketou",
            })
        
        # Déduplication par slug puis URL
        seen_slug = set()
        seen_url = set()
        unique = []
        for p in products:
            slug = p.get('slug')
            url = p.get('product_url') or p.get('url')
            if slug and slug not in seen_slug:
                seen_slug.add(slug)
                unique.append(p)
            elif url and url not in seen_url:
                seen_url.add(url)
                unique.append(p)
        return unique
    
    async def _extract_products_from_dom(self, page, shop_url: str) -> List[dict]:
        """
        Extrait les produits depuis le DOM directement avec Playwright.
        Plus lent mais plus fiable pour récupérer tous les champs (titre, prix, image).
        """
        products = []
        parsed = urlparse(shop_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        try:
            # Extraire les produits depuis les cartes produits dans le DOM
            products_data = await page.evaluate(f"""
                () => {{
                    const base = '{base}';
                    const products = [];
                    
                    // Chercher toutes les cartes produits (structure Maketou)
                    // Les cartes ont souvent des classes comme "overflow-hidden", "rounded-xl", etc.
                    const selectors = [
                        'div[class*="overflow-hidden"][class*="rounded"]',
                        'div[class*="product"]',
                        'article',
                        '[class*="card"]'
                    ];
                    
                    let allCards = [];
                    for (const sel of selectors) {{
                        const cards = Array.from(document.querySelectorAll(sel));
                        allCards = allCards.concat(cards);
                    }}
                    
                    // Déduplication des cartes
                    const uniqueCards = [];
                    const seen = new Set();
                    for (const card of allCards) {{
                        const rect = card.getBoundingClientRect();
                        const key = Math.round(rect.top) + '_' + Math.round(rect.left);
                        if (!seen.has(key) && rect.width > 100 && rect.height > 100) {{
                            seen.add(key);
                            uniqueCards.push(card);
                        }}
                    }}
                    
                    for (const card of uniqueCards) {{
                        // Chercher le titre - priorité aux h3 avec classes spécifiques Maketou
                        let titleEl = card.querySelector('h3[class*="font-bold"][class*="leading-7"]');
                        if (!titleEl) titleEl = card.querySelector('h3[class*="font-bold"]');
                        if (!titleEl) titleEl = card.querySelector('h3.line-clamp-2');
                        if (!titleEl) titleEl = card.querySelector('h3');
                        if (!titleEl) titleEl = card.querySelector('h2');
                        if (!titleEl) {{
                            // Chercher dans les enfants directs
                            const h3s = card.querySelectorAll('h3, h2');
                            for (const h of h3s) {{
                                if (h.textContent && h.textContent.trim().length > 10) {{
                                    titleEl = h;
                                    break;
                                }}
                            }}
                        }}
                        const title = titleEl ? titleEl.textContent.trim() : null;
                        
                        // Chercher l'image
                        const imgEl = card.querySelector('img[src*="imagedelivery"], img[src*="image"], img[alt]');
                        const image = imgEl ? imgEl.src : null;
                        
                        // Chercher le prix - chercher dans les spans avec classes de prix
                        let price = null;
                        
                        // Chercher dans les spans avec classes spécifiques (priorité au prix promo)
                        const priceSpans = card.querySelectorAll('span[class*="font-bold"], span[class*="text-primary"], [class*="price"]');
                        for (const priceSpan of priceSpans) {{
                            const priceText = priceSpan.textContent || '';
                            // Pattern pour "10 995 F CFA" ou "10995 FCFA" (gérer espaces insécables \u00A0)
                            const match = priceText.match(/([\\d\\s\\u00A0,]+)\\s*(?:F\\s*CFA|FCFA|XOF|€|\\$)/i);
                            if (match) {{
                                const numStr = match[1].replace(/[\\s\\u00A0,]/g, '').replace(/\\.(?!\\d)/g, '');
                                const parsed = parseFloat(numStr);
                                if (!isNaN(parsed) && parsed > 0) {{
                                    price = parsed;
                                    break;
                                }}
                            }}
                        }}
                        
                        // Si pas trouvé, chercher dans tout le texte de la carte
                        if (!price) {{
                            const cardText = card.textContent || '';
                            // Chercher tous les patterns de prix
                            const matches = cardText.match(/([\\d\\s\\u00A0,]+)\\s*(?:F\\s*CFA|FCFA|XOF)/gi);
                            if (matches && matches.length > 0) {{
                                // Prendre le premier prix valide trouvé
                                for (const match of matches) {{
                                    const numMatch = match.match(/([\\d\\s\\u00A0,]+)/);
                                    if (numMatch) {{
                                        const numStr = numMatch[1].replace(/[\\s\\u00A0,]/g, '').replace(/\\.(?!\\d)/g, '');
                                        const parsed = parseFloat(numStr);
                                        if (!isNaN(parsed) && parsed > 0) {{
                                            price = parsed;
                                            break;
                                        }}
                                    }}
                                }}
                            }}
                        }}
                        
                        // Chercher le lien produit
                        let linkEl = card.querySelector('a[href*="/products/"]');
                        if (!linkEl) {{
                            // Chercher dans les parents
                            let parent = card;
                            for (let i = 0; i < 3 && parent; i++) {{
                                linkEl = parent.querySelector('a[href*="/products/"]');
                                if (linkEl) break;
                                parent = parent.parentElement;
                            }}
                        }}
                        
                        const href = linkEl ? linkEl.href : null;
                        
                        if (title && href && href.includes('/products/')) {{
                            const slugMatch = href.match(/\\/products\\/([^\\/?#]+)/);
                            const slug = slugMatch ? slugMatch[1] : null;
                            
                            if (slug) {{
                                products.push({{
                                    name: title,
                                    title: title,
                                    product_title: title,
                                    slug: slug,
                                    product_url: href,
                                    url: href,
                                    price: price || 0,
                                    promotedPrice: price || 0,
                                    promo_price: price || 0,
                                    image: image,
                                    featuredImage: image,
                                    images: image ? [image] : []
                                }});
                            }}
                        }}
                    }}
                    
                    return products;
                }}
            """)
            
            if products_data and len(products_data) > 0:
                for p in products_data:
                    p['marketplace'] = 'maketou'
                print(f"      ✅ {len(products_data)} produits extraits depuis le DOM")
                return products_data
        except Exception as e:
            print(f"      ⚠️ Erreur extraction DOM: {e}")
            import traceback
            traceback.print_exc()
        
        return []
    
    async def _go_to_next_page(self, page, current_page: int) -> bool:
        """
        Essaie de naviguer vers la page suivante (pagination Maketou).
        Retourne True si une page suivante est trouvée et chargée.
        """
        try:
            # Stratégie 1: Bouton "next" spécifique à Maketou (data-slot="next")
            next_button = page.locator('[data-slot="next"]')
            count = await next_button.count()
            if count > 0:
                try:
                    # Vérifier si le bouton est désactivé
                    is_disabled = await next_button.get_attribute("aria-disabled")
                    if is_disabled != "true":
                        await next_button.click()
                        await page.wait_for_timeout(3000)  # Attendre le chargement
                        await page.wait_for_load_state("networkidle", timeout=30000)
                        print(f"    ✅ Clic sur bouton 'next' (data-slot)")
                        return True
                    else:
                        print(f"    ℹ️ Bouton 'next' désactivé (fin de pagination)")
                except Exception as e:
                    print(f"    ⚠️ Erreur lors du clic sur 'next': {e}")
            
            # Stratégie 2: Lien vers la page suivante (numéro de page) - Maketou utilise data-slot="item"
            next_page_number = current_page + 1
            page_item = page.locator(f'[data-slot="item"][aria-label*="pagination item {next_page_number}"]')
            count = await page_item.count()
            if count > 0:
                try:
                    await page_item.click()
                    await page.wait_for_timeout(3000)
                    await page.wait_for_load_state("networkidle", timeout=30000)
                    print(f"    ✅ Clic sur page {next_page_number}")
                    return True
                except Exception as e:
                    print(f"    ⚠️ Erreur lors du clic sur page {next_page_number}: {e}")
            
            # Stratégie 3: Vérifier le nombre total de pages depuis data-total
            try:
                pagination_nav = page.locator('nav[role="navigation"][aria-label*="pagination"]')
                if await pagination_nav.count() > 0:
                    total_pages = await pagination_nav.get_attribute("data-total")
                    active_page = await pagination_nav.get_attribute("data-active-page")
                    if total_pages and active_page:
                        total = int(total_pages)
                        active = int(active_page)
                        print(f"    📊 Pages: {active}/{total}")
                        if active >= total:
                            print(f"    ℹ️ Dernière page atteinte ({active}/{total})")
                            return False
            except Exception as e:
                print(f"    ⚠️ Erreur lors de la lecture des attributs de pagination: {e}")
            
            # Stratégie 4: Fallback - chercher des boutons "Suivant" / "Next" génériques
            next_texts = ["Suivant", "Next", "›", "»"]
            for text in next_texts:
                locator = page.locator(f'xpath=//*[contains(text(), "{text}") and (self::a or self::button or self::li[@role="button"])]')
                count = await locator.count()
                if count > 0:
                    for i in range(count):
                        btn = locator.nth(i)
                        try:
                            disabled = await btn.get_attribute("aria-disabled")
                            if disabled != "true":
                                await btn.click()
                                await page.wait_for_timeout(3000)
                                await page.wait_for_load_state("networkidle", timeout=30000)
                                print(f"    ✅ Clic sur bouton générique '{text}'")
                                return True
                        except Exception:
                            continue

            return False

        except Exception as e:
            print(f"    ⚠️ Erreur lors de la recherche de la page suivante: {e}")
            import traceback
            traceback.print_exc()
            return False
    
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
            # Sélecteur spécifique Maketou: p.font-bold.mb-1.leading-10.text-4xl
            price = await page.evaluate("""
                () => {
                    // Sélecteur spécifique Maketou: p avec classes font-bold mb-1 leading-10 text-4xl
                    const maketouPriceSelectors = [
                        'p.font-bold.mb-1.leading-10.text-4xl',
                        'p[class*="font-bold"][class*="text-4xl"]',
                        'p.text-4xl.font-bold',
                    ];
                    
                    for (const selector of maketouPriceSelectors) {
                        const elems = document.querySelectorAll(selector);
                        for (const elem of elems) {
                            const text = elem.textContent || elem.innerText || '';
                            // Chercher un prix avec FCFA (format: "999 F CFA" avec espaces insécables)
                            const fcfaMatch = text.match(/([\\d\\s,\\.]+)\\s*F\\s*CFA/i) || text.match(/([\\d\\s,\\.]+)\\s*FCFA/i);
                            if (fcfaMatch) {
                                // Nettoyer: remplacer espaces insécables, espaces normaux, virgules
                                let priceStr = fcfaMatch[1].replace(/[\\u00A0\\s,]/g, '');
                                // Gérer les points
                                if (priceStr.includes('.')) {
                                    const parts = priceStr.split('.');
                                    if (parts.length === 2 && parts[1].length <= 2) {
                                        priceStr = parts[0] + parts[1];
                                    } else {
                                        priceStr = priceStr.replace(/\\./g, '');
                                    }
                                }
                                const price = parseFloat(priceStr);
                                // Filtrer les années et valeurs suspectes
                                if (price >= 100 && price <= 1000000 && !(price >= 2000 && price <= 2099 && priceStr.length <= 4)) {
                                    return price;
                                }
                            }
                        }
                    }
                    
                    // Fallback: chercher dans les autres sélecteurs
                    const priceSelectors = [
                        '[class*="price"]',
                        '[class*="amount"]',
                        '[data-price]',
                        '.product-price',
                        '.price-value',
                    ];
                    
                    for (const selector of priceSelectors) {
                        const elems = document.querySelectorAll(selector);
                        for (const elem of elems) {
                            const text = elem.textContent || elem.innerText || '';
                            const fcfaMatch = text.match(/([\\d\\s,]+)\\s*(?:F\\s*CFA|XOF|francs?)/i);
                            if (fcfaMatch) {
                                const priceStr = fcfaMatch[1].replace(/[\\u00A0\\s,]/g, '').replace('.', '');
                                const price = parseFloat(priceStr);
                                if (price >= 100 && price <= 1000000) {
                                    return price;
                                }
                            }
                            // Chercher $ et convertir
                            const dollarMatch = text.match(/\\$(\\d+[\\.]?\\d*)/);
                            if (dollarMatch) {
                                const price = parseFloat(dollarMatch[1]) * 600;
                                if (price >= 100 && price <= 1000000) {
                                    return price;
                                }
                            }
                        }
                    }
                    
                    const dataPriceElems = document.querySelectorAll('[data-price]');
                    for (const elem of dataPriceElems) {
                        const price = parseFloat(elem.getAttribute('data-price'));
                        if (price >= 100 && price <= 1000000) {
                            return price;
                        }
                    }
                    
                    return null;
                }
            """)
            
            if price and 100 <= price <= 1000000:
                return float(price)
        except Exception as e:
            print(f"      ⚠️  Erreur extraction prix Playwright: {e}")
        
        return 0.0
    
    def _extract_price(self, soup: BeautifulSoup) -> float:
        """Extrait le prix en FCFA depuis BeautifulSoup (fallback)"""
        # Sélecteur spécifique Maketou: p.font-bold.mb-1.leading-10.text-4xl
        maketou_selectors = [
            'p.font-bold.mb-1.leading-10.text-4xl',
            'p[class*="font-bold"][class*="text-4xl"]',
            'p.text-4xl.font-bold',
        ]
        
        for selector in maketou_selectors:
            try:
                elems = soup.select(selector)
                for elem in elems:
                    price_text = elem.get_text(strip=True)
                    # Format: "999 F CFA" avec espaces insécables
                    fcfa_match = re.search(r'([\d\s,\.]+)\s*F\s*CFA', price_text, re.IGNORECASE) or re.search(r'([\d\s,\.]+)\s*FCFA', price_text, re.IGNORECASE)
                    if fcfa_match:
                        try:
                            # Nettoyer: remplacer espaces insécables (\u00A0), espaces, virgules
                            price_str = fcfa_match.group(1).replace('\u00A0', '').replace(',', '').replace(' ', '').strip()
                            # Gérer les points
                            if '.' in price_str:
                                parts = price_str.split('.')
                                if len(parts) == 2 and len(parts[1]) <= 2:
                                    price_str = parts[0] + parts[1]
                                else:
                                    price_str = price_str.replace('.', '')
                            price_val = float(price_str)
                            # Filtrer les années et valeurs suspectes
                            if 100 <= price_val <= 1000000 and not (2000 <= price_val <= 2099 and len(price_str) <= 4):
                                return price_val
                        except Exception:
                            continue
            except Exception:
                continue
        
        # Fallback: autres sélecteurs
        price_selectors = [
            '.price',
            '[class*="price"]',
            '[class*="amount"]',
            '[data-price]',
            '.product-price',
            '.price-value'
        ]
        
        for selector in price_selectors:
            elems = soup.select(selector)
            for elem in elems:
                price_text = elem.get_text(strip=True)
                # Chercher spécifiquement FCFA/XOF
                fcfa_match = re.search(r'([\d\s,]+)\s*(?:F\s*CFA|XOF|francs?)', price_text, re.IGNORECASE)
                if fcfa_match:
                    try:
                        price_str = fcfa_match.group(1).replace('\u00A0', '').replace(',', '').replace(' ', '').replace('.', '').strip()
                        price_val = float(price_str)
                        if 100 <= price_val <= 1000000:
                            return price_val
                    except Exception:
                        continue
                # Chercher $ et convertir
                dollar_match = re.search(r'\$(\d+[\.]?\d*)', price_text)
                if dollar_match:
                    try:
                        price_val = float(dollar_match.group(1)) * 600
                        if 100 <= price_val <= 1000000:
                            return price_val
                    except Exception:
                        continue
        
        # Chercher dans les attributs data-price
        data_price_elems = soup.select('[data-price]')
        for elem in data_price_elems:
            try:
                price_val = float(elem.get('data-price', 0))
                if 100 <= price_val <= 1000000:
                    return price_val
            except Exception:
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
