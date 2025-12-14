# 🔍 Explication du Système de Scraping - MarketPulse Africa

## 📖 Qu'est-ce que le Scraping ?

Le **scraping** (ou "web scraping") est une technique qui permet d'extraire automatiquement des données depuis des sites web. Dans notre cas, nous scrapons les marketplaces africaines (Chariow, Maketou, Systeme.io) pour collecter des informations sur les boutiques et produits.

## 🎯 Ce que fait notre Scraper

### 1. **Découverte de Boutiques** 🔍

Le scraper commence par **découvrir de nouvelles boutiques** en visitant les pages de listing des marketplaces :

```
📋 Pages visitées :
- https://chariow.com/shops
- https://chariow.com/vendors
- https://maketou.com/stores

🔎 Ce qu'il fait :
1. Ouvre la page avec un navigateur (Playwright)
2. Attend que la page charge complètement
3. Cherche tous les liens vers les boutiques
4. Extrait les URLs (ex: https://numerik.mymaketou.store/)
5. Stocke ces URLs pour les scraper ensuite
```

### 2. **Scraping d'une Boutique** 🏪

Pour chaque boutique découverte, le scraper :

#### Étape 1 : Chargement de la Page
```
🌐 URL : https://numerik.mymaketou.store/
📥 Actions :
- Ouvre la page avec Playwright (navigateur automatisé)
- Attend que tout le contenu charge (images, JavaScript)
- Récupère le code HTML complet
```

#### Étape 2 : Extraction des Données
```
📊 Données extraites :

🏪 Informations de la Boutique :
- Nom : "LuminaHub"
- URL : https://numerik.mymaketou.store/
- Nombre de produits visibles

📦 Pour chaque Produit trouvé :
- Nom du produit : "Agrobusiness Simplifié"
- Prix : 5.31 $ (converti en FCFA)
- URL du produit
- Image du produit
- Description (si disponible)
```

#### Étape 3 : Calcul des Scores
```
⭐ Calcul automatique :

Pour la Boutique :
- Score basé sur :
  * Nombre de produits
  * Diversité des prix
  * Présence sur la marketplace
  * Qualité des descriptions

Pour chaque Produit :
- Score basé sur :
  * Prix du produit
  * Potentiel de ventes estimé
  * Niveau de concurrence
  * Tendance du marché
```

#### Étape 4 : Estimation des Revenus
```
💰 Calculs automatiques :

Ventes estimées :
- Basé sur le nombre de produits
- Basé sur les prix moyens
- Basé sur les tendances du marché

Revenus estimés :
- Ventes min/max par mois
- CA estimé en FCFA
- Projections sur 30 jours
```

### 3. **Sauvegarde en Base de Données** 💾

Toutes les données extraites sont sauvegardées dans PostgreSQL :

```sql
-- Table : shops_global
INSERT INTO shops_global (
    shop_name,           -- "LuminaHub"
    shop_url,            -- "https://numerik.mymaketou.store/"
    marketplace,         -- "maketou"
    score_global,        -- 85.5
    revenue_est_min,     -- 250000
    revenue_est_max,     -- 750000
    winners_count,       -- 12
    last_scraped_at      -- 2025-01-15 10:30:00
);

-- Table : products_global
INSERT INTO products_global (
    product_name,        -- "Agrobusiness Simplifié"
    shop_name,           -- "LuminaHub"
    product_url,         -- URL du produit
    price,               -- 3186 (en FCFA)
    score_winner,        -- 88.5
    sales_est_min,       -- 25
    sales_est_max,       -- 35
    revenue_est_min,     -- 55650
    revenue_est_max,     -- 111510
    category,            -- "Électronique"
    last_scraped_at      -- 2025-01-15 10:30:00
);
```

## ⏰ Quand le Scraping se Déclenche ?

### Scraping Continu (Automatique)

Le scraper tourne **en permanence** et exécute des cycles :

```
🔄 Cycle toutes les 6 heures :
1. Récupère toutes les boutiques scrapées il y a plus de 6h
2. Scrape chaque boutique pour mettre à jour les données
3. Met à jour les produits et scores
4. Sauvegarde dans la base de données

🔍 Découverte toutes les 24 heures :
1. Visite les pages de listing
2. Découvre de nouvelles boutiques
3. Scrape les nouvelles boutiques
4. Les ajoute à la base de données
```

### Scraping Manuel (Via API)

