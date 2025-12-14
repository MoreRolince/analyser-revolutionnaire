"""
Script de test simple - Scrape une boutique pour vérifier que ça fonctionne
"""
import asyncio
from services.chariow_scraper import ChariowScraper
from services.maketou_scraper import MaketouScraper


async def test_chariow():
    """Test scraping Chariow"""
    print("🧪 TEST SCRAPER CHARIOW")
    print("=" * 70)
    
    scraper = ChariowScraper()
    shop_url = "https://lumiahub.mychariow.shop/fr"  # Exemple de boutique
    
    print(f"📦 Scraping: {shop_url}")
    shop_data = await scraper.scrape_shop(shop_url)
    
    print(f"\n✅ Résultats:")
    print(f"   Nom boutique: {shop_data.get('shop_name', 'N/A')}")
    print(f"   Nombre produits: {shop_data.get('product_count', 0)}")
    
    if shop_data.get('products'):
        print(f"\n📋 Produits trouvés:")
        for i, product in enumerate(shop_data['products'][:5], 1):
            print(f"   {i}. {product.get('title', 'N/A')[:60]}")
            print(f"      URL: {product.get('url', 'N/A')[:60]}")
            print(f"      Prix: {product.get('price', 0)} FCFA")
    else:
        print("   ⚠️  Aucun produit trouvé")


async def test_maketou():
    """Test scraping Maketou"""
    print("\n🧪 TEST SCRAPER MAKETOU")
    print("=" * 70)
    
    scraper = MaketouScraper()
    shop_url = "https://numerik.mymaketou.store/fr"
    
    print(f"📦 Scraping: {shop_url}")
    shop_data = await scraper.scrape_shop(shop_url)
    
    print(f"\n✅ Résultats:")
    print(f"   Nom boutique: {shop_data.get('shop_name', 'N/A')}")
    print(f"   Nombre produits: {shop_data.get('product_count', 0)}")
    
    if shop_data.get('products'):
        print(f"\n📋 Produits trouvés:")
        for i, product in enumerate(shop_data['products'][:5], 1):
            print(f"   {i}. {product.get('title', 'N/A')[:60]}")
            print(f"      URL: {product.get('url', 'N/A')[:60]}")
            print(f"      Prix: {product.get('price', 0)} FCFA")
    else:
        print("   ⚠️  Aucun produit trouvé")


async def main():
    """Test les deux scrapers"""
    await test_chariow()
    # await test_maketou()  # Décommenter pour tester Maketou aussi


if __name__ == "__main__":
    asyncio.run(main())


"""
import asyncio
from services.chariow_scraper import ChariowScraper
from services.maketou_scraper import MaketouScraper


async def test_chariow():
    """Test scraping Chariow"""
    print("🧪 TEST SCRAPER CHARIOW")
    print("=" * 70)
    
    scraper = ChariowScraper()
    shop_url = "https://lumiahub.mychariow.shop/fr"  # Exemple de boutique
    
    print(f"📦 Scraping: {shop_url}")
    shop_data = await scraper.scrape_shop(shop_url)
    
    print(f"\n✅ Résultats:")
    print(f"   Nom boutique: {shop_data.get('shop_name', 'N/A')}")
    print(f"   Nombre produits: {shop_data.get('product_count', 0)}")
    
    if shop_data.get('products'):
        print(f"\n📋 Produits trouvés:")
        for i, product in enumerate(shop_data['products'][:5], 1):
            print(f"   {i}. {product.get('title', 'N/A')[:60]}")
            print(f"      URL: {product.get('url', 'N/A')[:60]}")
            print(f"      Prix: {product.get('price', 0)} FCFA")
    else:
        print("   ⚠️  Aucun produit trouvé")


async def test_maketou():
    """Test scraping Maketou"""
    print("\n🧪 TEST SCRAPER MAKETOU")
    print("=" * 70)
    
    scraper = MaketouScraper()
    shop_url = "https://numerik.mymaketou.store/fr"
    
    print(f"📦 Scraping: {shop_url}")
    shop_data = await scraper.scrape_shop(shop_url)
    
    print(f"\n✅ Résultats:")
    print(f"   Nom boutique: {shop_data.get('shop_name', 'N/A')}")
    print(f"   Nombre produits: {shop_data.get('product_count', 0)}")
    
    if shop_data.get('products'):
        print(f"\n📋 Produits trouvés:")
        for i, product in enumerate(shop_data['products'][:5], 1):
            print(f"   {i}. {product.get('title', 'N/A')[:60]}")
            print(f"      URL: {product.get('url', 'N/A')[:60]}")
            print(f"      Prix: {product.get('price', 0)} FCFA")
    else:
        print("   ⚠️  Aucun produit trouvé")


async def main():
    """Test les deux scrapers"""
    await test_chariow()
    # await test_maketou()  # Décommenter pour tester Maketou aussi


if __name__ == "__main__":
    asyncio.run(main())

