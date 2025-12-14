# Comment lancer le pipeline Facebook Ads

## 📋 Prérequis

1. **Base de données PostgreSQL** doit être lancée
2. **Python 3.8+** avec les dépendances installées
3. **Playwright** doit être installé

## 🔧 Installation des dépendances

```bash
# Activer l'environnement virtuel (si vous en avez un)
# Windows:
.venv\Scripts\activate

# Installer Playwright si ce n'est pas déjà fait
pip install playwright
playwright install chromium
```

## 🗄️ Créer les tables de base de données

Avant de lancer le pipeline, vous devez créer les nouvelles tables :

### Option 1: Via Alembic (recommandé)

```bash
cd backend
alembic upgrade head
```

### Option 2: Création manuelle

Si Alembic n'est pas configuré, vous pouvez créer les tables directement :

```bash
cd backend
python -c "
from app.database import engine
from app.models import FacebookAdRaw, DigitalProductDetected, DigitalProductScore
from app.database import Base
Base.metadata.create_all(bind=engine)
print('✅ Tables créées!')
"
```

## 🚀 Lancer le pipeline

### Méthode 1: Script direct

```bash
cd scraper
python facebook_ads_pipeline.py
```

### Méthode 2: Script simplifié

```bash
cd scraper
python run_facebook_pipeline.py
```

## 📊 Ce qui va se passer

Le pipeline va exécuter 4 étapes :

1. **Scraping Facebook Ads Library** (5-10 minutes)
   - Recherche avec mots-clés produits digitaux
   - Scrape les annonces Facebook
   - Sauvegarde dans `fb_ads_raw`

2. **Analyse des landing pages** (10-20 minutes selon le nombre)
   - Analyse chaque landing page détectée
   - Extrait les données du produit
   - Sauvegarde dans `digital_products_detected`

3. **Déduplication** (1-2 minutes)
   - Détecte les produits dupliqués
   - Fusionne les versions multiples
   - Détecte les changements de prix

4. **Calcul des scores Winner** (2-5 minutes)
   - Calcule le score Winner (0-100) pour chaque produit
   - Sauvegarde dans `digital_products_scores`

## ✅ Vérifier les résultats

### Dans la base de données

```sql
-- Voir les annonces scrapées
SELECT COUNT(*) FROM fb_ads_raw;

-- Voir les produits détectés
SELECT COUNT(*) FROM digital_products_detected;

-- Voir les WINNERS (score >= 60)
SELECT 
    d.product_title,
    d.price,
    d.marketplace,
    s.winner_score
FROM digital_products_detected d
JOIN digital_products_scores s ON s.product_id = d.id
WHERE s.winner_score >= 60
ORDER BY s.winner_score DESC
LIMIT 20;
```

### Via Python

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import DigitalProductDetected, DigitalProductScore

DATABASE_URL = "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Compter les winners
winners = db.query(DigitalProductScore).filter(
    DigitalProductScore.winner_score >= 60
).count()

print(f"🏆 {winners} WINNERS détectés!")

# Voir les top 10
top_products = db.query(DigitalProductDetected, DigitalProductScore).join(
    DigitalProductScore, DigitalProductScore.product_id == DigitalProductDetected.id
).order_by(DigitalProductScore.winner_score.desc()).limit(10).all()

for product, score in top_products:
    print(f"{product.product_title[:50]} - Score: {score.winner_score:.1f}")
```

## ⚙️ Configuration

### Modifier les mots-clés

Éditez `scraper/services/facebook_ads_scraper.py` :
```python
DIGITAL_PRODUCT_KEYWORDS = [
    "formation", "ebook", "coaching",  # Vos mots-clés
    # ...
]
```

### Modifier les pays ciblés

Éditez `scraper/facebook_ads_pipeline.py` :
```python
countries = ["FR", "CM", "SN", "CI", "ML"]  # Vos pays
```

### Modifier le seuil Winner

Éditez `scraper/facebook_ads_pipeline.py` :
```python
winners = db.query(DigitalProductScore).filter(
    DigitalProductScore.winner_score >= 60  # Votre seuil
).count()
```

## 🐛 Dépannage

### Erreur: "No module named 'app'"
```bash
# S'assurer d'être dans le bon répertoire
cd scraper
# Vérifier que le chemin backend est dans sys.path
```

### Erreur: "Table does not exist"
```bash
# Créer les tables (voir section "Créer les tables")
```

### Erreur: "Playwright browser not found"
```bash
playwright install chromium
```

### Facebook bloque le scraping
- Le scraping Facebook peut être limité
- Utilisez des pauses plus longues entre les requêtes
- Modifiez `await asyncio.sleep(2)` dans le code

## 📝 Notes

- Le pipeline peut prendre 20-30 minutes pour compléter
- Le scraping Facebook peut être ralenti par les protections anti-bot
- Les résultats dépendent de la disponibilité des annonces Facebook



## 📋 Prérequis

1. **Base de données PostgreSQL** doit être lancée
2. **Python 3.8+** avec les dépendances installées
3. **Playwright** doit être installé

## 🔧 Installation des dépendances

```bash
# Activer l'environnement virtuel (si vous en avez un)
# Windows:
.venv\Scripts\activate

