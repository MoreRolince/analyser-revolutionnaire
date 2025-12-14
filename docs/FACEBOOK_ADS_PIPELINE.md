# Pipeline Facebook Ads Library - Détection de Produits Digitaux Winners

## 🎯 Objectif

Détecter automatiquement les produits digitaux "winners" (gagnants) en analysant les publicités Facebook qui les promouvant.

## 🔄 Architecture du Pipeline

### 1️⃣ Scraper Facebook Ads Library (`facebook_ads_scraper.py`)

**Fonctionnalités :**
- Recherche dans Facebook Ads Library avec mots-clés produits digitaux
- Extraction des données d'annonces :
  - Titre du produit
  - Description
  - Media (image/video URL)
  - Landing page URL
  - Page publicitaire
  - Date de début / Statut actif
  - Ciblage pays

**Mots-clés recherchés :**
- "formation", "e-book", "ebook", "coaching", "guide", "programme"
- "make money", "digital product", "cours", "pdf"
- "business en ligne", "revenus", "astuces"
- "Makétou", "Chariow", "Systeme.io"
- Et plus de 30 autres mots-clés

**Stockage :** Table `fb_ads_raw`

### 2️⃣ Analyseur de Landing Pages (`landing_page_analyzer.py`)

**Fonctionnalités :**
- Analyse automatique des landing pages
- Détection des domaines de produits digitaux :
  - `maketou.com` / `mymaketou.store`
  - `chariow.com` / `mychariow.shop`
  - `systeme.io` / `systeme.io/marketplace`
  - `gumroad.com`, `payhip.com`
  - `notion.so`, `drive.google.com`

**Données extraites :**
- Titre du produit
- Prix
- Nom du vendeur
- Description
- Images
- Points clés (bullet points)
- CTA (Call To Action)
- Preuves sociales (avis, commentaires, témoignages)
- Structure de la page (vidéo, garantie, bonus, countdown)

**Stockage :** Table `digital_products_detected`

### 3️⃣ Déduplication et Matching (`product_deduplicator.py`)

**Fonctionnalités :**
- Détection de produits dupliqués (même produit, URLs différentes)
- Fusion automatique des versions multiples
- Détection des changements de prix
- Historique des versions

**Algorithme :**
- Hash basé sur URL normalisée + titre
- Similarité de texte (titre + description)
- Matching intelligent

### 4️⃣ Modèle de Scoring Winner (`winner_scorer.py`)

**Score Winner (0-100) basé sur :**

#### 📌 Métriques au niveau des annonces (40 points max)
- **Nombre d'annonces** (15 pts) : Plus il y a d'annonces, plus le produit est promu
- **Nombre de pays ciblés** (10 pts) : Indicateur de portée internationale
- **Longévité des annonces** (10 pts) : Produits actifs depuis longtemps = stables
- **Nombre de pages publicitaires** (5 pts) : Plusieurs annonceurs = produit populaire

#### 📌 Métriques au niveau de la landing page (40 points max)
- **Attractivité du prix** (10 pts) : Prix optimal pour marché africain (5000-50000 FCFA)
- **Clarté de l'offre** (10 pts) : Titre + description + bullet points clairs
- **Présence de bonus** (5 pts) : Bonus offerts = meilleure offre
- **Force du CTA** (5 pts) : CTA clair et incitatif
- **Niche de positionnement** (10 pts) : Finance, IA, Formation, Relation, Santé, Business, Digital

#### 📌 Bonus marketplace (20 points max)
- **Maketou/Chariow** : +15 pts (marketplace africain spécialisé)
- **Systeme.io** : +10 pts (indicateur de funnel structuré)
- **Gumroad/Payhip** : +5 pts (plateformes connues)

**Stockage :** Table `digital_products_scores`

## 📊 Modèles de Base de Données

### `fb_ads_raw`
- Stocke toutes les annonces Facebook scrapées
- Permet de tracker l'historique des publicités

### `digital_products_detected`
- Stocke les produits digitaux détectés depuis les landing pages
- Données complètes du produit

### `digital_products_scores`
- Stocke les scores Winner calculés
- Métriques détaillées pour chaque produit
- Relation 1-1 avec `digital_products_detected`

## 🚀 Utilisation

### Lancer le pipeline complet

```bash
cd scraper
python facebook_ads_pipeline.py
```

### Processus automatique

1. **Scraping Facebook Ads** → Recherche avec mots-clés
2. **Analyse Landing Pages** → Détection produits digitaux
3. **Déduplication** → Fusion des doublons
4. **Scoring** → Calcul des scores Winner
5. **Sauvegarde** → Base de données

### Résultat

- Tous les produits digitaux détectés dans `digital_products_detected`
- Scores Winner dans `digital_products_scores`
- **WINNERS** = Produits avec `winner_score >= 60`

## 📈 Avantages de cette approche

1. **Découverte automatique** : Pas besoin de connaître les boutiques à l'avance
2. **Données réelles** : Basé sur ce qui est réellement promu sur Facebook
3. **Détection de tendances** : Produits avec beaucoup d'annonces = tendance
4. **Scoring intelligent** : Multi-critères pour identifier les vrais winners
5. **Historique** : Suivi des changements de prix et de popularité

## 🔧 Configuration

### Pays ciblés (par défaut)
- FR, CM, SN, CI, ML, BF, BJ, TG, GA, CD

### Mots-clés prioritaires
Modifiables dans `facebook_ads_scraper.py` → `DIGITAL_PRODUCT_KEYWORDS`

### Seuil Winner
Modifiable dans `facebook_ads_pipeline.py` → `winner_score >= 60`

## 📝 Notes

