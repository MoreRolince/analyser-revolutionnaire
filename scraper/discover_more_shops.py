"""
Script pour découvrir plus de boutiques en explorant les liens depuis les boutiques connues
"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

async def discover_shops_from_page(url: str, marketplace: str) -> list:
    """Découvre des boutiques depuis une page donnée"""
    shop_urls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print(f"🔍 Exploration de: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            content = await page.content()
            try:
                soup = BeautifulSoup(content, 'lxml')
            except:
                soup = BeautifulSoup(content, 'html.parser')
            
            # Chercher tous les liens
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                if not href:
                    continue
                
                # Convertir en URL absolue
                if not href.startswith('http'):
                    href = urljoin(url, href)
                
                # Vérifier si c'est une boutique
                if marketplace == 'chariow':
                    if '.mychariow.shop' in href.lower():
                        if href not in shop_urls:
                            shop_urls.append(href)
                            print(f"  ✅ Boutique trouvée: {href}")
                elif marketplace == 'maketou':
                    if '.mymaketou.store' in href.lower():
                        if href not in shop_urls:
                            shop_urls.append(href)
                            print(f"  ✅ Boutique trouvée: {href}")
            
            # Scroll pour charger plus
            for i in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                
                content = await page.content()
                try:
                    soup = BeautifulSoup(content, 'lxml')
                except:
                    soup = BeautifulSoup(content, 'html.parser')
                
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    if not href:
                        continue
                    if not href.startswith('http'):
                        href = urljoin(url, href)
                    
                    if marketplace == 'chariow':
                        if '.mychariow.shop' in href.lower() and href not in shop_urls:
                            shop_urls.append(href)
                            print(f"  ✅ Boutique trouvée: {href}")
                    elif marketplace == 'maketou':
                        if '.mymaketou.store' in href.lower() and href not in shop_urls:
                            shop_urls.append(href)
                            print(f"  ✅ Boutique trouvée: {href}")
        
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
        finally:
            await browser.close()
    
    return shop_urls

async def main():
    """Découvre des boutiques depuis plusieurs sources"""
    print("🔍 Découverte de boutiques...")
    print("=" * 70)
    
    all_shops = {
        'chariow': [],
        'maketou': []
    }
    
    # Explorer les pages principales
    chariow_pages = [
        "https://chariow.com",
        "https://chariow.com/shops",
        "https://chariow.com/vendors",
    ]
    
    maketou_pages = [
        "https://maketou.com",
        "https://maketou.com/stores",
    ]
    
    # Découvrir depuis les pages Chariow
    print("\n📦 Découverte Chariow...")
    for page in chariow_pages:
        shops = await discover_shops_from_page(page, 'chariow')
        all_shops['chariow'].extend(shops)
        await asyncio.sleep(2)
    
    # Découvrir depuis les pages Maketou
    print("\n📦 Découverte Maketou...")
    for page in maketou_pages:
        shops = await discover_shops_from_page(page, 'maketou')
        all_shops['maketou'].extend(shops)
        await asyncio.sleep(2)
    
    # Explorer depuis les boutiques connues
    known_chariow = []  # Boutiques à découvrir automatiquement
    known_maketou = ["https://numerik.mymaketou.store/"]
    
    print("\n📦 Exploration depuis les boutiques connues...")
    for shop in known_chariow:
        shops = await discover_shops_from_page(shop, 'chariow')
        all_shops['chariow'].extend(shops)
        await asyncio.sleep(2)
    
    for shop in known_maketou:
        shops = await discover_shops_from_page(shop, 'maketou')
        all_shops['maketou'].extend(shops)
        await asyncio.sleep(2)
    
    # Afficher les résultats
    print(f"\n{'='*70}")
    print(f"✅ DÉCOUVERTE TERMINÉE")
    print(f"{'='*70}")
    print(f"Chariow: {len(set(all_shops['chariow']))} boutiques uniques")
    print(f"Maketou: {len(set(all_shops['maketou']))} boutiques uniques")
    
    # Afficher les URLs
    print(f"\n📋 Boutiques Chariow trouvées:")
    for shop in set(all_shops['chariow']):
        print(f"  - {shop}")
    
    print(f"\n📋 Boutiques Maketou trouvées:")
    for shop in set(all_shops['maketou']):
        print(f"  - {shop}")
    
    return all_shops

if __name__ == "__main__":
    result = asyncio.run(main())
    
    # Sauvegarder dans un fichier
    with open('discovered_shops.txt', 'w') as f:
        f.write("# Boutiques Chariow\n")
        for shop in set(result['chariow']):
            f.write(f"{shop}\n")
        f.write("\n# Boutiques Maketou\n")
        for shop in set(result['maketou']):
            f.write(f"{shop}\n")
    
    print(f"\n💾 URLs sauvegardées dans 'discovered_shops.txt'")




"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

async def discover_shops_from_page(url: str, marketplace: str) -> list:
    """Découvre des boutiques depuis une page donnée"""
    shop_urls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print(f"🔍 Exploration de: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            content = await page.content()
            try:
                soup = BeautifulSoup(content, 'lxml')
            except:
                soup = BeautifulSoup(content, 'html.parser')
            
            # Chercher tous les liens
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                if not href:
                    continue
                
                # Convertir en URL absolue
                if not href.startswith('http'):
                    href = urljoin(url, href)
                
                # Vérifier si c'est une boutique
                if marketplace == 'chariow':
                    if '.mychariow.shop' in href.lower():
                        if href not in shop_urls:
                            shop_urls.append(href)
                            print(f"  ✅ Boutique trouvée: {href}")
                elif marketplace == 'maketou':
                    if '.mymaketou.store' in href.lower():
                        if href not in shop_urls:
                            shop_urls.append(href)
                            print(f"  ✅ Boutique trouvée: {href}")
            
            # Scroll pour charger plus
            for i in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                
                content = await page.content()
                try:
                    soup = BeautifulSoup(content, 'lxml')
                except:
                    soup = BeautifulSoup(content, 'html.parser')
                
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    if not href:
                        continue
                    if not href.startswith('http'):
                        href = urljoin(url, href)
                    
                    if marketplace == 'chariow':
                        if '.mychariow.shop' in href.lower() and href not in shop_urls:
                            shop_urls.append(href)
                            print(f"  ✅ Boutique trouvée: {href}")
                    elif marketplace == 'maketou':
                        if '.mymaketou.store' in href.lower() and href not in shop_urls:
                            shop_urls.append(href)
                            print(f"  ✅ Boutique trouvée: {href}")
        
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
        finally:
            await browser.close()
    
    return shop_urls

async def main():
    """Découvre des boutiques depuis plusieurs sources"""
    print("🔍 Découverte de boutiques...")
    print("=" * 70)
    
    all_shops = {
        'chariow': [],
        'maketou': []
    }
    
    # Explorer les pages principales
    chariow_pages = [
        "https://chariow.com",
        "https://chariow.com/shops",
        "https://chariow.com/vendors",
    ]
    
    maketou_pages = [
        "https://maketou.com",
        "https://maketou.com/stores",
    ]
    
    # Découvrir depuis les pages Chariow
    print("\n📦 Découverte Chariow...")
    for page in chariow_pages:
        shops = await discover_shops_from_page(page, 'chariow')
        all_shops['chariow'].extend(shops)
        await asyncio.sleep(2)
    
    # Découvrir depuis les pages Maketou
    print("\n📦 Découverte Maketou...")
    for page in maketou_pages:
        shops = await discover_shops_from_page(page, 'maketou')
        all_shops['maketou'].extend(shops)
        await asyncio.sleep(2)
    
    # Explorer depuis les boutiques connues
    known_chariow = []  # Boutiques à découvrir automatiquement
    known_maketou = ["https://numerik.mymaketou.store/"]
    
    print("\n📦 Exploration depuis les boutiques connues...")
    for shop in known_chariow:
        shops = await discover_shops_from_page(shop, 'chariow')
        all_shops['chariow'].extend(shops)
        await asyncio.sleep(2)
    
    for shop in known_maketou:
        shops = await discover_shops_from_page(shop, 'maketou')
        all_shops['maketou'].extend(shops)
        await asyncio.sleep(2)
    
    # Afficher les résultats
    print(f"\n{'='*70}")
    print(f"✅ DÉCOUVERTE TERMINÉE")
    print(f"{'='*70}")
    print(f"Chariow: {len(set(all_shops['chariow']))} boutiques uniques")
    print(f"Maketou: {len(set(all_shops['maketou']))} boutiques uniques")
    
    # Afficher les URLs
    print(f"\n📋 Boutiques Chariow trouvées:")
    for shop in set(all_shops['chariow']):
        print(f"  - {shop}")
    
    print(f"\n📋 Boutiques Maketou trouvées:")
    for shop in set(all_shops['maketou']):
        print(f"  - {shop}")
    
    return all_shops

if __name__ == "__main__":
    result = asyncio.run(main())
    
    # Sauvegarder dans un fichier
    with open('discovered_shops.txt', 'w') as f:
        f.write("# Boutiques Chariow\n")
        for shop in set(result['chariow']):
            f.write(f"{shop}\n")
        f.write("\n# Boutiques Maketou\n")
        for shop in set(result['maketou']):
            f.write(f"{shop}\n")
    
    print(f"\n💾 URLs sauvegardées dans 'discovered_shops.txt'")



