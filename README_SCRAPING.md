# 🚀 Système de Scraping Continu - MarketPulse Africa

## Vue d'ensemble

Le système de scraping continu permet de maintenir les données des boutiques et produits à jour en temps réel, similaire à Copyfy. Il fonctionne en permanence et :

- ✅ Scrape les boutiques toutes les **6 heures** pour mettre à jour les données
- ✅ Découvre automatiquement de **nouvelles boutiques** toutes les **24 heures**
- ✅ Maintient une base de données à jour avec les **vraies données** des marketplaces
- ✅ Calcule les scores en temps réel basés sur les données réelles

## Architecture

### Composants

1. **Continuous Scraper** (`scraper/services/continuous_scraper.py`)
   - Scraper principal qui tourne en continu
   - Met à jour les boutiques existantes
   - Découvre de nouvelles boutiques

2. **Discovery Service** (`scraper/services/discovery.py`)
   - Découvre automatiquement de nouvelles boutiques
   - Scrape les pages de listing des marketplaces
   - Extrait les URLs des boutiques

3. **Continuous Worker** (`scraper/continuous_worker.py`)
   - Worker qui tourne en permanence
   - Exécute les cycles de scraping automatiquement

## Démarrage

### Option 1 : Via Docker Compose (Recommandé)

Le scraper continu démarre automatiquement avec Docker :

```bash
docker-compose up -d continuous_scraper
```

### Option 2 : Manuellement

```bash
cd scraper
python continuous_worker.py
```

### Option 3 : En arrière-plan (Linux/Mac)

```bash
cd scraper
nohup python continuous_worker.py > scraper.log 2>&1 &
```

## Configuration

### Variables d'environnement

- `DATABASE_URL` : URL de connexion PostgreSQL
- `SCRAPE_INTERVAL_HOURS` : Intervalle entre chaque scraping (défaut: 6h)
- `DISCOVERY_INTERVAL_HOURS` : Intervalle pour découvrir de nouvelles boutiques (défaut: 24h)

### Modifier les intervalles

Éditez `scraper/services/continuous_scraper.py` :

```python
self.scrape_interval_hours = 6  # Scraper toutes les 6 heures
self.discovery_interval_hours = 24  # Découvrir toutes les 24h
```

## API Endpoints (Admin uniquement)

### Déclencher un cycle manuellement

```bash
POST /api/v1/scraper/run-cycle
Authorization: Bearer <admin_token>
```

### Vérifier le statut

```bash
GET /api/v1/scraper/status
Authorization: Bearer <admin_token>
```

Réponse :
```json
{
  "total_shops": 150,
  "total_products": 2500,
  "last_update": "2025-01-15T10:30:00",
  "shops_by_marketplace": {
    "chariow": 80,
    "maketou": 70
  }
}
```

## Fonctionnement

### Cycle de scraping

1. **Mise à jour des boutiques existantes**
   - Récupère toutes les boutiques scrapées il y a plus de 6 heures
   - Scrape chaque boutique pour mettre à jour les données
   - Met à jour les produits et scores

2. **Découverte de nouvelles boutiques** (toutes les 24h)
   - Scrape les pages de listing des marketplaces
   - Extrait les URLs des nouvelles boutiques
   - Scrape et ajoute les nouvelles boutiques à la base

### Données collectées

Pour chaque boutique :
- Nom de la boutique
- URL
- Score global
- Revenus estimés (min/max)
- Nombre de produits winners
- Date de dernier scraping

Pour chaque produit :
- Nom du produit
- Prix
- Score winner
- Ventes estimées (min/max)
- Revenus estimés (min/max)
- Catégorie
- Date de dernier scraping

## Monitoring

### Logs

Les logs sont affichés dans la console avec des emojis pour faciliter le suivi :
- 🔄 Scraping en cours
- ✅ Succès
- ❌ Erreur
- 🔍 Découverte
- 📊 Statistiques

### Vérifier que ça fonctionne

1. Vérifier les logs :
```bash
docker logs marketpulse_continuous_scraper
```

