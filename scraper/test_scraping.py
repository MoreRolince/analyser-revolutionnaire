"""
Script de test pour scraper les vraies données depuis Chariow et Maketou
"""
import os
import sys
import asyncio
from datetime import datetime

# Ajouter le chemin parent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.services.chariow import ChariowScraper
from scraper.services.maketou import MaketouScraper
from scraper.utils.scoring import calculate_product_score, calculate_shop_score

# URLs de test fournies par l'utilisateur
TEST_URLS = {
    "maketou": "https://numerik.mymaketou.store/",
    "chariow": "https://lumiahub.mychariow.shop/fr"  # Exemple de boutique
}

async def test_scrape_shop(url: str, marketplace: str):
    """Test le scraping d'une boutique"""
    print(f"\n{'='*60}")
    print(f"Test scraping: {marketplace.upper()}")
    print(f"URL: {url}")
    print(f"{'='*60}\n")
    
    if marketplace == "maketou":
        scraper = MaketouScraper()
    elif marketplace == "chariow":
        scraper = ChariowScraper()
    else:
        print(f"Marketplace non supporté: {marketplace}")
        return None
    
    try:
        data = await scraper.scrape_async(url)
        
        print(f"✅ Scraping réussi!")
        print(f"\n📊 Données extraites:")
        print(f"  - Nom: {data.get('name', 'N/A')}")
        print(f"  - Nombre de produits: {data.get('product_count', 0)}")
        print(f"  - Ventes estimées/mois: {data.get('estimated_sales', 'N/A')}")
        print(f"  - Revenus estimés: {data.get('estimated_revenue', 'N/A')}")
        
        if data.get('products'):
            print(f"\n📦 Produits trouvés ({len(data['products'])}):")
            for i, product in enumerate(data['products'][:5], 1):
                print(f"  {i}. {product.get('name', 'N/A')} - {product.get('price', 0):,.0f} FCFA")
        
        # Calculer le score
        shop_score = calculate_shop_score(data)
        print(f"\n⭐ Score de la boutique: {shop_score:.1f}/100")
        
        return data
        
    except Exception as e:
        print(f"❌ Erreur lors du scraping: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Fonction principale"""
    print("🚀 Démarrage des tests de scraping...")
    
    results = {}
    
    # Tester Maketou
    maketou_data = await test_scrape_shop(TEST_URLS["maketou"], "maketou")
    results["maketou"] = maketou_data
    
    # Tester Chariow
    chariow_data = await test_scrape_shop(TEST_URLS["chariow"], "chariow")
    results["chariow"] = chariow_data
    
    # Résumé
    print(f"\n{'='*60}")
    print("📋 RÉSUMÉ DES TESTS")
    print(f"{'='*60}\n")
    
    for marketplace, data in results.items():
        if data:
            print(f"✅ {marketplace.upper()}: {data.get('product_count', 0)} produits trouvés")
        else:
            print(f"❌ {marketplace.upper()}: Échec du scraping")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())




"""
import os
import sys
import asyncio
from datetime import datetime

# Ajouter le chemin parent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.services.chariow import ChariowScraper
from scraper.services.maketou import MaketouScraper
from scraper.utils.scoring import calculate_product_score, calculate_shop_score

# URLs de test fournies par l'utilisateur
TEST_URLS = {
    "maketou": "https://numerik.mymaketou.store/",
    "chariow": "https://lumiahub.mychariow.shop/fr"  # Exemple de boutique
}

async def test_scrape_shop(url: str, marketplace: str):
    """Test le scraping d'une boutique"""
    print(f"\n{'='*60}")
    print(f"Test scraping: {marketplace.upper()}")
    print(f"URL: {url}")
    print(f"{'='*60}\n")
    
    if marketplace == "maketou":
        scraper = MaketouScraper()
    elif marketplace == "chariow":
        scraper = ChariowScraper()
    else:
        print(f"Marketplace non supporté: {marketplace}")
        return None
    
    try:
        data = await scraper.scrape_async(url)
        
        print(f"✅ Scraping réussi!")
        print(f"\n📊 Données extraites:")
        print(f"  - Nom: {data.get('name', 'N/A')}")
        print(f"  - Nombre de produits: {data.get('product_count', 0)}")
        print(f"  - Ventes estimées/mois: {data.get('estimated_sales', 'N/A')}")
        print(f"  - Revenus estimés: {data.get('estimated_revenue', 'N/A')}")
        
        if data.get('products'):
            print(f"\n📦 Produits trouvés ({len(data['products'])}):")
            for i, product in enumerate(data['products'][:5], 1):
                print(f"  {i}. {product.get('name', 'N/A')} - {product.get('price', 0):,.0f} FCFA")
        
        # Calculer le score
        shop_score = calculate_shop_score(data)
        print(f"\n⭐ Score de la boutique: {shop_score:.1f}/100")
        
        return data
        
    except Exception as e:
        print(f"❌ Erreur lors du scraping: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Fonction principale"""
    print("🚀 Démarrage des tests de scraping...")
    
    results = {}
    
    # Tester Maketou
    maketou_data = await test_scrape_shop(TEST_URLS["maketou"], "maketou")
    results["maketou"] = maketou_data
    
    # Tester Chariow
    chariow_data = await test_scrape_shop(TEST_URLS["chariow"], "chariow")
    results["chariow"] = chariow_data
    
    # Résumé
    print(f"\n{'='*60}")
    print("📋 RÉSUMÉ DES TESTS")
    print(f"{'='*60}\n")
    
    for marketplace, data in results.items():
        if data:
            print(f"✅ {marketplace.upper()}: {data.get('product_count', 0)} produits trouvés")
        else:
            print(f"❌ {marketplace.upper()}: Échec du scraping")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())



