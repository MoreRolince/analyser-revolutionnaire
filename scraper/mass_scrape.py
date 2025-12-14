"""
Script pour scraper massivement des boutiques et collecter beaucoup de données
"""
import asyncio
import os
import sys
from datetime import datetime

# Ajouter les chemins
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_path)

from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from services.continuous_scraper import ContinuousScraper

# Liste de boutiques connues à scraper
KNOWN_SHOPS = {
    "maketou": [
        "https://numerik.mymaketou.store/",
        "https://luminahub.mymaketou.store/",
        "https://africashop.mymaketou.store/",
        "https://techzone.mymaketou.store/",
        "https://digitalstore.mymaketou.store/",
    ],
    "chariow": [
        "https://africamarket.mychariow.shop/",
        "https://techshop.mychariow.shop/",
        "https://digitalhub.mychariow.shop/",
        "https://businessstore.mychariow.shop/",
    ]
}

async def mass_scrape():
    """Scrape massivement des boutiques"""
    print("="*70)
    print("🚀 SCRAPING MASSIF - COLLECTE DE DONNÉES")
    print("="*70)
    print()
    
    continuous_scraper = ContinuousScraper()
    
    total_shops = 0
    total_products = 0
    successful = 0
    failed = 0
    
    # Scraper toutes les boutiques connues
    for marketplace, shop_urls in KNOWN_SHOPS.items():
        print(f"\n📦 Marketplace: {marketplace.upper()}")
        print(f"   {len(shop_urls)} boutiques à scraper")
        print()
        
        for shop_url in shop_urls:
            try:
                print(f"🔄 Scraping: {shop_url}")
                result = await continuous_scraper.scrape_shop(shop_url, marketplace)
                
                if result.get('status') == 'success':
                    successful += 1
                    total_shops += 1
                    products_count = result.get('products_saved', 0)
                    total_products += products_count
                    print(f"   ✅ Succès: {products_count} produits sauvegardés")
                else:
                    failed += 1
                    print(f"   ⚠️  {result.get('message', 'Erreur inconnue')}")
                
                # Pause entre chaque scraping pour ne pas surcharger
                await asyncio.sleep(3)
                
            except Exception as e:
                failed += 1
                print(f"   ❌ Erreur: {e}")
                continue
    
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DU SCRAPING MASSIF")
    print("="*70)
    print(f"✅ Boutiques réussies: {successful}")
    print(f"❌ Boutiques échouées: {failed}")
    print(f"📦 Total produits collectés: {total_products}")
    print(f"🏪 Total boutiques: {total_shops}")
    print()
    print("✅ Scraping massif terminé!")

if __name__ == "__main__":
    asyncio.run(mass_scrape())




"""
import asyncio
import os
import sys
from datetime import datetime

# Ajouter les chemins
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_path)

from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from services.continuous_scraper import ContinuousScraper

# Liste de boutiques connues à scraper
KNOWN_SHOPS = {
    "maketou": [
        "https://numerik.mymaketou.store/",
        "https://luminahub.mymaketou.store/",
        "https://africashop.mymaketou.store/",
        "https://techzone.mymaketou.store/",
        "https://digitalstore.mymaketou.store/",
    ],
    "chariow": [
        "https://africamarket.mychariow.shop/",
        "https://techshop.mychariow.shop/",
        "https://digitalhub.mychariow.shop/",
        "https://businessstore.mychariow.shop/",
    ]
}

async def mass_scrape():
    """Scrape massivement des boutiques"""
    print("="*70)
    print("🚀 SCRAPING MASSIF - COLLECTE DE DONNÉES")
    print("="*70)
    print()
    
    continuous_scraper = ContinuousScraper()
    
    total_shops = 0
    total_products = 0
    successful = 0
    failed = 0
    
    # Scraper toutes les boutiques connues
    for marketplace, shop_urls in KNOWN_SHOPS.items():
        print(f"\n📦 Marketplace: {marketplace.upper()}")
        print(f"   {len(shop_urls)} boutiques à scraper")
        print()
        
        for shop_url in shop_urls:
            try:
                print(f"🔄 Scraping: {shop_url}")
                result = await continuous_scraper.scrape_shop(shop_url, marketplace)
                
                if result.get('status') == 'success':
                    successful += 1
                    total_shops += 1
                    products_count = result.get('products_saved', 0)
                    total_products += products_count
                    print(f"   ✅ Succès: {products_count} produits sauvegardés")
                else:
                    failed += 1
                    print(f"   ⚠️  {result.get('message', 'Erreur inconnue')}")
                
                # Pause entre chaque scraping pour ne pas surcharger
                await asyncio.sleep(3)
                
            except Exception as e:
                failed += 1
                print(f"   ❌ Erreur: {e}")
                continue
    
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DU SCRAPING MASSIF")
    print("="*70)
    print(f"✅ Boutiques réussies: {successful}")
    print(f"❌ Boutiques échouées: {failed}")
    print(f"📦 Total produits collectés: {total_products}")
    print(f"🏪 Total boutiques: {total_shops}")
    print()
    print("✅ Scraping massif terminé!")

if __name__ == "__main__":
    asyncio.run(mass_scrape())



