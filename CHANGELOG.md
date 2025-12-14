# Changelog - Mise à jour Catalog Winners

## 🔥 Suppression du Module RAG

### Fichiers supprimés
- `backend/app/services/rag_service.py` - Service RAG avec ChromaDB
- `backend/app/routers/ai.py` - Routes API pour le chatbot
- `frontend/app/assistant-ia/page.tsx` - Page du chatbot

### Modifications
- `backend/main.py` - Suppression de l'import et du router `ai`
- `backend/app/models.py` - Suppression du modèle `AIMessage` et de la relation dans `User`
- `backend/app/schemas.py` - Suppression des schémas `AIMessageRequest` et `AIMessageResponse`
- `backend/requirements.txt` - Suppression de `openai`, `chromadb`, `sentence-transformers`
- `frontend/components/dashboard/dashboard-content.tsx` - Suppression des références au chatbot

## ✨ Ajout du Module Catalog Winners

### Nouveaux Modèles de Base de Données

#### `ProductGlobal`
- `id`, `marketplace`, `product_name`, `shop_name`, `product_url`
- `price`, `sales_est_min`, `sales_est_max`
- `revenue_est_min`, `revenue_est_max`
- `score_winner` (0-100), `category`
- `last_scraped_at`, `created_at`, `updated_at`

#### `ShopGlobal`
- `id`, `marketplace`, `shop_name`, `shop_url`
- `score_global` (0-100)
- `revenue_est_min`, `revenue_est_max`
- `winners_count`
- `last_scraped_at`, `created_at`, `updated_at`

### Nouvelles Routes API (`/api/v1/winners`)

- `GET /winners/products` - Liste des produits winners avec filtres
  - Query params: `marketplace`, `min_score`, `max_price`, `category`, `limit`, `skip`
- `GET /winners/products/{id}` - Détails d'un produit winner
- `GET /winners/shops` - Liste des boutiques winners avec filtres
  - Query params: `marketplace`, `min_score`, `min_revenue`, `limit`, `skip`
- `GET /winners/shops/{id}` - Détails d'une boutique winner
- `GET /winners/categories` - Liste des catégories disponibles

### Nouveau Scraper Périodique

#### Fichiers créés
- `scraper/services/winners_crawler.py` - Crawler pour extraire les winners
- `scraper/cron_worker.py` - Worker CRON pour exécution périodique
- `docs/CRON_SETUP.md` - Documentation pour configurer le CRON

#### Fonctionnalités
- Crawl automatique des marketplaces (CHARIOW, Maketou, System.io)
- Extraction des top produits et boutiques
- Calcul automatique des scores
- Sauvegarde dans `products_global` et `shops_global`
- Exécution toutes les 6 heures (configurable)

### Nouvelles Pages Next.js

#### `/dashboard/winners`
- **Onglet 1**: Top Produits Winners
  - Grille de cartes produits
  - Filtres (marketplace, score, prix, catégorie)
  - Affichage du score, prix, CA estimé
- **Onglet 2**: Top Boutiques Winners
  - Grille de cartes boutiques
  - Filtres (marketplace, score, revenu)
  - Affichage du score, nombre de winners, CA estimé
- **Onglet 3**: Explorer par Catégorie
  - Liste des catégories disponibles
  - Navigation vers les produits par catégorie

### Mise à jour du Dashboard

#### Nouveau Widget "Insights du Marché"
- Affichage des top 3 produits winners
- Affichage des top 3 boutiques winners
- Données provenant de `products_global` et `shops_global`

#### Modifications
- Remplacement du lien "Assistant IA" par "Catalog Winners"
- Suppression de la section "Recommandation du Jour"
- Ajout du widget Market Insights

### Migration Base de Données

#### Fichier créé
- `backend/alembic/versions/001_add_winners_tables.py`
  - Création des tables `products_global` et `shops_global`
  - Suppression de la table `ai_messages`
  - Index pour optimiser les requêtes

### Composants UI Ajoutés

- `frontend/components/ui/tabs.tsx` - Composant Tabs pour les onglets

## 📝 Notes Importantes

1. **Migration nécessaire**: Exécuter `alembic upgrade head` après la mise à jour
2. **CRON à configurer**: Voir `docs/CRON_SETUP.md` pour configurer le crawler périodique
3. **URLs de scraping**: Les URLs dans `winners_crawler.py` sont des exemples - à adapter selon les vraies URLs des marketplaces
4. **Seuils de score**: Seuls les produits/boutiques avec score >= 70 sont considérés comme "winners"

## 🔄 Fonctionnalités Conservées

- ✅ Analyse URL (inchangée)
- ✅ Authentification utilisateur (inchangée)
- ✅ Panel admin (inchangée)
- ✅ Suivi de boutiques favorites (inchangé)
- ✅ Système de paiement (inchangé)
- ✅ Scraping de queues pour URLs spécifiques (inchangé)

## 🚀 Prochaines Étapes

1. Configurer le CRON pour le crawler automatique
2. Adapter les URLs de scraping aux vraies marketplaces
3. Ajuster les formules de scoring selon vos besoins
4. Tester le crawler manuellement avant de l'automatiser
5. Configurer les alertes en cas d'échec du crawler





