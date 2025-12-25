#!/usr/bin/env python3
"""
Script de test pour déboguer l'extraction des prix Chariow
"""
import asyncio
import os
import sys
from playwright.async_api import async_playwright

async def test_chariow_price(url: str):
    """Test l'extraction du prix sur une page Chariow"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headless=False pour voir
        page = await browser.new_page()
        
        try:
            print(f"🔍 Chargement de: {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)  # Attendre le chargement JS
            
            # 1. Chercher tous les éléments avec "raiton-Text-root"
            print("\n📋 Éléments avec 'raiton-Text-root':")
            raiton_elements = await page.evaluate("""
                () => {
                    const elems = document.querySelectorAll('[class*="raiton-Text-root"]');
                    return Array.from(elems).slice(0, 20).map(elem => ({
                        classes: elem.className,
                        text: elem.textContent?.trim().substring(0, 100) || '',
                        innerHTML: elem.innerHTML.substring(0, 200)
                    }));
                }
            """)
            for i, elem in enumerate(raiton_elements, 1):
                print(f"  {i}. Classes: {elem['classes']}")
                print(f"     Texte: {elem['text']}")
                print()
            
            # 2. Chercher tous les éléments avec "price" dans la classe
            print("\n📋 Éléments avec 'price' dans la classe:")
            price_elements = await page.evaluate("""
                () => {
                    const elems = document.querySelectorAll('[class*="price"], [class*="Price"], [class*="amount"], [class*="Amount"]');
                    return Array.from(elems).slice(0, 20).map(elem => ({
                        classes: elem.className,
                        text: elem.textContent?.trim().substring(0, 100) || '',
                    }));
                }
            """)
            for i, elem in enumerate(price_elements, 1):
                print(f"  {i}. Classes: {elem['classes']}")
                print(f"     Texte: {elem['text']}")
                print()
            
            # 3. Chercher tous les textes contenant "FCFA" ou "F CFA"
            print("\n📋 Éléments contenant 'FCFA' ou 'F CFA':")
            fcfa_elements = await page.evaluate("""
                () => {
                    const allElems = document.querySelectorAll('*');
                    const results = [];
                    for (const elem of allElems) {
                        const text = elem.textContent || '';
                        if (text.includes('FCFA') || text.includes('F CFA') || text.includes('franc')) {
                            if (elem.children.length === 0) {  // Élément feuille
                                results.push({
                                    tag: elem.tagName,
                                    classes: elem.className,
                                    text: text.trim().substring(0, 150)
                                });
                            }
                        }
                        if (results.length >= 30) break;
                    }
                    return results;
                }
            """)
            for i, elem in enumerate(fcfa_elements, 1):
                print(f"  {i}. Tag: {elem['tag']}, Classes: {elem['classes']}")
                print(f"     Texte: {elem['text']}")
                print()
            
            # 4. Essayer d'extraire le prix avec différents sélecteurs
            print("\n💰 Tentatives d'extraction du prix:")
            test_selectors = [
                'div.raiton-Text-root.text-red-500',
                'div[class*="raiton-Text-root"][class*="text-red-500"]',
                'div[class*="raiton-Text-root"][class*="text-heading"]',
                '[class*="price"]',
                '[class*="Price"]',
                '[data-price]',
            ]
            
            for selector in test_selectors:
                try:
                    result = await page.evaluate(f"""
                        () => {{
                            const elems = document.querySelectorAll('{selector}');
                            return Array.from(elems).map(e => e.textContent?.trim() || '').filter(t => t.length > 0);
                        }}
                    """)
                    if result:
                        print(f"  ✅ '{selector}': {result[:3]}")
                    else:
                        print(f"  ❌ '{selector}': Aucun résultat")
                except Exception as e:
                    print(f"  ⚠️  '{selector}': Erreur - {e}")
            
            # Garder le navigateur ouvert pour inspection manuelle
            print("\n⏸️  Navigateur ouvert pour inspection manuelle (fermez-le pour terminer)...")
            await asyncio.sleep(30)  # Attendre 30 secondes
            
        finally:
            await browser.close()

if __name__ == "__main__":
    # Tester avec une URL Chariow
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://africaservice.mychariow.shop/prd_2tvq7a"
    asyncio.run(test_chariow_price(test_url))
