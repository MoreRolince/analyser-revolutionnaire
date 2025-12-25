# Vérification Complète Frontend ↔ Backend

## ✅ Configuration de Base

### Frontend (`lib/api.ts`)
- ✅ Base URL: `http://localhost:8000/api/v1`
- ✅ Headers: `Content-Type: application/json`
- ✅ Token: Ajouté automatiquement via interceptor
- ✅ Timeout: 10 secondes
- ✅ Gestion d'erreurs: 401 → redirection vers login

### Backend (`main.py`)
- ✅ Port: 8000
- ✅ CORS: Configuré pour `localhost:3000`
- ✅ Tous les routers enregistrés avec préfixe `/api/v1`

---

## 📋 Mapping Complet des Endpoints

### ✅ Authentification
| Frontend | Backend | Méthode | Auth Requise |
|----------|---------|---------|--------------|
| `/auth/login` | `/api/v1/auth/login` | POST | ❌ |
| `/auth/register` | `/api/v1/auth/register` | POST | ❌ |

### ✅ Utilisateurs
| Frontend | Backend | Méthode | Auth Requise |
|----------|---------|---------|--------------|
| `/users/me` | `/api/v1/users/me` | GET | ✅ |

### ✅ Dashboard
| Frontend | Backend | Méthode | Auth Requise |
|----------|---------|---------|--------------|
| `/dashboard/stats` | `/api/v1/dashboard/stats` | GET | ✅ |

### ✅ Winners
| Frontend | Backend | Méthode | Auth Requise |
|----------|---------|---------|--------------|
| `/winners/products` | `/api/v1/winners/products` | GET | ✅ |
| `/winners/products/{id}` | `/api/v1/winners/products/{product_id}` | GET | ✅ |
| `/winners/shops` | `/api/v1/winners/shops` | GET | ✅ |
| `/winners/shops/{id}` | `/api/v1/winners/shops/{shop_id}` | GET | ✅ |
| `/winners/shop-by-name` | `/api/v1/winners/shop-by-name` | GET | ✅ |
| `/winners/categories` | `/api/v1/winners/categories` | GET | ✅ |
| `/winners/check-products` | `/api/v1/winners/check-products` | GET | ✅ |

### ✅ Analyse
| Frontend | Backend | Méthode | Auth Requise |
|----------|---------|---------|--------------|
| `/analyse` | `/api/v1/analyse` | POST | ✅ |
| `/analyse/jobs/{id}` | `/api/v1/analyse/jobs/{job_id}` | GET | ✅ |

### ✅ Favoris
| Frontend | Backend | Méthode | Auth Requise |
|----------|---------|---------|--------------|
| `/favorites/shops` | `/api/v1/favorites/shops` | GET | ✅ |
| `/favorites/shops/{id}` | `/api/v1/favorites/shops/{shop_id}` | POST | ✅ |
| `/favorites/shops/{id}` | `/api/v1/favorites/shops/{shop_id}` | DELETE | ✅ |

### ✅ Admin
| Frontend | Backend | Méthode | Auth Requise | Admin Requis |
|----------|---------|---------|--------------|--------------|
| `/admin/users` | `/api/v1/admin/users` | GET | ✅ | ✅ |
| `/admin/users/pending` | `/api/v1/admin/users/pending` | GET | ✅ | ✅ |
| `/admin/users/{id}/approve` | `/api/v1/admin/users/{user_id}/approve` | POST | ✅ | ✅ |
| `/admin/payments/pending` | `/api/v1/admin/payments/pending` | GET | ✅ | ✅ |
| `/admin/payments/{id}/approve` | `/api/v1/admin/payments/{payment_id}/approve` | POST | ✅ | ✅ |
| `/admin/stats` | `/api/v1/admin/stats` | GET | ✅ | ✅ |
| `/admin/logs` | `/api/v1/admin/logs` | GET | ✅ | ✅ |

### ✅ Market Stats
| Frontend | Backend | Méthode | Auth Requise |
|----------|---------|---------|--------------|
| `/market-stats/overview` | `/api/v1/market-stats/overview` | GET | ✅ |
| `/market-stats/winners` | `/api/v1/market-stats/winners` | GET | ✅ |
| `/market-stats/trends` | `/api/v1/market-stats/trends` | GET | ✅ |