2. Vérifier le statut via l'API :
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8001/api/v1/scraper/status
```

3. Vérifier dans la base de données :
```sql
SELECT COUNT(*) FROM shops_global;
SELECT COUNT(*) FROM products_global;
SELECT MAX(last_scraped_at) FROM shops_global;
```

## Dépannage

### Le scraper ne démarre pas

1. Vérifier que PostgreSQL est accessible
2. Vérifier les variables d'environnement
3. Vérifier les logs : `docker logs marketpulse_continuous_scraper`

### Aucune nouvelle boutique découverte

- Les pages de listing peuvent avoir changé
- Vérifier les URLs dans `discovery.py`
- Augmenter le `discovery_interval_hours` si nécessaire

### Erreurs de scraping

- Vérifier que Playwright est installé : `playwright install chromium`
- Vérifier la connexion internet
- Vérifier que les URLs des marketplaces sont accessibles

## Performance

- **Scraping par cycle** : ~20 boutiques (configurable)
- **Temps par boutique** : ~5-10 secondes
- **Découverte** : ~50 nouvelles boutiques par marketplace
- **Base de données** : Mise à jour en temps réel

## Sécurité

- Le scraper respecte les `robots.txt` des sites
- Délai entre chaque scraping pour ne pas surcharger
- Limite le nombre de requêtes par cycle
- Gestion d'erreurs robuste

## Maintenance

### Ajouter de nouvelles marketplaces

1. Créer un scraper dans `scraper/services/`
2. Ajouter la logique de découverte dans `discovery.py`
3. Mettre à jour `continuous_scraper.py`

### Modifier les intervalles

Éditez `continuous_scraper.py` et redémarrez le worker.





## Vue d'ensemble

Le système de scraping continu permet de maintenir les données des boutiques et produits à jour en temps réel, similaire à Copyfy. Il fonctionne en permanence et :

- ✅ Scrape les boutiques toutes les **6 heures** pour mettre à jour les données
- ✅ Découvre automatiquement de **nouvelles boutiques** toutes les **24 heures**
- ✅ Maintient une base de données à jour avec les **vraies données** des marketplaces
- ✅ Calcule les scores en temps réel basés sur les données réelles

## Architecture

### Composants

1. **Continuous Scraper** (`scraper/services/continuous_scraper.py`)
   - Scraper principal qui tourne en continu
   - Met à jour les boutiques existantes
   - Découvre de nouvelles boutiques

2. **Discovery Service** (`scraper/services/discovery.py`)
   - Découvre automatiquement de nouvelles boutiques
   - Scrape les pages de listing des marketplaces
   - Extrait les URLs des boutiques

3. **Continuous Worker** (`scraper/continuous_worker.py`)
   - Worker qui tourne en permanence
   - Exécute les cycles de scraping automatiquement

## Démarrage

### Option 1 : Via Docker Compose (Recommandé)

Le scraper continu démarre automatiquement avec Docker :

```bash
docker-compose up -d continuous_scraper
```

### Option 2 : Manuellement

```bash
cd scraper
python continuous_worker.py
```

### Option 3 : En arrière-plan (Linux/Mac)

```bash
cd scraper
nohup python continuous_worker.py > scraper.log 2>&1 &
```

## Configuration

### Variables d'environnement

- `DATABASE_URL` : URL de connexion PostgreSQL
- `SCRAPE_INTERVAL_HOURS` : Intervalle entre chaque scraping (défaut: 6h)
- `DISCOVERY_INTERVAL_HOURS` : Intervalle pour découvrir de nouvelles boutiques (défaut: 24h)

### Modifier les intervalles

Éditez `scraper/services/continuous_scraper.py` :

```python
self.scrape_interval_hours = 6  # Scraper toutes les 6 heures
self.discovery_interval_hours = 24  # Découvrir toutes les 24h
```

## API Endpoints (Admin uniquement)

### Déclencher un cycle manuellement

```bash
POST /api/v1/scraper/run-cycle
Authorization: Bearer <admin_token>
```

### Vérifier le statut

```bash
GET /api/v1/scraper/status
Authorization: Bearer <admin_token>
```

Réponse :
```json
{
  "total_shops": 150,
  "total_products": 2500,
  "last_update": "2025-01-15T10:30:00",
  "shops_by_marketplace": {
    "chariow": 80,
    "maketou": 70
  }
}
```

## Fonctionnement

### Cycle de scraping

1. **Mise à jour des boutiques existantes**
   - Récupère toutes les boutiques scrapées il y a plus de 6 heures
   - Scrape chaque boutique pour mettre à jour les données
   - Met à jour les produits et scores

2. **Découverte de nouvelles boutiques** (toutes les 24h)
   - Scrape les pages de listing des marketplaces
   - Extrait les URLs des nouvelles boutiques
   - Scrape et ajoute les nouvelles boutiques à la base

### Données collectées

Pour chaque boutique :
- Nom de la boutique
- URL
- Score global
- Revenus estimés (min/max)
- Nombre de produits winners
- Date de dernier scraping

Pour chaque produit :
- Nom du produit
- Prix
- Score winner
- Ventes estimées (min/max)
- Revenus estimés (min/max)
- Catégorie
- Date de dernier scraping

## Monitoring

### Logs

Les logs sont affichés dans la console avec des emojis pour faciliter le suivi :
- 🔄 Scraping en cours
- ✅ Succès
- ❌ Erreur
- 🔍 Découverte
- 📊 Statistiques

### Vérifier que ça fonctionne

1. Vérifier les logs :
```bash
docker logs marketpulse_continuous_scraper
```

2. Vérifier le statut via l'API :
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8001/api/v1/scraper/status
```

3. Vérifier dans la base de données :
```sql
SELECT COUNT(*) FROM shops_global;
SELECT COUNT(*) FROM products_global;
SELECT MAX(last_scraped_at) FROM shops_global;
```

## Dépannage

### Le scraper ne démarre pas

1. Vérifier que PostgreSQL est accessible
2. Vérifier les variables d'environnement
3. Vérifier les logs : `docker logs marketpulse_continuous_scraper`

### Aucune nouvelle boutique découverte

- Les pages de listing peuvent avoir changé
- Vérifier les URLs dans `discovery.py`
- Augmenter le `discovery_interval_hours` si nécessaire

### Erreurs de scraping

- Vérifier que Playwright est installé : `playwright install chromium`
- Vérifier la connexion internet
- Vérifier que les URLs des marketplaces sont accessibles

## Performance

- **Scraping par cycle** : ~20 boutiques (configurable)
- **Temps par boutique** : ~5-10 secondes
- **Découverte** : ~50 nouvelles boutiques par marketplace
- **Base de données** : Mise à jour en temps réel

## Sécurité

- Le scraper respecte les `robots.txt` des sites
- Délai entre chaque scraping pour ne pas surcharger
- Limite le nombre de requêtes par cycle
- Gestion d'erreurs robuste

## Maintenance

### Ajouter de nouvelles marketplaces

1. Créer un scraper dans `scraper/services/`
2. Ajouter la logique de découverte dans `discovery.py`
3. Mettre à jour `continuous_scraper.py`

### Modifier les intervalles

Éditez `continuous_scraper.py` et redémarrez le worker.



