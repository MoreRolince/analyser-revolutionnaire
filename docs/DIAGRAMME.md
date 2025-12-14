# Diagramme d'Architecture - MarketPulse Africa

## Architecture Générale

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│                    (Next.js 14 + Tailwind)                     │
│                         Port: 3000                              │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Dashboard   │  │   Analyse    │  │ Assistant IA │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Market Radar │  │   Favoris    │  │    Admin     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API                               │
│                    (FastAPI + SQLAlchemy)                      │
│                         Port: 8000                              │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Auth API   │  │  Analyse API │  │    AI API    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Shops API  │  │ Products API │  │  Admin API   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │    Redis     │    │   RAG Engine │
│   Port:5432  │    │   Port:6379  │    │  (ChromaDB)  │
└──────────────┘    └──────────────┘    └──────────────┘
         │                    │                    │
         │                    │                    │
         └────────────────────┴────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  SCRAPER WORKER │
                    │  (Playwright)    │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   MARKETPLACES  │
                    │ CHARIOW/Maketou │
                    │   System.io     │
                    └─────────────────┘
```

## Flux d'Analyse d'URL

```
Utilisateur
    │
    │ 1. POST /api/v1/analyse {url}
    ▼
Backend API
    │
    │ 2. Créer AnalysisJob
    │ 3. Enqueue job dans Redis Queue
    ▼
Redis Queue
    │
    │ 4. Worker récupère le job
    ▼
Scraper Worker
    │
    │ 5. Détecter marketplace
    │ 6. Scraper la page (Playwright)
    │ 7. Calculer les scores
    │ 8. Générer insights IA
    │
    │ 9. Sauvegarder résultat
    ▼
PostgreSQL
    │
    │ 10. Mettre à jour AnalysisJob
    │ 11. Notifier le backend
    ▼
Backend API
    │
    │ 12. Frontend poll le statut
    ▼
Frontend
    │
    │ 13. Afficher les résultats
    ▼
Utilisateur
```

## Flux Assistant IA (RAG)

```
Utilisateur
    │
    │ 1. POST /api/v1/ai/chat {message}
    ▼
Backend API
    │
    │ 2. Générer embedding de la question
    ▼
RAG Service
    │
    │ 3. Recherche dans ChromaDB
    │ 4. Récupérer contexte similaire
    │
    │ 5. Construire prompt avec contexte
    ▼
OpenAI GPT
    │
    │ 6. Générer réponse contextuelle
    ▼
Backend API
    │
    │ 7. Sauvegarder conversation
    │ 8. Retourner réponse
    ▼
Frontend
    │
    │ 9. Afficher la réponse
    ▼
Utilisateur
```

## Base de Données - Relations

```
users
  ├── payments (1:N)
  ├── tracked_shops (1:N)
  ├── analysis_jobs (1:N)
  └── ai_messages (1:N)

shops
  ├── products (1:N)
  ├── shop_snapshots (1:N)
  └── tracked_shops (1:N)

analysis_jobs
  └── users (N:1)
```

## Technologies par Couche

### Frontend
- Next.js 14 (React)
- TypeScript
- Tailwind CSS
- ShadCN UI
- Axios
- Zustand (state management)

### Backend
- FastAPI
- SQLAlchemy (ORM)
- Alembic (migrations)
- Pydantic (validation)
- JWT (auth)
- Redis Queue

### Scraping
- Playwright
- BeautifulSoup
- Redis Queue (worker)

### IA & RAG
- ChromaDB (vector store)
- Sentence Transformers (embeddings)
- OpenAI GPT-4

### Infrastructure
- Docker & Docker Compose
- PostgreSQL 15
- Redis 7
- Nginx (optionnel pour production)

