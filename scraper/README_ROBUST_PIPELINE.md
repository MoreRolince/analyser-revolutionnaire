# Pipeline Facebook Ads - Version Robuste et Scalable

## 🎯 Objectif

Cette version améliorée du pipeline est conçue pour gérer de grandes quantités de données (plusieurs milliers d'annonces, plusieurs dizaines de mots-clés, plusieurs pays) de manière robuste et scalable.

## ✨ Améliorations principales

### 1. **Gestion de la mémoire optimisée**
- ✅ Traitement par batch des requêtes DB (1000 annonces à la fois)
- ✅ Pagination pour éviter de charger toutes les données en mémoire
- ✅ Pool de connexions DB configuré (10 connexions, max 20 overflow)

### 2. **Gestion d'erreurs robuste**
- ✅ Retry automatique avec backoff exponentiel (3 tentatives par défaut)
- ✅ Gestion des erreurs individuelles (continue même si une annonce échoue)
- ✅ Commit périodique pour éviter les pertes de données
- ✅ Logs détaillés des erreurs

### 3. **Timeouts et limites configurables**
- ✅ Timeout landing pages: 60 secondes (au lieu de 30)
- ✅ Max retries: 3 tentatives avec délai exponentiel
- ✅ Limite d'annonces par mot-clé: 200 (configurable)
- ✅ Batch size scraping: 50 annonces (au lieu de 3)

### 4. **Rate limiting intelligent**
- ✅ Délai entre mots-clés: 3 secondes
- ✅ Délai entre landing pages: 1 seconde
- ✅ Délai après erreur: 5 secondes
- ✅ Pause automatique si trop d'erreurs consécutives

### 5. **Monitoring et logs**
- ✅ Logs de progression détaillés
- ✅ Statistiques en temps réel
- ✅ Temps d'exécution total
- ✅ Compteurs par étape

## 📊 Configuration

Tous les paramètres sont dans la classe `PipelineConfig` :

```python
class PipelineConfig:
    SCRAPING_BATCH_SIZE = 50  # Sauvegarder toutes les 50 annonces
    DB_QUERY_BATCH_SIZE = 1000  # Traiter 1000 annonces à la fois
    LANDING_PAGE_TIMEOUT = 60000  # 60 secondes
    LANDING_PAGE_MAX_RETRIES = 3
    DELAY_BETWEEN_KEYWORDS = 3  # Secondes
    DELAY_BETWEEN_LANDING_PAGES = 1  # Secondes
    MAX_ADS_PER_KEYWORD = 200
```

## 🚀 Utilisation

### Test avec peu de données (actuel)
```bash
cd scraper
python3 facebook_ads_pipeline.py
```

### Production avec beaucoup de données
```bash
cd scraper
python3 facebook_ads_pipeline_robust.py
```

## 🔧 Personnalisation

### Ajouter plus de mots-clés

Modifiez la liste `keywords` dans `main()` :

```python
keywords = [
    "formation",
    "coaching",
    "business en ligne",
    # ... ajoutez vos mots-clés ici
]
```

### Ajouter plus de pays

Modifiez le paramètre `country_targeting` dans la conversion des annonces :

```python
"country_targeting": "SN,CI,ML,BF,BJ,TG",  # Plusieurs pays
```

### Ajuster les batch sizes

Pour des volumes encore plus importants :

```python
PipelineConfig.SCRAPING_BATCH_SIZE = 100  # Plus grand batch
PipelineConfig.DB_QUERY_BATCH_SIZE = 2000  # Plus de données par requête
```

## 📈 Performance attendue

- **Petit volume** (10 mots-clés, 1 pays): ~30-60 minutes
- **Volume moyen** (50 mots-clés, 5 pays): ~3-6 heures
- **Grand volume** (200+ mots-clés, 10 pays): ~12-24 heures

## ⚠️ Points d'attention

1. **Base de données** : Assurez-vous que PostgreSQL a assez de ressources (RAM, connexions)
2. **Réseau** : Le pipeline fait beaucoup de requêtes HTTP, une connexion stable est importante
3. **Disque** : Les logs peuvent devenir volumineux sur de longues exécutions
4. **Playwright** : Ferme automatiquement les navigateurs, mais surveillez la mémoire

## 🐛 Dépannage

### Erreurs de connexion DB
- Vérifiez que PostgreSQL est démarré
- Vérifiez le port (5433 par défaut)
- Augmentez `pool_size` si nécessaire

### Timeouts fréquents
- Augmentez `LANDING_PAGE_TIMEOUT`
- Augmentez `DELAY_BETWEEN_LANDING_PAGES`

### Mémoire insuffisante
- Réduisez `DB_QUERY_BATCH_SIZE`
- Réduisez `MAX_ADS_PER_KEYWORD`

## 📝 Logs

Les logs sont affichés en temps réel avec :
- Progression par étape
- Nombre d'annonces/produits traités
- Erreurs détaillées
- Statistiques finales
