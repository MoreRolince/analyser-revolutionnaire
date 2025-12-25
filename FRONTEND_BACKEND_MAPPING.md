# Mapping Frontend ↔ Backend

## ✅ Vérification Complète des Endpoints

### 🔐 Authentification

| Frontend | Backend | Status |
|----------|---------|--------|
| `POST /auth/login` | `POST /api/v1/auth/login` | ✅ |
| `POST /auth/register` | `POST /api/v1/auth/register` | ✅ |

### 👤 Utilisateurs

| Frontend | Backend | Status |
|----------|---------|--------|
| `GET /users/me` | `GET /api/v1/users/me` | ✅ |

### 📊 Dashboard

| Frontend | Backend | Status |
|----------|---------|--------|
| `GET /dashboard/stats` | `GET /api/v1/dashboard/stats` | ✅ |

### 🏆 Winners

| Frontend | Backend | Status |
|----------|---------|--------|
| `GET /winners/products` | `GET /api/v1/winners/products` | ✅ |
| `GET /winners/products/{id}` | `GET /api/v1/winners/products/{product_id}` | ✅ |
| `GET /winners/shops` | `GET /api/v1/winners/shops` | ✅ |
| `GET /winners/shops/{id}` | `GET /api/v1/winners/shops/{shop_id}` | ✅ |
| `GET /winners/shop-by-name` | `GET /api/v1/winners/shop-by-name` | ✅ |
| `GET /winners/categories` | `GET /api/v1/winners/categories` | ✅ |
| `GET /winners/check-products` | `GET /api/v1/winners/check-products` | ✅ |

### 🔍 Analyse

| Frontend | Backend | Status |
|----------|---------|--------|
| `POST /analyse` | `POST /api/v1/analyse` | ✅ |
| `GET /analyse/jobs/{id}` | `GET /api/v1/analyse/jobs/{job_id}` | ✅ |

### ⭐ Favoris

| Frontend | Backend | Status |
|----------|---------|--------|
| `GET /favorites/shops` | `GET /api/v1/favorites/shops` | ✅ |
| `POST /favorites/shops/{id}` | `POST /api/v1/favorites/shops/{shop_id}` | ✅ |
| `DELETE /favorites/shops/{id}` | `DELETE /api/v1/favorites/shops/{shop_id}` | ✅ |

### 👨‍💼 Admin

| Frontend | Backend | Status |
|----------|---------|--------|
| `GET /admin/users` | `GET /api/v1/admin/users` | ✅ |
| `GET /admin/users/pending` | `GET /api/v1/admin/users/pending` | ✅ |
| `POST /admin/users/{id}/approve` | `POST /api/v1/admin/users/{user_id}/approve` | ✅ |
| `GET /admin/payments/pending` | `GET /api/v1/admin/payments/pending` | ✅ |
| `POST /admin/payments/{id}/approve` | `POST /api/v1/admin/payments/{payment_id}/approve` | ✅ |
| `GET /admin/stats` | `GET /api/v1/admin/stats` | ✅ |
| `GET /admin/logs` | `GET /api/v1/admin/logs` | ✅ |

### 📈 Market Stats

| Frontend | Backend | Status |
|----------|---------|--------|
| `GET /market-stats/overview` | `GET /api/v1/market-stats/overview` | ✅ |
| `GET /market-stats/winners` | `GET /api/v1/market-stats/winners` | ✅ |
| `GET /market-stats/trends` | `GET /api/v1/market-stats/trends` | ✅ |

### 🕷️ Scraper (Admin)

| Frontend | Backend | Status |
|----------|---------|--------|
| `POST /scraper/crawl` | `POST /api/v1/scraper/crawl` | ✅ |
| `POST /scraper/crawl-all` | `POST /api/v1/scraper/crawl-all` | ✅ |
| `POST /scraper/run-cycle` | `POST /api/v1/scraper/run-cycle` | ✅ |
| `GET /scraper/status` | `GET /api/v1/scraper/status` | ✅ |

### 📦 Produits

| Frontend | Backend | Status |
|----------|---------|--------|
| `GET /products` | `GET /api/v1/products` | ✅ |
| `GET /products/trending` | `GET /api/v1/products/trending` | ✅ |

### 🏪 Boutiques

| Frontend | Backend | Status |
|----------|---------|--------|
| `GET /shops` | `GET /api/v1/shops` | ✅ |
| `GET /shops/{id}` | `GET /api/v1/shops/{shop_id}` | ✅ |

---

## 🔧 Configuration API

### Frontend (`lib/api.ts`)

- **Base URL** : `http://localhost:8000/api/v1` ✅
- **Headers** : `Content-Type: application/json` ✅
- **Auth** : Token ajouté automatiquement via interceptor ✅
- **Timeout** : 10 secondes ✅

### Backend (`main.py`)

- **Port** : 8000 ✅
- **CORS** : Configuré pour `localhost:3000` ✅
- **Routers** : Tous enregistrés avec préfixe `/api/v1` ✅

---

## ✅ Tous les endpoints sont correctement mappés !
