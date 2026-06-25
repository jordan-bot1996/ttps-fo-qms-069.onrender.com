# FO-QMS-069 — Déploiement sur Render (gratuit)

## Étapes (10 minutes)

### 1. Créer un compte GitHub (gratuit)
- Allez sur https://github.com
- Cliquez "Sign up" et créez un compte

### 2. Créer un nouveau dépôt GitHub
- Cliquez "+" → "New repository"
- Nom : `fo-qms-069`
- Cochez "Public"
- Cliquez "Create repository"

### 3. Uploader les fichiers
Glissez-déposez ces fichiers dans le dépôt :
- `app.py`
- `requirements.txt`
- `render.yaml`
- Le dossier `static/` avec `index.html` dedans

### 4. Créer un compte Render (gratuit)
- Allez sur https://render.com
- Cliquez "Get Started for Free"
- Connectez-vous avec votre compte GitHub

### 5. Déployer
- Dans Render, cliquez "New +" → "Web Service"
- Choisissez votre dépôt `fo-qms-069`
- Render détecte automatiquement la configuration
- Cliquez "Create Web Service"
- Attendez 2-3 minutes

### 6. Accéder à l'application
Render vous donnera une URL du type :
`https://fo-qms-069.onrender.com`

Partagez ce lien avec vos opérateurs — fonctionne sur
n'importe quelle tablette ou PC, sans installation !

## Notes
- Le plan gratuit Render peut mettre 30 secondes à démarrer
  si l'application n'a pas été utilisée depuis un moment
- Les données sont sauvegardées localement sur chaque tablette
- Le PIN admin par défaut est 1234 (changez-le dans index.html)
