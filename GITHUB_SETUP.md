# Instructions pour créer le dépôt GitHub

## Étape 1 : Créer le dépôt sur GitHub

1. Allez sur [GitHub.com](https://github.com) et connectez-vous
2. Cliquez sur le bouton **"+"** en haut à droite → **"New repository"**
3. Remplissez les informations :
   - **Repository name** : `analyser-revolutionnaire` (ou le nom de votre choix)
   - **Description** : `Plateforme d'analyse de produits digitaux avec scraping Facebook Ads`
   - **Visibility** : Choisissez **Public** ou **Private**
   - **NE COCHEZ PAS** "Initialize this repository with a README" (on a déjà un README)
4. Cliquez sur **"Create repository"**

## Étape 2 : Connecter le dépôt local à GitHub

Après avoir créé le dépôt, GitHub vous donnera des instructions. Utilisez ces commandes :

```bash
# Remplacez VOTRE_USERNAME par votre nom d'utilisateur GitHub
# Remplacez analyser-revolutionnaire par le nom que vous avez choisi

git remote add origin https://github.com/VOTRE_USERNAME/analyser-revolutionnaire.git
git branch -M main
git push -u origin main
```

## Alternative : Avec SSH (si vous avez configuré une clé SSH)

```bash
git remote add origin git@github.com:VOTRE_USERNAME/analyser-revolutionnaire.git
git branch -M main
git push -u origin main
```

## Étape 3 : Vérifier

Après le push, allez sur votre dépôt GitHub et vérifiez que tous les fichiers sont bien présents.

## Commandes utiles pour la suite

```bash
# Voir l'état des fichiers
git status

# Ajouter des fichiers modifiés
git add .

# Faire un commit
git commit -m "Description des changements"

# Pousser vers GitHub
git push

# Voir l'historique
git log --oneline
```

