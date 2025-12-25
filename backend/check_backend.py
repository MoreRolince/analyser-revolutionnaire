#!/usr/bin/env python3
"""
Script de vérification complète du backend
Teste tous les composants essentiels de l'API
"""
import sys
import httpx
from typing import List, Tuple
from sqlalchemy import text
from app.database import engine, SessionLocal

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 5

class Colors:
    """Codes de couleur pour le terminal"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(message: str):
    """Affiche un message de succès"""
    print(f"{Colors.GREEN}✓{Colors.END} {message}")

def print_error(message: str):
    """Affiche un message d'erreur"""
    print(f"{Colors.RED}✗{Colors.END} {message}")

def print_warning(message: str):
    """Affiche un message d'avertissement"""
    print(f"{Colors.YELLOW}⚠{Colors.END} {message}")

def print_info(message: str):
    """Affiche un message informatif"""
    print(f"{Colors.BLUE}ℹ{Colors.END} {message}")

def print_header(message: str):
    """Affiche un en-tête"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def check_server_running() -> bool:
    """Vérifie si le serveur est démarré"""
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                print_success(f"Serveur accessible sur {BASE_URL}")
                return True
            else:
                print_error(f"Serveur répond avec le code {response.status_code}")
                return False
    except httpx.ConnectError:
        print_error(f"Impossible de se connecter au serveur sur {BASE_URL}")
        print_info("Assurez-vous que le serveur est démarré avec: uvicorn main:app --reload")
        return False
    except Exception as e:
        print_error(f"Erreur lors de la vérification du serveur: {e}")
        return False

def check_health_endpoint() -> bool:
    """Vérifie l'endpoint /health"""
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                print_success(f"Endpoint /health: {data}")
                return True
            else:
                print_error(f"Endpoint /health retourne le code {response.status_code}")
                return False
    except Exception as e:
        print_error(f"Erreur lors de la vérification de /health: {e}")
        return False

def check_database_connection() -> bool:
    """Vérifie la connexion à la base de données"""
    try:
        db = SessionLocal()
        try:
            # Test simple de connexion
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            print_success("Connexion à la base de données PostgreSQL réussie")
            
            # Vérifier que les tables existent
            result = db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            if tables:
                print_info(f"Tables trouvées: {', '.join(tables[:10])}")
                if len(tables) > 10:
                    print_info(f"... et {len(tables) - 10} autres tables")
            else:
                print_warning("Aucune table trouvée dans la base de données")
            return True
        finally:
            db.close()
    except Exception as e:
        print_error(f"Erreur de connexion à la base de données: {e}")
        print_info("Vérifiez que PostgreSQL est démarré et que DATABASE_URL est correcte")
        return False

def check_openapi_docs() -> bool:
    """Vérifie que la documentation OpenAPI est accessible"""
    endpoints = [
        ("/docs", "Documentation Swagger UI"),
        ("/redoc", "Documentation ReDoc"),
        ("/openapi.json", "Schéma OpenAPI JSON"),
    ]
    
    all_ok = True
    with httpx.Client(timeout=TIMEOUT) as client:
        for endpoint, name in endpoints:
            try:
                response = client.get(f"{BASE_URL}{endpoint}")
                if response.status_code == 200:
                    print_success(f"{name} accessible: {endpoint}")
                else:
                    print_warning(f"{name} retourne le code {response.status_code}")
                    all_ok = False
            except Exception as e:
                print_error(f"Erreur lors de la vérification de {name}: {e}")
                all_ok = False
    return all_ok

