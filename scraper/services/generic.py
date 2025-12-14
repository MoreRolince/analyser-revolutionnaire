from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, Any
import re

class GenericScraper:
    def __init__(self):
        self.marketplace = "other"
    
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrape générique pour n'importe quelle URL
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
        # Recherche générique de patterns communs
        shop_keywords = ['shop', 'store', 'boutique', 'vendor', 'seller', 'merchant']
        page_text = soup.get_text().lower()
        
        for keyword in shop_keywords:
            if keyword in page_text:
                return True
        
        # Chercher des listes de produits
        product_lists = soup.find_all(['ul', 'div'], class_=re.compile(r'product|item|grid', re.I))
        return len(product_lists) > 0
    
    def _scrape_shop(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Scrape générique d'une boutique"""
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
        
        # Compter les produits de manière générique
        products = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'product|item|card', re.I))
        data["product_count"] = len(products)
        
        if data["product_count"] > 0:
            data["estimated_sales"] = data["product_count"] * 5
            data["estimated_revenue"] = f"€{data['estimated_sales'] * 15}-{data['estimated_sales'] * 25}/mois"
        
        return data
    
    def _scrape_product(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Scrape générique d'un produit"""
        data = {
            "name": "",
            "url": url,
            "marketplace": self.marketplace,
            "estimated_daily_sales": 0,
            "ideal_price": None,
            "competition_level": "Inconnu",
            "trend": "stable",
            "risks": []
        }
        
        name_elem = soup.find('h1') or soup.find('title')
        if name_elem:
            data["name"] = name_elem.get_text(strip=True)
        
        # Chercher le prix
        price_patterns = [
            soup.find(string=re.compile(r'€|\$|FCFA|XOF', re.I)),
            soup.find('span', class_=re.compile(r'price|cost', re.I)),
            soup.find('div', class_=re.compile(r'price|cost', re.I))
        ]
        
        for price_elem in price_patterns:
            if price_elem:
                if isinstance(price_elem, str):
                    price_match = re.search(r'[\d,]+\.?\d*', price_elem)
                else:
                    price_match = re.search(r'[\d,]+\.?\d*', price_elem.get_text())
                if price_match:
                    data["ideal_price"] = f"€{price_match.group()}"
                    break
        
        data["estimated_daily_sales"] = 3
        
        return data
    
    def is_shop_page(self, data: Dict[str, Any]) -> bool:
        return "product_count" in data

