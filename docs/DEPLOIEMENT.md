# Guide de Déploiement - MarketPulse Africa

Ce guide présente plusieurs solutions de déploiement adaptées à votre projet SaaS.

## 📋 Architecture du Projet

Votre projet comprend :
- **Frontend** : Next.js 14 (port 3000)
- **Backend** : FastAPI (port 8000)
- **Base de données** : PostgreSQL 15
- **Cache/Queue** : Redis 7
- **Workers** : Scrapers Python avec Playwright (processus lourds)

---

## 🎯 Options de Déploiement

### Option 1 : VPS (Hetzner / OVH / DigitalOcean) ⭐ RECOMMANDÉ

**Prix** : 15-50€/mois  
**Complexité** : Moyenne  
**Avantages** : Contrôle total, bon rapport qualité/prix, Docker Compose prêt

#### Configuration Recommandée
- **CPU** : 4-8 cores (Playwright est gourmand)
- **RAM** : 8-16 GB (Playwright nécessite beaucoup de mémoire)
- **Stockage** : 100-200 GB SSD
- **OS** : Ubuntu 22.04 LTS

#### Étapes de Déploiement

1. **Préparer le serveur**
```bash
# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer Docker et Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **Cloner et configurer le projet**
```bash
# Cloner le projet
git clone <votre-repo> /opt/marketpulse
cd /opt/marketpulse

# Créer le fichier .env de production
cp .env.example .env
nano .env
```

3. **Variables d'environnement (.env)**
```env
# Base de données
DATABASE_URL=postgresql://marketpulse:CHANGEZ_MOI_POSTGRES_PASSWORD@postgres:5432/marketpulse
POSTGRES_PASSWORD=CHANGEZ_MOI_POSTGRES_PASSWORD

# Sécurité
SECRET_KEY=GENERATEZ_UNE_CLE_SECRETE_ALEATOIRE_32_CARACTERES_MINIMUM
ENVIRONMENT=production

# Redis
REDIS_URL=redis://redis:6379/0

# Frontend
NEXT_PUBLIC_API_URL=https://api.votre-domaine.com

# Domaines autorisés (CORS)
ALLOWED_ORIGINS=https://votre-domaine.com,https://www.votre-domaine.com
```

4. **Docker Compose Production**
Créer `docker-compose.prod.yml` :
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: marketpulse_postgres
    environment:
      POSTGRES_DB: marketpulse
      POSTGRES_USER: marketpulse
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups  # Pour les backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U marketpulse"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: marketpulse_redis
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: marketpulse_backend
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: production
      ALLOWED_ORIGINS: ${ALLOWED_ORIGINS}
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod  # Voir ci-dessous
    container_name: marketpulse_frontend
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}
    restart: unless-stopped
    depends_on:
      - backend

  scraper_worker:
    build:
      context: ./scraper
      dockerfile: Dockerfile
    container_name: marketpulse_scraper
    environment:
      REDIS_URL: ${REDIS_URL}
      DATABASE_URL: ${DATABASE_URL}
    restart: unless-stopped
    depends_on:
      - redis
      - postgres
      - backend

  continuous_scraper:
    build:
      context: ./scraper
      dockerfile: Dockerfile
    container_name: marketpulse_continuous_scraper
    environment:
      DATABASE_URL: ${DATABASE_URL}
      SCRAPE_INTERVAL_HOURS: 6
    restart: unless-stopped
    depends_on:
      - postgres

volumes:
  postgres_data:
  redis_data:
```

5. **Dockerfile Frontend Production**
Créer `frontend/Dockerfile.prod` :
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

Mettre à jour `frontend/next.config.js` :
```javascript
const nextConfig = {
  output: 'standalone', // Pour la production
  reactStrictMode: true,
  images: {
    domains: ['localhost', 'votre-domaine.com', 'api.votre-domaine.com'],
  },
}
```

6. **Nginx (Reverse Proxy)**
Installer et configurer Nginx :
```bash
sudo apt install nginx certbot python3-certbot-nginx
```

