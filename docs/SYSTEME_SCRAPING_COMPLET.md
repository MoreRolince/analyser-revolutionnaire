# Système Complet de Scraping - Documentation

## Architecture du Système

Le système de scraping est maintenant complet et fonctionnel avec tous les modules nécessaires.

## Modules Créés

### 1. ChariowScraper (`scraper/services/chariow_scraper.py`)
- **Détection exacte** : Pattern `prd_` pour identifier tous les produits
- **Scraping boutique** : Charge la boutique et détecte tous les produits
- **Scraping produit** : Extrait toutes les données d'un produit individuel
- **Format unifié** : Retourne les données dans le format standard

**Patterns utilisés** :
- Boutique : `https://<nom>.mychariow.shop/fr`
- Produit : `https://<boutique>.mychariow.shop/prd_<id>`

### 2. MaketouScraper (`scraper/services/maketou_scraper.py`)
- **Détection exacte** : Pattern `/products/` pour identifier tous les produits
- **Scraping boutique** : Charge la boutique et détecte tous les produits
- **Scraping produit** : Extrait toutes les données d'un produit individuel
- **Format unifié** : Retourne les données dans le format standard

**Patterns utilisés** :
- Boutique : `https://<nom>.mymaketou.store/fr`
- Produit : `https://<boutique>.mymaketou.store/products/<slug>`

### 3. ShopDetector (`scraper/services/shop_detector.py`)
- **Détection automatique** : Patterns regex pour Chariow et Maketou
- **Validation HTTP** : Vérifie que la boutique existe (status 200)
- **Normalisation** : Normalise les URLs de boutiques
- **Extraction** : Extrait les boutiques depuis n'importe quel texte

**Patterns regex** :
- Chariow : `https://([a-zA-Z0-9\-]+)\.mychariow\.shop(/fr)?`
- Maketou : `https://([a-zA-Z0-9\-]+)\.mymaketou\.store(/fr)?`