Un admin peut déclencher un scraping manuellement :

```bash
POST /api/v1/scraper/run-cycle
```

## 🛠️ Comment ça Fonctionne Techniquement ?

### 1. Playwright (Navigateur Automatisé)

```python
# Le scraper utilise Playwright pour simuler un vrai navigateur
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)  # Navigateur invisible
    page = await browser.new_page()
    
    # Visite la page
    await page.goto("https://numerik.mymaketou.store/")
    
    # Attend que tout charge
    await page.wait_for_timeout(2000)
    
    # Récupère le HTML
    content = await page.content()
```

### 2. BeautifulSoup (Parsing HTML)

```python
# Parse le HTML pour extraire les données
soup = BeautifulSoup(content, 'lxml')

# Trouve tous les produits
products = soup.find_all('div', class_='product')

# Pour chaque produit
for product in products:
    name = product.find('h2').text
    price = product.find('.price').text
    # ... etc
```

### 3. Calcul des Scores

```python
# Utilise des algorithmes pour calculer les scores
def calculate_shop_score(shop_data):
    score = 0
    
    # Points basés sur le nombre de produits
    if shop_data['product_count'] > 20:
        score += 30
    
    # Points basés sur les prix
    if avg_price > 0:
        score += 25
    
    # Points basés sur la diversité
    # ... etc
    
    return min(score, 100)  # Score sur 100
```

## 📊 Exemple Concret : Scraping d'une Boutique

### Boutique : LuminaHub (Maketou)

```
1️⃣ DÉCOUVERTE
   URL trouvée : https://numerik.mymaketou.store/
   Source : Page de listing Maketou

2️⃣ SCRAPING
   ✅ Page chargée
   ✅ 10 produits trouvés
   
   Produits extraits :
   - "Agrobusiness Simplifié" - 5.31$ (3186 FCFA)
   - "Mon Ventre Portera la Vie" - 6.91$ (4146 FCFA)
   - "PRIÈRE DE PROTECTION" - 5.14$ (3084 FCFA)
   - ... (7 autres produits)

3️⃣ CALCULS
   Score boutique : 85.5/100
   Ventes estimées : 80-120/mois
   CA estimé : 250,000 - 750,000 FCFA/mois
   Winners : 8 produits avec score > 70

4️⃣ SAUVEGARDE
   ✅ Boutique sauvegardée dans shops_global
   ✅ 8 produits sauvegardés dans products_global
   ✅ Scores calculés et stockés
```

## 🎯 Résultat Final

Après le scraping, les utilisateurs peuvent :

1. **Voir les Top Boutiques** dans le dashboard
2. **Voir les Top Produits Winners** dans le catalog
3. **Analyser une boutique** avec les vraies données
4. **Suivre l'évolution** des boutiques dans le temps

## 🔄 Mise à Jour Continue

Le scraper met à jour automatiquement :

```
⏰ Toutes les 6 heures :
- Re-scrape les boutiques existantes
- Met à jour les prix si changés
- Met à jour les scores
- Ajoute les nouveaux produits
- Supprime les produits supprimés

⏰ Toutes les 24 heures :
- Découvre de nouvelles boutiques
- Scrape les nouvelles boutiques
- Les ajoute à la base de données
```

## 🛡️ Sécurité et Respect

Le scraper :
- ✅ Respecte les délais entre requêtes (2 secondes)
- ✅ Limite le nombre de requêtes par cycle
- ✅ Gère les erreurs gracieusement
- ✅ Ne surcharge pas les serveurs
- ✅ Utilise un navigateur réel (pas de bot simple)

## 📈 Avantages

1. **Données Réelles** : Pas de données fictives, tout vient des vraies boutiques
2. **Toujours à Jour** : Mise à jour automatique toutes les 6 heures
3. **Découverte Automatique** : Trouve de nouvelles boutiques automatiquement
4. **Scores Fiables** : Basés sur les vraies données extraites
5. **Scalable** : Peut scraper des centaines de boutiques

## 🚀 En Résumé

Le scraping fonctionne comme un **robot qui visite automatiquement les boutiques** toutes les 6 heures, **extrait les vraies données** (produits, prix, descriptions), **calcule des scores** basés sur ces données, et **sauvegarde tout dans la base de données** pour que les utilisateurs aient toujours accès aux **données réelles et à jour** des marketplaces africaines.

C'est comme avoir un **assistant qui surveille en permanence** toutes les boutiques et vous tient informé des nouveautés et changements ! 🎯





