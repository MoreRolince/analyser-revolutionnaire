# Architecture MarketPulse Africa

## Vue d'ensemble

MarketPulse Africa est un SaaS modulaire composé de plusieurs microservices communiquant via des APIs REST et des queues Redis.

## Composants Principaux

### 1. Frontend (Next.js 14)
- **Technologies**: Next.js 14, React, TypeScript, Tailwind CSS, ShadCN UI
- **Port**: 3000
- **Responsabilités**:
  - Interface utilisateur complète en français
  - Authentification et gestion de session
  - Dashboard utilisateur et admin
  - Visualisation des données et graphiques
  - Communication avec l'API backend

### 2. Backend API (FastAPI)
- **Technologies**: FastAPI, SQLAlchemy, PostgreSQL, Redis
- **Port**: 8000
- **Responsabilités**:
  - API REST pour toutes les opérations
  - Authentification JWT
  - Gestion des utilisateurs et abonnements
  - Endpoints pour analyses, boutiques, produits
  - Service RAG pour l'assistant IA
  - Panel admin

### 3. Scraper Service (Python + Playwright)
- **Technologies**: Python, Playwright, Redis Queue, BeautifulSoup
- **Responsabilités**:
  - Scraping asynchrone des marketplaces
  - Support CHARIOW, Maketou, System.io
  - Scraping générique pour autres URLs
  - Calcul de scores et analyses
  - Traitement en queue Redis

### 4. Base de Données (PostgreSQL)
- **Port**: 5432
- **Tables principales**:
  - `users`: Utilisateurs et abonnements
  - `payments`: Preuves de paiement
  - `shops`: Boutiques analysées
  - `products`: Produits analysés
  - `shop_snapshots`: Historique des boutiques
  - `tracked_shops`: Boutiques suivies par utilisateurs
  - `analysis_jobs`: Jobs de scraping
  - `ai_messages`: Historique des conversations IA
  - `admin_logs`: Logs d'administration

### 5. Redis Queue
- **Port**: 6379
- **Responsabilités**:
  - Queue de jobs de scraping
  - Cache des données fréquemment accédées
  - Gestion des tâches asynchrones

### 6. RAG Engine (ChromaDB + OpenAI)
- **Technologies**: ChromaDB, Sentence Transformers, OpenAI GPT
- **Responsabilités**:
  - Stockage vectoriel des connaissances
  - Génération d'embeddings
  - Recherche sémantique
  - Génération de réponses contextuelles

## Flux de Données

### Analyse d'URL
1. Utilisateur soumet une URL via le frontend
2. Frontend envoie la requête au backend API
3. Backend crée un job dans la queue Redis
4. Worker scraper traite le job de manière asynchrone
5. Scraper détecte le marketplace et scrape la page
6. Calcul des scores et génération d'insights IA
7. Résultat sauvegardé en base de données
8. Frontend poll le statut ou reçoit une notification

### Assistant IA
1. Utilisateur envoie un message via le frontend
2. Backend génère un embedding de la question
3. Recherche dans ChromaDB pour contexte similaire
4. Construction du prompt avec contexte
5. Appel à OpenAI GPT pour génération de réponse
6. Réponse retournée à l'utilisateur
7. Conversation sauvegardée en base

## Sécurité

- Authentification JWT avec expiration
- Hashage des mots de passe avec bcrypt
- Validation des quotas par utilisateur
- Rôles utilisateur/admin
- CORS configuré pour le frontend
- Variables d'environnement pour secrets

## Déploiement

Le projet utilise Docker Compose pour orchestrer tous les services:
- PostgreSQL avec volume persistant
- Redis avec volume persistant
- Backend FastAPI avec hot-reload
- Frontend Next.js avec hot-reload
- Worker scraper avec Redis Queue

## Scalabilité

- Workers de scraping peuvent être multipliés
- Base de données peut être répliquée
- Redis peut être clusterisé
- Frontend peut être servi via CDN
- Backend peut être load-balancé

