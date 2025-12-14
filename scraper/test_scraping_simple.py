"""
Test de scraping simple - Un seul mot-cle
"""
import asyncio
import sys
import os

# Configuration Windows
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configuration DB
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, 'backend')

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from services.facebook_ads_scraper_working import scrape_ads_library

async def test():
    print("=" * 70)
    print("TEST DE SCRAPING SIMPLE")
    print("=" * 70)
    print("\nTest avec le mot-cle: 'formation'")
    print("Attente de 30 secondes maximum...")
    sys.stdout.flush()
    
    try:
        ads = await scrape_ads_library(search_term="formation", limit=5)
        print(f"\nRESULTAT: {len(ads)} annonces trouvees")
        
        if ads:
            print("\nPremiere annonce:")
            ad = ads[0]
            print(f"  - Page: {ad.get('pageName', 'N/A')}")
            print(f"  - Texte: {ad.get('text', 'N/A')[:100]}...")
            print(f"  - Image: {'OUI' if ad.get('imageUrl') else 'NON'}")
            url = ad.get('productUrl') or 'N/A'
            if url != 'N/A':
                print(f"  - URL: {url[:80]}...")
            else:
                print(f"  - URL: N/A")
        else:
            print("\nAucune annonce trouvee")
            
    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Debut du test...")
    sys.stdout.flush()
    asyncio.run(test())
    print("\nFin du test")

