#!/usr/bin/env python3
"""
Scraper Playwright pour récupérer les VRAIES publicités depuis Facebook Ads Library
Style Minea - Simple et efficace
ZÉRO données mockées - Seulement des données réelles scrapées
Mots-clés UNIQUEMENT en français
"""

import asyncio
import sys
import hashlib
import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import quote, urlparse, parse_qs, unquote

# Configuration Windows pour asyncio (nécessaire pour Playwright)
if sys.platform == 'win32':
    # Utiliser ProactorEventLoopPolicy pour Playwright sur Windows
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except:
        # Fallback si ProactorEventLoopPolicy n'est pas disponible
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = Any
    print("[WARN] Playwright non installé. Installez avec: pip install playwright && playwright install chromium")

# Type pour une publicité scrapée
ScrapedAd = Dict[str, Any]

# MOTS-CLÉS UNIQUEMENT EN FRANÇAIS
MOTS_CLES_FRANCAIS = [
    # Business & Marketing
    "formation", "ebook", "coaching", "cours", "guide", "programme",
    "gagner de l'argent", "revenus passifs", "business en ligne",
    "formation marketing", "formation digitale", "cours en ligne",
    "formation en ligne", "tutoriel", "gagne argent",
    "revenus en ligne", "business digital", "formation WhatsApp",
    "tunnel de vente", "systeme.io", "marketing digital",
    "e-commerce", "dropshipping", "affiliation", "entrepreneuriat",
    "liberté financière", "créer entreprise", "vente en ligne",
    
    # Spiritualité
    "prière", "prières", "délivrance", "prospérité", "abondance",
    "destinée", "bénédiction", "miracle", "éveil spirituel",
    "loi de l'attraction", "prières financières", "jeûne et prière",
    "manifestation", "spiritualité africaine", "protection spirituelle",
    "guérison", "foi", "prière puissante", "prière efficace",
    "prière qui marche", "prière pour argent",
    
    # Contexte Africain
    "FCFA", "Orange Money", "MTN MoMo", "paiement mobile",
    "WhatsApp Business", "Afrique", "Bénin", "Côte d'Ivoire",
    "Cameroun", "Sénégal", "Mali", "Burkina Faso", "Niger",
    "Gabon", "Congo", "Guinée", "Sénégalais", "Ivoirien", "Camerounais",
]


async def scrape_ads_library(
    search_term: Optional[str] = None,
    limit: int = 20
) -> List[ScrapedAd]:
    """
    Scrape les publicités depuis Facebook Ads Library avec Playwright
    
    Args:
        search_term: Terme de recherche (optionnel)
        limit: Nombre maximum de publicités à récupérer
    
    Returns:
        Liste de dictionnaires contenant les données scrapées (VRAIES uniquement)
    """
    if not PLAYWRIGHT_AVAILABLE:
        print("[ERREUR] Playwright non disponible")
        return []
    
    ads = []
    
    try:
        print(f"[INFO] Debut scraping pour: {search_term or 'Tous'}")
        sys.stdout.flush()
        
        async with async_playwright() as p:
            print(f"[INFO] Lancement Playwright pour scraping: {search_term or 'Tous'}")
            sys.stdout.flush()
            
            # Lancer Chromium en mode headless
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # Créer un contexte avec un user agent réaliste
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='fr-FR',
                timezone_id='Europe/Paris'
            )
            
            page = await context.new_page()
            
            # Construire l'URL de Facebook Ads Library (GLOBAL - pas de filtre pays)
            base_url = "https://www.facebook.com/ads/library"
            params = {
                'active_status': 'all',
                'ad_type': 'all',
            }
            if search_term:
                params['q'] = search_term
            
            url = f"{base_url}?{'&'.join([f'{k}={quote(str(v))}' for k, v in params.items()])}"
            
            print(f"[INFO] Ouverture: {url}")
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=90000)
            except Exception:
                await page.goto(url, wait_until='load', timeout=90000)
            
            # Attendre que les publicités se chargent
            print("[INFO] Attente du chargement des publicités...")
            await asyncio.sleep(5)
            
            # Scroller pour charger plus de publicités
            print("[INFO] Scrolling pour charger plus de publicités...")
            for i in range(5):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(3)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.8)")
                await asyncio.sleep(2)
            
            # Attendre que les images et le contenu se chargent
            await asyncio.sleep(5)
            
            # Forcer le chargement des images lazy
            await page.evaluate("""
                () => {
                    const images = document.querySelectorAll('img[data-src]');
                    images.forEach(img => {
                        img.src = img.dataset.src;
                    });
                }
            """)
            await asyncio.sleep(2)
            
            # Extraire les publicités
            print("[INFO] Extraction des publicités...")
            ads = await extract_ads_from_page(page, search_term or '', limit)
            
            await browser.close()
            
            print(f"[OK] {len(ads)} publicités récupérées")
            return ads
            
    except Exception as e:
        print(f"[ERREUR] Erreur scraping Playwright: {e}")
        import traceback
        traceback.print_exc()
        return []