- Le scraping Facebook peut être limité par les protections anti-bot
- Les landing pages peuvent nécessiter du temps de chargement
- Le scoring est basé sur des heuristiques et peut être ajusté



## 🎯 Objectif

Détecter automatiquement les produits digitaux "winners" (gagnants) en analysant les publicités Facebook qui les promouvant.

## 🔄 Architecture du Pipeline

### 1️⃣ Scraper Facebook Ads Library (`facebook_ads_scraper.py`)

**Fonctionnalités :**
- Recherche dans Facebook Ads Library avec mots-clés produits digitaux
- Extraction des données d'annonces :
  - Titre du produit
  - Description
  - Media (image/video URL)
  - Landing page URL
  - Page publicitaire
  - Date de début / Statut actif
  - Ciblage pays

**Mots-clés recherchés :**
- "formation", "e-book", "ebook", "coaching", "guide", "programme"
- "make money", "digital product", "cours", "pdf"
- "business en ligne", "revenus", "astuces"
- "Makétou", "Chariow", "Systeme.io"
- Et plus de 30 autres mots-clés

**Stockage :** Table `fb_ads_raw`

### 2️⃣ Analyseur de Landing Pages (`landing_page_analyzer.py`)

**Fonctionnalités :**
- Analyse automatique des landing pages
- Détection des domaines de produits digitaux :
  - `maketou.com` / `mymaketou.store`
  - `chariow.com` / `mychariow.shop`
  - `systeme.io` / `systeme.io/marketplace`
  - `gumroad.com`, `payhip.com`
  - `notion.so`, `drive.google.com`

**Données extraites :**
- Titre du produit
- Prix
- Nom du vendeur
- Description
- Images
- Points clés (bullet points)
- CTA (Call To Action)
- Preuves sociales (avis, commentaires, témoignages)
- Structure de la page (vidéo, garantie, bonus, countdown)

**Stockage :** Table `digital_products_detected`

### 3️⃣ Déduplication et Matching (`product_deduplicator.py`)

**Fonctionnalités :**
- Détection de produits dupliqués (même produit, URLs différentes)
- Fusion automatique des versions multiples
- Détection des changements de prix
- Historique des versions

**Algorithme :**
- Hash basé sur URL normalisée + titre
- Similarité de texte (titre + description)
- Matching intelligent

### 4️⃣ Modèle de Scoring Winner (`winner_scorer.py`)

**Score Winner (0-100) basé sur :**

#### 📌 Métriques au niveau des annonces (40 points max)
- **Nombre d'annonces** (15 pts) : Plus il y a d'annonces, plus le produit est promu
- **Nombre de pays ciblés** (10 pts) : Indicateur de portée internationale
- **Longévité des annonces** (10 pts) : Produits actifs depuis longtemps = stables
- **Nombre de pages publicitaires** (5 pts) : Plusieurs annonceurs = produit populaire

#### 📌 Métriques au niveau de la landing page (40 points max)
- **Attractivité du prix** (10 pts) : Prix optimal pour marché africain (5000-50000 FCFA)
- **Clarté de l'offre** (10 pts) : Titre + description + bullet points clairs
- **Présence de bonus** (5 pts) : Bonus offerts = meilleure offre
- **Force du CTA** (5 pts) : CTA clair et incitatif
- **Niche de positionnement** (10 pts) : Finance, IA, Formation, Relation, Santé, Business, Digital

#### 📌 Bonus marketplace (20 points max)
- **Maketou/Chariow** : +15 pts (marketplace africain spécialisé)
- **Systeme.io** : +10 pts (indicateur de funnel structuré)
- **Gumroad/Payhip** : +5 pts (plateformes connues)

**Stockage :** Table `digital_products_scores`

## 📊 Modèles de Base de Données

### `fb_ads_raw`
- Stocke toutes les annonces Facebook scrapées
- Permet de tracker l'historique des publicités

### `digital_products_detected`
- Stocke les produits digitaux détectés depuis les landing pages
- Données complètes du produit

### `digital_products_scores`
- Stocke les scores Winner calculés
- Métriques détaillées pour chaque produit
- Relation 1-1 avec `digital_products_detected`

## 🚀 Utilisation

### Lancer le pipeline complet

```bash
cd scraper
python facebook_ads_pipeline.py
```

### Processus automatique

1. **Scraping Facebook Ads** → Recherche avec mots-clés
2. **Analyse Landing Pages** → Détection produits digitaux
3. **Déduplication** → Fusion des doublons
4. **Scoring** → Calcul des scores Winner
5. **Sauvegarde** → Base de données

### Résultat

- Tous les produits digitaux détectés dans `digital_products_detected`
- Scores Winner dans `digital_products_scores`
- **WINNERS** = Produits avec `winner_score >= 60`

## 📈 Avantages de cette approche

1. **Découverte automatique** : Pas besoin de connaître les boutiques à l'avance
2. **Données réelles** : Basé sur ce qui est réellement promu sur Facebook
3. **Détection de tendances** : Produits avec beaucoup d'annonces = tendance
4. **Scoring intelligent** : Multi-critères pour identifier les vrais winners
5. **Historique** : Suivi des changements de prix et de popularité

## 🔧 Configuration

### Pays ciblés (par défaut)
- FR, CM, SN, CI, ML, BF, BJ, TG, GA, CD

### Mots-clés prioritaires
Modifiables dans `facebook_ads_scraper.py` → `DIGITAL_PRODUCT_KEYWORDS`

### Seuil Winner
Modifiable dans `facebook_ads_pipeline.py` → `winner_score >= 60`

## 📝 Notes

- Le scraping Facebook peut être limité par les protections anti-bot
- Les landing pages peuvent nécessiter du temps de chargement
- Le scoring est basé sur des heuristiques et peut être ajusté

