# Déploiement Rapide - MarketPulse Africa

## 🎯 Solution Recommandée : VPS (Hetzner/OVH/DigitalOcean)

**Prix estimé** : 20-50€/mois  
**Temps de déploiement** : 1-2 heures

---

## 📋 Checklist Rapide

### 1. Prérequis
- [ ] Serveur VPS avec Ubuntu 22.04 (4+ cores, 8+ GB RAM)
- [ ] Nom de domaine pointant vers l'IP du serveur
- [ ] Accès SSH au serveur

### 2. Installation Serveur (10 min)

```bash
# Sur votre serveur
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Installer Nginx
sudo apt install nginx certbot python3-certbot-nginx -y
```

### 3. Préparer le Projet (5 min)

```bash
# Cloner le projet
cd /opt
sudo git clone <votre-repo> marketpulse
cd marketpulse

# Créer le fichier de configuration production
cp docker-compose.prod.yml.example docker-compose.prod.yml
cp .env.production.example .env
nano .env  # Éditer avec vos valeurs
```

### 4. Configuration .env

```env
# Générer un secret fort
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Dans .env, remplacer:
POSTGRES_PASSWORD=votre_mot_de_passe_fort_ici
SECRET_KEY=la_cle_generee_ci_dessus
NEXT_PUBLIC_API_URL=https://api.votre-domaine.com
ALLOWED_ORIGINS=https://votre-domaine.com,https://www.votre-domaine.com
```

### 5. Configurer Nginx (10 min)

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
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/marketpulse /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Obtenir SSL
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com -d api.votre-domaine.com
```

### 6. Déployer (5 min)

```bash
cd /opt/marketpulse

# Déployer
./scripts/deploy.sh

# Initialiser la base de données
docker exec marketpulse_backend alembic upgrade head
```

### 7. Créer un Admin

```bash
docker exec -it marketpulse_backend python create_admin.py
```

### 8. Configurer Backups Automatiques (5 min)

```bash
# Éditer crontab
crontab -e

# Ajouter cette ligne (backup tous les jours à 2h du matin)
0 2 * * * /opt/marketpulse/scripts/backup.sh
```

---

## ✅ Vérification

1. Frontend accessible : https://votre-domaine.com
2. API accessible : https://api.votre-domaine.com/docs
3. Health check : https://api.votre-domaine.com/health

---

## 🔧 Maintenance

### Voir les logs
```bash
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Redémarrer un service
```bash
docker-compose -f docker-compose.prod.yml restart backend
```

### Mettre à jour le code
```bash
cd /opt/marketpulse
git pull
./scripts/deploy.sh
```

### Backup manuel
```bash
./scripts/backup.sh
```

---

## 🆘 Problèmes Courants

### Le backend ne démarre pas
- Vérifier les logs : `docker logs marketpulse_backend`
- Vérifier que PostgreSQL est prêt : `docker exec marketpulse_postgres pg_isready`

### Le frontend ne charge pas
- Vérifier que NEXT_PUBLIC_API_URL pointe vers le bon backend
- Vérifier les logs : `docker logs marketpulse_frontend`

### Playwright ne fonctionne pas
- Vérifier que les dépendances système sont installées dans le Dockerfile scraper
- Augmenter la mémoire allouée au container scraper

---

## 📚 Documentation Complète

Voir `docs/DEPLOIEMENT.md` pour toutes les options de déploiement.


