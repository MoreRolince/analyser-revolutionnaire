from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, Any
import re

class SystemioScraper:
    def __init__(self):
        self.marketplace = "systemio"
    
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrape une page System.io (boutique ou produit)
        """
        import asyncio
        
        async def _async_scrape():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                try:
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    content = await page.content()
                    
                    soup = BeautifulSoup(content, 'lxml')
                    
                    if self._is_shop_page(soup):
                        return self._scrape_shop(soup, url)
                    else:
                        return self._scrape_product(soup, url)
                        
                finally:
                    await browser.close()
        
        return asyncio.run(_async_scrape())
    
    def _is_shop_page(self, soup: BeautifulSoup) -> bool:
        """Détecte si c'est une page boutique"""
        shop_indicators = [
            soup.find('div', class_=re.compile(r'shop|store|merchant', re.I)),
            soup.find('h1', string=re.compile(r'shop|store|boutique', re.I))
        ]
        return any(shop_indicators)
    
    def _scrape_shop(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Scrape les données d'une boutique System.io"""
        data = {
            "name": "",
            "url": url,
            "marketplace": self.marketplace,
            "estimated_revenue": None,
            "estimated_sales": None,
            "product_count": 0,
            "age": None,
            "growth_rate": None,
            "strengths": [],
            "weaknesses": []
        }
        
        name_elem = soup.find('h1') or soup.find('title')
        if name_elem:
            data["name"] = name_elem.get_text(strip=True)
        
        products = soup.find_all(['div', 'article'], class_=re.compile(r'product|item', re.I))
        data["product_count"] = len(products)
        
        if data["product_count"] > 0:
            data["estimated_sales"] = data["product_count"] * 8
            data["estimated_revenue"] = f"€{data['estimated_sales'] * 30}-{data['estimated_sales'] * 40}/mois"
        
        if data["product_count"] > 30:
            data["strengths"].append("Catalogue très complet")
        if data["product_count"] < 8:
            data["weaknesses"].append("Peu de produits disponibles")
        
        return data
    
    def _scrape_product(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Scrape les données d'un produit System.io"""
        data = {
            "name": "",
            "url": url,
            "marketplace": self.marketplace,
            "estimated_daily_sales": 0,
            "ideal_price": None,
            "competition_level": "Moyen",
            "trend": "stable",
            "risks": []
        }
        
        name_elem = soup.find('h1') or soup.find('title')
        if name_elem:
            data["name"] = name_elem.get_text(strip=True)
        
        price_elem = soup.find(string=re.compile(r'€|\$', re.I))
        if price_elem:
            price_match = re.search(r'[\d,]+\.?\d*', price_elem)
            if price_match:
                data["ideal_price"] = f"€{price_match.group()}"
        
        data["estimated_daily_sales"] = 4
        
        return data
    
    def is_shop_page(self, data: Dict[str, Any]) -> bool:
        return "product_count" in data