async def extract_ads_from_page(page: Page, search_term: str, limit: int) -> List[ScrapedAd]:
    """Extrait les publicités depuis la page chargée"""
    ads = []
    
    try:
        # Sélecteurs pour trouver les cartes de publicités
        selectors = [
            'div[role="article"]',
            'div[data-testid*="ad"]',
            'div[data-testid*="AdCard"]',
            'div[data-testid*="ad-card"]',
            'div[class*="x1y1aw1k"][class*="x1n2onr6"]',
            'div[class*="x1y1aw1k"]',
            'div[class*="x1n2onr6"]',
            'article',
            'div[class*="card"]',
            'div[class*="Card"]'
        ]
        
        # Essayer de trouver les conteneurs de pubs
        ad_containers = []
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"[INFO] {len(elements)} éléments trouvés avec selector: {selector}")
                    filtered = []
                    for elem in elements:
                        try:
                            text = await elem.inner_text()
                            if text and len(text.strip()) > 10:
                                filtered.append(elem)
                        except:
                            continue
                    
                    if filtered:
                        print(f"[INFO] {len(filtered)} éléments valides après filtrage")
                        ad_containers = filtered
                        break
            except Exception as e:
                print(f"[DEBUG] Erreur avec selector {selector}: {e}")
                continue
        
        if not ad_containers:
            print("[WARN] Aucun conteneur de pub trouvé")
            return ads
        
        print(f"[INFO] Extraction depuis {len(ad_containers)} conteneurs...")
        
        seen_ids = set()
        
        for container in ad_containers[:limit * 3]:
            try:
                ad = await extract_single_ad(container, search_term)
                
                if ad and ad['id'] not in seen_ids:
                    # VALIDATION ASSOUPLIE : Texte obligatoire, image et page optionnels
                    has_text = ad.get('text') and len(ad.get('text', '').strip()) >= 15  # Réduit de 20 à 15
                    has_page = ad.get('pageName') and ad.get('pageName') != 'Page Facebook'
                    has_image = ad.get('imageUrl') and len(ad.get('imageUrl', '').strip()) > 0
                    
                    if not has_text:
                        continue
                    
                    # Si pas d'image, essayer de l'extraire depuis la snapshot
                    if not has_image and ad.get('snapshotUrl'):
                        try:
                            better_image = await extract_creative_from_snapshot(ad['snapshotUrl'])
                            if better_image:
                                ad['imageUrl'] = better_image
                                has_image = True
                        except:
                            pass
                    
                    # Validation finale : texte obligatoire, page préférée mais pas obligatoire
                    if has_text:
                        # Si pas de page, utiliser un nom par défaut
                        if not has_page:
                            ad['pageName'] = 'Page Facebook'
                        
                        ads.append(ad)
                        seen_ids.add(ad['id'])
                        image_status = "OUI" if has_image else "NON"
                        print(f"  [OK] Pub {len(ads)} VALIDEE: {ad['pageName'][:30]}... | Texte: {len(ad['text'])} chars | Image: {image_status}")
                        sys.stdout.flush()
                        
                        if len(ads) >= limit:
                            break
            except Exception as e:
                print(f"  [WARN] Erreur extraction pub: {e}")
                continue
        
    except Exception as e:
        print(f"[ERREUR] Erreur extraction: {e}")
        import traceback
        traceback.print_exc()
    
    return ads


