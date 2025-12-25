# Référence Rapide des Endpoints

## 🔐 Authentification (`/api/v1/auth`)

| Méthode | Endpoint | Description | Auth | Admin |
|---------|----------|-------------|------|-------|
| POST | `/register` | Inscription d'un utilisateur | ❌ | ❌ |
| POST | `/login` | Connexion (retourne token) | ❌ | ❌ |

---

## 👤 Utilisateur (`/api/v1/users`)

| Méthode | Endpoint | Description | Auth | Admin |
|---------|----------|-------------|------|-------|
| GET | `/me` | Informations de l'utilisateur connecté | ✅ | ❌ |

---

## 📊 Dashboard (`/api/v1/dashboard`)

| Méthode | Endpoint | Description | Auth | Admin |
|---------|----------|-------------|------|-------|
| GET | `/stats` | Statistiques personnalisées du dashboard | ✅ | ❌ |

---

## 👨‍💼 Admin (`/api/v1/admin`)

| Méthode | Endpoint | Description | Auth | Admin |
|---------|----------|-------------|------|-------|
| GET | `/stats` | Statistiques globales admin | ✅ | ✅ |
| GET | `/users` | Liste tous les utilisateurs | ✅ | ✅ |
| GET | `/users/pending` | Utilisateurs en attente | ✅ | ✅ |
| POST | `/users/{id}/approve` | Approuver/rejeter un utilisateur | ✅ | ✅ |
| GET | `/payments/pending` | Paiements en attente | ✅ | ✅ |
| POST | `/payments/{id}/approve` | Approuver/rejeter un paiement | ✅ | ✅ |
| GET | `/logs` | Logs des actions admin | ✅ | ✅ |

---

## 🔍 Analyse (`/api/v1/analyse`)

| Méthode | Endpoint | Description | Auth | Admin |
|---------|----------|-------------|------|-------|
| POST | `` | Analyser une URL (produit/boutique) | ✅ | ❌ |
| GET | `/jobs/{job_id}` | Statut d'une analyse | ✅ | ❌ |

---

## 🏆 Winners (`/api/v1/winners`)

| Méthode | Endpoint | Description | Auth | Admin |
|---------|----------|-------------|------|-------|
| GET | `/products` | Liste des produits winners | ✅ | ❌ |
| GET | `/products/{id}` | Détails d'un produit winner | ✅ | ❌ |
| GET | `/shops` | Liste des boutiques winners | ✅ | ❌ |
| GET | `/shops/{id}` | Détails d'une boutique winner | ✅ | ❌ |
| GET | `/shop-by-name` | Rechercher boutique par nom | ✅ | ❌ |
| GET | `/categories` | Liste des catégories | ✅ | ❌ |
| GET | `/check-products` | Vérifier les produits | ✅ | ❌ |

---

## ⭐ Favoris (`/api/v1/favorites`)

| Méthode | Endpoint | Description | Auth | Admin |
|---------|----------|-------------|------|-------|
| POST | `/shops/{id}` | Ajouter une boutique aux favoris | ✅ | ❌ |
| GET | `/shops` | Liste des boutiques suivies | ✅ | ❌ |
| DELETE | `/shops/{id}` | Retirer une boutique des favoris | ✅ | ❌ |

---

## 📈 Statistiques Marché (`/api/v1/market-stats`)

| Méthode | Endpoint | Description | Auth | Admin |
|---------|----------|-------------|------|-------|
| GET | `/overview` | Vue d'ensemble du marché | ✅ | ❌ |
| GET | `/winners` | Winners du marché | ✅ | ❌ |
| GET | `/trends` | Tendances du marché | ✅ | ❌ |

---

## 🕷️ Scraper (`/api/v1/scraper`)

| Méthode | Endpoint | Description | Auth | Admin |
|---------|----------|-------------|------|-------|
| POST | `/crawl` | Déclencher un crawl | ✅ | ✅ |
| POST | `/crawl-all` | Crawl toutes les marketplaces | ✅ | ✅ |
| POST | `/run-cycle` | Cycle de scraping continu | ✅ | ✅ |
| GET | `/status` | Statut du scraper | ✅ | ✅ |

---

## 🏪 Boutiques (`/api/v1/shops`)

| Méthode | Endpoint | Description | Auth | Admin |
|---------|----------|-------------|------|-------|
| GET | `` | Liste des boutiques | ✅ | ❌ |
| GET | `/{id}` | Détails d'une boutique | ✅ | ❌ |

---

## 📦 Produits (`/api/v1/products`)

| Méthode | Endpoint | Description | Auth | Admin |
|---------|----------|-------------|------|-------|
| GET | `` | Liste des produits | ✅ | ❌ |
| GET | `/trending` | Produits tendance | ✅ | ❌ |

---

## 🎯 Légende

- **Auth** : Authentification requise (token JWT)
- **Admin** : Rôle admin requis
- ✅ : Oui
- ❌ : Non

---

## 📝 Notes

1. **Token JWT** : Obtenu via `/api/v1/auth/login`
2. **Format Authorization** : `Bearer <token>`
3. **Swagger UI** : Utilisez le bouton "Authorize" pour ajouter le token
4. **Statuts utilisateur** : `pending`, `approved`, `rejected`
5. **Quotas** : Vérifiez selon le plan (trial, 3months, 6months)

---

## 🚀 Ordre de Test Recommandé

1. **Auth** → Inscription → Login → Obtenir token
2. **Admin** → (Si admin) Approuver utilisateurs
3. **Dashboard** → Voir ses stats
4. **Winners** → Explorer produits/boutiques
5. **Analyse** → Analyser une URL
6. **Favoris** → Ajouter des boutiques
7. **Market Stats** → Voir les statistiques
8. **Scraper** → (Si admin) Déclencher scrapings