Créer `/etc/nginx/sites-available/marketpulse` :
```nginx
# Frontend
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# Backend API
server {
    listen 80;
    server_name api.votre-domaine.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activer et obtenir SSL :
```bash
sudo ln -s /etc/nginx/sites-available/marketpulse /etc/nginx/sites-enabled/
sudo nginx -t
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com -d api.votre-domaine.com
```

7. **Démarrer les services**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

8. **Initialiser la base de données**
```bash
docker exec -it marketpulse_backend alembic upgrade head
```

9. **Backups automatiques (Cron)**
Créer `/opt/marketpulse/backup.sh` :
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec marketpulse_postgres pg_dump -U marketpulse marketpulse > /opt/marketpulse/backups/backup_$DATE.sql
# Garder seulement les 7 derniers backups
find /opt/marketpulse/backups -name "backup_*.sql" -mtime +7 -delete
```

Cron : `0 2 * * * /opt/marketpulse/backup.sh`

---

### Option 2 : Railway.app 🚂

**Prix** : 20-100$/mois  
**Complexité** : Faible  
**Avantages** : Déploiement simple, gestion automatique, PostgreSQL inclus

#### Configuration

1. **Connecter votre repo GitHub**

2. **Services à créer** :
   - **PostgreSQL** : Service Railway (gratuit jusqu'à 1GB)
   - **Redis** : Railway Redis (ou Upstash externe)
   - **Backend** : Service Python avec variables d'environnement
   - **Frontend** : Service Node.js avec build Next.js
   - **Worker Scraper** : Service Python séparé

3. **Variables d'environnement** :
```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
SECRET_KEY=GENERATEZ_UNE_CLE_SECRETE
NEXT_PUBLIC_API_URL=https://backend-production.up.railway.app
```

4. **Limitations** : 
   - Playwright nécessite beaucoup de ressources
   - Peut être coûteux avec plusieurs workers
   - Timeout de 5 minutes par défaut

---

### Option 3 : Render.com 🎨

**Prix** : 25-75$/mois  
**Complexité** : Faible-Moyenne  
**Avantages** : Bon pour les débuts, PostgreSQL gratuit

#### Configuration

1. **Services Render** :
   - **PostgreSQL** : Database (gratuit)
   - **Redis** : Redis Instance
   - **Web Service Backend** : Python (Dockerfile backend/)
   - **Web Service Frontend** : Node.js (Dockerfile frontend/)
   - **Background Worker** : Python (Worker scraper)

2. **Fichier `render.yaml`** (à la racine) :
```yaml
services:
  - type: web
    name: marketpulse-backend
    env: docker
    dockerfilePath: ./backend/Dockerfile
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: marketpulse-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: marketpulse-redis
          type: redis
          property: connectionString
      - key: SECRET_KEY
        generateValue: true

  - type: web
    name: marketpulse-frontend
    env: docker
    dockerfilePath: ./frontend/Dockerfile.prod
    envVars:
      - key: NEXT_PUBLIC_API_URL
        sync: false
        value: https://marketpulse-backend.onrender.com

  - type: worker
    name: marketpulse-scraper
    env: docker
    dockerfilePath: ./scraper/Dockerfile
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: marketpulse-db
          property: connectionString

databases:
  - name: marketpulse-db
    plan: free  # ou starter pour la prod
```

---

### Option 4 : Fly.io 🪰

**Prix** : 20-60$/mois  
**Complexité** : Moyenne  
**Avantages** : Global, bon pour la scalabilité, support Docker natif

#### Configuration

1. **Installer Fly CLI**
```bash
curl -L https://fly.io/install.sh | sh
fly auth login
```

2. **Créer `fly.toml` pour chaque service**

`fly.backend.toml` :
```toml
app = "marketpulse-backend"
primary_region = "cdg"  # Paris

[build]
  dockerfile = "./backend/Dockerfile"

[env]
  DATABASE_URL = "postgres://..."
  REDIS_URL = "redis://..."
  SECRET_KEY = "..."

[[services]]
  http_checks = []
  internal_port = 8000
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

3. **Déployer**
```bash
fly deploy -c fly.backend.toml
```

---

### Option 5 : AWS / GCP / Azure ☁️

**Prix** : 50-300$/mois  
**Complexité** : Élevée  
**Avantages** : Scalabilité maximale, services managés

#### Architecture AWS (ECS/Fargate)

1. **Services AWS** :
   - **RDS PostgreSQL** : Base de données managée
   - **ElastiCache Redis** : Cache/Queue
   - **ECS Fargate** : Containers (Backend, Frontend, Workers)
   - **ECR** : Registry Docker
   - **ALB** : Load Balancer
   - **Route53** : DNS
   - **CloudFront** : CDN pour le frontend

2. **Coûts estimés** :
   - RDS db.t3.medium : ~70$/mois
   - ElastiCache cache.t3.medium : ~35$/mois
   - Fargate (3 tasks) : ~50-100$/mois
   - Total : ~150-250$/mois

---

## 🔒 Sécurité Production

### Checklist Sécurité

- [ ] Changer tous les mots de passe par défaut
- [ ] Générer une `SECRET_KEY` forte (32+ caractères)
- [ ] Activer HTTPS (SSL/TLS)
- [ ] Configurer CORS correctement
- [ ] Activer les backups automatiques PostgreSQL
- [ ] Limiter les ports exposés (seulement 80/443)
- [ ] Configurer un firewall (UFW/iptables)
- [ ] Utiliser des variables d'environnement (jamais de secrets en dur)
- [ ] Activer les logs et monitoring
- [ ] Configurer rate limiting sur l'API
- [ ] Mettre à jour régulièrement les dépendances

### Rate Limiting (Backend)

Ajouter à `backend/main.py` :
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Appliquer sur les routes sensibles
@router.post("/analyse")
@limiter.limit("10/minute")
async def analyse(...):
    ...
```

---

## 📊 Monitoring et Logs

### Option 1 : Logs Docker
```bash
# Voir les logs
docker-compose logs -f backend

# Logs avec rotation
docker-compose up > logs/app.log 2>&1
```

### Option 2 : Sentry (Recommandé)
```python
# backend/requirements.txt
sentry-sdk[fastapi]==1.38.0

# backend/main.py
import sentry_sdk
sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN",
    traces_sample_rate=1.0,
)
```

### Option 3 : Prometheus + Grafana
Pour un monitoring avancé.

---

## 🔄 CI/CD (GitHub Actions)

Créer `.github/workflows/deploy.yml` :
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/marketpulse
            git pull
            docker-compose -f docker-compose.prod.yml up -d --build
            docker exec marketpulse_backend alembic upgrade head
```

---

## 💰 Comparaison des Coûts

| Solution | Coût/mois | Complexité | Scalabilité | Recommandation |
|----------|-----------|------------|-------------|----------------|
| **VPS (Hetzner)** | 15-50€ | Moyenne | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Railway** | 20-100$ | Faible | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Render** | 25-75$ | Faible | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Fly.io** | 20-60$ | Moyenne | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **AWS/GCP** | 50-300$ | Élevée | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 🎯 Recommandation Finale

**Pour commencer** : **VPS Hetzner (20€/mois)** ou **Render.com**
- Bon rapport qualité/prix
- Contrôle total
- Docker Compose fonctionne out-of-the-box
- Assez de ressources pour Playwright

**Pour scaler** : Migrer vers **AWS/GCP** ou **Fly.io**

---

## 📝 Checklist Déploiement

- [ ] Avoir un nom de domaine
- [ ] Configurer DNS (A record vers l'IP du serveur)
- [ ] Configurer les variables d'environnement
- [ ] Générer les secrets (SECRET_KEY, mots de passe DB)
- [ ] Configurer SSL/HTTPS
- [ ] Tester les backups PostgreSQL
- [ ] Configurer le monitoring
- [ ] Documenter les procédures de déploiement
- [ ] Tester la restauration depuis un backup
- [ ] Configurer les alertes (disque plein, service down)

---

## 🆘 Support

Pour des questions spécifiques sur le déploiement, voir :
- Documentation Docker : https://docs.docker.com
- Documentation Next.js : https://nextjs.org/docs/deployment
- Documentation FastAPI : https://fastapi.tiangolo.com/deployment/