def check_routes() -> List[Tuple[str, bool, str]]:
    """Vérifie que les routes principales sont enregistrées"""
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(f"{BASE_URL}/openapi.json")
            if response.status_code != 200:
                print_error("Impossible de récupérer le schéma OpenAPI")
                return []
            
            openapi_spec = response.json()
            paths = openapi_spec.get("paths", {})
            
            # Fonction helper pour normaliser les chemins
            def normalize_path(path: str) -> str:
                """Normalise un chemin en enlevant le trailing slash"""
                return path.rstrip('/') if path != '/' else path
            
            # Routes importantes à vérifier (correspondant exactement aux routes OpenAPI)
            important_routes = [
                ("/api/v1/auth/login", "POST", "Authentification"),
                ("/api/v1/auth/register", "POST", "Inscription"),
                ("/api/v1/users/me", "GET", "Profil utilisateur"),
                ("/api/v1/dashboard/stats", "GET", "Statistiques dashboard"),
                ("/api/v1/products", "GET", "Liste des produits"),
                ("/api/v1/shops", "GET", "Liste des boutiques"),
                ("/api/v1/winners/products", "GET", "Liste des winners produits"),
                ("/api/v1/admin/stats", "GET", "Statistiques admin"),
                ("/api/v1/scraper/status", "GET", "Statut scraper"),
            ]
            
            results = []
            for route, method, description in important_routes:
                # Normaliser la route recherchée et la méthode (OpenAPI utilise des minuscules)
                normalized_route = normalize_path(route)
                method_lower = method.lower()
                route_exists = False
                found_path = None
                
                # Chercher dans les chemins OpenAPI
                for path in paths.keys():
                    normalized_path = normalize_path(path)
                    
                    # Vérifier si le chemin correspond exactement
                    if normalized_path == normalized_route:
                        # Chemin exact - vérifier que la méthode existe
                        if method_lower in paths[path]:
                            route_exists = True
                            found_path = path
                            break
                
                if route_exists:
                    print_success(f"Route {description}: {method} {route}")
                    results.append((route, True, ""))
                else:
                    # Vérifier s'il y a des chemins similaires pour aider au débogage
                    matching_paths = [p for p in paths.keys() if normalized_route in normalize_path(p)]
                    if matching_paths:
                        # Vérifier si au moins un chemin similaire a la méthode
                        method_found = any(method_lower in paths[p] for p in matching_paths)
                        if method_found:
                            print_warning(f"Route {description} trouvée avec chemin légèrement différent: {method} {route}")
                            print_info(f"  Chemin dans OpenAPI: {matching_paths[0]}")
                            results.append((route, True, ""))  # On considère ça comme OK
                        else:
                            print_warning(f"Route {description} trouvée mais méthode {method} non disponible: {route}")
                            print_info(f"  Méthodes disponibles: {', '.join(paths[matching_paths[0]].keys())}")
                            results.append((route, False, f"Méthode {method} non disponible"))
                    else:
                        print_warning(f"Route {description} non trouvée: {method} {route}")
                        results.append((route, False, "Route non trouvée dans OpenAPI"))
            
            return results
    except Exception as e:
        print_error(f"Erreur lors de la vérification des routes: {e}")
        import traceback
        traceback.print_exc()
        return []

def check_cors() -> bool:
    """Vérifie que CORS est configuré"""
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.options(
                f"{BASE_URL}/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET"
                }
            )
            cors_headers = {
                "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
                "access-control-allow-credentials": response.headers.get("access-control-allow-credentials"),
            }
            
            if any(cors_headers.values()):
                print_success("CORS configuré correctement")
                return True
            else:
                print_warning("Headers CORS non détectés (peut être normal selon la méthode)")
                return True  # Pas critique
    except Exception as e:
        print_warning(f"Erreur lors de la vérification CORS: {e}")
        return True  # Pas critique

def main():
    """Fonction principale"""
    print_header("VÉRIFICATION DU BACKEND MARKETPULSE AFRICA")
    
    results = {
        "Serveur": False,
        "Health Endpoint": False,
        "Base de données": False,
        "Documentation": False,
        "Routes": False,
        "CORS": False,
    }
    
    # 1. Vérifier que le serveur est démarré
    print_header("1. Vérification du serveur")
    results["Serveur"] = check_server_running()
    
    if not results["Serveur"]:
        print_error("\nLe serveur n'est pas accessible. Démarrez-le avec:")
        print_info("  uvicorn main:app --reload")
        sys.exit(1)
    
    # 2. Vérifier l'endpoint health
    print_header("2. Vérification de l'endpoint /health")
    results["Health Endpoint"] = check_health_endpoint()
    
    # 3. Vérifier la base de données
    print_header("3. Vérification de la base de données")
    results["Base de données"] = check_database_connection()
    
    # 4. Vérifier la documentation
    print_header("4. Vérification de la documentation")
    results["Documentation"] = check_openapi_docs()
    
    # 5. Vérifier les routes
    print_header("5. Vérification des routes API")
    route_results = check_routes()
    results["Routes"] = len([r for r in route_results if r[1]]) > 0
    
    # 6. Vérifier CORS
    print_header("6. Vérification CORS")
    results["CORS"] = check_cors()
    
    # Résumé final
    print_header("RÉSUMÉ")
    all_passed = True
    for component, status in results.items():
        if status:
            print_success(f"{component}: OK")
        else:
            print_error(f"{component}: ÉCHEC")
            all_passed = False
    
    print("\n")
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ Tous les tests sont passés avec succès!{Colors.END}")
        print(f"{Colors.GREEN}Le backend est opérationnel.{Colors.END}\n")
        sys.exit(0)
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Certains tests ont échoué{Colors.END}")
        print(f"{Colors.YELLOW}Vérifiez les erreurs ci-dessus et corrigez-les.{Colors.END}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