### 4. ProductUpdater (`scraper/services/product_updater.py`)
- **Détection de changements** : Compare produits existants vs nouveaux
- **Nouveaux produits** : Détecte les produits qui n'existent pas encore
- **Changements détectés** :
  - Prix (ancien → nouveau)
  - Description (hash MD5 pour détecter les changements)
  - Images (nouvelles images ajoutées)
  - Avis (augmentation du nombre d'avis)
  - Rating (changement de note)
  - Catégorie (changement de catégorie)
- **Scoring de croissance** : Calcule un score basé sur les changements

### 5. MarketplaceDiscovery (`scraper/services/discovery.py`)
- **Découverte multi-sources** :
  - Seeds (boutiques de départ)
  - Listings (pages de listing des marketplaces)
  - Google (recherches spécialisées)
  - Exploration en profondeur (liens entre boutiques)
- **Scroll multiple** : Charge tout le contenu dynamique
- **Normalisation** : Normalise toutes les URLs

### 6. Script Principal (`scraper/scrape_complete_system.py`)
- **Processus complet** :
  1. Découverte automatique de toutes les boutiques
  2. Validation des boutiques (HTTP 200)
  3. Scraping de chaque boutique
  4. Détection de changements
  5. Sauvegarde en base de données

## Format de Données Unifié

Tous les produits retournent le même format :

```python
{
    "id": str,                    # ID unique du produit
    "url": str,                   # URL complète
    "title": str,                 # Titre/nom
    "price": float,               # Prix en FCFA
    "description": str,           # Description
    "images": list[str],          # Array d'URLs d'images
    "category": str | None,       # Catégorie
    "rating": float | None,       # Note (0-5)
    "reviews_count": int | None,  # Nombre d'avis
    "date_added": str | None,     # Date d'ajout
    "shop_name": str,             # Nom de la boutique
    "shop_url": str,              # URL de la boutique
    "marketplace": str,           # "chariow" ou "maketou"
    "scraped_at": str             # Timestamp ISO
}
```

## Utilisation

### Lancer le scraping complet

```bash
cd scraper
python scrape_complete_system.py
```

Le script va :
1. Découvrir toutes les boutiques Chariow et Maketou
2. Valider qu'elles existent
3. Scraper toutes les boutiques
4. Détecter les changements (nouveaux produits, prix, avis, etc.)
5. Sauvegarder tout dans la base de données

## Détection de Changements

Le système détecte automatiquement :
- ✨ **Nouveaux produits** : Produits qui n'existent pas encore
- 💰 **Changement de prix** : Prix modifié
- 📝 **Changement de description** : Description mise à jour
- 🖼️ **Nouvelles images** : Images ajoutées
- ⭐ **Augmentation des avis** : Plus d'avis qu'avant
- 📊 **Changement de rating** : Note modifiée
- 🏷️ **Changement de catégorie** : Catégorie modifiée

## Scoring de Croissance

Le système calcule un score de croissance basé sur :
- Nouveau produit : +20 points
- Augmentation des avis : +2 points par avis
- Amélioration du rating : +10 points par point de rating
- Nouvelles images : +2 points par image
- Description mise à jour : +5 points

Ce score permet d'identifier les "winners" (produits en forte croissance).



## Architecture du Système

Le système de scraping est maintenant complet et fonctionnel avec tous les modules nécessaires.

## Modules Créés

### 1. ChariowScraper (`scraper/services/chariow_scraper.py`)
- **Détection exacte** : Pattern `prd_` pour identifier tous les produits
- **Scraping boutique** : Charge la boutique et détecte tous les produits
- **Scraping produit** : Extrait toutes les données d'un produit individuel
- **Format unifié** : Retourne les données dans le format standard

**Patterns utilisés** :
- Boutique : `https://<nom>.mychariow.shop/fr`
- Produit : `https://<boutique>.mychariow.shop/prd_<id>`

### 2. MaketouScraper (`scraper/services/maketou_scraper.py`)
- **Détection exacte** : Pattern `/products/` pour identifier tous les produits
- **Scraping boutique** : Charge la boutique et détecte tous les produits
- **Scraping produit** : Extrait toutes les données d'un produit individuel
- **Format unifié** : Retourne les données dans le format standard

**Patterns utilisés** :
- Boutique : `https://<nom>.mymaketou.store/fr`
- Produit : `https://<boutique>.mymaketou.store/products/<slug>`

### 3. ShopDetector (`scraper/services/shop_detector.py`)
- **Détection automatique** : Patterns regex pour Chariow et Maketou
- **Validation HTTP** : Vérifie que la boutique existe (status 200)
- **Normalisation** : Normalise les URLs de boutiques
- **Extraction** : Extrait les boutiques depuis n'importe quel texte

**Patterns regex** :
- Chariow : `https://([a-zA-Z0-9\-]+)\.mychariow\.shop(/fr)?`
- Maketou : `https://([a-zA-Z0-9\-]+)\.mymaketou\.store(/fr)?`

### 4. ProductUpdater (`scraper/services/product_updater.py`)
- **Détection de changements** : Compare produits existants vs nouveaux
- **Nouveaux produits** : Détecte les produits qui n'existent pas encore
- **Changements détectés** :
  - Prix (ancien → nouveau)
  - Description (hash MD5 pour détecter les changements)
  - Images (nouvelles images ajoutées)
  - Avis (augmentation du nombre d'avis)
  - Rating (changement de note)
  - Catégorie (changement de catégorie)
- **Scoring de croissance** : Calcule un score basé sur les changements

### 5. MarketplaceDiscovery (`scraper/services/discovery.py`)
- **Découverte multi-sources** :
  - Seeds (boutiques de départ)
  - Listings (pages de listing des marketplaces)
  - Google (recherches spécialisées)
  - Exploration en profondeur (liens entre boutiques)
- **Scroll multiple** : Charge tout le contenu dynamique
- **Normalisation** : Normalise toutes les URLs

### 6. Script Principal (`scraper/scrape_complete_system.py`)
- **Processus complet** :
  1. Découverte automatique de toutes les boutiques
  2. Validation des boutiques (HTTP 200)
  3. Scraping de chaque boutique
  4. Détection de changements
  5. Sauvegarde en base de données

## Format de Données Unifié

Tous les produits retournent le même format :

```python
{
    "id": str,                    # ID unique du produit
    "url": str,                   # URL complète
    "title": str,                 # Titre/nom
    "price": float,               # Prix en FCFA
    "description": str,           # Description
    "images": list[str],          # Array d'URLs d'images
    "category": str | None,       # Catégorie
    "rating": float | None,       # Note (0-5)
    "reviews_count": int | None,  # Nombre d'avis
    "date_added": str | None,     # Date d'ajout
    "shop_name": str,             # Nom de la boutique
    "shop_url": str,              # URL de la boutique
    "marketplace": str,           # "chariow" ou "maketou"
    "scraped_at": str             # Timestamp ISO
}
```

## Utilisation

### Lancer le scraping complet

```bash
cd scraper
python scrape_complete_system.py
```

Le script va :
1. Découvrir toutes les boutiques Chariow et Maketou
2. Valider qu'elles existent
3. Scraper toutes les boutiques
4. Détecter les changements (nouveaux produits, prix, avis, etc.)
5. Sauvegarder tout dans la base de données

## Détection de Changements

Le système détecte automatiquement :
- ✨ **Nouveaux produits** : Produits qui n'existent pas encore
- 💰 **Changement de prix** : Prix modifié
- 📝 **Changement de description** : Description mise à jour
- 🖼️ **Nouvelles images** : Images ajoutées
- ⭐ **Augmentation des avis** : Plus d'avis qu'avant
- 📊 **Changement de rating** : Note modifiée
- 🏷️ **Changement de catégorie** : Catégorie modifiée

## Scoring de Croissance

Le système calcule un score de croissance basé sur :
- Nouveau produit : +20 points
- Augmentation des avis : +2 points par avis
- Amélioration du rating : +10 points par point de rating
- Nouvelles images : +2 points par image
- Description mise à jour : +5 points

Ce score permet d'identifier les "winners" (produits en forte croissance).

