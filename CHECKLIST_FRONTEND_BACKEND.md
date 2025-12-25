# ✅ Checklist Frontend ↔ Backend

## 🔧 Configuration de Base

### Frontend
- [x] **Base URL** : `http://localhost:8000/api/v1` (dans `lib/api.ts`)
- [x] **Token automatique** : Ajouté via interceptor
- [x] **Gestion erreurs 401** : Redirection vers login
- [x] **Timeout** : 10 secondes

### Backend
- [x] **Port** : 8000
- [x] **CORS** : Configuré pour `localhost:3000`
- [x] **Tous les routers** : Enregistrés avec préfixe `/api/v1`

---

## 📋 Vérification des Endpoints

### ✅ Authentification
- [x] `POST /auth/login` → `POST /api/v1/auth/login`
- [x] `POST /auth/register` → `POST /api/v1/auth/register`

### ✅ Utilisateurs
- [x] `GET /users/me` → `GET /api/v1/users/me`

### ✅ Dashboard
- [x] `GET /dashboard/stats` → `GET /api/v1/dashboard/stats`

### ✅ Winners
- [x] `GET /winners/products` → `GET /api/v1/winners/products`
- [x] `GET /winners/products/{id}` → `GET /api/v1/winners/products/{product_id}`
- [x] `GET /winners/shops` → `GET /api/v1/winners/shops`
- [x] `GET /winners/shops/{id}` → `GET /api/v1/winners/shops/{shop_id}`
- [x] `GET /winners/shop-by-name` → `GET /api/v1/winners/shop-by-name`
- [x] `GET /winners/categories` → `GET /api/v1/winners/categories`
- [x] `GET /winners/check-products` → `GET /api/v1/winners/check-products`

### ✅ Analyse
- [x] `POST /analyse` → `POST /api/v1/analyse`
- [x] `GET /analyse/jobs/{id}` → `GET /api/v1/analyse/jobs/{job_id}`

### ✅ Favoris
- [x] `GET /favorites/shops` → `GET /api/v1/favorites/shops`
- [x] `POST /favorites/shops/{id}` → `POST /api/v1/favorites/shops/{shop_id}`
- [x] `DELETE /favorites/shops/{id}` → `DELETE /api/v1/favorites/shops/{shop_id}`

### ✅ Admin
- [x] `GET /admin/users` → `GET /api/v1/admin/users`
- [x] `GET /admin/users/pending` → `GET /api/v1/admin/users/pending`
- [x] `POST /admin/users/{id}/approve` → `POST /api/v1/admin/users/{user_id}/approve`
- [x] `GET /admin/payments/pending` → `GET /api/v1/admin/payments/pending`
- [x] `POST /admin/payments/{id}/approve` → `POST /api/v1/admin/payments/{payment_id}/approve`
- [x] `GET /admin/stats` → `GET /api/v1/admin/stats`
- [x] `GET /admin/logs` → `GET /api/v1/admin/logs`

### ✅ Market Stats
- [x] `GET /market-stats/overview` → `GET /api/v1/market-stats/overview`
- [x] `GET /market-stats/winners` → `GET /api/v1/market-stats/winners`
- [x] `GET /market-stats/trends` → `GET /api/v1/market-stats/trends`

### ✅ Scraper
- [x] `POST /scraper/crawl` → `POST /api/v1/scraper/crawl`
- [x] `POST /scraper/crawl-all` → `POST /api/v1/scraper/crawl-all`
- [x] `POST /scraper/run-cycle` → `POST /api/v1/scraper/run-cycle`
- [x] `GET /scraper/status` → `GET /api/v1/scraper/status`

### ✅ Produits
- [x] `GET /products` → `GET /api/v1/products`
- [x] `GET /products/trending` → `GET /api/v1/products/trending`

### ✅ Boutiques
- [x] `GET /shops` → `GET /api/v1/shops`
- [x] `GET /shops/{id}` → `GET /api/v1/shops/{shop_id}`

---

## 🔍 Corrections Apportées

1. ✅ **Schéma PaymentApproval** : Retiré `payment_id` (déjà dans l'URL)
2. ✅ **Endpoint /users/me** : Tous les appels `/auth/me` remplacés par `/users/me`
3. ✅ **Login avec nom d'utilisateur** : Accepte maintenant email OU nom

---

## 🧪 Test Rapide

```bash
# 1. Obtenir un token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=ARAYE&password=Lapeuff666" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 2. Tester les endpoints critiques du dashboard
curl -X GET "http://localhost:8000/api/v1/dashboard/stats" \
  -H "Authorization: Bearer $TOKEN"

curl -X GET "http://localhost:8000/api/v1/winners/products?limit=10" \
  -H "Authorization: Bearer $TOKEN"

curl -X GET "http://localhost:8000/api/v1/winners/shops?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

## ✅ Résultat

**Tous les endpoints sont correctement mappés et configurés !**

Le frontend est complètement lié au backend. Si vous rencontrez encore des erreurs :

1. Vérifiez la console du navigateur (F12) pour les erreurs exactes
2. Vérifiez l'onglet Network pour voir les requêtes qui échouent
3. Partagez-moi les erreurs exactes pour un diagnostic précis
