"""
Script de test pour vérifier que le scraping fonctionne réellement
et scrape de vraies données depuis Chariow et Maketou
"""
import asyncio
import os
import sys
from datetime import datetime

# Ajouter les chemins
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from services.continuous_scraper import ContinuousScraper

# URLs de test
TEST_URLS = {
    "maketou": "https://numerik.mymaketou.store/",
    "chariow": "https://lumiahub.mychariow.shop/fr"  # Exemple de boutique
}

async def test_real_scraping():
    """Test le scraping réel d'une boutique"""
    print("="*70)
    print("🧪 TEST DE SCRAPING RÉEL")
    print("="*70)
    print()
    
    # Tester Maketou
    print("📦 Test scraping Maketou...")
    print(f"URL: {TEST_URLS['maketou']}")
    print()
    
    maketou_scraper = MaketouScraper()
    try:
        shop_data = await maketou_scraper.scrape_async(TEST_URLS['maketou'])
        
        print("✅ Scraping Maketou réussi!")
        print(f"\n📊 Données extraites:")
        print(f"  - Nom boutique: {shop_data.get('name', 'N/A')}")
        print(f"  - Nombre de produits: {shop_data.get('product_count', 0)}")
        print(f"  - Ventes estimées/mois: {shop_data.get('estimated_sales', 'N/A')}")
        print(f"  - Revenus estimés: {shop_data.get('estimated_revenue', 'N/A')}")
        
        if shop_data.get('products'):
            print(f"\n📦 Produits trouvés ({len(shop_data['products'])}):")
            for i, product in enumerate(shop_data['products'][:5], 1):
                print(f"  {i}. {product.get('name', 'N/A')[:50]} - {product.get('price', 0):,.0f} FCFA")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"❌ Erreur scraping Maketou: {e}")
        import traceback
        traceback.print_exc()
    
    # Tester Chariow
    print("\n📦 Test scraping Chariow...")
    print(f"URL: {TEST_URLS['chariow']}")
    print()
    
    chariow_scraper = ChariowScraper()
    try:
        shop_data = await chariow_scraper.scrape_async(TEST_URLS['chariow'])
        
        print("✅ Scraping Chariow réussi!")
        print(f"\n📊 Données extraites:")
        print(f"  - Nom boutique: {shop_data.get('name', 'N/A')}")
        print(f"  - Nombre de produits: {shop_data.get('product_count', 0)}")
        print(f"  - Ventes estimées/mois: {shop_data.get('estimated_sales', 'N/A')}")
        print(f"  - Revenus estimés: {shop_data.get('estimated_revenue', 'N/A')}")
        
        if shop_data.get('products'):
            print(f"\n📦 Produits trouvés ({len(shop_data['products'])}):")
            for i, product in enumerate(shop_data['products'][:5], 1):
                print(f"  {i}. {product.get('name', 'N/A')[:50]} - {product.get('price', 0):,.0f} FCFA")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"❌ Erreur scraping Chariow: {e}")
        import traceback
        traceback.print_exc()
    
    # Tester le scraper continu (un cycle)
    print("\n🔄 Test d'un cycle complet de scraping continu...")
    print()
    
    try:
        continuous_scraper = ContinuousScraper()
        result = await continuous_scraper.run_cycle()
        
        print("\n✅ Cycle de scraping terminé!")
        print(f"📊 Résultats:")
        print(f"  - Boutiques mises à jour: {result.get('updated', 0)}")
        print(f"  - Nouvelles boutiques: {result.get('new_shops', 0)}")
        print(f"  - Timestamp: {result.get('timestamp', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur cycle scraping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_scraping())




et scrape de vraies données depuis Chariow et Maketou
"""
import asyncio
import os
import sys
from datetime import datetime

# Ajouter les chemins
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chariow import ChariowScraper
from services.maketou import MaketouScraper
from services.continuous_scraper import ContinuousScraper

# URLs de test
TEST_URLS = {
    "maketou": "https://numerik.mymaketou.store/",
    "chariow": "https://lumiahub.mychariow.shop/fr"  # Exemple de boutique
}

async def test_real_scraping():
    """Test le scraping réel d'une boutique"""
    print("="*70)
    print("🧪 TEST DE SCRAPING RÉEL")
    print("="*70)
    print()
    
    # Tester Maketou
    print("📦 Test scraping Maketou...")
    print(f"URL: {TEST_URLS['maketou']}")
    print()
    
    maketou_scraper = MaketouScraper()
    try:
        shop_data = await maketou_scraper.scrape_async(TEST_URLS['maketou'])
        
        print("✅ Scraping Maketou réussi!")
        print(f"\n📊 Données extraites:")
        print(f"  - Nom boutique: {shop_data.get('name', 'N/A')}")
        print(f"  - Nombre de produits: {shop_data.get('product_count', 0)}")
        print(f"  - Ventes estimées/mois: {shop_data.get('estimated_sales', 'N/A')}")
        print(f"  - Revenus estimés: {shop_data.get('estimated_revenue', 'N/A')}")
        
        if shop_data.get('products'):
            print(f"\n📦 Produits trouvés ({len(shop_data['products'])}):")
            for i, product in enumerate(shop_data['products'][:5], 1):
                print(f"  {i}. {product.get('name', 'N/A')[:50]} - {product.get('price', 0):,.0f} FCFA")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"❌ Erreur scraping Maketou: {e}")
        import traceback
        traceback.print_exc()
    
    # Tester Chariow
    print("\n📦 Test scraping Chariow...")
    print(f"URL: {TEST_URLS['chariow']}")
    print()
    
    chariow_scraper = ChariowScraper()
    try:
        shop_data = await chariow_scraper.scrape_async(TEST_URLS['chariow'])
        
        print("✅ Scraping Chariow réussi!")
        print(f"\n📊 Données extraites:")
        print(f"  - Nom boutique: {shop_data.get('name', 'N/A')}")
        print(f"  - Nombre de produits: {shop_data.get('product_count', 0)}")
        print(f"  - Ventes estimées/mois: {shop_data.get('estimated_sales', 'N/A')}")
        print(f"  - Revenus estimés: {shop_data.get('estimated_revenue', 'N/A')}")
        
        if shop_data.get('products'):
            print(f"\n📦 Produits trouvés ({len(shop_data['products'])}):")
            for i, product in enumerate(shop_data['products'][:5], 1):
                print(f"  {i}. {product.get('name', 'N/A')[:50]} - {product.get('price', 0):,.0f} FCFA")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"❌ Erreur scraping Chariow: {e}")
        import traceback
        traceback.print_exc()
    
    # Tester le scraper continu (un cycle)
    print("\n🔄 Test d'un cycle complet de scraping continu...")
    print()
    
    try:
        continuous_scraper = ContinuousScraper()
        result = await continuous_scraper.run_cycle()
        
        print("\n✅ Cycle de scraping terminé!")
        print(f"📊 Résultats:")
        print(f"  - Boutiques mises à jour: {result.get('updated', 0)}")
        print(f"  - Nouvelles boutiques: {result.get('new_shops', 0)}")
        print(f"  - Timestamp: {result.get('timestamp', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur cycle scraping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_scraping())



