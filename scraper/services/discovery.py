"""
Découverte automatique de boutiques sur Chariow et Maketou.
Ajoute des sources multiples : listings, Google dorks, seeds locales.
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import List, Dict
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


SEED_FILE = Path(__file__).resolve().parents[1] / "discovered_shops.txt"


def normalize_shop_url(url: str, marketplace: str) -> str:
    """Ne garder que le domaine racine et filtrer par marketplace ciblée."""
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if marketplace == "chariow" and "mychariow.shop" not in host:
            return ""
        if marketplace == "maketou" and "mymaketou.store" not in host:
            return ""
        return urlunparse((parsed.scheme or "https", host, "", "", "", "")).rstrip("/")
    except Exception:
        return ""


def load_seed_shops(marketplace: str) -> list[str]:
    seeds: list[str] = []
    if not SEED_FILE.exists():
        return seeds
    for line in SEED_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if marketplace == "chariow" and "mychariow.shop" in line:
            clean = normalize_shop_url(line, marketplace)
            if clean:
                seeds.append(clean)
        if marketplace == "maketou" and "mymaketou.store" in line:
            clean = normalize_shop_url(line, marketplace)
            if clean:
                seeds.append(clean)
    return list(dict.fromkeys(seeds))


class MarketplaceDiscovery:
    """Découvre automatiquement de nouvelles boutiques sur les marketplaces."""

    def __init__(self):
        # URLs pour découvrir des boutiques sur les marketplaces principales
        self.chariow_listing_urls = [
            "https://chariow.com/shops",
            "https://chariow.com/vendors",
            "https://chariow.com/stores",
            "https://chariow.com/categories",
            "https://chariow.com/collections",
            # Recherches spécifiques produits digitaux
            "https://chariow.com/search?q=digital",
            "https://chariow.com/search?q=ebook",
            "https://chariow.com/search?q=template",
            "https://chariow.com/search?q=formation",
            "https://chariow.com/search?q=cours",
            "https://chariow.com/search?q=logiciel",
            "https://chariow.com/search?q=application",
            "https://chariow.com/search?q=plugin",
            "https://chariow.com/search?q=theme",
        ]
        self.maketou_listing_urls = [
            "https://maketou.com/stores",
            "https://maketou.com/shops",
            "https://maketou.com/collections",
            # Recherches spécifiques produits digitaux
            "https://maketou.com/search?q=digital",
            "https://maketou.com/search?q=ebook",
            "https://maketou.com/search?q=template",
            "https://maketou.com/search?q=formation",
            "https://maketou.com/search?q=cours",
            "https://maketou.com/search?q=logiciel",
            "https://maketou.com/search?q=application",
            "https://maketou.com/search?q=plugin",
            "https://maketou.com/search?q=theme",
        ]
        # Requêtes Google optimisées pour produits digitaux
        self.google_queries = {
            "chariow": [
                # Recherche générale de boutiques
                "https://www.google.com/search?q=site:mychariow.shop",
                # Produits digitaux spécifiques
                "https://www.google.com/search?q=site:mychariow.shop+produit+digital",
                "https://www.google.com/search?q=site:mychariow.shop+ebook",
                "https://www.google.com/search?q=site:mychariow.shop+template",
                "https://www.google.com/search?q=site:mychariow.shop+formation",
                "https://www.google.com/search?q=site:mychariow.shop+cours+en+ligne",
                "https://www.google.com/search?q=site:mychariow.shop+logiciel",
                "https://www.google.com/search?q=site:mychariow.shop+application",
                "https://www.google.com/search?q=site:mychariow.shop+plugin",
                "https://www.google.com/search?q=site:mychariow.shop+theme",
                "https://www.google.com/search?q=site:mychariow.shop+affiliation",
                "https://www.google.com/search?q=site:mychariow.shop+dropshipping+digital",
            ],
            "maketou": [
                # Recherche générale de boutiques
                "https://www.google.com/search?q=site:mymaketou.store",
                # Produits digitaux spécifiques
                "https://www.google.com/search?q=site:mymaketou.store+produit+digital",
                "https://www.google.com/search?q=site:mymaketou.store+ebook",
                "https://www.google.com/search?q=site:mymaketou.store+template",
                "https://www.google.com/search?q=site:mymaketou.store+formation",
                "https://www.google.com/search?q=site:mymaketou.store+cours+en+ligne",
                "https://www.google.com/search?q=site:mymaketou.store+logiciel",
                "https://www.google.com/search?q=site:mymaketou.store+application",
                "https://www.google.com/search?q=site:mymaketou.store+plugin",
                "https://www.google.com/search?q=site:mymaketou.store+theme",
                "https://www.google.com/search?q=site:mymaketou.store+affiliation",
                "https://www.google.com/search?q=site:mymaketou.store+dropshipping+digital",
            ],
        }

    async def _discover_from_urls(self, urls: list[str], marketplace: str) -> list[str]:
        found: list[str] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                for listing_url in urls:
                    try:
                        await page.goto(listing_url, wait_until="networkidle", timeout=30000)
                        await page.wait_for_timeout(1500)
                        content = await page.content()
                        try:
                            soup = BeautifulSoup(content, "lxml")
                        except Exception:
                            soup = BeautifulSoup(content, "html.parser")
                        links = soup.find_all("a", href=True)
                        for link in links:
                            href = link.get("href", "")
                            if not href:
                                continue
                            if not href.startswith("http"):
                                href = urljoin(listing_url, href)
                            clean = normalize_shop_url(href, marketplace)
                            if clean and clean not in found:
                                found.append(clean)
                        # Scroll léger pour charger plus de liens
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(1000)
                    except Exception as e:
                        print(f"[discovery] erreur {listing_url}: {e}")
                        continue
            finally:
                await browser.close()
        return found

    async def _discover_from_google(self, marketplace: str) -> list[str]:
        queries = self.google_queries.get(marketplace, [])
        found: list[str] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                for q in queries:
                    try:
                        await page.goto(q, wait_until="networkidle", timeout=25000)
                        await page.wait_for_timeout(1200)
                        content = await page.content()
                        soup = BeautifulSoup(content, "html.parser")
                        links = soup.find_all("a", href=True)
                        for link in links:
                            href = link.get("href", "")
                            if not href:
                                continue
                            # Google redirections
                            if href.startswith("/url?q="):
                                href = href.split("/url?q=")[-1].split("&")[0]
                            if not href.startswith("http"):
                                continue
                            clean = normalize_shop_url(href, marketplace)
                            if clean and clean not in found:
                                found.append(clean)
                    except Exception as e:
                        print(f"[discovery] google erreur {q}: {e}")
                        continue
            finally:
                await browser.close()
        return found

    async def discover_chariow_shops(self) -> List[str]:
        """Découvre toutes les boutiques Chariow disponibles"""
        print("🔍 Découverte des boutiques Chariow...")
        seeds = load_seed_shops("chariow")
        print(f"  📌 {len(seeds)} boutiques de départ (seeds)")
        
        listings = await self._discover_from_urls(self.chariow_listing_urls, "chariow")
        print(f"  📋 {len(listings)} boutiques depuis les listings")
        
        google = await self._discover_from_google("chariow")
        print(f"  🌐 {len(google)} boutiques depuis Google")
        
        merged = list(dict.fromkeys(seeds + listings + google))
        print(f"  ✅ Total: {len(merged)} boutiques uniques découvertes")
        
        # Explorer les boutiques découvertes pour en trouver d'autres
        if merged:
            print("  🔄 Exploration en profondeur des boutiques découvertes...")
            additional = await self._discover_from_known_shops("chariow", merged[:50])  # Explorer les 50 premières
            merged.extend(additional)
            merged = list(dict.fromkeys(merged))
            print(f"  ✅ Après exploration: {len(merged)} boutiques totales")
        
        # Normaliser les URLs (ajouter /fr si nécessaire)
        normalized = []
        for shop_url in merged:
            if isinstance(shop_url, dict):
                shop_url = shop_url.get("shop_url", "")
            if shop_url and not shop_url.endswith('/fr'):
                shop_url = shop_url.rstrip('/') + '/fr'
            if shop_url:
                normalized.append(shop_url)
        
        return normalized

    async def discover_maketou_shops(self) -> List[str]:
        """Découvre toutes les boutiques Maketou disponibles"""
        print("🔍 Découverte des boutiques Maketou...")
        seeds = load_seed_shops("maketou")
        print(f"  📌 {len(seeds)} boutiques de départ (seeds)")
        
        listings = await self._discover_from_urls(self.maketou_listing_urls, "maketou")
        print(f"  📋 {len(listings)} boutiques depuis les listings")
        
        google = await self._discover_from_google("maketou")
        print(f"  🌐 {len(google)} boutiques depuis Google")
        
        merged = list(dict.fromkeys(seeds + listings + google))
        print(f"  ✅ Total: {len(merged)} boutiques uniques découvertes")
        
        # Explorer les boutiques découvertes pour en trouver d'autres
        if merged:
            print("  🔄 Exploration en profondeur des boutiques découvertes...")
            additional = await self._discover_from_known_shops("maketou", merged[:50])  # Explorer les 50 premières
            merged.extend(additional)
            merged = list(dict.fromkeys(merged))
            print(f"  ✅ Après exploration: {len(merged)} boutiques totales")
        
        # Normaliser les URLs (ajouter /fr si nécessaire)
        normalized = []
        for shop_url in merged:
            if isinstance(shop_url, dict):
                shop_url = shop_url.get("shop_url", "")
            if shop_url and not shop_url.endswith('/fr'):
                shop_url = shop_url.rstrip('/') + '/fr'
            if shop_url:
                normalized.append(shop_url)
        
        return normalized

    async def _discover_from_known_shops(self, marketplace: str, shop_urls: List[str]) -> List[str]:
        """Explore les liens depuis des boutiques connues pour découvrir d'autres boutiques"""
        found: list[str] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                for shop_url in shop_urls[:20]:  # Limiter à 20 pour ne pas être trop long
                    try:
                        await page.goto(shop_url, wait_until="networkidle", timeout=30000)
                        await page.wait_for_timeout(2000)
                        
                        # Scroll pour charger le contenu
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(1500)
                        
                        content = await page.content()
                        try:
                            soup = BeautifulSoup(content, "lxml")
                        except Exception:
                            soup = BeautifulSoup(content, "html.parser")
                        
                        links = soup.find_all("a", href=True)
                        for link in links:
                            href = link.get("href", "")
                            if not href:
                                continue
                            if not href.startswith("http"):
                                href = urljoin(shop_url, href)
                            clean = normalize_shop_url(href, marketplace)
                            if clean and clean not in found and clean != shop_url:
                                found.append(clean)
                    except Exception as e:
                        continue
            finally:
                await browser.close()
        return found

    async def _discover_from_known_shops(self, marketplace: str, shop_urls: List[str]) -> List[str]:
        """Explore les liens depuis des boutiques connues pour découvrir d'autres boutiques"""
        found: list[str] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                for shop_url in shop_urls[:20]:  # Limiter à 20 pour ne pas être trop long
                    try:
                        await page.goto(shop_url, wait_until="networkidle", timeout=30000)
                        await page.wait_for_timeout(2000)
                        
                        # Scroll pour charger le contenu
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(1500)
                        
                        content = await page.content()
                        try:
                            soup = BeautifulSoup(content, "lxml")
                        except Exception:
                            soup = BeautifulSoup(content, "html.parser")
                        
                        links = soup.find_all("a", href=True)
                        for link in links:
                            href = link.get("href", "")
                            if not href:
                                continue
                            if not href.startswith("http"):
                                href = urljoin(shop_url, href)
                            clean = normalize_shop_url(href, marketplace)
                            if clean and clean not in found and clean != shop_url:
                                found.append(clean)
                    except Exception as e:
                        continue
            finally:
                await browser.close()
        return found

    async def discover_all_shops(self) -> Dict[str, List[str]]:
        chariow_shops = await self.discover_chariow_shops()
        maketou_shops = await self.discover_maketou_shops()
        return {"chariow": chariow_shops, "maketou": maketou_shops}

