# 🚀 Guide de Démarrage Rapide - MarketPulse Africa

## Vue d'ensemble

MarketPulse Africa est un SaaS complet d'analyse de marketplaces africaines avec :
- ✅ Analyse automatique de boutiques et produits
- ✅ Support CHARIOW, Maketou, System.io
- ✅ Assistant IA stratégique (RAG)
- ✅ Radar du marché avec tendances
- ✅ Suivi de boutiques favorites
- ✅ Panel admin complet

## Structure du Projet

```
marketpulse-africa/
├── frontend/          # Next.js 14 + Tailwind + ShadCN
├── backend/           # FastAPI + PostgreSQL
├── scraper/           # Python + Playwright + Redis Queue
├── docs/              # Documentation complète
├── docker-compose.yml # Orchestration Docker
└── README.md          # Documentation principale
```

## Démarrage Rapide (5 minutes)

### 1. Prérequis
- Docker & Docker Compose installés
- Git

### 2. Cloner et Configurer

```bash
# Cloner le projet
git clone <repo-url>
cd marketpulse-africa

# Copier le fichier d'environnement
cp .env.example .env

# Éditer .env avec vos valeurs (optionnel pour développement)
```

### 3. Démarrer avec Docker

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier que tout fonctionne
docker-compose ps
```

### 4. Initialiser la Base de Données

```bash
# Entrer dans le container backend
docker exec -it marketpulse_backend bash

# Créer les migrations
alembic revision --autogenerate -m "Initial migration"

# Appliquer les migrations
alembic upgrade head

# Créer un utilisateur admin (optionnel)
python -c "
from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash
db = SessionLocal()
admin = User(email='admin@marketpulse.africa', name='Admin', hashed_password=get_password_hash('admin123'), role='admin')
db.add(admin)
db.commit()
print('Admin créé!')
"
```

### 5. Installer Playwright (Scraper)

```bash
# Entrer dans le container scraper
docker exec -it marketpulse_scraper bash

# Installer les navigateurs
playwright install chromium
```

### 6. Accéder à l'Application

- **Frontend**: http://localhost:3000
- **API Backend**: http://localhost:8000
- **Documentation API**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Premiers Pas

### 1. Créer un Compte

1. Aller sur http://localhost:3000
2. Cliquer sur "S'inscrire"
3. Remplir le formulaire
4. Se connecter

### 2. Analyser une URL

1. Aller dans "Analyser une URL"
2. Coller une URL de boutique ou produit
3. Cliquer sur "Analyser"
4. Attendre les résultats (traitement asynchrone)

### 3. Utiliser l'Assistant IA

1. Aller dans "Assistant IA"
2. Poser une question stratégique
3. Recevoir des recommandations basées sur les données du marché

### 4. Explorer le Radar du Marché

1. Aller dans "Radar du Marché"
2. Voir les top produits et boutiques
3. Analyser les tendances

## Configuration Avancée

### Variables d'Environnement Importantes

```env
# Backend
DATABASE_URL=postgresql://marketpulse:marketpulse_password@postgres:5432/marketpulse
REDIS_URL=redis://redis:6379/0
SECRET_KEY=changez-moi-en-production

# OpenAI (pour le RAG)
OPENAI_API_KEY=sk-...

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Développement Local (sans Docker)

Voir `docs/INSTALLATION.md` pour les instructions détaillées.

## Architecture

Voir `docs/ARCHITECTURE.md` et `docs/DIAGRAMME.md` pour une vue complète de l'architecture.

## Support

- Documentation complète: `/docs`
- Issues: GitHub Issues
- Email: support@marketpulse.africa

## Prochaines Étapes

1. ✅ Configurer votre clé OpenAI pour le RAG
2. ✅ Personnaliser les scrapers pour vos marketplaces
3. ✅ Configurer les quotas selon vos besoins
4. ✅ Déployer en production avec HTTPS
5. ✅ Configurer les backups de base de données

## Notes Importantes

- Le scraper nécessite Playwright installé
- L'assistant IA nécessite une clé OpenAI
- En production, changez tous les secrets par défaut
- Configurez les backups réguliers de PostgreSQL
- Surveillez les logs pour détecter les erreurs

---

**Bon développement ! 🚀**

