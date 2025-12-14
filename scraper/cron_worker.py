"""
Worker CRON pour crawler les winners toutes les 6 heures
À exécuter avec un scheduler (cron, systemd timer, etc.)
"""
import time
import os
from services.winners_crawler import crawl_all_marketplaces

def main():
    """Fonction principale du worker CRON"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Démarrage du crawl des winners...")
    
    try:
        results = crawl_all_marketplaces()
        
        total_products = sum(r.get('products', 0) for r in results if isinstance(r, dict))
        total_shops = sum(r.get('shops', 0) for r in results if isinstance(r, dict))
        
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Crawl terminé: {total_products} produits, {total_shops} boutiques")
        
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors du crawl: {e}")
        raise

if __name__ == "__main__":
    main()




Worker CRON pour crawler les winners toutes les 6 heures
À exécuter avec un scheduler (cron, systemd timer, etc.)
"""
import time
import os
from services.winners_crawler import crawl_all_marketplaces

def main():
    """Fonction principale du worker CRON"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Démarrage du crawl des winners...")
    
    try:
        results = crawl_all_marketplaces()
        
        total_products = sum(r.get('products', 0) for r in results if isinstance(r, dict))
        total_shops = sum(r.get('shops', 0) for r in results if isinstance(r, dict))
        
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Crawl terminé: {total_products} produits, {total_shops} boutiques")
        
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors du crawl: {e}")
        raise

if __name__ == "__main__":
    main()



