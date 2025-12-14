# MarketPulse Africa - Système 45K

SaaS professionnel d'analyse automatique des marketplaces africaines.

## 🏗️ Architecture

```
marketpulse-africa/
├── frontend/          # Next.js 14 + Tailwind + ShadCN
├── backend/           # FastAPI
├── scraper/           # Python + Playwright + Redis Queue
├── rag-engine/        # ChromaDB + Embeddings + GPT
├── docker-compose.yml # Orchestration complète
└── docs/              # Documentation
```

## 🚀 Démarrage Rapide

### Prérequis
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+

### Installation

```bash
# Cloner le projet
git clone <repo-url>
cd marketpulse-africa

# Démarrer tous les services
docker-compose up -d

# Installer les dépendances frontend
cd frontend
npm install

# Installer les dépendances backend
cd ../backend
pip install -r requirements.txt

# Installer les dépendances scraper
cd ../scraper
pip install -r requirements.txt
```

## 📋 Fonctionnalités

- ✅ Analyse automatique de boutiques et produits
- ✅ Support CHARIOW, Maketou, System.io
- ✅ Radar du marché avec top produits/boutiques
- ✅ Assistant IA stratégique (RAG)
- ✅ Suivi de boutiques avec alertes
- ✅ Gestion d'abonnements
- ✅ Panel admin complet

## 🔧 Technologies

- **Frontend**: Next.js 14, Tailwind CSS, ShadCN UI
- **Backend**: FastAPI, PostgreSQL, Redis
- **Scraping**: Playwright, Python
- **IA**: ChromaDB, OpenAI/Open Source LLM
- **Queue**: Redis Queue (RQ)

## 📝 Documentation

Voir `/docs` pour la documentation complète.