async def extract_single_ad(container, search_term: str) -> Optional[ScrapedAd]:
    """Extrait les données d'une seule publicité depuis un conteneur"""
    try:
        # Extraire le texte de la pub
        text = ""
        try:
            all_text = await container.inner_text()
            if all_text and len(all_text.strip()) > 20:
                cleaned = ' '.join(all_text.strip().split())
                lines = cleaned.split('\n')
                valid_lines = []
                for line in lines:
                    line_clean = line.strip()
                    if (len(line_clean) > 15 and 
                        line_clean.lower() not in ['sponsorisé', 'sponsored', 'voir plus', 'see more', '...', ''] and
                        not line_clean.startswith('http') and
                        'facebook.com' not in line_clean.lower()):
                        valid_lines.append(line_clean)
                
                if valid_lines:
                    text = ' '.join(valid_lines)
                    if len(text) > 2000:
                        text = text[:2000] + '...'
                else:
                    text = cleaned[:2000] if len(cleaned) > 2000 else cleaned
        except:
            pass
        
        if not text or len(text.strip()) < 20:
            return None
        
        # Extraire le nom de la page
        page_name = "Page Facebook"
        try:
            page_selectors = [
                'a[href*="/pages/"]',
                'a[href*="facebook.com"]',
                '[class*="page"]',
                '[class*="Page"]'
            ]
            for selector in page_selectors:
                try:
                    page_elem = await container.query_selector(selector)
                    if page_elem:
                        page_text = await page_elem.inner_text()
                        if page_text and len(page_text.strip()) > 0:
                            page_name = page_text.strip()
                            break
                except:
                    continue
        except:
            pass
        
        # Extraire le titre
        title = None
        try:
            if text:
                excluded_words = ['sponsorisé', 'sponsored', 'publicité', 'ad', 'checkout', 'voir plus']
                first_sentence = text.split('.')[0].strip()
                first_sentence = first_sentence.split('http')[0].strip()
                first_sentence = first_sentence.split('www.')[0].strip()
                
                first_sentence_lower = first_sentence.lower()
                if (len(first_sentence) > 10 and len(first_sentence) < 150 and
                    not any(excluded in first_sentence_lower for excluded in excluded_words) and
                    first_sentence != page_name):
                    title = first_sentence
                else:
                    words = text.split()
                    valid_words = [w for w in words if not any(excluded in w.lower() for excluded in excluded_words)]
                    if valid_words:
                        title = ' '.join(valid_words[:15])[:80].strip()
                    else:
                        title = text[:80].strip()
        except:
            if text:
                title = text.split('http')[0].split('www.')[0].strip()[:100]
        
        # Extraire l'image créative
        image_url = None
        try:
            img_elements = await container.query_selector_all('img')
            
            candidates = []
            for img_elem in img_elements:
                try:
                    img_src = None
                    attrs_to_try = ['src', 'data-src', 'data-lazy-src', 'data-original', 'data-url']
                    
                    for attr in attrs_to_try:
                        try:
                            val = await img_elem.get_attribute(attr)
                            if val and val != 'null' and not val.startswith('data:'):
                                img_src = val
                                break
                        except:
                            continue
                    
                    if not img_src:
                        try:
                            img_src = await img_elem.evaluate('el => el.currentSrc || el.src || el.dataset.src || el.dataset.lazySrc')
                        except:
                            pass
                    
                    if not img_src or img_src == 'null' or img_src.startswith('data:'):
                        continue
                    
                    img_lower = img_src.lower()
                    exclude = ['avatar', 'profile-pic', 'profile_pic', 'icon-', 'emoji', 'sprite', 'loading.gif']
                    
                    if 'scontent' not in img_lower and 'fbcdn' not in img_lower:
                        if any(ex in img_lower for ex in exclude):
                            continue
                    
                    if 'scontent' in img_lower or 'fbcdn' in img_lower:
                        try:
                            width = await img_elem.evaluate('el => el.naturalWidth || el.width || el.clientWidth || 0')
                            height = await img_elem.evaluate('el => el.naturalHeight || el.height || el.clientHeight || 0')
                            score = 10000
                            if width > 0 and height > 0:
                                score += width * height
                            candidates.append((img_src, score))
                        except:
                            candidates.append((img_src, 10000))
                    elif 'facebook.com' in img_lower:
                        candidates.append((img_src, 5000))
                    else:
                        try:
                            width = await img_elem.evaluate('el => el.naturalWidth || el.width || el.clientWidth || 0')
                            height = await img_elem.evaluate('el => el.naturalHeight || el.height || el.clientHeight || 0')
                            if width > 300 and height > 300:
                                score = width * height
                                candidates.append((img_src, score))
                        except:
                            pass
                except:
                    continue
            
            if candidates:
                candidates.sort(key=lambda x: x[1], reverse=True)
                image_url = candidates[0][0]
        except:
            pass
        
        # Extraire le lien snapshot
        snapshot_url = None
        try:
            detail_button_selectors = [
                'a[aria-label*="détails"]',
                'a[aria-label*="details"]',
                'a[href*="/ads/library"]',
                '[data-testid*="detail"]',
            ]
            
            for selector in detail_button_selectors:
                try:
                    button = await container.query_selector(selector)
                    if button:
                        href = await button.get_attribute('href')
                        if href and ('/ads/library' in href or 'ads-transparency' in href):
                            if href.startswith('/'):
                                href = f"https://www.facebook.com{href}"
                            snapshot_url = href
                            break
                except:
                    continue
        except:
            pass
        
        # Extraire le CTA
        cta_text = None
        try:
            cta_keywords = [
                'voir le produit', 'acheter', 'commander', 'télécharger',
                'découvrir', 'en savoir plus', 'shop', 'boutique',
                'inscription', "s'inscrire", 'rejoindre', 'obtenir',
            ]
            
            all_elements = await container.query_selector_all('[aria-label], [title], button, a[href]')
            for elem in all_elements:
                try:
                    aria_label = await elem.get_attribute('aria-label')
                    if aria_label:
                        aria_lower = aria_label.lower()
                        for keyword in cta_keywords:
                            if keyword in aria_lower:
                                cta_text = aria_label.strip()
                                if len(cta_text) <= 50:
                                    break
                    if cta_text:
                        break
                except:
                    continue
        except:
            pass
        
        # Extraire le lien produit
        product_url = None
        try:
            product_url = await extract_product_url_from_container(container)
        except:
            pass
        
        # Générer un ID stable
        ad_id = generate_ad_id(text, page_name, search_term)
        
        # Extraire les insights
        insights = extract_insights(text)
        
        ad = {
            'id': ad_id,
            'pageName': page_name,
            'text': text,
            'title': title,
            'imageUrl': image_url,
            'snapshotUrl': snapshot_url,
            'productUrl': product_url,
            'cta_text': cta_text,
            'insights': insights,
            'keyword': search_term,
        }
        
        return ad
        
    except Exception as e:
        print(f"  [WARN] Erreur extraction pub: {e}")
        return None