Ajoute des sources multiples : listings, Google dorks, seeds locales.
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import List, Dict
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


SEED_FILE = Path(__file__).resolve().parents[1] / "discovered_shops.txt"


def normalize_shop_url(url: str, marketplace: str) -> str:
    """Ne garder que le domaine racine et filtrer par marketplace ciblée."""
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if marketplace == "chariow" and "mychariow.shop" not in host:
            return ""
        if marketplace == "maketou" and "mymaketou.store" not in host:
            return ""
        return urlunparse((parsed.scheme or "https", host, "", "", "", "")).rstrip("/")
    except Exception:
        return ""


def load_seed_shops(marketplace: str) -> list[str]:
    seeds: list[str] = []
    if not SEED_FILE.exists():
        return seeds
    for line in SEED_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if marketplace == "chariow" and "mychariow.shop" in line:
            clean = normalize_shop_url(line, marketplace)
            if clean:
                seeds.append(clean)
        if marketplace == "maketou" and "mymaketou.store" in line:
            clean = normalize_shop_url(line, marketplace)
            if clean:
                seeds.append(clean)
    return list(dict.fromkeys(seeds))


class MarketplaceDiscovery:
    """Découvre automatiquement de nouvelles boutiques sur les marketplaces."""

    def __init__(self):
        # URLs pour découvrir des boutiques sur les marketplaces principales
        self.chariow_listing_urls = [
            "https://chariow.com/shops",
            "https://chariow.com/vendors",
            "https://chariow.com/stores",
            "https://chariow.com/categories",
            "https://chariow.com/collections",
            # Recherches spécifiques produits digitaux
            "https://chariow.com/search?q=digital",
            "https://chariow.com/search?q=ebook",
            "https://chariow.com/search?q=template",
            "https://chariow.com/search?q=formation",
            "https://chariow.com/search?q=cours",
            "https://chariow.com/search?q=logiciel",
            "https://chariow.com/search?q=application",
            "https://chariow.com/search?q=plugin",
            "https://chariow.com/search?q=theme",
        ]
        self.maketou_listing_urls = [
            "https://maketou.com/stores",
            "https://maketou.com/shops",
            "https://maketou.com/collections",
            # Recherches spécifiques produits digitaux
            "https://maketou.com/search?q=digital",
            "https://maketou.com/search?q=ebook",
            "https://maketou.com/search?q=template",
            "https://maketou.com/search?q=formation",
            "https://maketou.com/search?q=cours",
            "https://maketou.com/search?q=logiciel",
            "https://maketou.com/search?q=application",
            "https://maketou.com/search?q=plugin",
            "https://maketou.com/search?q=theme",
        ]
        # Requêtes Google optimisées pour produits digitaux
        self.google_queries = {
            "chariow": [
                # Recherche générale de boutiques
                "https://www.google.com/search?q=site:mychariow.shop",
                # Produits digitaux spécifiques
                "https://www.google.com/search?q=site:mychariow.shop+produit+digital",
                "https://www.google.com/search?q=site:mychariow.shop+ebook",
                "https://www.google.com/search?q=site:mychariow.shop+template",
                "https://www.google.com/search?q=site:mychariow.shop+formation",
                "https://www.google.com/search?q=site:mychariow.shop+cours+en+ligne",
                "https://www.google.com/search?q=site:mychariow.shop+logiciel",
                "https://www.google.com/search?q=site:mychariow.shop+application",
                "https://www.google.com/search?q=site:mychariow.shop+plugin",
                "https://www.google.com/search?q=site:mychariow.shop+theme",
                "https://www.google.com/search?q=site:mychariow.shop+affiliation",
                "https://www.google.com/search?q=site:mychariow.shop+dropshipping+digital",
            ],
            "maketou": [
                # Recherche générale de boutiques
                "https://www.google.com/search?q=site:mymaketou.store",
                # Produits digitaux spécifiques
                "https://www.google.com/search?q=site:mymaketou.store+produit+digital",
                "https://www.google.com/search?q=site:mymaketou.store+ebook",
                "https://www.google.com/search?q=site:mymaketou.store+template",
                "https://www.google.com/search?q=site:mymaketou.store+formation",
                "https://www.google.com/search?q=site:mymaketou.store+cours+en+ligne",
                "https://www.google.com/search?q=site:mymaketou.store+logiciel",
                "https://www.google.com/search?q=site:mymaketou.store+application",
                "https://www.google.com/search?q=site:mymaketou.store+plugin",
                "https://www.google.com/search?q=site:mymaketou.store+theme",
                "https://www.google.com/search?q=site:mymaketou.store+affiliation",
                "https://www.google.com/search?q=site:mymaketou.store+dropshipping+digital",
            ],
        }

    async def _discover_from_urls(self, urls: list[str], marketplace: str) -> list[str]:
        found: list[str] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                for listing_url in urls:
                    try:
                        await page.goto(listing_url, wait_until="networkidle", timeout=30000)
                        await page.wait_for_timeout(1500)
                        content = await page.content()
                        try:
                            soup = BeautifulSoup(content, "lxml")
                        except Exception:
                            soup = BeautifulSoup(content, "html.parser")
                        links = soup.find_all("a", href=True)
                        for link in links:
                            href = link.get("href", "")
                            if not href:
                                continue
                            if not href.startswith("http"):
                                href = urljoin(listing_url, href)
                            clean = normalize_shop_url(href, marketplace)
                            if clean and clean not in found:
                                found.append(clean)
                        # Scroll léger pour charger plus de liens
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(1000)
                    except Exception as e:
                        print(f"[discovery] erreur {listing_url}: {e}")
                        continue
            finally:
                await browser.close()
        return found

    async def _discover_from_google(self, marketplace: str) -> list[str]:
        queries = self.google_queries.get(marketplace, [])
        found: list[str] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                for q in queries:
                    try:
                        await page.goto(q, wait_until="networkidle", timeout=25000)
                        await page.wait_for_timeout(1200)
                        content = await page.content()
                        soup = BeautifulSoup(content, "html.parser")
                        links = soup.find_all("a", href=True)
                        for link in links:
                            href = link.get("href", "")
                            if not href:
                                continue
                            # Google redirections
                            if href.startswith("/url?q="):
                                href = href.split("/url?q=")[-1].split("&")[0]
                            if not href.startswith("http"):
                                continue
                            clean = normalize_shop_url(href, marketplace)
                            if clean and clean not in found:
                                found.append(clean)
                    except Exception as e:
                        print(f"[discovery] google erreur {q}: {e}")
                        continue
            finally:
                await browser.close()
        return found

    async def discover_chariow_shops(self) -> List[str]:
        """Découvre toutes les boutiques Chariow disponibles"""
        print("🔍 Découverte des boutiques Chariow...")
        seeds = load_seed_shops("chariow")
        print(f"  📌 {len(seeds)} boutiques de départ (seeds)")
        
        listings = await self._discover_from_urls(self.chariow_listing_urls, "chariow")
        print(f"  📋 {len(listings)} boutiques depuis les listings")
        
        google = await self._discover_from_google("chariow")
        print(f"  🌐 {len(google)} boutiques depuis Google")
        
        merged = list(dict.fromkeys(seeds + listings + google))
        print(f"  ✅ Total: {len(merged)} boutiques uniques découvertes")
        
        # Explorer les boutiques découvertes pour en trouver d'autres
        if merged:
            print("  🔄 Exploration en profondeur des boutiques découvertes...")
            additional = await self._discover_from_known_shops("chariow", merged[:50])  # Explorer les 50 premières
            merged.extend(additional)
            merged = list(dict.fromkeys(merged))
            print(f"  ✅ Après exploration: {len(merged)} boutiques totales")
        
        # Normaliser les URLs (ajouter /fr si nécessaire)
        normalized = []
        for shop_url in merged:
            if isinstance(shop_url, dict):
                shop_url = shop_url.get("shop_url", "")
            if shop_url and not shop_url.endswith('/fr'):
                shop_url = shop_url.rstrip('/') + '/fr'
            if shop_url:
                normalized.append(shop_url)
        
        return normalized

    async def discover_maketou_shops(self) -> List[str]:
        """Découvre toutes les boutiques Maketou disponibles"""
        print("🔍 Découverte des boutiques Maketou...")
        seeds = load_seed_shops("maketou")
        print(f"  📌 {len(seeds)} boutiques de départ (seeds)")
        
        listings = await self._discover_from_urls(self.maketou_listing_urls, "maketou")
        print(f"  📋 {len(listings)} boutiques depuis les listings")
        
        google = await self._discover_from_google("maketou")
        print(f"  🌐 {len(google)} boutiques depuis Google")
        
        merged = list(dict.fromkeys(seeds + listings + google))
        print(f"  ✅ Total: {len(merged)} boutiques uniques découvertes")
        
        # Explorer les boutiques découvertes pour en trouver d'autres
        if merged:
            print("  🔄 Exploration en profondeur des boutiques découvertes...")
            additional = await self._discover_from_known_shops("maketou", merged[:50])  # Explorer les 50 premières
            merged.extend(additional)
            merged = list(dict.fromkeys(merged))
            print(f"  ✅ Après exploration: {len(merged)} boutiques totales")
        
        # Normaliser les URLs (ajouter /fr si nécessaire)
        normalized = []
        for shop_url in merged:
            if isinstance(shop_url, dict):
                shop_url = shop_url.get("shop_url", "")
            if shop_url and not shop_url.endswith('/fr'):
                shop_url = shop_url.rstrip('/') + '/fr'
            if shop_url:
                normalized.append(shop_url)
        
        return normalized

    async def _discover_from_known_shops(self, marketplace: str, shop_urls: List[str]) -> List[str]:
        """Explore les liens depuis des boutiques connues pour découvrir d'autres boutiques"""
        found: list[str] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                for shop_url in shop_urls[:20]:  # Limiter à 20 pour ne pas être trop long
                    try:
                        await page.goto(shop_url, wait_until="networkidle", timeout=30000)
                        await page.wait_for_timeout(2000)
                        
                        # Scroll pour charger le contenu
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(1500)
                        
                        content = await page.content()
                        try:
                            soup = BeautifulSoup(content, "lxml")
                        except Exception:
                            soup = BeautifulSoup(content, "html.parser")
                        
                        links = soup.find_all("a", href=True)
                        for link in links:
                            href = link.get("href", "")
                            if not href:
                                continue
                            if not href.startswith("http"):
                                href = urljoin(shop_url, href)
                            clean = normalize_shop_url(href, marketplace)
                            if clean and clean not in found and clean != shop_url:
                                found.append(clean)
                    except Exception as e:
                        continue
            finally:
                await browser.close()
        return found

    async def _discover_from_known_shops(self, marketplace: str, shop_urls: List[str]) -> List[str]:
        """Explore les liens depuis des boutiques connues pour découvrir d'autres boutiques"""
        found: list[str] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                for shop_url in shop_urls[:20]:  # Limiter à 20 pour ne pas être trop long
                    try:
                        await page.goto(shop_url, wait_until="networkidle", timeout=30000)
                        await page.wait_for_timeout(2000)
                        
                        # Scroll pour charger le contenu
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(1500)
                        
                        content = await page.content()
                        try:
                            soup = BeautifulSoup(content, "lxml")
                        except Exception:
                            soup = BeautifulSoup(content, "html.parser")
                        
                        links = soup.find_all("a", href=True)
                        for link in links:
                            href = link.get("href", "")
                            if not href:
                                continue
                            if not href.startswith("http"):
                                href = urljoin(shop_url, href)
                            clean = normalize_shop_url(href, marketplace)
                            if clean and clean not in found and clean != shop_url:
                                found.append(clean)
                    except Exception as e:
                        continue
            finally:
                await browser.close()
        return found

    async def discover_all_shops(self) -> Dict[str, List[str]]:
        chariow_shops = await self.discover_chariow_shops()
        maketou_shops = await self.discover_maketou_shops()
        return {"chariow": chariow_shops, "maketou": maketou_shops}