# Installer Playwright si ce n'est pas déjà fait
pip install playwright
playwright install chromium
```

## 🗄️ Créer les tables de base de données

Avant de lancer le pipeline, vous devez créer les nouvelles tables :

### Option 1: Via Alembic (recommandé)

```bash
cd backend
alembic upgrade head
```

### Option 2: Création manuelle

Si Alembic n'est pas configuré, vous pouvez créer les tables directement :

```bash
cd backend
python -c "
from app.database import engine
from app.models import FacebookAdRaw, DigitalProductDetected, DigitalProductScore
from app.database import Base
Base.metadata.create_all(bind=engine)
print('✅ Tables créées!')
"
```

## 🚀 Lancer le pipeline

### Méthode 1: Script direct

```bash
cd scraper
python facebook_ads_pipeline.py
```

### Méthode 2: Script simplifié

```bash
cd scraper
python run_facebook_pipeline.py
```

## 📊 Ce qui va se passer

Le pipeline va exécuter 4 étapes :

1. **Scraping Facebook Ads Library** (5-10 minutes)
   - Recherche avec mots-clés produits digitaux
   - Scrape les annonces Facebook
   - Sauvegarde dans `fb_ads_raw`

2. **Analyse des landing pages** (10-20 minutes selon le nombre)
   - Analyse chaque landing page détectée
   - Extrait les données du produit
   - Sauvegarde dans `digital_products_detected`

3. **Déduplication** (1-2 minutes)
   - Détecte les produits dupliqués
   - Fusionne les versions multiples
   - Détecte les changements de prix

4. **Calcul des scores Winner** (2-5 minutes)
   - Calcule le score Winner (0-100) pour chaque produit
   - Sauvegarde dans `digital_products_scores`

## ✅ Vérifier les résultats

### Dans la base de données

```sql
-- Voir les annonces scrapées
SELECT COUNT(*) FROM fb_ads_raw;

-- Voir les produits détectés
SELECT COUNT(*) FROM digital_products_detected;

-- Voir les WINNERS (score >= 60)
SELECT 
    d.product_title,
    d.price,
    d.marketplace,
    s.winner_score
FROM digital_products_detected d
JOIN digital_products_scores s ON s.product_id = d.id
WHERE s.winner_score >= 60
ORDER BY s.winner_score DESC
LIMIT 20;
```

### Via Python

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import DigitalProductDetected, DigitalProductScore

DATABASE_URL = "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Compter les winners
winners = db.query(DigitalProductScore).filter(
    DigitalProductScore.winner_score >= 60
).count()

print(f"🏆 {winners} WINNERS détectés!")

# Voir les top 10
top_products = db.query(DigitalProductDetected, DigitalProductScore).join(
    DigitalProductScore, DigitalProductScore.product_id == DigitalProductDetected.id
).order_by(DigitalProductScore.winner_score.desc()).limit(10).all()

for product, score in top_products:
    print(f"{product.product_title[:50]} - Score: {score.winner_score:.1f}")
```

## ⚙️ Configuration

### Modifier les mots-clés

Éditez `scraper/services/facebook_ads_scraper.py` :
```python
DIGITAL_PRODUCT_KEYWORDS = [
    "formation", "ebook", "coaching",  # Vos mots-clés
    # ...
]
```

### Modifier les pays ciblés

Éditez `scraper/facebook_ads_pipeline.py` :
```python
countries = ["FR", "CM", "SN", "CI", "ML"]  # Vos pays
```

### Modifier le seuil Winner

Éditez `scraper/facebook_ads_pipeline.py` :
```python
winners = db.query(DigitalProductScore).filter(
    DigitalProductScore.winner_score >= 60  # Votre seuil
).count()
```

## 🐛 Dépannage

### Erreur: "No module named 'app'"
```bash
# S'assurer d'être dans le bon répertoire
cd scraper
# Vérifier que le chemin backend est dans sys.path
```

### Erreur: "Table does not exist"
```bash
# Créer les tables (voir section "Créer les tables")
```

### Erreur: "Playwright browser not found"
```bash
playwright install chromium
```

### Facebook bloque le scraping
- Le scraping Facebook peut être limité
- Utilisez des pauses plus longues entre les requêtes
- Modifiez `await asyncio.sleep(2)` dans le code

## 📝 Notes

- Le pipeline peut prendre 20-30 minutes pour compléter
- Le scraping Facebook peut être ralenti par les protections anti-bot
- Les résultats dépendent de la disponibilité des annonces Facebook

