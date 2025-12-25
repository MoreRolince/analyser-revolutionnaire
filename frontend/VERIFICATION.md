# Guide de vérification du frontend

Ce guide explique comment vérifier que votre frontend Next.js fonctionne correctement.

## Méthodes de vérification

### 1. Vérification automatique complète (Recommandé)

Un script de vérification complète teste tous les composants essentiels :

```bash
cd frontend
./check_frontend.sh
```

Ce script vérifie :
- ✓ Node.js et npm sont installés et aux bonnes versions
- ✓ Les fichiers essentiels existent
- ✓ Les dépendances npm sont installées
- ✓ La configuration est correcte
- ✓ La connexion au backend est fonctionnelle
- ✓ Le serveur de développement est accessible
- ✓ TypeScript compile sans erreur
- ✓ ESLint est disponible

**Exemple de sortie réussie :**
```
============================================================
VÉRIFICATION DU FRONTEND MARKETPULSE AFRICA
============================================================

✓ Node.js installé: v20.x.x
✓ npm installé: 10.x.x
✓ Fichier trouvé: package.json
✓ Dossier node_modules existe
✓ Backend accessible: http://localhost:8000
...
```

### 2. Vérification manuelle rapide

#### 2.1. Installer les dépendances

```bash
cd frontend
npm install
```

#### 2.2. Vérifier TypeScript

```bash
npm run build
# ou
npx tsc --noEmit
```

#### 2.3. Lancer le serveur de développement

```bash
npm run dev
```

Le frontend devrait être accessible sur http://localhost:3000

#### 2.4. Vérifier ESLint

```bash
npm run lint
```

### 3. Vérification de la configuration

#### 3.1. URL de l'API backend

Le frontend doit pointer vers le bon backend. Par défaut, il utilise `http://localhost:8000`.

Vous pouvez configurer l'URL de l'API de plusieurs façons :

**Option 1 : Variable d'environnement (recommandé)**

Créez un fichier `.env.local` :

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Option 2 : Modifier next.config.js**

```javascript
env: {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
}
```

**Option 3 : Fichier env-config.js (pour usage dynamique)**

Modifiez `public/env-config.js` si vous l'utilisez dans votre application.

#### 3.2. Vérifier que le backend est accessible

```bash
# Vérifier le health endpoint du backend
curl http://localhost:8000/health

# Devrait retourner:
# {"status":"healthy","database":"connected","timestamp":"..."}
```

### 4. Tests des pages principales

Une fois le serveur démarré, vérifiez que les pages principales sont accessibles :

- **Page d'accueil**: http://localhost:3000
- **Login**: http://localhost:3000/auth/login
- **Register**: http://localhost:3000/auth/register
- **Dashboard**: http://localhost:3000/dashboard (nécessite authentification)
- **Admin**: http://localhost:3000/admin (nécessite authentification admin)

### 5. Vérification dans le navigateur

Ouvrez les outils de développement du navigateur (F12) et vérifiez :

#### Console

- Aucune erreur JavaScript
- L'URL de l'API est correctement loggée en développement :
  ```
  API Configuration: {
    baseURL: "http://localhost:8000/api/v1",
    apiUrl: "http://localhost:8000"
  }
  ```

#### Network

- Les requêtes vers `/api/v1/*` pointent vers `http://localhost:8000`
- Les réponses du backend arrivent correctement
- Pas d'erreurs CORS (404, 403, etc.)

#### Application (Storage)

- Le token d'authentification est stocké dans `localStorage`
- Le token est automatiquement ajouté aux requêtes API

## Checklist de vérification complète

Avant de considérer que le frontend est opérationnel, vérifiez :

- [ ] Node.js >= 18 est installé
- [ ] Les dépendances sont installées (`npm install`)
- [ ] Le script de vérification passe (`./check_frontend.sh`)
- [ ] TypeScript compile sans erreur (`npm run build`)
- [ ] Le serveur démarre sans erreur (`npm run dev`)
- [ ] Le frontend est accessible sur http://localhost:3000
- [ ] L'URL de l'API backend est correcte (port 8000)
- [ ] Le backend est accessible et répond
- [ ] Les pages principales se chargent correctement
- [ ] Aucune erreur dans la console du navigateur
- [ ] Les requêtes API fonctionnent

## Dépannage

### Le serveur ne démarre pas

1. **Vérifiez que Node.js est installé** :
   ```bash
   node --version  # Doit être >= 18
   npm --version
   ```

2. **Installez les dépendances** :
   ```bash
   npm install
   ```

3. **Vérifiez les erreurs de compilation** :
   ```bash
   npm run build
   ```

4. **Vérifiez que le port 3000 est libre** :
   ```bash
   # Linux/Mac
   lsof -i :3000
   # ou
   netstat -an | grep 3000
   ```

### Erreurs TypeScript

```bash
# Voir les erreurs TypeScript
npx tsc --noEmit

# Si nécessaire, régénérer les types
npm install --save-dev @types/node @types/react @types/react-dom
```

### Le frontend ne peut pas se connecter au backend

1. **Vérifiez que le backend est démarré** :
   ```bash
   curl http://localhost:8000/health
   ```

2. **Vérifiez l'URL de l'API** dans :
   - `.env.local` (si vous en avez un)
   - `next.config.js`
   - `lib/api.ts`

3. **Vérifiez CORS** dans le backend :
   - Le backend doit autoriser `http://localhost:3000`
   - Vérifiez `main.py` dans le backend

### Erreurs CORS dans le navigateur

Si vous voyez des erreurs CORS dans la console :

1. **Vérifiez la configuration CORS dans le backend** (`backend/main.py`) :
   ```python
   allow_origins=["http://localhost:3000", ...]
   ```

2. **Assurez-vous que le backend est bien démarré**

3. **Vérifiez que l'URL de l'API est correcte**

### Erreurs 401 (Unauthorized)

Si vous obtenez des erreurs 401 :

1. **Vérifiez que vous êtes connecté** :
   - Le token doit être dans `localStorage`
   - Ouvrez les DevTools > Application > Local Storage

2. **Vérifiez que le token est valide** :
   - Essayez de vous reconnecter
   - Le token peut avoir expiré

3. **Vérifiez que l'endpoint backend existe** :
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/users/me
   ```

### Erreurs de build

```bash
# Nettoyer et reconstruire
rm -rf .next
rm -rf node_modules
npm install
npm run build
```

## Tests automatisés

Pour intégrer la vérification dans un pipeline CI/CD, vous pouvez utiliser :

```bash
# Dans un script CI
./check_frontend.sh && echo "Frontend OK" || exit 1

# Ou vérifier spécifiquement la compilation
npm run build && echo "Build OK" || exit 1
```

## Prochaines étapes

Une fois que toutes les vérifications passent :

1. ✅ Testez l'authentification (login/register)
2. ✅ Testez les pages protégées (dashboard)
3. ✅ Vérifiez l'intégration avec le backend
4. ✅ Testez les fonctionnalités principales de l'application

## Commandes utiles

```bash
# Démarrer le serveur de développement
npm run dev

# Build de production
npm run build

# Démarrer le serveur de production
npm start

# Linter le code
npm run lint

# Vérifier TypeScript
npx tsc --noEmit

# Exécuter le script de vérification
./check_frontend.sh
```
