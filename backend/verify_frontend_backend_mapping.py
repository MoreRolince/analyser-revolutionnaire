#!/usr/bin/env python3
"""
Script pour vérifier que tous les appels API du frontend correspondent aux endpoints backend
"""

import os
import re
from pathlib import Path

# Mapping des appels frontend vers les endpoints backend
FRONTEND_CALLS = {
    # Auth
    '/auth/login': ('POST', '/api/v1/auth/login'),
    '/auth/register': ('POST', '/api/v1/auth/register'),
    
    # Users
    '/users/me': ('GET', '/api/v1/users/me'),
    
    # Dashboard
    '/dashboard/stats': ('GET', '/api/v1/dashboard/stats'),
    
    # Winners
    '/winners/products': ('GET', '/api/v1/winners/products'),
    '/winners/products/{id}': ('GET', '/api/v1/winners/products/{product_id}'),
    '/winners/shops': ('GET', '/api/v1/winners/shops'),
    '/winners/shops/{id}': ('GET', '/api/v1/winners/shops/{shop_id}'),
    '/winners/shop-by-name': ('GET', '/api/v1/winners/shop-by-name'),
    '/winners/categories': ('GET', '/api/v1/winners/categories'),
    '/winners/check-products': ('GET', '/api/v1/winners/check-products'),
    
    # Analyse
    '/analyse': ('POST', '/api/v1/analyse'),
    '/analyse/jobs/{id}': ('GET', '/api/v1/analyse/jobs/{job_id}'),
    
    # Favorites
    '/favorites/shops': ('GET', '/api/v1/favorites/shops'),
    '/favorites/shops/{id}': ('POST', '/api/v1/favorites/shops/{shop_id}'),
    '/favorites/shops/{id}/delete': ('DELETE', '/api/v1/favorites/shops/{shop_id}'),
    
    # Admin
    '/admin/users': ('GET', '/api/v1/admin/users'),
    '/admin/users/pending': ('GET', '/api/v1/admin/users/pending'),
    '/admin/users/{id}/approve': ('POST', '/api/v1/admin/users/{user_id}/approve'),
    '/admin/payments/pending': ('GET', '/api/v1/admin/payments/pending'),
    '/admin/payments/{id}/approve': ('POST', '/api/v1/admin/payments/{payment_id}/approve'),
    '/admin/stats': ('GET', '/api/v1/admin/stats'),
    '/admin/logs': ('GET', '/api/v1/admin/logs'),
    
    # Market Stats
    '/market-stats/overview': ('GET', '/api/v1/market-stats/overview'),
    '/market-stats/winners': ('GET', '/api/v1/market-stats/winners'),
    '/market-stats/trends': ('GET', '/api/v1/market-stats/trends'),
    
    # Scraper
    '/scraper/crawl': ('POST', '/api/v1/scraper/crawl'),
    '/scraper/crawl-all': ('POST', '/api/v1/scraper/crawl-all'),
    '/scraper/run-cycle': ('POST', '/api/v1/scraper/run-cycle'),
    '/scraper/status': ('GET', '/api/v1/scraper/status'),
    
    # Products
    '/products': ('GET', '/api/v1/products'),
    '/products/trending': ('GET', '/api/v1/products/trending'),
    
    # Shops
    '/shops': ('GET', '/api/v1/shops'),
    '/shops/{id}': ('GET', '/api/v1/shops/{shop_id}'),
}

# Endpoints backend réels (depuis main.py)
BACKEND_ENDPOINTS = {
    '/api/v1/auth/login': 'POST',
    '/api/v1/auth/register': 'POST',
    '/api/v1/users/me': 'GET',
    '/api/v1/dashboard/stats': 'GET',
    '/api/v1/winners/products': 'GET',
    '/api/v1/winners/products/{product_id}': 'GET',
    '/api/v1/winners/shops': 'GET',
    '/api/v1/winners/shops/{shop_id}': 'GET',
    '/api/v1/winners/shop-by-name': 'GET',
    '/api/v1/winners/categories': 'GET',
    '/api/v1/winners/check-products': 'GET',
    '/api/v1/analyse': 'POST',
    '/api/v1/analyse/jobs/{job_id}': 'GET',
    '/api/v1/favorites/shops': 'GET',
    '/api/v1/favorites/shops/{shop_id}': 'POST',
    '/api/v1/favorites/shops/{shop_id}': 'DELETE',
    '/api/v1/admin/users': 'GET',
    '/api/v1/admin/users/pending': 'GET',
    '/api/v1/admin/users/{user_id}/approve': 'POST',
    '/api/v1/admin/payments/pending': 'GET',
    '/api/v1/admin/payments/{payment_id}/approve': 'POST',
    '/api/v1/admin/stats': 'GET',
    '/api/v1/admin/logs': 'GET',
    '/api/v1/market-stats/overview': 'GET',
    '/api/v1/market-stats/winners': 'GET',
    '/api/v1/market-stats/trends': 'GET',
    '/api/v1/scraper/crawl': 'POST',
    '/api/v1/scraper/crawl-all': 'POST',
    '/api/v1/scraper/run-cycle': 'POST',
    '/api/v1/scraper/status': 'GET',
    '/api/v1/products': 'GET',
    '/api/v1/products/trending': 'GET',
    '/api/v1/shops': 'GET',
    '/api/v1/shops/{shop_id}': 'GET',
}

