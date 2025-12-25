# Guide de création d'un compte Admin

Ce guide explique comment créer ou promouvoir un utilisateur en administrateur.

## Script disponible

Le script `create_admin.py` permet de :
- ✅ Créer un nouvel utilisateur admin
- ✅ Promouvoir un utilisateur existant en admin
- ✅ Lister tous les admins existants

## Utilisation

### 1. Créer un nouvel admin

```bash
cd /home/maxdo/projets/analyser-revolutionnaire/backend
python3 create_admin.py --create
```

Le script vous demandera :
- Email
- Nom
- Mot de passe (masqué lors de la saisie)
- Confirmation du mot de passe

**Exemple :**
```bash
$ python3 create_admin.py --create

🔐 Création d'un nouvel utilisateur admin
--------------------------------------------------
Email: admin@example.com
Nom: Admin Principal
Mot de passe: 
Confirmer le mot de passe: 

✅ Admin créé avec succès!
   ID: 1
   Email: admin@example.com
   Nom: Admin Principal
   Rôle: UserRole.ADMIN
   Statut: approved
```

### 2. Promouvoir un utilisateur existant en admin

Si vous avez déjà créé un utilisateur via l'API d'inscription et que vous voulez le promouvoir en admin :

```bash
python3 create_admin.py --promote <email>
```

**Exemple :**
```bash
$ python3 create_admin.py --promote user@example.com

⬆️  Promotion de l'utilisateur 'user@example.com' en admin
--------------------------------------------------
✅ Utilisateur promu en admin avec succès!
   ID: 2
   Email: user@example.com
   Nom: John Doe
   Rôle: UserRole.ADMIN (mis à jour)
   Statut: approved
```

### 3. Lister tous les admins

Pour voir tous les administrateurs existants :

```bash
python3 create_admin.py --list
```

**Exemple :**
```bash
$ python3 create_admin.py --list

📋 Liste des admins (2):
--------------------------------------------------------------------------------
  ID:    1 | Email: admin@example.com        | Nom: Admin Principal    | Statut: approved
  ID:    2 | Email: user@example.com         | Nom: John Doe           | Statut: approved
--------------------------------------------------------------------------------
```

## Fonctionnalités du script

- ✅ **Validation des entrées** : Vérifie que l'email n'existe pas déjà (pour création)
- ✅ **Sécurité** : Le mot de passe est masqué lors de la saisie
- ✅ **Hashing sécurisé** : Utilise la même fonction de hashage que l'application (`get_password_hash`)
- ✅ **Statut automatique** : Les admins créés sont automatiquement approuvés (`approved`)
- ✅ **Gestion des erreurs** : Messages clairs en cas d'erreur

## Après la création

Une fois l'admin créé, vous pouvez :

1. **Vous connecter via l'API** :
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin@example.com&password=votre_mot_de_passe"
   ```

2. **Utiliser le token pour accéder aux endpoints admin** :
   ```bash
   # Lister les utilisateurs en attente
   curl -X GET "http://localhost:8000/api/v1/admin/users/pending" \
     -H "Authorization: Bearer <votre_token>"
   
   # Approuver un utilisateur
   curl -X POST "http://localhost:8000/api/v1/admin/users/123/approve?approve=true" \
     -H "Authorization: Bearer <votre_token>"
   ```

## Notes importantes

- ⚠️ Le script doit être exécuté depuis le répertoire `backend/`
- ⚠️ Assurez-vous que la base de données est accessible
- ⚠️ Les variables d'environnement (`.env`) doivent être configurées correctement
- ⚠️ Le mot de passe doit contenir au moins 8 caractères

## Dépannage

### Erreur : "ModuleNotFoundError"
Assurez-vous d'être dans l'environnement virtuel :
```bash
source env/bin/activate  # Linux/Mac
# ou
env\Scripts\activate  # Windows
```

### Erreur : "Could not connect to database"
Vérifiez que :
- PostgreSQL est démarré
- Les variables `DATABASE_URL` dans `.env` sont correctes
- La base de données existe

### L'utilisateur existe déjà
Si vous essayez de créer un admin avec un email existant, utilisez `--promote` à la place.
