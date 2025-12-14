# Guide d'Installation - MarketPulse Africa

## Prérequis

- Docker & Docker Compose
- Node.js 18+ (pour développement local)
- Python 3.11+ (pour développement local)
- PostgreSQL 15+ (si non Docker)
- Redis 7+ (si non Docker)

## Installation avec Docker (Recommandé)

### 1. Cloner le projet

```bash
git clone <repo-url>
cd marketpulse-africa
```

### 2. Configurer les variables d'environnement

```bash
cp .env.example .env
# Éditer .env avec vos valeurs
```

### 3. Démarrer les services

```bash
docker-compose up -d
```

Cela démarre:
- PostgreSQL sur le port 5432
- Redis sur le port 6379
- Backend FastAPI sur le port 8000
- Frontend Next.js sur le port 3000
- Worker scraper

### 4. Initialiser la base de données

```bash
# Entrer dans le container backend
docker exec -it marketpulse_backend bash

# Créer les migrations
alembic revision --autogenerate -m "Initial migration"

# Appliquer les migrations
alembic upgrade head
```

### 5. Installer les navigateurs Playwright

```bash
# Entrer dans le container scraper
docker exec -it marketpulse_scraper bash

# Installer les navigateurs
playwright install chromium
```

## Installation Locale (Développement)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurer .env
cp .env.example .env

# Démarrer le serveur
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install

# Configurer .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000

# Démarrer le serveur
npm run dev
```

### Scraper Worker

```bash
cd scraper
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Installer Playwright
playwright install chromium

# Démarrer le worker
python worker.py
```

## Configuration Initiale

### Créer un utilisateur admin

```python
# Dans le backend Python shell
from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash

db = SessionLocal()
admin = User(
    email="admin@marketpulse.africa",
    name="Admin",
    hashed_password=get_password_hash("admin_password"),
    role="admin"
)
db.add(admin)
db.commit()
```

### Configurer OpenAI (pour le RAG)

Ajouter votre clé API OpenAI dans `.env`:
```
OPENAI_API_KEY=sk-...
```

## Vérification

1. Accéder au frontend: http://localhost:3000
2. Accéder à l'API: http://localhost:8000/docs
3. Vérifier la santé: http://localhost:8000/health

## Dépannage

### Erreur de connexion à la base de données
- Vérifier que PostgreSQL est démarré
- Vérifier les credentials dans `.env`

### Erreur Playwright
- Installer les navigateurs: `playwright install chromium`

### Erreur Redis Queue
- Vérifier que Redis est démarré
- Vérifier la connexion dans `.env`

