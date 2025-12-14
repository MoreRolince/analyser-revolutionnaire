"""
Script pour booster rapidement la collecte de données
Lance plusieurs cycles de scraping et de découverte
"""
import asyncio
import os
import sys
from datetime import datetime

# Ajouter les chemins
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_path)

from services.continuous_scraper import ContinuousScraper

async def boost_data_collection():
    """Lance plusieurs cycles pour collecter beaucoup de données"""
    print("="*70)
    print("🚀 BOOST DE COLLECTE DE DONNÉES")
    print("="*70)
    print()
    
    scraper = ContinuousScraper()
    
    # 1. Découvrir de nouvelles boutiques
    print("🔍 Étape 1: Découverte de nouvelles boutiques...")
    print()
    new_shops = await scraper.discover_and_add_new_shops()
    print(f"✅ {new_shops} nouvelles boutiques découvertes")
    print()
    
    # 2. Scraper toutes les boutiques existantes
    print("📦 Étape 2: Scraping de toutes les boutiques...")
    print()
    result = await scraper.run_cycle()
    print(f"✅ Cycle terminé: {result.get('updated', 0)} boutiques mises à jour")
    print()
    
    # 3. Relancer un cycle pour s'assurer que tout est à jour
    print("🔄 Étape 3: Second cycle de mise à jour...")
    print()
    result2 = await scraper.run_cycle()
    print(f"✅ Second cycle: {result2.get('updated', 0)} boutiques mises à jour")
    print()
    
    print("="*70)
    print("✅ BOOST TERMINÉ!")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(boost_data_collection())




Script pour booster rapidement la collecte de données
Lance plusieurs cycles de scraping et de découverte
"""
import asyncio
import os
import sys
from datetime import datetime

# Ajouter les chemins
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_path)

from services.continuous_scraper import ContinuousScraper

async def boost_data_collection():
    """Lance plusieurs cycles pour collecter beaucoup de données"""
    print("="*70)
    print("🚀 BOOST DE COLLECTE DE DONNÉES")
    print("="*70)
    print()
    
    scraper = ContinuousScraper()
    
    # 1. Découvrir de nouvelles boutiques
    print("🔍 Étape 1: Découverte de nouvelles boutiques...")
    print()
    new_shops = await scraper.discover_and_add_new_shops()
    print(f"✅ {new_shops} nouvelles boutiques découvertes")
    print()
    
    # 2. Scraper toutes les boutiques existantes
    print("📦 Étape 2: Scraping de toutes les boutiques...")
    print()
    result = await scraper.run_cycle()
    print(f"✅ Cycle terminé: {result.get('updated', 0)} boutiques mises à jour")
    print()
    
    # 3. Relancer un cycle pour s'assurer que tout est à jour
    print("🔄 Étape 3: Second cycle de mise à jour...")
    print()
    result2 = await scraper.run_cycle()
    print(f"✅ Second cycle: {result2.get('updated', 0)} boutiques mises à jour")
    print()
    
    print("="*70)
    print("✅ BOOST TERMINÉ!")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(boost_data_collection())



