# Stratégie de Découverte des Produits Digitaux

## Vue d'ensemble

Le système Revenux découvre automatiquement les produits digitaux vendus sur **Chariow** et **Maketou**, deux plateformes populaires pour créer des boutiques de produits digitaux (similaires à Minea).

## Comment ça fonctionne

### 1. Découverte des Boutiques

Le système utilise **3 méthodes principales** pour découvrir les boutiques :

#### A. Recherche sur les Marketplaces Principales
- **Chariow** : `chariow.com/shops`, `chariow.com/vendors`, `chariow.com/stores`
- **Maketou** : `maketou.com/stores`, `maketou.com/shops`
- Recherches ciblées produits digitaux :
  - `digital`, `ebook`, `template`, `formation`, `cours`
  - `logiciel`, `application`, `plugin`, `theme`

#### B. Recherche Google (Google Dorks)
Le système utilise des requêtes Google spécialisées pour trouver des boutiques :
- `site:mychariow.shop+produit+digital`
- `site:mychariow.shop+ebook`
- `site:mychariow.shop+template`
- `site:mychariow.shop+formation`
- `site:mychariow.shop+cours+en+ligne`
- `site:mychariow.shop+affiliation`
- `site:mychariow.shop+dropshipping+digital`

Même chose pour Maketou avec `site:mymaketou.store`

#### C. Boutiques de Départ (Seeds)
Le fichier `discovered_shops.txt` contient des boutiques connues qui servent de point de départ. Le système explore ensuite les liens de ces boutiques pour en découvrir d'autres.

### 2. Scraping des Produits

Une fois une boutique découverte, le scraper :

1. **Visite la page de la boutique** (ex: `https://nom-boutique.mychariow.shop/`)
2. **Identifie tous les produits** sur la page en utilisant plusieurs stratégies :
   - Sélecteurs CSS spécifiques (`div.product`, `article.product`, etc.)
   - Recherche de liens contenant `/product`, `/p/`, `/item`
   - Scroll automatique pour charger les produits dynamiques
3. **Extrait les données de chaque produit** :
   - Nom du produit
   - URL du produit
   - Image du produit
   - Prix
   - Description
   - Catégorie
4. **Sauvegarde dans la base de données** avec scoring automatique

### 3. Types de Produits Digitaux Ciblés

Le système est optimisé pour découvrir :
- 📚 **Ebooks** et livres numériques
- 🎨 **Templates** (WordPress, Canva, etc.)
- 🎓 **Formations en ligne** et cours
- 💻 **Logiciels** et applications
- 🔌 **Plugins** et extensions
- 🎨 **Thèmes** (WordPress, Shopify, etc.)
- 📱 **Applications mobiles**
- 🎯 **Produits d'affiliation**

## Architecture Technique

```
┌─────────────────────────────────────────┐
│   MarketplaceDiscovery                   │
│   - discover_chariow_shops()             │
│   - discover_maketou_shops()             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   ChariowScraper / MaketouScraper       │
│   - scrape_shop()                       │
│   - extract_products()                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Base de Données (PostgreSQL)          │
│   - products_global                     │
│   - shops_global                        │
└─────────────────────────────────────────┘
```

## Exécution

### Scraping Automatique
```bash
cd scraper
python scrape_marketplaces.py
```

### Scraping Ciblé (1000 produits)
```bash
cd scraper
python scrape_1000_products.py
```

## Améliorations Futures

1. **Découverte par Catégories** : Explorer les catégories spécifiques aux produits digitaux
2. **Détection de Tendances** : Identifier les produits digitaux en forte croissance
3. **Analyse de Concurrence** : Comparer les prix et performances entre boutiques
4. **Alertes Automatiques** : Notifier quand de nouveaux produits digitaux intéressants sont découverts



## Vue d'ensemble

Le système Revenux découvre automatiquement les produits digitaux vendus sur **Chariow** et **Maketou**, deux plateformes populaires pour créer des boutiques de produits digitaux (similaires à Minea).

## Comment ça fonctionne

### 1. Découverte des Boutiques

Le système utilise **3 méthodes principales** pour découvrir les boutiques :

#### A. Recherche sur les Marketplaces Principales
- **Chariow** : `chariow.com/shops`, `chariow.com/vendors`, `chariow.com/stores`
- **Maketou** : `maketou.com/stores`, `maketou.com/shops`
- Recherches ciblées produits digitaux :
  - `digital`, `ebook`, `template`, `formation`, `cours`
  - `logiciel`, `application`, `plugin`, `theme`

#### B. Recherche Google (Google Dorks)
Le système utilise des requêtes Google spécialisées pour trouver des boutiques :
- `site:mychariow.shop+produit+digital`
- `site:mychariow.shop+ebook`
- `site:mychariow.shop+template`
- `site:mychariow.shop+formation`
- `site:mychariow.shop+cours+en+ligne`
- `site:mychariow.shop+affiliation`
- `site:mychariow.shop+dropshipping+digital`

Même chose pour Maketou avec `site:mymaketou.store`

#### C. Boutiques de Départ (Seeds)
Le fichier `discovered_shops.txt` contient des boutiques connues qui servent de point de départ. Le système explore ensuite les liens de ces boutiques pour en découvrir d'autres.

### 2. Scraping des Produits

Une fois une boutique découverte, le scraper :

1. **Visite la page de la boutique** (ex: `https://nom-boutique.mychariow.shop/`)
2. **Identifie tous les produits** sur la page en utilisant plusieurs stratégies :
   - Sélecteurs CSS spécifiques (`div.product`, `article.product`, etc.)
   - Recherche de liens contenant `/product`, `/p/`, `/item`
   - Scroll automatique pour charger les produits dynamiques
3. **Extrait les données de chaque produit** :
   - Nom du produit
   - URL du produit
   - Image du produit
   - Prix
   - Description
   - Catégorie
4. **Sauvegarde dans la base de données** avec scoring automatique

### 3. Types de Produits Digitaux Ciblés

Le système est optimisé pour découvrir :
- 📚 **Ebooks** et livres numériques
- 🎨 **Templates** (WordPress, Canva, etc.)
- 🎓 **Formations en ligne** et cours
- 💻 **Logiciels** et applications
- 🔌 **Plugins** et extensions
- 🎨 **Thèmes** (WordPress, Shopify, etc.)
- 📱 **Applications mobiles**
- 🎯 **Produits d'affiliation**

## Architecture Technique

```
┌─────────────────────────────────────────┐
│   MarketplaceDiscovery                   │
│   - discover_chariow_shops()             │
│   - discover_maketou_shops()             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   ChariowScraper / MaketouScraper       │
│   - scrape_shop()                       │
│   - extract_products()                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Base de Données (PostgreSQL)          │
│   - products_global                     │
│   - shops_global                        │
└─────────────────────────────────────────┘
```

## Exécution

### Scraping Automatique
```bash
cd scraper
python scrape_marketplaces.py
```

### Scraping Ciblé (1000 produits)
```bash
cd scraper
python scrape_1000_products.py
```

## Améliorations Futures

1. **Découverte par Catégories** : Explorer les catégories spécifiques aux produits digitaux
2. **Détection de Tendances** : Identifier les produits digitaux en forte croissance
3. **Analyse de Concurrence** : Comparer les prix et performances entre boutiques
4. **Alertes Automatiques** : Notifier quand de nouveaux produits digitaux intéressants sont découverts

