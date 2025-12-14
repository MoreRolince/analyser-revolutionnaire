"""
Générateur d'URLs de boutiques possibles pour Chariow et Maketou
Génère des URLs basées sur des noms communs et les teste
"""
import asyncio
from typing import List, Set
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


class ShopURLGenerator:
    """Génère et teste des URLs de boutiques possibles"""
    
    # Noms de boutiques communs pour produits digitaux
    SHOP_NAMES = [
        # Produits digitaux
        'digital', 'digitalstore', 'digitalhub', 'digitalshop', 'digitalmarket',
        'ebook', 'ebookstore', 'ebookshop', 'ebookhub', 'ebookmarket',
        'template', 'templatestore', 'templateshop', 'templatehub', 'templatemarket',
        'formation', 'formationstore', 'formationshop', 'formationhub',
        'cours', 'coursstore', 'coursshop', 'courshub',
        'logiciel', 'logicielstore', 'logicielshop', 'logicielhub',
        'plugin', 'pluginstore', 'pluginshop', 'pluginhub',
        'theme', 'themestore', 'themeshop', 'themehub',
        'software', 'softwarestore', 'softwareshop', 'softwarehub',
        'app', 'appstore', 'appshop', 'apphub',
        'guide', 'guidestore', 'guideshop', 'guidehub',
        'tutoriel', 'tutorielstore', 'tutorielshop',
        'coaching', 'coachingstore', 'coachingshop',
        'consultation', 'consultationstore', 'consultationshop',
        'graphisme', 'graphismestore', 'graphismeshop',
        'design', 'designstore', 'designshop', 'designhub',
        'marketing', 'marketingstore', 'marketingshop',
        'affiliation', 'affiliationstore', 'affiliationshop',
        'dropshipping', 'dropshippingstore', 'dropshippingshop',
        # Mots africains
        'afrique', 'africastore', 'africashop', 'africahub',
        'cameroun', 'camerounstore', 'camerounshop',
        'senegal', 'senegalstore', 'senegalshop',
        'cotedivoire', 'cotedivoirestore', 'cotedivoireshop',
        'mali', 'malistore', 'malishop',
        'benin', 'beninstore', 'beninshop',
        'togo', 'togostore', 'togoshop',
        # Combinaisons
        'digitalafrique', 'ebookafrique', 'formationafrique',
        'digitalcameroun', 'ebooksenegal', 'formationmali',
        'africadigital', 'africaebook', 'africaformation',
        # Noms génériques
        'store', 'shop', 'hub', 'market', 'boutique', 'magasin',
        'digitalstore', 'digitalshop', 'digitalhub',
        'online', 'online-store', 'online-shop',
        'web', 'webstore', 'webshop',
        'pro', 'prostore', 'proshop',
        'premium', 'premiumstore', 'premiumshop',
        'expert', 'expertstore', 'expertshop',
        'master', 'masterstore', 'mastershop',
        'elite', 'elitestore', 'eliteshop',
        # Noms courts
        'dig', 'digi', 'ebk', 'tmp', 'frm', 'log', 'plg', 'thm',
        'afr', 'cmr', 'sng', 'ml', 'bn', 'tg',
    ]
    
    # Suffixes communs
    SUFFIXES = [
        '', 'store', 'shop', 'hub', 'market', 'boutique', 'magasin',
        'online', 'digital', 'pro', 'premium', 'expert', 'master', 'elite',
        'afrique', 'africa', 'west', 'central', 'north',
    ]
    
    @classmethod
    def generate_chariow_urls(cls, limit: int = 500) -> List[str]:
        """Génère des URLs Chariow possibles"""
        urls = set()
        
        # Combinaisons de noms + suffixes
        for name in cls.SHOP_NAMES:
            if len(urls) >= limit:
                break
            
            # Nom seul
            urls.add(f"https://{name}.mychariow.shop/fr")
            
            # Nom + suffixe
            for suffix in cls.SUFFIXES[:10]:  # Limiter les suffixes
                if len(urls) >= limit:
                    break
                if suffix:
                    combined = f"{name}{suffix}"
                    urls.add(f"https://{combined}.mychariow.shop/fr")
        
        # Ajouter des variations avec tirets
        base_urls = list(urls)
        for url in base_urls[:limit//2]:
            if len(urls) >= limit:
                break
            # Remplacer certains caractères par des tirets
            url_with_dash = url.replace('store', '-store').replace('shop', '-shop')
            if url_with_dash != url:
                urls.add(url_with_dash)
        
        return sorted(list(urls))[:limit]
    
    @classmethod
    def generate_maketou_urls(cls, limit: int = 500) -> List[str]:
        """Génère des URLs Maketou possibles"""
        urls = set()
        
        # Combinaisons de noms + suffixes
        for name in cls.SHOP_NAMES:
            if len(urls) >= limit:
                break
            
            # Nom seul
            urls.add(f"https://{name}.mymaketou.store/fr")
            
            # Nom + suffixe
            for suffix in cls.SUFFIXES[:10]:  # Limiter les suffixes
                if len(urls) >= limit:
                    break
                if suffix:
                    combined = f"{name}{suffix}"
                    urls.add(f"https://{combined}.mymaketou.store/fr")
        
        # Ajouter des variations avec tirets
        base_urls = list(urls)
        for url in base_urls[:limit//2]:
            if len(urls) >= limit:
                break
            # Remplacer certains caractères par des tirets
            url_with_dash = url.replace('store', '-store').replace('shop', '-shop')
            if url_with_dash != url:
                urls.add(url_with_dash)
        
        return sorted(list(urls))[:limit]
    
    @classmethod
    async def validate_shops_batch(cls, urls: List[str], max_concurrent: int = 20) -> List[str]:
        """
        Valide un batch d'URLs en parallèle
        Retourne uniquement les URLs qui existent (status 200)
        """
        valid_shops = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def validate_one(url: str) -> str | None:
            async with semaphore:
                try:
                    # Utiliser urllib de manière asynchrone
                    def check_url():
                        try:
                            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urlopen(req, timeout=5) as response:
                                if response.getcode() == 200:
                                    content = response.read().decode('utf-8', errors='ignore')
                                    # Vérifier des indicateurs de boutique
                                    if any(indicator in content.lower() for indicator in ['product', 'produit', 'shop', 'boutique', 'store', 'acheter', 'buy', 'prix', 'price']):
                                        return url
                        except (URLError, HTTPError, Exception):
                            pass
                        return None
                    
                    # Exécuter dans un thread pour ne pas bloquer
                    result = await asyncio.to_thread(check_url)
                    return result
                except Exception:
                    pass
                return None
        
        tasks = [validate_one(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if result and isinstance(result, str):
                valid_shops.append(result)
        
        return valid_shops
    
    @classmethod
    async def discover_shops(cls, marketplace: str, limit: int = 500) -> List[str]:
        """
        Découvre des boutiques en générant des URLs et en les validant
        """
        print(f"  🔧 Génération de {limit} URLs possibles pour {marketplace}...")
        
        if marketplace == 'chariow':
            urls = cls.generate_chariow_urls(limit)
        elif marketplace == 'maketou':
            urls = cls.generate_maketou_urls(limit)
        else:
            return []
        
        print(f"  ✅ {len(urls)} URLs générées")
        print(f"  🔍 Validation des URLs (cela peut prendre du temps)...")
        
        # Valider par batches pour ne pas surcharger
        batch_size = 100
        all_valid = []
        
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i+batch_size]
            print(f"    Validation batch {i//batch_size + 1}/{(len(urls)-1)//batch_size + 1} ({len(batch)} URLs)...")
            valid = await cls.validate_shops_batch(batch, max_concurrent=20)
            all_valid.extend(valid)
            print(f"    ✅ {len(valid)} boutiques valides trouvées dans ce batch")
            await asyncio.sleep(1)  # Pause entre les batches
        
        return all_valid


Génère des URLs basées sur des noms communs et les teste
"""
import asyncio
from typing import List, Set
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


class ShopURLGenerator:
    """Génère et teste des URLs de boutiques possibles"""
    
    # Noms de boutiques communs pour produits digitaux
    SHOP_NAMES = [
        # Produits digitaux
        'digital', 'digitalstore', 'digitalhub', 'digitalshop', 'digitalmarket',
        'ebook', 'ebookstore', 'ebookshop', 'ebookhub', 'ebookmarket',
        'template', 'templatestore', 'templateshop', 'templatehub', 'templatemarket',
        'formation', 'formationstore', 'formationshop', 'formationhub',
        'cours', 'coursstore', 'coursshop', 'courshub',
        'logiciel', 'logicielstore', 'logicielshop', 'logicielhub',
        'plugin', 'pluginstore', 'pluginshop', 'pluginhub',
        'theme', 'themestore', 'themeshop', 'themehub',
        'software', 'softwarestore', 'softwareshop', 'softwarehub',
        'app', 'appstore', 'appshop', 'apphub',
        'guide', 'guidestore', 'guideshop', 'guidehub',
        'tutoriel', 'tutorielstore', 'tutorielshop',
        'coaching', 'coachingstore', 'coachingshop',
        'consultation', 'consultationstore', 'consultationshop',
        'graphisme', 'graphismestore', 'graphismeshop',
        'design', 'designstore', 'designshop', 'designhub',
        'marketing', 'marketingstore', 'marketingshop',
        'affiliation', 'affiliationstore', 'affiliationshop',
        'dropshipping', 'dropshippingstore', 'dropshippingshop',
        # Mots africains
        'afrique', 'africastore', 'africashop', 'africahub',
        'cameroun', 'camerounstore', 'camerounshop',
        'senegal', 'senegalstore', 'senegalshop',
        'cotedivoire', 'cotedivoirestore', 'cotedivoireshop',
        'mali', 'malistore', 'malishop',
        'benin', 'beninstore', 'beninshop',
        'togo', 'togostore', 'togoshop',
        # Combinaisons
        'digitalafrique', 'ebookafrique', 'formationafrique',
        'digitalcameroun', 'ebooksenegal', 'formationmali',
        'africadigital', 'africaebook', 'africaformation',
        # Noms génériques
        'store', 'shop', 'hub', 'market', 'boutique', 'magasin',
        'digitalstore', 'digitalshop', 'digitalhub',
        'online', 'online-store', 'online-shop',
        'web', 'webstore', 'webshop',
        'pro', 'prostore', 'proshop',
        'premium', 'premiumstore', 'premiumshop',
        'expert', 'expertstore', 'expertshop',
        'master', 'masterstore', 'mastershop',
        'elite', 'elitestore', 'eliteshop',
        # Noms courts
        'dig', 'digi', 'ebk', 'tmp', 'frm', 'log', 'plg', 'thm',
        'afr', 'cmr', 'sng', 'ml', 'bn', 'tg',
    ]
    
    # Suffixes communs
    SUFFIXES = [
        '', 'store', 'shop', 'hub', 'market', 'boutique', 'magasin',
        'online', 'digital', 'pro', 'premium', 'expert', 'master', 'elite',
        'afrique', 'africa', 'west', 'central', 'north',
    ]
    
    @classmethod
    def generate_chariow_urls(cls, limit: int = 500) -> List[str]:
        """Génère des URLs Chariow possibles"""
        urls = set()
        
        # Combinaisons de noms + suffixes
        for name in cls.SHOP_NAMES:
            if len(urls) >= limit:
                break
            
            # Nom seul
            urls.add(f"https://{name}.mychariow.shop/fr")
            
            # Nom + suffixe
            for suffix in cls.SUFFIXES[:10]:  # Limiter les suffixes
                if len(urls) >= limit:
                    break
                if suffix:
                    combined = f"{name}{suffix}"
                    urls.add(f"https://{combined}.mychariow.shop/fr")
        
        # Ajouter des variations avec tirets
        base_urls = list(urls)
        for url in base_urls[:limit//2]:
            if len(urls) >= limit:
                break
            # Remplacer certains caractères par des tirets
            url_with_dash = url.replace('store', '-store').replace('shop', '-shop')
            if url_with_dash != url:
                urls.add(url_with_dash)
        
        return sorted(list(urls))[:limit]
    
    @classmethod
    def generate_maketou_urls(cls, limit: int = 500) -> List[str]:
        """Génère des URLs Maketou possibles"""
        urls = set()
        
        # Combinaisons de noms + suffixes
        for name in cls.SHOP_NAMES:
            if len(urls) >= limit:
                break
            
            # Nom seul
            urls.add(f"https://{name}.mymaketou.store/fr")
            
            # Nom + suffixe
            for suffix in cls.SUFFIXES[:10]:  # Limiter les suffixes
                if len(urls) >= limit:
                    break
                if suffix:
                    combined = f"{name}{suffix}"
                    urls.add(f"https://{combined}.mymaketou.store/fr")
        
        # Ajouter des variations avec tirets
        base_urls = list(urls)
        for url in base_urls[:limit//2]:
            if len(urls) >= limit:
                break
            # Remplacer certains caractères par des tirets
            url_with_dash = url.replace('store', '-store').replace('shop', '-shop')
            if url_with_dash != url:
                urls.add(url_with_dash)
        
        return sorted(list(urls))[:limit]
    
    @classmethod
    async def validate_shops_batch(cls, urls: List[str], max_concurrent: int = 20) -> List[str]:
        """
        Valide un batch d'URLs en parallèle
        Retourne uniquement les URLs qui existent (status 200)
        """
        valid_shops = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def validate_one(url: str) -> str | None:
            async with semaphore:
                try:
                    # Utiliser urllib de manière asynchrone
                    def check_url():
                        try:
                            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urlopen(req, timeout=5) as response:
                                if response.getcode() == 200:
                                    content = response.read().decode('utf-8', errors='ignore')
                                    # Vérifier des indicateurs de boutique
                                    if any(indicator in content.lower() for indicator in ['product', 'produit', 'shop', 'boutique', 'store', 'acheter', 'buy', 'prix', 'price']):
                                        return url
                        except (URLError, HTTPError, Exception):
                            pass
                        return None
                    
                    # Exécuter dans un thread pour ne pas bloquer
                    result = await asyncio.to_thread(check_url)
                    return result
                except Exception:
                    pass
                return None
        
        tasks = [validate_one(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if result and isinstance(result, str):
                valid_shops.append(result)
        
        return valid_shops
    
    @classmethod
    async def discover_shops(cls, marketplace: str, limit: int = 500) -> List[str]:
        """
        Découvre des boutiques en générant des URLs et en les validant
        """
        print(f"  🔧 Génération de {limit} URLs possibles pour {marketplace}...")
        
        if marketplace == 'chariow':
            urls = cls.generate_chariow_urls(limit)
        elif marketplace == 'maketou':
            urls = cls.generate_maketou_urls(limit)
        else:
            return []
        
        print(f"  ✅ {len(urls)} URLs générées")
        print(f"  🔍 Validation des URLs (cela peut prendre du temps)...")
        
        # Valider par batches pour ne pas surcharger
        batch_size = 100
        all_valid = []
        
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i+batch_size]
            print(f"    Validation batch {i//batch_size + 1}/{(len(urls)-1)//batch_size + 1} ({len(batch)} URLs)...")
            valid = await cls.validate_shops_batch(batch, max_concurrent=20)
            all_valid.extend(valid)
            print(f"    ✅ {len(valid)} boutiques valides trouvées dans ce batch")
            await asyncio.sleep(1)  # Pause entre les batches
        
        return all_valid

