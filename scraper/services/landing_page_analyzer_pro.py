"""
Analyseur de landing pages PRO - Détection type produit, prix, funnel
"""
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
import re
from urllib.parse import urlparse


class LandingPageAnalyzerPro:
    """Analyseur professionnel de landing pages"""
    
    def __init__(self):
        self.analyzed_pages = {}
    
    async def analyze_landing_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Analyse une landing page pour identifier:
        - Type de produit (ebook, formation, template, etc.)
        - Prix
        - Funnel type (System.io, WhatsApp, custom)
        - Niche (business, spirituality, mixed)
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                page = await browser.new_page()
                
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    await asyncio.sleep(2)  # Attendre chargement JS
                    
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Analyse complète
                    analysis = {
                        'landing_page_url': url,
                        'product_type': self._detect_product_type(soup, url),
                        'niche': self._detect_niche(soup, url),
                        'price': self._extract_price(soup),
                        'currency': self._detect_currency(soup),
                        'funnel_type': self._detect_funnel_type(url, soup),
                        'has_whatsapp_funnel': self._has_whatsapp_funnel(soup, url),
                        'template_ready': False,  # Sera calculé après
                        'resell_potential': False,  # Sera calculé après
                    }
                    
                    await browser.close()
                    return analysis
                    
                except Exception as e:
                    await browser.close()
                    return None
                    
        except Exception as e:
            return None
    
    def _detect_product_type(self, soup: BeautifulSoup, url: str) -> str:
        """Détecte le type de produit"""
        url_lower = url.lower()
        text = soup.get_text().lower()
        
        # Patterns par type
        if any(kw in text or kw in url_lower for kw in ['ebook', 'livre numérique', 'pdf']):
            return 'ebook'
        elif any(kw in text or kw in url_lower for kw in ['formation', 'cours', 'training']):
            return 'formation'
        elif any(kw in text or kw in url_lower for kw in ['template', 'modèle']):
            return 'template'
        elif any(kw in text or kw in url_lower for kw in ['audio', 'podcast', 'mp3']):
            return 'audio'
        elif any(kw in text or kw in url_lower for kw in ['prière', 'prières', 'prayer']):
            return 'spiritual_guide'
        elif any(kw in text or kw in url_lower for kw in ['abonnement', 'subscription', 'membre']):
            return 'subscription'
        else:
            return 'other'
    
    def _detect_niche(self, soup: BeautifulSoup, url: str) -> str:
        """Détecte la niche (business, spirituality, mixed)"""
        text = soup.get_text().lower()
        url_lower = url.lower()
        
        business_keywords = [
            'business', 'marketing', 'revenus', 'argent', 'gagner',
            'dropshipping', 'affiliation', 'e-commerce'
        ]
        
        spirituality_keywords = [
            'prière', 'spiritualité', 'délivrance', 'prospérité',
            'bénédiction', 'miracle', 'éveil', 'manifestation'
        ]
        
        business_score = sum(1 for kw in business_keywords if kw in text or kw in url_lower)
        spirituality_score = sum(1 for kw in spirituality_keywords if kw in text or kw in url_lower)
        
        if business_score > 0 and spirituality_score > 0:
            return 'mixed'
        elif spirituality_score > business_score:
            return 'spirituality'
        else:
            return 'business'
    
    def _extract_price(self, soup: BeautifulSoup) -> float:
        """Extrait le prix"""
        text = soup.get_text()
        
        # Patterns de prix
        patterns = [
            r'(\d+[\s,.]?\d*)\s*(?:FCFA|XOF)',
            r'(?:FCFA|XOF)\s*(\d+[\s,.]?\d*)',
            r'(\d+[\s,.]?\d*)\s*(?:€|EUR)',
            r'\$(\d+[\s,.]?\d*\.?\d*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    price_str = str(matches[-1]).replace(',', '').replace(' ', '').strip()
                    return float(price_str)
                except:
                    continue
        
        return 0.0
    
    def _detect_currency(self, soup: BeautifulSoup) -> str:
        """Détecte la devise"""
        text = soup.get_text()
        
        if 'FCFA' in text or 'XOF' in text:
            return 'FCFA'
        elif '€' in text or 'EUR' in text:
            return 'EUR'
        elif '$' in text or 'USD' in text:
            return 'USD'
        else:
            return 'FCFA'  # Par défaut pour l'Afrique
    
    def _detect_funnel_type(self, url: str, soup: BeautifulSoup) -> str:
        """Détecte le type de funnel"""
        url_lower = url.lower()
        text = soup.get_text().lower()
        
        if 'systeme.io' in url_lower:
            return 'systeme.io'
        elif 'whatsapp' in url_lower or 'wa.me' in url_lower or 'whatsapp' in text:
            return 'whatsapp'
        elif 'maketou' in url_lower or 'chariow' in url_lower:
            return 'marketplace'
        else:
            return 'custom'
    
    def _has_whatsapp_funnel(self, soup: BeautifulSoup, url: str) -> bool:
        """Détecte si le funnel utilise WhatsApp"""
        text = soup.get_text().lower()
        url_lower = url.lower()
        
        whatsapp_indicators = [
            'whatsapp', 'wa.me', 'chat whatsapp', 'contact whatsapp',
            'cliquez pour whatsapp', 'message whatsapp'
        ]
        
        return any(indicator in text or indicator in url_lower for indicator in whatsapp_indicators)
    
    def assess_template_ready(self, analysis: Dict[str, Any], ad_text: str) -> bool:
        """Évalue si le produit est prêt à être utilisé comme template"""
        # Critères pour template ready
        if analysis.get('product_type') in ['ebook', 'template', 'spiritual_guide']:
            if analysis.get('niche') == 'spirituality':
                # Les produits spirituels sont souvent template-ready
                return True
            elif 'prière' in ad_text.lower() or 'prières' in ad_text.lower():
                return True
        return False
    
    def assess_resell_potential(self, analysis: Dict[str, Any], ads_count: int, duration_days: int) -> bool:
        """Évalue le potentiel de revente"""
        # Produits avec plusieurs ads et longue durée = bon potentiel
        if ads_count >= 3 and duration_days >= 14:
            return True
        if analysis.get('niche') == 'spirituality' and ads_count >= 2:
            return True
        return False