### ✅ Scraper (Admin)
| Frontend | Backend | Méthode | Auth Requise | Admin Requis |
|----------|---------|---------|--------------|--------------|
| `/scraper/crawl` | `/api/v1/scraper/crawl` | POST | ✅ | ✅ |
| `/scraper/crawl-all` | `/api/v1/scraper/crawl-all` | POST | ✅ | ✅ |
| `/scraper/run-cycle` | `/api/v1/scraper/run-cycle` | POST | ✅ | ✅ |
| `/scraper/status` | `/api/v1/scraper/status` | GET | ✅ | ✅ |

### ✅ Produits
| Frontend | Backend | Méthode | Auth Requise |
|----------|---------|---------|--------------|
| `/products` | `/api/v1/products` | GET | ✅ |
| `/products/trending` | `/api/v1/products/trending` | GET | ✅ |

### ✅ Boutiques
| Frontend | Backend | Méthode | Auth Requise |
|----------|---------|---------|--------------|
| `/shops` | `/api/v1/shops` | GET | ✅ |
| `/shops/{id}` | `/api/v1/shops/{shop_id}` | GET | ✅ |

---

## 🔍 Points de Vérification

### 1. Format des Données

#### Dashboard Stats
**Backend retourne** (`/api/v1/dashboard/stats`):
```json
{
  "market_opportunity_score": 85.0,
  "remaining_analyses": 10,
  "tracked_shops": 0,
  "trending_products": [...],
  "daily_recommendation": "...",
  "market_stats": {...}
}
```
**Frontend attend** : ✅ Correspond

#### Winners Products
**Backend retourne** (`/api/v1/winners/products`):
```json
[
  {
    "id": 1,
    "marketplace": "chariow",
    "product_name": "...",
    "shop_name": "...",
    "product_url": "...",
    "price": 15000.0,
    "score_winner": 88.5,
    ...
  }
]
```
**Frontend attend** : ✅ Correspond

### 2. Paramètres de Requête

#### Winners avec filtres
- ✅ `limit` : Supporté
- ✅ `skip` : Supporté
- ✅ `marketplace` : Supporté
- ✅ `min_score` : Supporté
- ✅ `max_price` : Supporté
- ✅ `category` : Supporté

### 3. Gestion des Erreurs

#### Frontend (`lib/api.ts`)
- ✅ 401 → Supprime token et redirige vers login
- ✅ Logs détaillés en développement
- ✅ Timeout de 10 secondes

#### Backend
- ✅ 401 pour token invalide
- ✅ 403 pour permissions insuffisantes
- ✅ 404 pour ressources non trouvées
- ✅ 500 pour erreurs serveur

---

## 🧪 Test Rapide

### Étape 1 : Obtenir un token

```bash
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=ARAYE&password=Lapeuff666" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

### Étape 2 : Tester les endpoints critiques

```bash
# Dashboard stats
curl -X GET "http://localhost:8000/api/v1/dashboard/stats" \
  -H "Authorization: Bearer $TOKEN"

# Winners products
curl -X GET "http://localhost:8000/api/v1/winners/products?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Winners shops
curl -X GET "http://localhost:8000/api/v1/winners/shops?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Étape 3 : Utiliser le script de test

```bash
cd backend
source env/bin/activate
python3 test_all_endpoints.py "$TOKEN"
```

---

## ✅ Conclusion

**Tous les endpoints sont correctement mappés !**

Le frontend et le backend sont bien liés. Si vous rencontrez des erreurs :

1. **Vérifiez que le backend est démarré** : `uvicorn main:app --reload`
2. **Vérifiez que le token est valide** : Dans la console navigateur, `localStorage.getItem('token')`
3. **Vérifiez que l'utilisateur est approuvé** : `python3 check_user.py --all`
4. **Vérifiez les erreurs dans la console** : F12 → Console et Network

---

## 🚨 Problèmes Courants et Solutions

### Problème : Erreur 404
**Solution** : Vérifier que le router est enregistré dans `main.py`

### Problème : Erreur 401
**Solution** : Se reconnecter pour obtenir un nouveau token

### Problème : Erreur 403
**Solution** : Vérifier que l'utilisateur est approuvé et a les bonnes permissions

### Problème : CORS Error
**Solution** : Vérifier que `localhost:3000` est dans `allow_origins` de `main.py`

---

## 📝 Checklist Finale

- [x] Base URL configurée correctement
- [x] Tous les routers enregistrés
- [x] CORS configuré
- [x] Token ajouté automatiquement
- [x] Gestion d'erreurs en place
- [x] Tous les endpoints mappés correctement

**✅ Le frontend est complètement lié au backend !**