async def extract_product_url_from_container(container) -> Optional[str]:
    """Extrait le lien produit directement depuis le conteneur"""
    if not PLAYWRIGHT_AVAILABLE:
        return None
    
    excluded_domains = [
        'facebook.com', 'instagram.com', 'meta.com', 'fb.com', 'fb.me', 
        'messenger.com', 'metastatus.com', 'whatsapp.com', 'oculus.com',
        'facebook.net', 'fbcdn.net', 'fbsbx.com', 'fbstatic.com',
        'l.facebook.com'
    ]
    
    try:
        all_links = await container.query_selector_all('a[href]')
        
        for link in all_links:
            try:
                href = await link.get_attribute('href')
                if not href:
                    continue
                
                # Décoder les liens de tracking Facebook
                if 'l.facebook.com' in href:
                    try:
                        parsed = urlparse(href)
                        params = parse_qs(parsed.query)
                        if 'u' in params:
                            real_url = unquote(params['u'][0])
                            if not any(domain in real_url.lower() for domain in excluded_domains):
                                if real_url.startswith('http://') or real_url.startswith('https://'):
                                    return real_url
                    except:
                        continue
                
                # URLs directes
                elif href.startswith('http://') or href.startswith('https://'):
                    if not any(domain in href.lower() for domain in excluded_domains):
                        if 'facebook.com' not in href.lower() and 'fb.me' not in href.lower():
                            return href
            except:
                continue
    except:
        pass
    
    return None


async def extract_creative_from_snapshot(snapshot_url: str, timeout: int = 30) -> Optional[str]:
    """Extrait la vraie image créative depuis la snapshot URL"""
    if not snapshot_url or not PLAYWRIGHT_AVAILABLE:
        return None
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            await page.goto(snapshot_url, wait_until='domcontentloaded', timeout=timeout * 1000)
            await asyncio.sleep(3)
            
            image_url = None
            img_elements = await page.query_selector_all('img')
            
            candidates = []
            for img_elem in img_elements:
                try:
                    img_src = (await img_elem.get_attribute('src') or 
                              await img_elem.get_attribute('data-src') or
                              await img_elem.evaluate('el => el.currentSrc || el.src'))
                    
                    if not img_src or img_src.startswith('data:') or 'avatar' in img_src.lower():
                        continue
                    
                    if 'scontent' in img_src.lower() or 'fbcdn' in img_src.lower():
                        width = await img_elem.evaluate('el => el.naturalWidth || el.width || el.clientWidth || 0')
                        height = await img_elem.evaluate('el => el.naturalHeight || el.height || el.clientHeight || 0')
                        if width > 200 and height > 200:
                            score = width * height
                            candidates.append((img_src, score))
                except:
                    continue
            
            if candidates:
                candidates.sort(key=lambda x: x[1], reverse=True)
                image_url = candidates[0][0]
            
            await browser.close()
            return image_url
            
    except Exception as e:
        print(f"[WARN] Erreur extraction créative: {e}")
        return None


