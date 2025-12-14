"""
Worker qui tourne en permanence pour le scraping continu
Peut être lancé comme service Docker ou processus système
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter les chemins
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.continuous_scraper import ContinuousScraper

def main():
    """Point d'entrée principal"""
    print("="*60)
    print("🚀 MarketPulse Africa - Scraper Continu")
    print("="*60)
    print("\nCe worker va:")
    print("  - Scraper les boutiques toutes les 6 heures")
    print("  - Découvrir de nouvelles boutiques toutes les 24 heures")
    print("  - Maintenir les données à jour en temps réel")
    print("\nAppuyez sur Ctrl+C pour arrêter\n")
    
    scraper = ContinuousScraper()
    
    try:
        asyncio.run(scraper.run_continuous())
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du worker...")
        sys.exit(0)

if __name__ == "__main__":
    main()




Worker qui tourne en permanence pour le scraping continu
Peut être lancé comme service Docker ou processus système
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter les chemins
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.continuous_scraper import ContinuousScraper

def main():
    """Point d'entrée principal"""
    print("="*60)
    print("🚀 MarketPulse Africa - Scraper Continu")
    print("="*60)
    print("\nCe worker va:")
    print("  - Scraper les boutiques toutes les 6 heures")
    print("  - Découvrir de nouvelles boutiques toutes les 24 heures")
    print("  - Maintenir les données à jour en temps réel")
    print("\nAppuyez sur Ctrl+C pour arrêter\n")
    
    scraper = ContinuousScraper()
    
    try:
        asyncio.run(scraper.run_continuous())
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du worker...")
        sys.exit(0)

if __name__ == "__main__":
    main()



