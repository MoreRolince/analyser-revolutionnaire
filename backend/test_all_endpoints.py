#!/usr/bin/env python3
"""
Script pour tester tous les endpoints utilisés par le frontend
Usage:
    python3 test_all_endpoints.py <token>
"""

import sys
import httpx
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(name, method, endpoint, token=None, data=None, params=None, expected_status=200):
    """Teste un endpoint et retourne le résultat"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = httpx.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            if isinstance(data, str):
                # Pour form-urlencoded
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                response = httpx.post(url, headers=headers, content=data, timeout=10)
            else:
                response = httpx.post(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = httpx.delete(url, headers=headers, timeout=10)
        else:
            print(f"❌ Méthode {method} non supportée pour {name}")
            return False
        
        if response.status_code == expected_status:
            print(f"✅ {name}: {method} {endpoint}")
            return True
        else:
            print(f"❌ {name}: {method} {endpoint} - Status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Erreur: {error_detail.get('detail', response.text[:200])}")
            except:
                print(f"   Erreur: {response.text[:200]}")
            return False
    except httpx.ConnectError:
        print(f"❌ {name}: Impossible de se connecter au serveur {BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ {name}: Erreur - {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_all_endpoints.py <token>")
        print("\nPour obtenir un token:")
        print("  curl -X POST 'http://localhost:8000/api/v1/auth/login' \\")
        print("    -H 'Content-Type: application/x-www-form-urlencoded' \\")
        print("    -d 'username=ARAYE&password=Lapeuff666'")
        sys.exit(1)
    
    token = sys.argv[1]
    
    print("=" * 80)
    print("TEST COMPLET DES ENDPOINTS FRONTEND-BACKEND")
    print("=" * 80)
    print()
    
    results = []
    
    # 1. Authentification
    print("1. AUTHENTIFICATION")
    print("-" * 80)
    # Note: login ne nécessite pas de token
    results.append(("Login (sans token)", test_endpoint(
        "Login", "POST", "/api/v1/auth/login",
        data="username=ARAYE&password=Lapeuff666",
        expected_status=200
    )))
    print()
    
    # 2. Utilisateurs
    print("2. UTILISATEURS")
    print("-" * 80)
    results.append(("GET /users/me", test_endpoint(
        "Get current user", "GET", "/api/v1/users/me",
        token=token
    )))
    print()
    
    # 3. Dashboard
    print("3. DASHBOARD")
    print("-" * 80)
    results.append(("GET /dashboard/stats", test_endpoint(
        "Dashboard stats", "GET", "/api/v1/dashboard/stats",
        token=token
    )))
    print()
    
    # 4. Winners
    print("4. WINNERS")
    print("-" * 80)
    results.append(("GET /winners/products", test_endpoint(
        "Winners products", "GET", "/api/v1/winners/products",
        token=token, params={"limit": 10}
    )))
    results.append(("GET /winners/shops", test_endpoint(
        "Winners shops", "GET", "/api/v1/winners/shops",
        token=token, params={"limit": 10}
    )))
    results.append(("GET /winners/categories", test_endpoint(
        "Winners categories", "GET", "/api/v1/winners/categories",
        token=token
    )))
    results.append(("GET /winners/check-products", test_endpoint(
        "Winners check-products", "GET", "/api/v1/winners/check-products",
        token=token
    )))
    print()
    
    # 5. Favoris
    print("5. FAVORIS")
    print("-" * 80)
    results.append(("GET /favorites/shops", test_endpoint(
        "Favorites shops", "GET", "/api/v1/favorites/shops",
        token=token
    )))
    print()
    
    # 6. Analyse
    print("6. ANALYSE")
    print("-" * 80)
    results.append(("POST /analyse", test_endpoint(
        "Create analysis", "POST", "/api/v1/analyse",
        token=token, data={"url": "https://example.com"}
    )))
    print()
    
    # 7. Admin (si admin)
    print("7. ADMIN (si vous êtes admin)")
    print("-" * 80)
    results.append(("GET /admin/stats", test_endpoint(
        "Admin stats", "GET", "/api/v1/admin/stats",
        token=token, expected_status=[200, 403]  # 403 si pas admin
    )))
    results.append(("GET /admin/users/pending", test_endpoint(
        "Admin pending users", "GET", "/api/v1/admin/users/pending",
        token=token, expected_status=[200, 403]
    )))
    print()
    
    # Résumé
    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    success = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Endpoints testés: {total}")
    print(f"Succès: {success}")
    print(f"Échecs: {total - success}")
    
    if success == total:
        print("\n✅ Tous les endpoints fonctionnent correctement!")
    else:
        print("\n❌ Certains endpoints ont échoué.")
        print("\nVérifications:")
        print("  1. Backend démarré ? (uvicorn main:app --reload)")
        print("  2. Token valide ?")
        print("  3. Utilisateur approuvé ? (status = 'approved')")
        print("  4. Pour les endpoints admin: êtes-vous admin ?")

if __name__ == "__main__":
    main()
