# 🚀 Comment lancer le pipeline Facebook Ads

## Étape 1: Créer les tables de base de données

```bash
cd scraper
python create_tables.py
```

Cela va créer les 3 tables nécessaires :
- `fb_ads_raw` (annonces Facebook)
- `digital_products_detected` (produits détectés)
- `digital_products_scores` (scores Winner)

## Étape 2: Lancer le pipeline

```bash
cd scraper
python facebook_ads_pipeline.py
```

## 📊 Ce qui va se passer

Le pipeline va :

1. **Scraper Facebook Ads Library** (5-10 min)
   - Recherche avec mots-clés : "formation", "ebook", "coaching", etc.
   - Extrait les annonces Facebook
   - Sauvegarde dans `fb_ads_raw`

2. **Analyser les landing pages** (10-20 min)
   - Analyse chaque landing page détectée
   - Extrait : titre, prix, description, images, etc.
   - Sauvegarde dans `digital_products_detected`

3. **Dédupliquer les produits** (1-2 min)
   - Détecte les doublons
   - Fusionne les versions multiples

4. **Calculer les scores Winner** (2-5 min)
   - Score 0-100 pour chaque produit
   - Sauvegarde dans `digital_products_scores`

## ✅ Résultat

À la fin, vous aurez :
- Tous les produits digitaux détectés
- Les scores Winner calculés
- Les **WINNERS** (score >= 60) identifiés

## 🔍 Vérifier les résultats

### Compter les winners

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import DigitalProductScore

DATABASE_URL = "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

winners = db.query(DigitalProductScore).filter(
    DigitalProductScore.winner_score >= 60
).count()

print(f"🏆 {winners} WINNERS détectés!")
```

## ⚙️ Configuration

### Modifier les mots-clés

Éditez `scraper/services/facebook_ads_scraper.py` ligne 20-30

### Modifier les pays

Éditez `scraper/facebook_ads_pipeline.py` ligne 280

## 🐛 Problèmes courants

### "Table does not exist"
→ Lancez `python create_tables.py` d'abord

### "Playwright browser not found"
→ `playwright install chromium`

### Facebook bloque
→ Normal, le scraping peut être limité. Le script continue avec les annonces disponibles.



## Étape 1: Créer les tables de base de données

```bash
cd scraper
python create_tables.py
```

Cela va créer les 3 tables nécessaires :
- `fb_ads_raw` (annonces Facebook)
- `digital_products_detected` (produits détectés)
- `digital_products_scores` (scores Winner)

## Étape 2: Lancer le pipeline

```bash
cd scraper
python facebook_ads_pipeline.py
```

## 📊 Ce qui va se passer

Le pipeline va :

1. **Scraper Facebook Ads Library** (5-10 min)
   - Recherche avec mots-clés : "formation", "ebook", "coaching", etc.
   - Extrait les annonces Facebook
   - Sauvegarde dans `fb_ads_raw`

2. **Analyser les landing pages** (10-20 min)
   - Analyse chaque landing page détectée
   - Extrait : titre, prix, description, images, etc.
   - Sauvegarde dans `digital_products_detected`

3. **Dédupliquer les produits** (1-2 min)
   - Détecte les doublons
   - Fusionne les versions multiples

4. **Calculer les scores Winner** (2-5 min)
   - Score 0-100 pour chaque produit
   - Sauvegarde dans `digital_products_scores`

## ✅ Résultat

À la fin, vous aurez :
- Tous les produits digitaux détectés
- Les scores Winner calculés
- Les **WINNERS** (score >= 60) identifiés

## 🔍 Vérifier les résultats

### Compter les winners

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import DigitalProductScore

DATABASE_URL = "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

winners = db.query(DigitalProductScore).filter(
    DigitalProductScore.winner_score >= 60
).count()

print(f"🏆 {winners} WINNERS détectés!")
```

## ⚙️ Configuration

### Modifier les mots-clés

Éditez `scraper/services/facebook_ads_scraper.py` ligne 20-30

### Modifier les pays

Éditez `scraper/facebook_ads_pipeline.py` ligne 280

## 🐛 Problèmes courants

### "Table does not exist"
→ Lancez `python create_tables.py` d'abord

### "Playwright browser not found"
→ `playwright install chromium`

### Facebook bloque
→ Normal, le scraping peut être limité. Le script continue avec les annonces disponibles.