## 🔥 Suppression du Module RAG

### Fichiers supprimés
- `backend/app/services/rag_service.py` - Service RAG avec ChromaDB
- `backend/app/routers/ai.py` - Routes API pour le chatbot
- `frontend/app/assistant-ia/page.tsx` - Page du chatbot

### Modifications
- `backend/main.py` - Suppression de l'import et du router `ai`
- `backend/app/models.py` - Suppression du modèle `AIMessage` et de la relation dans `User`
- `backend/app/schemas.py` - Suppression des schémas `AIMessageRequest` et `AIMessageResponse`
- `backend/requirements.txt` - Suppression de `openai`, `chromadb`, `sentence-transformers`
- `frontend/components/dashboard/dashboard-content.tsx` - Suppression des références au chatbot

## ✨ Ajout du Module Catalog Winners

### Nouveaux Modèles de Base de Données

#### `ProductGlobal`
- `id`, `marketplace`, `product_name`, `shop_name`, `product_url`
- `price`, `sales_est_min`, `sales_est_max`
- `revenue_est_min`, `revenue_est_max`
- `score_winner` (0-100), `category`
- `last_scraped_at`, `created_at`, `updated_at`

#### `ShopGlobal`
- `id`, `marketplace`, `shop_name`, `shop_url`
- `score_global` (0-100)
- `revenue_est_min`, `revenue_est_max`
- `winners_count`
- `last_scraped_at`, `created_at`, `updated_at`

### Nouvelles Routes API (`/api/v1/winners`)

- `GET /winners/products` - Liste des produits winners avec filtres
  - Query params: `marketplace`, `min_score`, `max_price`, `category`, `limit`, `skip`
- `GET /winners/products/{id}` - Détails d'un produit winner
- `GET /winners/shops` - Liste des boutiques winners avec filtres
  - Query params: `marketplace`, `min_score`, `min_revenue`, `limit`, `skip`
- `GET /winners/shops/{id}` - Détails d'une boutique winner
- `GET /winners/categories` - Liste des catégories disponibles

### Nouveau Scraper Périodique

#### Fichiers créés
- `scraper/services/winners_crawler.py` - Crawler pour extraire les winners
- `scraper/cron_worker.py` - Worker CRON pour exécution périodique
- `docs/CRON_SETUP.md` - Documentation pour configurer le CRON

#### Fonctionnalités
- Crawl automatique des marketplaces (CHARIOW, Maketou, System.io)
- Extraction des top produits et boutiques
- Calcul automatique des scores
- Sauvegarde dans `products_global` et `shops_global`
- Exécution toutes les 6 heures (configurable)

### Nouvelles Pages Next.js

#### `/dashboard/winners`
- **Onglet 1**: Top Produits Winners
  - Grille de cartes produits
  - Filtres (marketplace, score, prix, catégorie)
  - Affichage du score, prix, CA estimé
- **Onglet 2**: Top Boutiques Winners
  - Grille de cartes boutiques
  - Filtres (marketplace, score, revenu)
  - Affichage du score, nombre de winners, CA estimé
- **Onglet 3**: Explorer par Catégorie
  - Liste des catégories disponibles
  - Navigation vers les produits par catégorie

### Mise à jour du Dashboard

#### Nouveau Widget "Insights du Marché"
- Affichage des top 3 produits winners
- Affichage des top 3 boutiques winners
- Données provenant de `products_global` et `shops_global`

#### Modifications
- Remplacement du lien "Assistant IA" par "Catalog Winners"
- Suppression de la section "Recommandation du Jour"
- Ajout du widget Market Insights

### Migration Base de Données

#### Fichier créé
- `backend/alembic/versions/001_add_winners_tables.py`
  - Création des tables `products_global` et `shops_global`
  - Suppression de la table `ai_messages`
  - Index pour optimiser les requêtes

### Composants UI Ajoutés

- `frontend/components/ui/tabs.tsx` - Composant Tabs pour les onglets

## 📝 Notes Importantes

1. **Migration nécessaire**: Exécuter `alembic upgrade head` après la mise à jour
2. **CRON à configurer**: Voir `docs/CRON_SETUP.md` pour configurer le crawler périodique
3. **URLs de scraping**: Les URLs dans `winners_crawler.py` sont des exemples - à adapter selon les vraies URLs des marketplaces
4. **Seuils de score**: Seuls les produits/boutiques avec score >= 70 sont considérés comme "winners"

## 🔄 Fonctionnalités Conservées

- ✅ Analyse URL (inchangée)
- ✅ Authentification utilisateur (inchangée)
- ✅ Panel admin (inchangée)
- ✅ Suivi de boutiques favorites (inchangé)
- ✅ Système de paiement (inchangé)
- ✅ Scraping de queues pour URLs spécifiques (inchangé)

## 🚀 Prochaines Étapes

1. Configurer le CRON pour le crawler automatique
2. Adapter les URLs de scraping aux vraies marketplaces
3. Ajuster les formules de scoring selon vos besoins
4. Tester le crawler manuellement avant de l'automatiser
5. Configurer les alertes en cas d'échec du crawler