def find_frontend_api_calls():
    """Trouve tous les appels API dans le frontend"""
    frontend_dir = Path(__file__).parent.parent / 'frontend'
    api_calls = []
    
    # Patterns pour trouver les appels API
    patterns = [
        r"api\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]",
        r"api\.(get|post|put|delete|patch)\(`([^`]+)`",
        r"fetch\(['\"]([^'\"]+/api/v1/[^'\"]+)['\"]",
    ]
    
    for file_path in frontend_dir.rglob('*.{ts,tsx,js,jsx}'):
        if 'node_modules' in str(file_path):
            continue
        
        try:
            content = file_path.read_text(encoding='utf-8')
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    if len(match.groups()) >= 2:
                        method = match.group(1).upper()
                        endpoint = match.group(2)
                        # Nettoyer l'endpoint (enlever les query params, variables, etc.)
                        endpoint_clean = re.sub(r'\?.*$', '', endpoint)
                        endpoint_clean = re.sub(r'\$\{.*?\}', '{id}', endpoint_clean)
                        endpoint_clean = re.sub(r'/\d+', '/{id}', endpoint_clean)
                        api_calls.append((method, endpoint_clean, str(file_path.relative_to(frontend_dir))))
        except Exception as e:
            pass
    
    return api_calls

def main():
    print("=" * 80)
    print("VÉRIFICATION DU MAPPING FRONTEND-BACKEND")
    print("=" * 80)
    print()
    
    # Trouver tous les appels API dans le frontend
    print("🔍 Recherche des appels API dans le frontend...")
    frontend_calls = find_frontend_api_calls()
    
    print(f"\n📋 Appels API trouvés dans le frontend: {len(frontend_calls)}")
    print("-" * 80)
    
    issues = []
    verified = []
    
    for method, endpoint, file_path in frontend_calls:
        # Normaliser l'endpoint
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        
        # Vérifier si l'endpoint existe dans le backend
        backend_endpoint = None
        for be in BACKEND_ENDPOINTS.keys():
            # Remplacer les variables pour la comparaison
            be_normalized = re.sub(r'\{[^}]+\}', '{id}', be)
            endpoint_normalized = re.sub(r'\{[^}]+\}', '{id}', endpoint)
            
            if be_normalized == endpoint_normalized or be == endpoint:
                backend_endpoint = be
                break
        
        if backend_endpoint:
            backend_method = BACKEND_ENDPOINTS[backend_endpoint]
            if method == backend_method:
                verified.append((method, endpoint, file_path, '✅'))
            else:
                issues.append((method, endpoint, file_path, f'❌ Méthode incorrecte: frontend={method}, backend={backend_method}'))
        else:
            issues.append((method, endpoint, file_path, '❌ Endpoint non trouvé dans le backend'))
    
    # Afficher les résultats
    print("\n✅ Endpoints vérifiés:")
    for method, endpoint, file_path, status in verified[:10]:  # Limiter l'affichage
        print(f"  {status} {method} {endpoint} ({file_path})")
    if len(verified) > 10:
        print(f"  ... et {len(verified) - 10} autres")
    
    if issues:
        print(f"\n❌ Problèmes détectés ({len(issues)}):")
        for method, endpoint, file_path, error in issues:
            print(f"  {error}")
            print(f"     {method} {endpoint}")
            print(f"     Fichier: {file_path}")
            print()
    
    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"✅ Endpoints vérifiés: {len(verified)}")
    print(f"❌ Problèmes: {len(issues)}")
    
    if issues:
        print("\n⚠️  Des corrections sont nécessaires.")
    else:
        print("\n✅ Tous les endpoints sont correctement mappés!")

if __name__ == "__main__":
    main()
