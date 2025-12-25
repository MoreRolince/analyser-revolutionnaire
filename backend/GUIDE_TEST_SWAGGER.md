# Guide Complet de Test des Endpoints - Swagger UI

Ce guide vous explique comment tester tous les endpoints de l'API depuis Swagger UI (`http://127.0.0.1:8000/docs`).

## 📋 Table des matières

1. [Préparation](#préparation)
2. [Scénario de test complet](#scénario-de-test-complet)
3. [Détail de chaque endpoint](#détail-de-chaque-endpoint)

---

## 🔧 Préparation

### 1. Démarrer le serveur

```bash
cd /home/maxdo/projets/analyser-revolutionnaire/backend
source env/bin/activate
uvicorn main:app --reload
```

### 2. Accéder à Swagger UI

Ouvrez votre navigateur : `http://127.0.0.1:8000/docs`

### 3. Créer un compte admin (si nécessaire)

```bash
python3 create_admin.py --create-direct
# Email: admin@marketpulse.com
# Nom: Admin Principal
# Password: admin123
```

---

## 🎯 Scénario de Test Complet

### **ÉTAPE 1 : Authentification**

#### 1.1. Inscription d'un utilisateur
**Endpoint** : `POST /api/v1/auth/register`

**Ce qu'il fait** : Crée un nouvel utilisateur avec statut `pending` (en attente de validation)

**Paramètres** :
- `name` : "Max Test"
- `email` : "test@example.com"
- `password` : "test123456" (min 8 caractères)
- `plan` : "trial" (ou "3months", "6months")
- `payment_proof` : (optionnel, requis pour plans payants)

**Réponse attendue** :
```json
{
  "id": 3,
  "email": "test@example.com",
  "name": "Max Test",
  "status": "pending",
  "message": "Votre inscription est en attente de validation..."
}
```

**✅ Test** : Vérifier que l'utilisateur est créé avec `status: "pending"`

---

#### 1.2. Connexion (Login)
**Endpoint** : `POST /api/v1/auth/login`

**Ce qu'il fait** : Authentifie un utilisateur et retourne un token JWT

**Paramètres** :
- `username` : "ARAYE" (nom) ou "donaldaraye667@gmail.com" (email)
- `password` : "Lapeuff666"
- `grant_type` : (laisser vide ou "password")

**Réponse attendue** :
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**✅ Test** : 
- Copier le `access_token`
- Cliquer sur le bouton **"Authorize"** en haut de Swagger
- Coller le token dans le champ (format: `Bearer <token>`)
- Cliquer sur **"Authorize"** puis **"Close"**

**⚠️ Important** : Seuls les utilisateurs avec `status: "approved"` peuvent se connecter.

---

### **ÉTAPE 2 : Endpoints Utilisateur (Authentification requise)**

#### 2.1. Obtenir mes informations
**Endpoint** : `GET /api/v1/users/me`

**Ce qu'il fait** : Retourne les informations de l'utilisateur connecté (profil, quotas, plan)

**Paramètres** : Aucun

**Réponse attendue** :
```json
{
  "id": 2,
  "email": "donaldaraye667@gmail.com",
  "name": "ARAYE",
  "role": "ADMIN",
  "plan": null,
  "quota": {
    "analyses": 10,
    "aiRequests": 50,
    "trackedShops": 3
  }
}
```

**✅ Test** : Vérifier que les informations correspondent à l'utilisateur connecté

---

#### 2.2. Statistiques du dashboard
**Endpoint** : `GET /api/v1/dashboard/stats`

**Ce qu'il fait** : Retourne les statistiques personnalisées pour le dashboard (analyses restantes, boutiques suivies, produits tendance)

**Paramètres** : Aucun

**Réponse attendue** :
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

**✅ Test** : Vérifier que les quotas correspondent au plan de l'utilisateur

---

### **ÉTAPE 3 : Endpoints Admin (Authentification admin requise)**

#### 3.1. Statistiques admin
**Endpoint** : `GET /api/v1/admin/stats`

**Ce qu'il fait** : Retourne les statistiques globales pour le dashboard admin

**Paramètres** : Aucun

**Réponse attendue** :
```json
{
  "total_users": 2,
  "active_users": 1,
  "pending_users": 1,
  "users_by_status": {...},
  "users_by_plan": {...},
  "pending_payments": 0
}
```

**✅ Test** : Vérifier que les statistiques sont correctes

---

#### 3.2. Lister tous les utilisateurs
**Endpoint** : `GET /api/v1/admin/users`

**Ce qu'il fait** : Liste tous les utilisateurs avec filtres optionnels

**Paramètres** :
- `skip` : 0 (pagination)
- `limit` : 100 (nombre max de résultats)
- `status` : (optionnel) "pending", "approved", "rejected"

**Réponse attendue** : Liste d'utilisateurs avec leurs informations

**✅ Test** : Vérifier que tous les utilisateurs sont listés

---

#### 3.3. Utilisateurs en attente
**Endpoint** : `GET /api/v1/admin/users/pending`

**Ce qu'il fait** : Liste uniquement les utilisateurs en attente de validation

**Paramètres** : Aucun

**Réponse attendue** : Liste des utilisateurs avec `status: "pending"`

**✅ Test** : Vérifier que seuls les utilisateurs en attente sont retournés

---

#### 3.4. Approuver/Rejeter un utilisateur
**Endpoint** : `POST /api/v1/admin/users/{user_id}/approve`

**Ce qu'il fait** : Approuve ou rejette un utilisateur (change son statut)

**Paramètres** :
- `user_id` : ID de l'utilisateur (dans l'URL)
- `approve` : `true` pour approuver, `false` pour rejeter (query parameter)

**Exemple** : `POST /api/v1/admin/users/3/approve?approve=true`

**Réponse attendue** :
```json
{
  "message": "Utilisateur approuvé avec succès",
  "user": {
    "id": 3,
    "email": "test@example.com",
    "status": "approved",
    ...
  }
}
```

**✅ Test** :
1. Approuver un utilisateur en attente
2. Vérifier qu'il peut maintenant se connecter
3. Tester avec `approve=false` pour rejeter

---

#### 3.5. Paiements en attente
**Endpoint** : `GET /api/v1/admin/payments/pending`

**Ce qu'il fait** : Liste les paiements en attente de validation

**Paramètres** : Aucun

**Réponse attendue** : Liste des paiements avec statut `pending`

**✅ Test** : Vérifier que les paiements en attente sont listés

---

#### 3.6. Approuver/Rejeter un paiement
**Endpoint** : `POST /api/v1/admin/payments/{payment_id}/approve`

**Ce qu'il fait** : Approuve ou rejette un paiement et met à jour le plan de l'utilisateur

**Paramètres** :
- `payment_id` : ID du paiement (dans l'URL)
- Body JSON :
```json
{
  "approve": true
}
```

**Réponse attendue** :
```json
{
  "message": "Payment updated successfully"
}
```

**✅ Test** : Vérifier que le plan de l'utilisateur est mis à jour après approbation

---

#### 3.7. Logs admin
**Endpoint** : `GET /api/v1/admin/logs`

**Ce qu'il fait** : Liste les actions effectuées par les admins (audit trail)

**Paramètres** :
- `skip` : 0
- `limit` : 100

**Réponse attendue** : Liste des logs avec actions, cibles, détails

**✅ Test** : Vérifier que les actions admin sont enregistrées

---

### **ÉTAPE 4 : Analyse de produits/boutiques**

#### 4.1. Analyser une URL
**Endpoint** : `POST /api/v1/analyse`

**Ce qu'il fait** : Analyse une URL de produit ou boutique et retourne un score + insights IA

**Paramètres** :
```json
{
  "url": "https://example.com/product"
}
```

**Réponse attendue** :
```json
{
  "type": "product",
  "score": 85.5,
  "data": {...},
  "ai_insights": "Ce produit présente un fort potentiel..."
}
```

**✅ Test** :
- Tester avec une URL de produit
- Tester avec une URL de boutique
- Vérifier que le quota d'analyses diminue

---

#### 4.2. Statut d'une analyse
**Endpoint** : `GET /api/v1/analyse/jobs/{job_id}`

**Ce qu'il fait** : Récupère le statut d'un job d'analyse (pending, processing, completed, failed)

**Paramètres** :
- `job_id` : ID du job retourné lors de la création

**Réponse attendue** :
```json
{
  "job_id": "uuid-here",
  "status": "completed",
  "result": {...},
  "created_at": "...",
  "completed_at": "..."
}
```

**✅ Test** : Vérifier le statut d'une analyse en cours

---

### **ÉTAPE 5 : Winners (Top Produits/Boutiques)**

#### 5.1. Liste des produits winners
**Endpoint** : `GET /api/v1/winners/products`

**Ce qu'il fait** : Liste les meilleurs produits (winners) avec filtres

**Paramètres** :
- `marketplace` : (optionnel) "chariow", "maketou", etc.
- `min_score` : (optionnel) Score minimum (0-100)
- `max_price` : (optionnel) Prix maximum
- `category` : (optionnel) Catégorie
- `limit` : 50 (nombre de résultats)
- `skip` : 0 (pagination)

**Réponse attendue** : Liste de produits triés par score décroissant

**✅ Test** :
- Tester avec différents filtres
- Vérifier le tri par score
- Tester la pagination

---

#### 5.2. Détails d'un produit winner
**Endpoint** : `GET /api/v1/winners/products/{product_id}`

**Ce qu'il fait** : Récupère les détails complets d'un produit winner

**Paramètres** :
- `product_id` : ID du produit (dans l'URL)

**Réponse attendue** : Détails complets du produit (prix, revenus estimés, score, etc.)

**✅ Test** : Vérifier que tous les détails sont présents

---

#### 5.3. Liste des boutiques winners
**Endpoint** : `GET /api/v1/winners/shops`

**Ce qu'il fait** : Liste les meilleures boutiques (winners) avec filtres

**Paramètres** : Similaires aux produits (marketplace, min_score, limit, skip)

**Réponse attendue** : Liste de boutiques triées par score décroissant

**✅ Test** : Similaire aux produits winners

---

#### 5.4. Détails d'une boutique winner
**Endpoint** : `GET /api/v1/winners/shops/{shop_id}`

**Ce qu'il fait** : Récupère les détails complets d'une boutique winner

**Paramètres** :
- `shop_id` : ID de la boutique (dans l'URL)

**Réponse attendue** : Détails complets de la boutique

**✅ Test** : Vérifier les détails de la boutique

---

#### 5.5. Rechercher une boutique par nom
**Endpoint** : `GET /api/v1/winners/shop-by-name`

**Ce qu'il fait** : Recherche une boutique par son nom

**Paramètres** :
- `name` : Nom de la boutique (query parameter)

**Réponse attendue** : Détails de la boutique trouvée

**✅ Test** : Rechercher une boutique existante

---

#### 5.6. Liste des catégories
**Endpoint** : `GET /api/v1/winners/categories`

**Ce qu'il fait** : Liste toutes les catégories disponibles

**Paramètres** : Aucun

**Réponse attendue** : Liste des catégories avec compteurs

**✅ Test** : Vérifier que les catégories sont listées

---

### **ÉTAPE 6 : Favoris (Boutiques suivies)**

#### 6.1. Ajouter une boutique aux favoris
**Endpoint** : `POST /api/v1/favorites/shops/{shop_id}`

**Ce qu'il fait** : Ajoute une boutique à la liste des boutiques suivies

**Paramètres** :
- `shop_id` : ID de la boutique (dans l'URL)

**Réponse attendue** :
```json
{
  "message": "Shop added to favorites"
}
```

**✅ Test** :
- Ajouter une boutique
- Vérifier le quota de boutiques suivies
- Tester l'ajout d'une boutique déjà suivie (erreur attendue)

---

#### 6.2. Liste des boutiques suivies
**Endpoint** : `GET /api/v1/favorites/shops`

**Ce qu'il fait** : Liste toutes les boutiques suivies par l'utilisateur

**Paramètres** : Aucun

**Réponse attendue** : Liste des boutiques suivies

**✅ Test** : Vérifier que les boutiques ajoutées apparaissent

---

#### 6.3. Retirer une boutique des favoris
**Endpoint** : `DELETE /api/v1/favorites/shops/{shop_id}`

**Ce qu'il fait** : Retire une boutique de la liste des favoris

**Paramètres** :
- `shop_id` : ID de la boutique (dans l'URL)

**Réponse attendue** :
```json
{
  "message": "Shop removed from favorites"
}
```

**✅ Test** : Vérifier que la boutique est retirée

---

### **ÉTAPE 7 : Statistiques du marché**

#### 7.1. Vue d'ensemble du marché
**Endpoint** : `GET /api/v1/market-stats/overview`

**Ce qu'il fait** : Retourne une vue d'ensemble complète du marché (totaux, top boutiques/produits, statistiques)

**Paramètres** : Aucun

**Réponse attendue** :
```json
{
  "total_shops": 150,
  "total_products": 500,
  "shops_by_marketplace": {...},
  "top_shops": [...],
  "top_products": [...],
  "market_stats": {...},
  "trending_products": [...]
}
```

**✅ Test** : Vérifier que toutes les statistiques sont présentes

---

#### 7.2. Winners du marché
**Endpoint** : `GET /api/v1/market-stats/winners`

**Ce qu'il fait** : Liste les winners du marché (boutiques et produits avec score élevé)

**Paramètres** :
- `limit` : 20 (nombre de résultats)

**Réponse attendue** :
```json
{
  "shops": [...],
  "products": [...]
}
```

**✅ Test** : Vérifier que seuls les winners (score >= 75/80) sont retournés

---

#### 7.3. Tendances du marché
**Endpoint** : `GET /api/v1/market-stats/trends`

**Ce qu'il fait** : Retourne les tendances du marché (produits en hausse, boutiques en croissance)

**Paramètres** : Aucun

**Réponse attendue** :
```json
{
  "rising_products": [...],
  "growing_shops": [...]
}
```

**✅ Test** : Vérifier les tendances

---

### **ÉTAPE 8 : Scraper (Admin uniquement)**

#### 8.1. Déclencher un crawl
**Endpoint** : `POST /api/v1/scraper/crawl`

**Ce qu'il fait** : Déclenche le scraping d'une marketplace spécifique

**Paramètres** :
```json
{
  "marketplace": "chariow",
  "shop_urls": ["https://example.com/shop"]
}
```

**Réponse attendue** :
```json
{
  "message": "Crawling terminé",
  "results": [
    {
      "marketplace": "chariow",
      "status": "success",
      "products": 50,
      "shops": 10
    }
  ]
}
```

**✅ Test** : Vérifier que le scraping fonctionne

---

#### 8.2. Crawl toutes les marketplaces
**Endpoint** : `POST /api/v1/scraper/crawl-all`

**Ce qu'il fait** : Déclenche le scraping de toutes les marketplaces

**Paramètres** : Aucun

**Réponse attendue** : Résultats pour chaque marketplace

**✅ Test** : Vérifier que toutes les marketplaces sont scrapées

---

#### 8.3. Statut du scraper
**Endpoint** : `GET /api/v1/scraper/status`

**Ce qu'il fait** : Retourne le statut du scraper (nombre de boutiques/produits, dernière mise à jour)

**Paramètres** : Aucun

**Réponse attendue** :
```json
{
  "total_shops": 150,
  "total_products": 500,
  "last_update": "2025-12-18T12:00:00",
  "shops_by_marketplace": {...}
}
```

**✅ Test** : Vérifier les statistiques du scraper

---

## 📝 Checklist de Test Complète

### Authentification
- [ ] Inscription d'un utilisateur
- [ ] Connexion avec email
- [ ] Connexion avec nom d'utilisateur
- [ ] Récupération du profil utilisateur

### Admin
- [ ] Voir les statistiques admin
- [ ] Lister tous les utilisateurs
- [ ] Voir les utilisateurs en attente
- [ ] Approuver un utilisateur
- [ ] Rejeter un utilisateur
- [ ] Voir les paiements en attente
- [ ] Approuver un paiement
- [ ] Voir les logs admin

### Analyse
- [ ] Analyser une URL de produit
- [ ] Analyser une URL de boutique
- [ ] Vérifier le statut d'une analyse
- [ ] Vérifier la diminution du quota

### Winners
- [ ] Lister les produits winners
- [ ] Filtrer les produits par marketplace
- [ ] Filtrer les produits par score
- [ ] Voir les détails d'un produit
- [ ] Lister les boutiques winners
- [ ] Voir les détails d'une boutique
- [ ] Rechercher une boutique par nom
- [ ] Lister les catégories

### Favoris
- [ ] Ajouter une boutique aux favoris
- [ ] Lister les boutiques suivies
- [ ] Retirer une boutique des favoris
- [ ] Vérifier le quota de favoris

### Statistiques
- [ ] Vue d'ensemble du marché
- [ ] Winners du marché
- [ ] Tendances du marché

### Scraper (Admin)
- [ ] Déclencher un crawl
- [ ] Crawl toutes les marketplaces
- [ ] Voir le statut du scraper

---

## 🔑 Points Importants

1. **Authentification** : La plupart des endpoints nécessitent un token. Utilisez le bouton "Authorize" dans Swagger.

2. **Rôles** : 
   - `USER` : Accès aux endpoints utilisateur
   - `ADMIN` : Accès à tous les endpoints + endpoints admin

3. **Statuts utilisateur** :
   - `pending` : En attente de validation (ne peut pas se connecter)
   - `approved` : Approuvé (peut se connecter)
   - `rejected` : Rejeté (ne peut pas se connecter)

4. **Quotas** : Vérifiez les quotas selon le plan :
   - `trial` : 10 analyses, 50 requêtes IA, 3 boutiques suivies
   - `3months` : 100 analyses, 500 requêtes IA, 10 boutiques suivies
   - `6months` : 300 analyses, 1500 requêtes IA, 30 boutiques suivies

5. **Erreurs courantes** :
   - `401 Unauthorized` : Token manquant ou invalide
   - `403 Forbidden` : Permissions insuffisantes ou quota atteint
   - `404 Not Found` : Ressource introuvable
   - `422 Validation Error` : Paramètres invalides

---

## 🎯 Ordre Recommandé de Test

1. **Authentification** (créer compte, se connecter)
2. **Admin** (si admin : approuver utilisateurs, voir stats)
3. **Dashboard** (voir ses statistiques)
4. **Winners** (explorer les produits/boutiques)
5. **Analyse** (analyser une URL)
6. **Favoris** (ajouter des boutiques)
7. **Statistiques** (voir les stats du marché)
8. **Scraper** (si admin : déclencher des scrapings)

---

Bon test ! 🚀
