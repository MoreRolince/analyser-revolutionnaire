"""
Script de test pour verifier que tout fonctionne
"""
import sys
import os

print("TEST 1: Imports Python")
print("-" * 50)
try:
    import asyncio
    print("OK: asyncio")
except Exception as e:
    print(f"ERREUR: asyncio - {e}")

try:
    from playwright.async_api import async_playwright
    print("OK: playwright")
except Exception as e:
    print(f"ERREUR: playwright - {e}")
    print("Installez avec: pip install playwright && playwright install chromium")

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    print("OK: sqlalchemy")
except Exception as e:
    print(f"ERREUR: sqlalchemy - {e}")

print("\nTEST 2: Connexion base de donnees")
print("-" * 50)
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    backend_path = os.path.join(project_root, 'backend')
    
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
    )
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Test connexion
    result = db.execute(text("SELECT 1")).scalar()
    print(f"OK: Connexion DB reussie (resultat: {result})")
    
    # Test tables
    try:
        count = db.execute(text("SELECT COUNT(*) FROM fb_ads_raw")).scalar()
        print(f"OK: Table fb_ads_raw existe ({count} annonces)")
    except Exception as e:
        print(f"ERREUR: Table fb_ads_raw - {e}")
    
    try:
        count = db.execute(text("SELECT COUNT(*) FROM digital_products_detected")).scalar()
        print(f"OK: Table digital_products_detected existe ({count} produits)")
    except Exception as e:
        print(f"ERREUR: Table digital_products_detected - {e}")
    
    db.close()
    
except Exception as e:
    print(f"ERREUR: Connexion DB - {e}")
    import traceback
    traceback.print_exc()

print("\nTEST 3: Playwright")
print("-" * 50)
try:
    async def test_playwright():
        try:
            async with async_playwright() as p:
                print("OK: Playwright initialise")
                browser = await p.chromium.launch(headless=True)
                print("OK: Navigateur lance")
                await browser.close()
                print("OK: Navigateur ferme")
                return True
        except Exception as e:
            print(f"ERREUR: Playwright - {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Configuration Windows
    if sys.platform == 'win32':
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    result = asyncio.run(test_playwright())
    if result:
        print("OK: Tous les tests Playwright reussis")
    else:
        print("ERREUR: Tests Playwright echoues")
        
except Exception as e:
    print(f"ERREUR: Test Playwright - {e}")
    import traceback
    traceback.print_exc()

print("\nTEST 4: Import du scraper")
print("-" * 50)
try:
    from services.facebook_ads_scraper_working import MOTS_CLES_FRANCAIS, scrape_ads_library
    print(f"OK: Scraper importe ({len(MOTS_CLES_FRANCAIS)} mots-cles)")
except Exception as e:
    print(f"ERREUR: Import scraper - {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("FIN DES TESTS")
print("=" * 50)

