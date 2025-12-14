# Scraping Direct - Guide d'utilisation

## Nouveau système simplifié

J'ai créé un **nouveau script de scraping direct** qui fonctionne sans découverte complexe.

## Fichiers créés

### 1. `scraper/scrape_direct.py`
Script principal qui :
- Scrape directement les boutiques de la liste
- Découvre de nouvelles boutiques depuis les pages principales
- Filtre les produits d'exemple/test/demo
- Sauvegarde directement dans la base de données

### 2. `scraper/test_scraper.py`
Script de test pour vérifier que les scrapers fonctionnent

## Utilisation

### Test rapide d'un scraper

```bash
cd scraper
python test_scraper.py
```

Cela va tester le scraper Chariow sur une boutique connue.

### Scraping complet

```bash
cd scraper
python scrape_direct.py
```

Le script va :
1. Scraper les boutiques de la liste directe (sans numerik)
2. Découvrir de nouvelles boutiques depuis les pages principales
3. Scraper toutes les boutiques trouvées
4. Filtrer les produits valides
5. Sauvegarder dans la base de données

## Améliorations apportées

### 1. Détection de produits améliorée
- **Chariow** : Détecte tous les produits via pattern `prd_` dans :
  - Les liens HTML
  - Le texte de la page (JS)
  - Les attributs data-*
  
- **Maketou** : Détecte tous les produits via pattern `/products/` dans :
  - Les liens HTML
  - Le texte de la page (JS)
  - Les attributs data-*

### 2. Filtrage des produits
Le script filtre automatiquement :
- Produits sans titre ou URL
- Produits avec "exemple", "test", "demo", "sample", "placeholder" dans le nom

### 3. Liste directe de boutiques
Le script utilise une liste directe de boutiques (sans numerik) :
- Chariow : 8 boutiques de départ
- Maketou : 6 boutiques de départ

## Comment trouver de nouvelles boutiques

Le script découvre automatiquement de nouvelles boutiques en :
1. Scrapant les pages principales de Chariow et Maketou
2. Cherchant tous les liens de boutiques
3. Scrapant les pages de catégories

## Résultat

Après le scraping, tous les produits sont dans la base de données et visibles sur le dashboard !



## Nouveau système simplifié

J'ai créé un **nouveau script de scraping direct** qui fonctionne sans découverte complexe.

## Fichiers créés

### 1. `scraper/scrape_direct.py`
Script principal qui :
- Scrape directement les boutiques de la liste
- Découvre de nouvelles boutiques depuis les pages principales
- Filtre les produits d'exemple/test/demo
- Sauvegarde directement dans la base de données

### 2. `scraper/test_scraper.py`
Script de test pour vérifier que les scrapers fonctionnent

## Utilisation

### Test rapide d'un scraper

```bash
cd scraper
python test_scraper.py
```

Cela va tester le scraper Chariow sur une boutique connue.

### Scraping complet

```bash
cd scraper
python scrape_direct.py
```

Le script va :
1. Scraper les boutiques de la liste directe (sans numerik)
2. Découvrir de nouvelles boutiques depuis les pages principales
3. Scraper toutes les boutiques trouvées
4. Filtrer les produits valides
5. Sauvegarder dans la base de données

## Améliorations apportées

### 1. Détection de produits améliorée
- **Chariow** : Détecte tous les produits via pattern `prd_` dans :
  - Les liens HTML
  - Le texte de la page (JS)
  - Les attributs data-*
  
- **Maketou** : Détecte tous les produits via pattern `/products/` dans :
  - Les liens HTML
  - Le texte de la page (JS)
  - Les attributs data-*

### 2. Filtrage des produits
Le script filtre automatiquement :
- Produits sans titre ou URL
- Produits avec "exemple", "test", "demo", "sample", "placeholder" dans le nom

### 3. Liste directe de boutiques
Le script utilise une liste directe de boutiques (sans numerik) :
- Chariow : 8 boutiques de départ
- Maketou : 6 boutiques de départ

## Comment trouver de nouvelles boutiques

Le script découvre automatiquement de nouvelles boutiques en :
1. Scrapant les pages principales de Chariow et Maketou
2. Cherchant tous les liens de boutiques
3. Scrapant les pages de catégories

## Résultat

Après le scraping, tous les produits sont dans la base de données et visibles sur le dashboard !

