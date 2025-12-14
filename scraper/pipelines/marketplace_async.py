"""
Pipeline de scraping async Chariow/Maketou avec Playwright + scoring + snapshots.
Objectif : remplir ProductGlobal/ShopGlobal et stocker des snapshots journaliers.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

from scraper.core.browser import BrowserPool
from scraper.core.normalize import clean_text, normalize_price
from scraper.core.signals import compute_product_signals, compute_shop_signals
from scraper.core.scoring import evaluate_winner
from scraper.storage.repository import (
    SessionLocal,
    ensure_snapshot_tables,
    upsert_product,
    upsert_shop,
    insert_product_snapshot,
    insert_shop_snapshot,
)
from scraper.services.discovery import MarketplaceDiscovery
from scraper.services.chariow import ChariowScraper
from scraper.services.maketou import MaketouScraper


def _extract_products(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """Extraction générique des produits sur une page boutique."""
    selectors = [
        'div[class*="product"]',
        'article[class*="product"]',
        'div[class*="item"]',
        'div[class*="card"]',
        'li.product',
        '.product-card',
        '.product-item',
        '[data-product]',
        'a[href*="/product"]',
        'a[href*="/p/"]',
    ]
    products_found = []
    for selector in selectors:
        products_found = soup.select(selector)
        if products_found:
            break

    results = []
    for elem in products_found[:120]:
        name_elem = elem.find(["h2", "h3"])
        if not name_elem:
            link = elem.find("a")
            name_elem = link
        name = clean_text(name_elem.get_text()) if name_elem else None

        link_elem = elem.find("a", href=True) or elem
        href = link_elem.get("href", "")
        if href:
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = urljoin(base_url, href)
            elif not href.startswith("http"):
                href = urljoin(base_url, href)
        image = None
        img = elem.find("img")
        if img:
            src = (
                img.get("src")
                or img.get("data-src")
                or img.get("data-lazy-src")
                or img.get("data-original")
                or img.get("data-image")
                or (img.get("srcset", "").split(",")[0].strip() if img.get("srcset") else None)
            )
            if src:
                if " " in src:
                    src = src.split(" ")[0]
                if src.startswith("//"):
                    image = "https:" + src
                elif src.startswith("/"):
                    image = urljoin(base_url, src)
                elif not src.startswith("http"):
                    image = urljoin(base_url, src)
                else:
                    image = src

        # Prix : matcher tous les nombres possibles
        price_text = elem.get_text(" ")
        for sub in elem.find_all(["span", "div", "p"], class_=re.compile(r"price|amount|cost", re.I)):
            price_text += " " + sub.get_text(" ")
        price = normalize_price(price_text)

        if name and href and image:
            results.append(
                {
                    "name": name,
                    "product_url": href,
                    "cover_image_url": image,
                    "price": price,
                    "description": None,
                    "number_of_reviews": None,
                    "ranking_position": None,
                    "category": None,
                    "tags": [],
                }
            )
    return results


async def scrape_shop(pool: BrowserPool, shop_url: str, marketplace: str) -> dict:
    """Scrape une boutique : shop info + produits."""
    # Utiliser les scrapers spécialisés existants (plus robustes)
    if marketplace == "chariow":
        scraper = ChariowScraper()
    else:
        scraper = MaketouScraper()

    data = await scraper.scrape_async(shop_url)
    if not data or not data.get("products"):
        # fallback générique si le scraper spécialisé n'a rien retourné
        page = await pool.new_page()
        await page.goto(shop_url, wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(1500)
        content = await page.content()
        try:
            soup = BeautifulSoup(content, "lxml")
        except Exception:
            soup = BeautifulSoup(content, "html.parser")

        title = soup.find("title")
        h1 = soup.find("h1")
        shop_name = clean_text(h1.get_text()) if h1 else None
        if not shop_name and title:
            shop_name = clean_text(title.get_text().split("-")[0])
        if not shop_name:
            shop_name = shop_url.split("//")[-1].split("/")[0]

        products = _extract_products(soup, shop_url)
        shop_data = {
            "name": shop_name,
            "url": shop_url.rstrip("/"),
            "marketplace": marketplace,
            "products": products,
            "product_count": len(products),
            "estimated_sales": None,
            "estimated_revenue": None,
            "growth_rate": 0,
            "strengths": [],
            "weaknesses": [],
        }
    else:
        shop_data = {
            "shop_name": data.get("name") or data.get("shop_name") or shop_url,
            "shop_url": data.get("url") or shop_url,
            "marketplace": marketplace,
            "products": data.get("products", []),
            "products_count": data.get("product_count") or len(data.get("products", [])),
            "total_reviews": sum([p.get("number_of_reviews") or 0 for p in data.get("products", [])]),
        }

    # Normalisation minimale
    for p in shop_data["products"]:
        if "product_url" not in p and p.get("url"):
            p["product_url"] = p["url"]
        if "cover_image_url" not in p and p.get("image"):
            p["cover_image_url"] = p["image"]
        p["marketplace"] = marketplace

    return shop_data


async def scrape_marketplace(marketplace: str):
    """Scrape complet d'une marketplace avec découverte + scoring + snapshots."""
    ensure_snapshot_tables()
    discovery = MarketplaceDiscovery()
    # Seeds connus en fallback
    seeds_chariow = []  # Boutiques à découvrir automatiquement
    seeds_maketou = ["https://numerik.mymaketou.store/"]
    if marketplace == "chariow":
        shops = await discovery.discover_chariow_shops()
        if not shops:
            shops = seeds_chariow
    elif marketplace == "maketou":
        shops = await discovery.discover_maketou_shops()
        if not shops:
            shops = seeds_maketou
    else:
        raise ValueError("Marketplace inconnue")

    async with BrowserPool(headless=True) as pool:
        with SessionLocal() as session:
            total_products = 0
            for idx, shop_url in enumerate(shops, 1):
                print(f"[{marketplace}] Boutique {idx}/{len(shops)}: {shop_url}")
                try:
                    shop_data = await scrape_shop(pool, shop_url, marketplace)
                except Exception as e:
                    print(f"  ❌ échec boutique {shop_url}: {e}")
                    continue
                if not shop_data.get("products"):
                    print("  ⚠️ aucun produit détecté")
                    continue

                # Signaux shop
                shop_signals = compute_shop_signals(shop_data, previous=None)
                shop_data.update(shop_signals)
                shop = upsert_shop(session, shop_data)
                insert_shop_snapshot(session, {**shop_data, **shop_signals})

                for p in shop_data["products"]:
                    sig = compute_product_signals(p, previous=None)
                    score, is_win, reasons = evaluate_winner(sig)
                    p.update(sig)
                    p["winner_score"] = score
                    p["winner"] = is_win
                    p["winner_reason"] = reasons
                    # Estimations simples
                    p["sales_est_min"] = 15
                    p["sales_est_max"] = 40
                    if p.get("price"):
                        p["revenue_est_min"] = p["price"] * p["sales_est_min"] * 0.6
                        p["revenue_est_max"] = p["price"] * p["sales_est_max"]
                    p["marketplace"] = marketplace
                    product = upsert_product(session, p, shop.shop_name)
                    insert_product_snapshot(session, p)
                    total_products += 1

                session.commit()
                print(f"  ✅ {len(shop_data['products'])} produits enregistrés")

            print(f"\n✅ Fin {marketplace}: {total_products} produits enregistrés.")