## 📖 Qu'est-ce que le Scraping ?

Le **scraping** (ou "web scraping") est une technique qui permet d'extraire automatiquement des données depuis des sites web. Dans notre cas, nous scrapons les marketplaces africaines (Chariow, Maketou, Systeme.io) pour collecter des informations sur les boutiques et produits.

## 🎯 Ce que fait notre Scraper

### 1. **Découverte de Boutiques** 🔍

Le scraper commence par **découvrir de nouvelles boutiques** en visitant les pages de listing des marketplaces :

```
📋 Pages visitées :
- https://chariow.com/shops
- https://chariow.com/vendors
- https://maketou.com/stores

🔎 Ce qu'il fait :
1. Ouvre la page avec un navigateur (Playwright)
2. Attend que la page charge complètement
3. Cherche tous les liens vers les boutiques
4. Extrait les URLs (ex: https://numerik.mymaketou.store/)
5. Stocke ces URLs pour les scraper ensuite
```

### 2. **Scraping d'une Boutique** 🏪

Pour chaque boutique découverte, le scraper :

#### Étape 1 : Chargement de la Page
```
🌐 URL : https://numerik.mymaketou.store/
📥 Actions :
- Ouvre la page avec Playwright (navigateur automatisé)
- Attend que tout le contenu charge (images, JavaScript)
- Récupère le code HTML complet
```

#### Étape 2 : Extraction des Données
```
📊 Données extraites :

🏪 Informations de la Boutique :
- Nom : "LuminaHub"
- URL : https://numerik.mymaketou.store/
- Nombre de produits visibles

📦 Pour chaque Produit trouvé :
- Nom du produit : "Agrobusiness Simplifié"
- Prix : 5.31 $ (converti en FCFA)
- URL du produit
- Image du produit
- Description (si disponible)
```

#### Étape 3 : Calcul des Scores
```
⭐ Calcul automatique :

Pour la Boutique :
- Score basé sur :
  * Nombre de produits
  * Diversité des prix
  * Présence sur la marketplace
  * Qualité des descriptions

Pour chaque Produit :
- Score basé sur :
  * Prix du produit
  * Potentiel de ventes estimé
  * Niveau de concurrence
  * Tendance du marché
```

#### Étape 4 : Estimation des Revenus
```
💰 Calculs automatiques :

Ventes estimées :
- Basé sur le nombre de produits
- Basé sur les prix moyens
- Basé sur les tendances du marché

Revenus estimés :
- Ventes min/max par mois
- CA estimé en FCFA
- Projections sur 30 jours
```

### 3. **Sauvegarde en Base de Données** 💾

Toutes les données extraites sont sauvegardées dans PostgreSQL :

```sql
-- Table : shops_global
INSERT INTO shops_global (
    shop_name,           -- "LuminaHub"
    shop_url,            -- "https://numerik.mymaketou.store/"
    marketplace,         -- "maketou"
    score_global,        -- 85.5
    revenue_est_min,     -- 250000
    revenue_est_max,     -- 750000
    winners_count,       -- 12
    last_scraped_at      -- 2025-01-15 10:30:00
);

-- Table : products_global
INSERT INTO products_global (
    product_name,        -- "Agrobusiness Simplifié"
    shop_name,           -- "LuminaHub"
    product_url,         -- URL du produit
    price,               -- 3186 (en FCFA)
    score_winner,        -- 88.5
    sales_est_min,       -- 25
    sales_est_max,       -- 35
    revenue_est_min,     -- 55650
    revenue_est_max,     -- 111510
    category,            -- "Électronique"
    last_scraped_at      -- 2025-01-15 10:30:00
);
```

## ⏰ Quand le Scraping se Déclenche ?

### Scraping Continu (Automatique)

Le scraper tourne **en permanence** et exécute des cycles :

```
🔄 Cycle toutes les 6 heures :
1. Récupère toutes les boutiques scrapées il y a plus de 6h
2. Scrape chaque boutique pour mettre à jour les données
3. Met à jour les produits et scores
4. Sauvegarde dans la base de données

🔍 Découverte toutes les 24 heures :
1. Visite les pages de listing
2. Découvre de nouvelles boutiques
3. Scrape les nouvelles boutiques
4. Les ajoute à la base de données
```

### Scraping Manuel (Via API)

Un admin peut déclencher un scraping manuellement :

