"""
Module de détection automatique des boutiques Chariow et Maketou
Utilise les patterns d'URL et validation HTTP
"""
import re
import asyncio
from typing import List, Set, Dict
from urllib.parse import urlparse, urlunparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


class ShopDetector:
    """Détecte automatiquement les boutiques via patterns d'URL et validation HTTP"""
    
    def __init__(self):
        # Patterns regex pour détecter les boutiques
        self.chariow_pattern = re.compile(r'https://([a-zA-Z0-9\-]+)\.mychariow\.shop(/fr)?')
        self.maketou_pattern = re.compile(r'https://([a-zA-Z0-9\-]+)\.mymaketou\.store(/fr)?')
    
    async def validate_shop(self, shop_url: str, marketplace: str) -> bool:
        """
        Valide qu'une boutique existe et est accessible
        → requête HTTP → si status = 200, on valide la boutique
        """
        try:
            # Normaliser l'URL
            if marketplace == 'chariow' and not shop_url.endswith('/fr'):
                shop_url = shop_url.rstrip('/') + '/fr'
            elif marketplace == 'maketou' and not shop_url.endswith('/fr'):
                shop_url = shop_url.rstrip('/') + '/fr'
            
            # Utiliser urllib (bibliothèque standard) au lieu de aiohttp
            req = Request(shop_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=10) as response:
                return response.getcode() == 200
        except (URLError, HTTPError, Exception):
            return False
    
    def extract_shop_from_url(self, url: str) -> Dict[str, str] | None:
        """
        Extrait une URL de boutique depuis n'importe quelle URL
        Retourne None si ce n'est pas une boutique valide
        """
        # Vérifier Chariow
        chariow_match = self.chariow_pattern.match(url)
        if chariow_match:
            shop_name = chariow_match.group(1)
            shop_url = f"https://{shop_name}.mychariow.shop/fr"
            return {
                "shop_name": shop_name,
                "shop_url": shop_url,
                "marketplace": "chariow"
            }
        
        # Vérifier Maketou
        maketou_match = self.maketou_pattern.match(url)
        if maketou_match:
            shop_name = maketou_match.group(1)
            shop_url = f"https://{shop_name}.mymaketou.store/fr"
            return {
                "shop_name": shop_name,
                "shop_url": shop_url,
                "marketplace": "maketou"
            }
        
        return None
    
    def normalize_shop_url(self, url: str, marketplace: str) -> str:
        """
        Normalise une URL de boutique
        Retourne l'URL normalisée ou "" si invalide
        """
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            
            if marketplace == 'chariow':
                if 'mychariow.shop' not in host:
                    return ""
                # Construire l'URL normalisée
                shop_name = host.split('.')[0]
                return f"https://{shop_name}.mychariow.shop/fr"
            
            elif marketplace == 'maketou':
                if 'mymaketou.store' not in host:
                    return ""
                shop_name = host.split('.')[0]
                return f"https://{shop_name}.mymaketou.store/fr"
            
            return ""
        except Exception:
            return ""
    
    async def discover_shops_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        Découvre des boutiques depuis un texte (HTML, liste d'URLs, etc.)
        """
        shops = []
        seen_urls = set()
        
        # Chercher tous les patterns Chariow
        chariow_matches = self.chariow_pattern.findall(text)
        for match in chariow_matches:
            shop_name = match[0] if isinstance(match, tuple) else match
            shop_url = f"https://{shop_name}.mychariow.shop/fr"
            if shop_url not in seen_urls:
                shops.append({
                    "shop_name": shop_name,
                    "shop_url": shop_url,
                    "marketplace": "chariow"
                })
                seen_urls.add(shop_url)
        
        # Chercher tous les patterns Maketou
        maketou_matches = self.maketou_pattern.findall(text)
        for match in maketou_matches:
            shop_name = match[0] if isinstance(match, tuple) else match
            shop_url = f"https://{shop_name}.mymaketou.store/fr"
            if shop_url not in seen_urls:
                shops.append({
                    "shop_name": shop_name,
                    "shop_url": shop_url,
                    "marketplace": "maketou"
                })
                seen_urls.add(shop_url)
        
        return shops
    
    async def validate_shops(self, shops: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Valide une liste de boutiques en parallèle
        Retourne uniquement les boutiques valides (status 200)
        """
        valid_shops = []
        
        async def validate_one(shop: Dict[str, str]) -> Dict[str, str] | None:
            is_valid = await self.validate_shop(shop["shop_url"], shop["marketplace"])
            return shop if is_valid else None
        
        # Valider en parallèle (max 10 simultanées)
        semaphore = asyncio.Semaphore(10)
        
        async def validate_with_semaphore(shop: Dict[str, str]):
            async with semaphore:
                return await validate_one(shop)
        
        tasks = [validate_with_semaphore(shop) for shop in shops]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if result and isinstance(result, dict):
                valid_shops.append(result)
        
        return valid_shops