async def main():
    await asyncio.gather(
        scrape_marketplace("chariow"),
        scrape_marketplace("maketou"),
    )


if __name__ == "__main__":
    asyncio.run(main())


Objectif : remplir ProductGlobal/ShopGlobal et stocker des snapshots journaliers.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

from scraper.core.browser import BrowserPool
from scraper.core.normalize import clean_text, normalize_price
from scraper.core.signals import compute_product_signals, compute_shop_signals
from scraper.core.scoring import evaluate_winner
from scraper.storage.repository import (
    SessionLocal,
    ensure_snapshot_tables,
    upsert_product,
    upsert_shop,
    insert_product_snapshot,
    insert_shop_snapshot,
)
from scraper.services.discovery import MarketplaceDiscovery
from scraper.services.chariow import ChariowScraper
from scraper.services.maketou import MaketouScraper


def _extract_products(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """Extraction générique des produits sur une page boutique."""
    selectors = [
        'div[class*="product"]',
        'article[class*="product"]',
        'div[class*="item"]',
        'div[class*="card"]',
        'li.product',
        '.product-card',
        '.product-item',
        '[data-product]',
        'a[href*="/product"]',
        'a[href*="/p/"]',
    ]
    products_found = []
    for selector in selectors:
        products_found = soup.select(selector)
        if products_found:
            break

    results = []
    for elem in products_found[:120]:
        name_elem = elem.find(["h2", "h3"])
        if not name_elem:
            link = elem.find("a")
            name_elem = link
        name = clean_text(name_elem.get_text()) if name_elem else None

        link_elem = elem.find("a", href=True) or elem
        href = link_elem.get("href", "")
        if href:
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = urljoin(base_url, href)
            elif not href.startswith("http"):
                href = urljoin(base_url, href)
        image = None
        img = elem.find("img")
        if img:
            src = (
                img.get("src")
                or img.get("data-src")
                or img.get("data-lazy-src")
                or img.get("data-original")
                or img.get("data-image")
                or (img.get("srcset", "").split(",")[0].strip() if img.get("srcset") else None)
            )
            if src:
                if " " in src:
                    src = src.split(" ")[0]
                if src.startswith("//"):
                    image = "https:" + src
                elif src.startswith("/"):
                    image = urljoin(base_url, src)
                elif not src.startswith("http"):
                    image = urljoin(base_url, src)
                else:
                    image = src

        # Prix : matcher tous les nombres possibles
        price_text = elem.get_text(" ")
        for sub in elem.find_all(["span", "div", "p"], class_=re.compile(r"price|amount|cost", re.I)):
            price_text += " " + sub.get_text(" ")
        price = normalize_price(price_text)

        if name and href and image:
            results.append(
                {
                    "name": name,
                    "product_url": href,
                    "cover_image_url": image,
                    "price": price,
                    "description": None,
                    "number_of_reviews": None,
                    "ranking_position": None,
                    "category": None,
                    "tags": [],
                }
            )
    return results


async def scrape_shop(pool: BrowserPool, shop_url: str, marketplace: str) -> dict:
    """Scrape une boutique : shop info + produits."""
    # Utiliser les scrapers spécialisés existants (plus robustes)
    if marketplace == "chariow":
        scraper = ChariowScraper()
    else:
        scraper = MaketouScraper()

    data = await scraper.scrape_async(shop_url)
    if not data or not data.get("products"):
        # fallback générique si le scraper spécialisé n'a rien retourné
        page = await pool.new_page()
        await page.goto(shop_url, wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(1500)
        content = await page.content()
        try:
            soup = BeautifulSoup(content, "lxml")
        except Exception:
            soup = BeautifulSoup(content, "html.parser")

        title = soup.find("title")
        h1 = soup.find("h1")
        shop_name = clean_text(h1.get_text()) if h1 else None
        if not shop_name and title:
            shop_name = clean_text(title.get_text().split("-")[0])
        if not shop_name:
            shop_name = shop_url.split("//")[-1].split("/")[0]

        products = _extract_products(soup, shop_url)
        shop_data = {
            "name": shop_name,
            "url": shop_url.rstrip("/"),
            "marketplace": marketplace,
            "products": products,
            "product_count": len(products),
            "estimated_sales": None,
            "estimated_revenue": None,
            "growth_rate": 0,
            "strengths": [],
            "weaknesses": [],
        }
    else:
        shop_data = {
            "shop_name": data.get("name") or data.get("shop_name") or shop_url,
            "shop_url": data.get("url") or shop_url,
            "marketplace": marketplace,
            "products": data.get("products", []),
            "products_count": data.get("product_count") or len(data.get("products", [])),
            "total_reviews": sum([p.get("number_of_reviews") or 0 for p in data.get("products", [])]),
        }

    # Normalisation minimale
    for p in shop_data["products"]:
        if "product_url" not in p and p.get("url"):
            p["product_url"] = p["url"]
        if "cover_image_url" not in p and p.get("image"):
            p["cover_image_url"] = p["image"]
        p["marketplace"] = marketplace

    return shop_data


async def scrape_marketplace(marketplace: str):
    """Scrape complet d'une marketplace avec découverte + scoring + snapshots."""
    ensure_snapshot_tables()
    discovery = MarketplaceDiscovery()
    # Seeds connus en fallback
    seeds_chariow = []  # Boutiques à découvrir automatiquement
    seeds_maketou = ["https://numerik.mymaketou.store/"]
    if marketplace == "chariow":
        shops = await discovery.discover_chariow_shops()
        if not shops:
            shops = seeds_chariow
    elif marketplace == "maketou":
        shops = await discovery.discover_maketou_shops()
        if not shops:
            shops = seeds_maketou
    else:
        raise ValueError("Marketplace inconnue")

    async with BrowserPool(headless=True) as pool:
        with SessionLocal() as session:
            total_products = 0
            for idx, shop_url in enumerate(shops, 1):
                print(f"[{marketplace}] Boutique {idx}/{len(shops)}: {shop_url}")
                try:
                    shop_data = await scrape_shop(pool, shop_url, marketplace)
                except Exception as e:
                    print(f"  ❌ échec boutique {shop_url}: {e}")
                    continue
                if not shop_data.get("products"):
                    print("  ⚠️ aucun produit détecté")
                    continue

                # Signaux shop
                shop_signals = compute_shop_signals(shop_data, previous=None)
                shop_data.update(shop_signals)
                shop = upsert_shop(session, shop_data)
                insert_shop_snapshot(session, {**shop_data, **shop_signals})

                for p in shop_data["products"]:
                    sig = compute_product_signals(p, previous=None)
                    score, is_win, reasons = evaluate_winner(sig)
                    p.update(sig)
                    p["winner_score"] = score
                    p["winner"] = is_win
                    p["winner_reason"] = reasons
                    # Estimations simples
                    p["sales_est_min"] = 15
                    p["sales_est_max"] = 40
                    if p.get("price"):
                        p["revenue_est_min"] = p["price"] * p["sales_est_min"] * 0.6
                        p["revenue_est_max"] = p["price"] * p["sales_est_max"]
                    p["marketplace"] = marketplace
                    product = upsert_product(session, p, shop.shop_name)
                    insert_product_snapshot(session, p)
                    total_products += 1

                session.commit()
                print(f"  ✅ {len(shop_data['products'])} produits enregistrés")

            print(f"\n✅ Fin {marketplace}: {total_products} produits enregistrés.")


async def main():
    await asyncio.gather(
        scrape_marketplace("chariow"),
        scrape_marketplace("maketou"),
    )


if __name__ == "__main__":
    asyncio.run(main())