```bash
POST /api/v1/scraper/run-cycle
```

## 🛠️ Comment ça Fonctionne Techniquement ?

### 1. Playwright (Navigateur Automatisé)

```python
# Le scraper utilise Playwright pour simuler un vrai navigateur
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)  # Navigateur invisible
    page = await browser.new_page()
    
    # Visite la page
    await page.goto("https://numerik.mymaketou.store/")
    
    # Attend que tout charge
    await page.wait_for_timeout(2000)
    
    # Récupère le HTML
    content = await page.content()
```

### 2. BeautifulSoup (Parsing HTML)

```python
# Parse le HTML pour extraire les données
soup = BeautifulSoup(content, 'lxml')

# Trouve tous les produits
products = soup.find_all('div', class_='product')

# Pour chaque produit
for product in products:
    name = product.find('h2').text
    price = product.find('.price').text
    # ... etc
```

### 3. Calcul des Scores

```python
# Utilise des algorithmes pour calculer les scores
def calculate_shop_score(shop_data):
    score = 0
    
    # Points basés sur le nombre de produits
    if shop_data['product_count'] > 20:
        score += 30
    
    # Points basés sur les prix
    if avg_price > 0:
        score += 25
    
    # Points basés sur la diversité
    # ... etc
    
    return min(score, 100)  # Score sur 100
```

## 📊 Exemple Concret : Scraping d'une Boutique

### Boutique : LuminaHub (Maketou)

```
1️⃣ DÉCOUVERTE
   URL trouvée : https://numerik.mymaketou.store/
   Source : Page de listing Maketou

2️⃣ SCRAPING
   ✅ Page chargée
   ✅ 10 produits trouvés
   
   Produits extraits :
   - "Agrobusiness Simplifié" - 5.31$ (3186 FCFA)
   - "Mon Ventre Portera la Vie" - 6.91$ (4146 FCFA)
   - "PRIÈRE DE PROTECTION" - 5.14$ (3084 FCFA)
   - ... (7 autres produits)

3️⃣ CALCULS
   Score boutique : 85.5/100
   Ventes estimées : 80-120/mois
   CA estimé : 250,000 - 750,000 FCFA/mois
   Winners : 8 produits avec score > 70

4️⃣ SAUVEGARDE
   ✅ Boutique sauvegardée dans shops_global
   ✅ 8 produits sauvegardés dans products_global
   ✅ Scores calculés et stockés
```

## 🎯 Résultat Final

Après le scraping, les utilisateurs peuvent :

1. **Voir les Top Boutiques** dans le dashboard
2. **Voir les Top Produits Winners** dans le catalog
3. **Analyser une boutique** avec les vraies données
4. **Suivre l'évolution** des boutiques dans le temps

## 🔄 Mise à Jour Continue

Le scraper met à jour automatiquement :

```
⏰ Toutes les 6 heures :
- Re-scrape les boutiques existantes
- Met à jour les prix si changés
- Met à jour les scores
- Ajoute les nouveaux produits
- Supprime les produits supprimés

⏰ Toutes les 24 heures :
- Découvre de nouvelles boutiques
- Scrape les nouvelles boutiques
- Les ajoute à la base de données
```

## 🛡️ Sécurité et Respect

Le scraper :
- ✅ Respecte les délais entre requêtes (2 secondes)
- ✅ Limite le nombre de requêtes par cycle
- ✅ Gère les erreurs gracieusement
- ✅ Ne surcharge pas les serveurs
- ✅ Utilise un navigateur réel (pas de bot simple)

## 📈 Avantages

1. **Données Réelles** : Pas de données fictives, tout vient des vraies boutiques
2. **Toujours à Jour** : Mise à jour automatique toutes les 6 heures
3. **Découverte Automatique** : Trouve de nouvelles boutiques automatiquement
4. **Scores Fiables** : Basés sur les vraies données extraites
5. **Scalable** : Peut scraper des centaines de boutiques

## 🚀 En Résumé

Le scraping fonctionne comme un **robot qui visite automatiquement les boutiques** toutes les 6 heures, **extrait les vraies données** (produits, prix, descriptions), **calcule des scores** basés sur ces données, et **sauvegarde tout dans la base de données** pour que les utilisateurs aient toujours accès aux **données réelles et à jour** des marketplaces africaines.

C'est comme avoir un **assistant qui surveille en permanence** toutes les boutiques et vous tient informé des nouveautés et changements ! 🎯