def generate_ad_id(text: str, page_name: str, keyword: str) -> str:
    """Génère un ID stable basé sur le contenu"""
    content = f"{page_name}|{text[:100]}|{keyword}"
    return hashlib.md5(content.encode()).hexdigest()


def extract_insights(text: str) -> Dict[str, Any]:
    """Extrait des insights automatiques depuis le texte de la pub"""
    if not text:
        return {
            'mainHook': None,
            'hasPrice': False,
            'priceExtracted': None,
            'callToAction': None
        }
    
    # Main hook
    sentences = text.split('.')
    main_hook = sentences[0].strip() if sentences else text[:100].strip()
    if len(main_hook) > 100:
        words = main_hook.split()[:15]
        main_hook = ' '.join(words) + '...'
    
    # Détecter un prix
    has_price = False
    price_extracted = None
    
    price_patterns = [
        r'(\d+[\s,.]?\d*)\s*(FCFA|F\s*CFA|francs|€|euros?|\$|dollars?)',
        r'(FCFA|F\s*CFA|€|\$)\s*(\d+[\s,.]?\d*)',
        r'(\d+[\s,.]?\d*)\s*(F|francs)',
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            has_price = True
            price_extracted = match.group(0)
            break
    
    # Détecter le Call To Action
    cta_keywords = [
        'acheter', 'buy', 'commander', 'order', 'télécharger', 'download',
        'découvrir', 'discover', 'en savoir plus', 'learn more',
        'inscription', 'register', "s'inscrire", 'sign up',
    ]
    
    call_to_action = None
    text_lower = text.lower()
    for keyword in cta_keywords:
        if keyword in text_lower:
            sentences = text.split('.')
            for sentence in sentences:
                if keyword in sentence.lower():
                    call_to_action = sentence.strip()
                    break
            if call_to_action:
                break
    
    return {
        'mainHook': main_hook if main_hook else None,
        'hasPrice': has_price,
        'priceExtracted': price_extracted,
        'callToAction': call_to_action
    }


async def scrape_all_keywords(limit_per_keyword: int = 20) -> List[ScrapedAd]:
    """Scrape tous les mots-clés français"""
    all_ads = []
    seen_ids = set()
    
    print(f"\nScraping de {len(MOTS_CLES_FRANCAIS)} mots-cles francais...")
    print("Initialisation de Playwright...")
    
    try:
        async with async_playwright() as p:
            print("Lancement du navigateur...")
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            print("Navigateur lance")
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='fr-FR',
                timezone_id='Europe/Paris'
            )
            
            page = await context.new_page()
            print("Page creee")
            
            try:
                for i, keyword in enumerate(MOTS_CLES_FRANCAIS, 1):
                    print(f"\n[{i}/{len(MOTS_CLES_FRANCAIS)}] Recherche: {keyword}...")
                    sys.stdout.flush()  # Force l'affichage
                    
                    try:
                        ads = await scrape_ads_library(search_term=keyword, limit=limit_per_keyword)
                        
                        for ad in ads:
                            if ad['id'] not in seen_ids:
                                seen_ids.add(ad['id'])
                                all_ads.append(ad)
                        
                        print(f"  {len(ads)} annonces trouvees (Total unique: {len(all_ads)})")
                        sys.stdout.flush()
                        
                        # Sauvegarder par batch tous les 10 mots-clés ou tous les 50 annonces
                        if len(all_ads) >= 50 or (i % 10 == 0 and len(all_ads) > 0):
                            print(f"  [SAUVEGARDE] Batch de {len(all_ads)} annonces...")
                            sys.stdout.flush()
                            # Note: La sauvegarde sera faite dans le script principal
                        
                        await asyncio.sleep(2)  # Délai entre les recherches
                    except Exception as e:
                        print(f"  ERREUR pour {keyword}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                    
            finally:
                print("Fermeture du navigateur...")
                await browser.close()
                print("Navigateur ferme")
    
    except Exception as e:
        print(f"ERREUR FATALE dans scrape_all_keywords: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    print(f"\n{len(all_ads)} annonces uniques scrapees au total")
    return all_ads

