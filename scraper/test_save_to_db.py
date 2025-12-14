"""
Test pour vérifier que les données scrapées sont bien sauvegardées en base
"""
import asyncio
import os
import sys

# Ajouter les chemins
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_path)

from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from services.continuous_scraper import ContinuousScraper

# URLs de test
TEST_URLS = {
    "maketou": "https://numerik.mymaketou.store/",
    "chariow": "https://lumiahub.mychariow.shop/fr"  # Exemple de boutique
}

async def test_save_to_database():
    """Test le scraping et la sauvegarde en base de données"""
    print("="*70)
    print("🧪 TEST DE SCRAPING ET SAUVEGARDE EN BASE")
    print("="*70)
    print()
    
    continuous_scraper = ContinuousScraper()
    
    # Tester le scraping d'une boutique Maketou et sauvegarde
    print("📦 Test scraping et sauvegarde Maketou...")
    print(f"URL: {TEST_URLS['maketou']}")
    print()
    
    try:
        result = await continuous_scraper.scrape_shop(TEST_URLS['maketou'], "maketou")
        print(f"✅ Résultat: {result.get('status')}")
        if result.get('status') == 'success':
            print(f"  - Produits sauvegardés: {result.get('products_saved', 0)}")
            print(f"  - Score boutique: {result.get('shop_score', 0):.1f}/100")
        else:
            print(f"  - Message: {result.get('message', 'N/A')}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    
    # Tester le scraping d'une boutique Chariow et sauvegarde
    print("\n📦 Test scraping et sauvegarde Chariow...")
    print(f"URL: {TEST_URLS['chariow']}")
    print()
    
    try:
        result = await continuous_scraper.scrape_shop(TEST_URLS['chariow'], "chariow")
        print(f"✅ Résultat: {result.get('status')}")
        if result.get('status') == 'success':
            print(f"  - Produits sauvegardés: {result.get('products_saved', 0)}")
            print(f"  - Score boutique: {result.get('shop_score', 0):.1f}/100")
        else:
            print(f"  - Message: {result.get('message', 'N/A')}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("\n✅ Test terminé! Vérifiez la base de données pour voir les données sauvegardées.")

if __name__ == "__main__":
    asyncio.run(test_save_to_database())




"""
import asyncio
import os
import sys

# Ajouter les chemins
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_path)

from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from services.continuous_scraper import ContinuousScraper

# URLs de test
TEST_URLS = {
    "maketou": "https://numerik.mymaketou.store/",
    "chariow": "https://lumiahub.mychariow.shop/fr"  # Exemple de boutique
}

async def test_save_to_database():
    """Test le scraping et la sauvegarde en base de données"""
    print("="*70)
    print("🧪 TEST DE SCRAPING ET SAUVEGARDE EN BASE")
    print("="*70)
    print()
    
    continuous_scraper = ContinuousScraper()
    
    # Tester le scraping d'une boutique Maketou et sauvegarde
    print("📦 Test scraping et sauvegarde Maketou...")
    print(f"URL: {TEST_URLS['maketou']}")
    print()
    
    try:
        result = await continuous_scraper.scrape_shop(TEST_URLS['maketou'], "maketou")
        print(f"✅ Résultat: {result.get('status')}")
        if result.get('status') == 'success':
            print(f"  - Produits sauvegardés: {result.get('products_saved', 0)}")
            print(f"  - Score boutique: {result.get('shop_score', 0):.1f}/100")
        else:
            print(f"  - Message: {result.get('message', 'N/A')}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    
    # Tester le scraping d'une boutique Chariow et sauvegarde
    print("\n📦 Test scraping et sauvegarde Chariow...")
    print(f"URL: {TEST_URLS['chariow']}")
    print()
    
    try:
        result = await continuous_scraper.scrape_shop(TEST_URLS['chariow'], "chariow")
        print(f"✅ Résultat: {result.get('status')}")
        if result.get('status') == 'success':
            print(f"  - Produits sauvegardés: {result.get('products_saved', 0)}")
            print(f"  - Score boutique: {result.get('shop_score', 0):.1f}/100")
        else:
            print(f"  - Message: {result.get('message', 'N/A')}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("\n✅ Test terminé! Vérifiez la base de données pour voir les données sauvegardées.")

if __name__ == "__main__":
    asyncio.run(test_save_to_database())



