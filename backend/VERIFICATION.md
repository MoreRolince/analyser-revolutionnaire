# Guide de vérification du backend

Ce guide explique comment vérifier que votre backend fonctionne correctement.

## Méthodes de vérification

### 1. Vérification automatique complète (Recommandé)

Un script de vérification complète teste tous les composants essentiels :

```bash
cd backend
python check_backend.py
```

Ce script vérifie :
- ✓ Que le serveur est accessible
- ✓ L'endpoint `/health` (avec vérification de la base de données)
- ✓ La connexion à PostgreSQL
- ✓ Les tables de la base de données
- ✓ La documentation OpenAPI (Swagger UI, ReDoc)
- ✓ Que toutes les routes importantes sont enregistrées
- ✓ La configuration CORS

**Exemple de sortie réussie :**
```
============================================================
VÉRIFICATION DU BACKEND MARKETPULSE AFRICA
============================================================

============================================================
1. Vérification du serveur
============================================================

✓ Serveur accessible sur http://127.0.0.1:8000
✓ Endpoint /health: {'status': 'healthy', 'database': 'connected', ...}
✓ Connexion à la base de données PostgreSQL réussie
ℹ Tables trouvées: users, products, shops, ...
✓ Route Authentification: POST /api/v1/auth/login
...
```

### 2. Vérification manuelle rapide

#### 2.1. Endpoint de santé

```bash
curl http://127.0.0.1:8000/health
```

**Réponse attendue si tout va bien :**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-01-15T10:30:00.123456"
}
```

**Si la base de données n'est pas connectée :**
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "...",
  "timestamp": "..."
}
```

#### 2.2. Documentation Swagger UI

Ouvrez dans votre navigateur :
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

Vous devriez voir toutes vos routes API documentées.

#### 2.3. Test d'une route simple

```bash
# Endpoint racine
curl http://127.0.0.1:8000/

# Réponse attendue:
# {"message": "MarketPulse Africa API", "version": "1.0.0"}
```

### 3. Vérification de la base de données

#### 3.1. Via le script Python

Le script `check_backend.py` vérifie automatiquement :
- La connexion à PostgreSQL
- L'existence des tables

#### 3.2. Via psql (manuellement)

```bash
# Se connecter à la base de données
psql -h localhost -p 5433 -U marketpulse -d marketpulse

# Dans psql, lister les tables
\dt

# Compter les utilisateurs
SELECT COUNT(*) FROM users;

# Vérifier la dernière migration
SELECT * FROM alembic_version;
```

### 4. Vérification des routes API

#### 4.1. Via la documentation OpenAPI

Ouvrez http://127.0.0.1:8000/docs et explorez toutes les routes disponibles.

#### 4.2. Via curl (exemples)

```bash
# Test d'authentification (sans token, devrait retourner 401)
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test"}'

# Test des produits (sans authentification, devrait retourner 401 ou 200 selon la route)
curl http://127.0.0.1:8000/api/v1/products/

# Test du statut scraper (nécessite token admin)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://127.0.0.1:8000/api/v1/scraper/status
```

## Checklist de vérification complète

Avant de considérer que le backend est opérationnel, vérifiez :

- [ ] Le serveur démarre sans erreur (`uvicorn main:app --reload`)
- [ ] L'endpoint `/health` retourne `"status": "healthy"` et `"database": "connected"`
- [ ] La documentation est accessible sur `/docs` et `/redoc`
- [ ] La base de données PostgreSQL est accessible
- [ ] Les migrations Alembic sont à jour (`alembic upgrade head`)
- [ ] Toutes les routes importantes sont visibles dans `/docs`
- [ ] Les tests de connexion passent avec `python check_backend.py`

## Dépannage

### Le serveur ne démarre pas

1. **Vérifiez les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

2. **Vérifiez les variables d'environnement** :
   ```bash
   # Créez un fichier .env si nécessaire
   echo "DATABASE_URL=postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse" > .env
   ```

3. **Vérifiez que PostgreSQL est démarré** :
   ```bash
   # Avec Docker Compose
   docker-compose up -d postgres
   
   # Ou vérifiez si PostgreSQL tourne
   sudo systemctl status postgresql
   ```

### L'endpoint `/health` retourne "unhealthy"

1. **Vérifiez la connexion à la base de données** :
   ```bash
   psql -h localhost -p 5433 -U marketpulse -d marketpulse
   ```

2. **Vérifiez DATABASE_URL dans votre `.env`** :
   ```bash
   echo $DATABASE_URL
   # ou
   cat .env | grep DATABASE_URL
   ```

3. **Vérifiez que les tables existent** :
   ```bash
   alembic upgrade head
   ```

### Les routes ne sont pas visibles dans `/docs`

1. **Vérifiez que les routers sont bien importés** dans `main.py`
2. **Vérifiez qu'il n'y a pas d'erreurs d'import** :
   ```bash
   python -c "from app.routers import auth, users, dashboard"
   ```
3. **Regardez les logs du serveur** pour voir s'il y a des erreurs au démarrage

### Erreurs CORS

1. **Vérifiez la configuration CORS** dans `main.py`
2. **Assurez-vous que les origines autorisées incluent votre frontend**

## Tests automatisés

Pour intégrer la vérification dans un pipeline CI/CD, vous pouvez utiliser :

```bash
# Dans un script CI
python check_backend.py && echo "Backend OK" || exit 1
```

Ou utiliser curl pour un test rapide :

```bash
# Test simple de santé
curl -f http://127.0.0.1:8000/health || exit 1
```

## Prochaines étapes

Une fois que toutes les vérifications passent :

1. ✅ Créez un utilisateur de test
2. ✅ Testez l'authentification
3. ✅ Testez les endpoints protégés avec un token
4. ✅ Vérifiez l'intégration avec le frontend
