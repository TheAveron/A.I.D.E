# A.I.D.E

[![CodeQL](https://github.com/TheAveron/A.I.D.E/actions/workflows/codeql.yml/badge.svg)](https://github.com/TheAveron/A.I.D.E/actions/workflows/codeql.yml)

**Assistant Intelligent Dédié à l'Économie**

A.I.D.E est une application web full-stack qui gère l'économie virtuelle d'un serveur Minecraft roleplay : factions, monnaies, marché, transactions, réseau de transport, documentation et cartes du serveur.

- **Backend** : FastAPI + PostgreSQL (SQLAlchemy 2.0, Alembic, authentification JWT)
- **Frontend** : React 19 + TypeScript, React Router 8 (mode SPA) et Vite
- **Déploiement** : le backend sert lui-même le frontend compilé, les cartes et la documentation

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Structure du dépôt](#structure-du-dépôt)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Lancer le projet](#lancer-le-projet)
- [Tests](#tests)
- [Déploiement](#déploiement)
- [Sécurité](#sécurité)
- [Contribuer](#contribuer)
- [Licence](#licence)

## Fonctionnalités

- **Comptes et authentification** : inscription, connexion par JWT, profils, préférences, notifications.
- **Factions** : création, rôles et permissions par faction, demandes d'adhésion, gestion des membres (inviter, exclure, quitter), approbation par un administrateur.
- **Monnaies** : une monnaie par faction, avec historique des modifications.
- **Marché** : offres (publiques ou privées), transactions et historique, visibles uniquement par les parties concernées et les membres autorisés de la faction.
- **Réseau de transport** : stations, lignes et trains, avec une page dédiée pour chacun.
- **Documentation** : documents Markdown par serveur et par faction, éditeur intégré.
- **Archives et cartes** : documentation et cartes des anciens serveurs (Cube Crusaders, Age of Steam), carte actuelle avec calques.
- **Administration** : panneau d'administration, rôles globaux, gestion du marché.

## Structure du dépôt

```
A.I.D.E/
├── backend/
│   ├── main.py              # Point d'entrée FastAPI (routes, CORS, logs, service du frontend)
│   ├── alembic/             # Migrations de base de données
│   ├── app/
│   │   ├── api/             # Routeurs (auth, faction, offer, currencies, trains, ...)
│   │   ├── core/            # Paramètres, sécurité, erreurs, logs, limitation de débit
│   │   ├── crud/            # Accès aux données
│   │   ├── database/        # Connexion et modèles SQLAlchemy
│   │   └── schemas/         # Schémas Pydantic
│   ├── documents/           # Documentation Markdown (AgeOfSteam, CubeCrusaders)
│   ├── scripts/             # Utilitaires en ligne de commande (create_admin.py)
│   └── tests/               # Tests pytest
├── frontend/
│   └── src/
│       ├── routes.ts        # Déclaration des routes
│       └── app/
│           ├── components/  # Composants, rangés par domaine
│           ├── hooks/       # Hooks, rangés par domaine
│           ├── pages/       # Pages (admin, factions, offers, network, archives, auth, users)
│           ├── types/       # Types TypeScript
│           └── utils/       # Utilitaires (dont la garde d'authentification)
└── .github/                 # CodeQL et Dependabot
```

## Prérequis

- Python 3.11 ou plus récent
- Node.js 20 ou plus récent et npm
- PostgreSQL

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/TheAveron/A.I.D.E.git
cd A.I.D.E
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

Créez le dossier `backend/app/config/` (il n'est pas versionné) avec deux fichiers.

`backend/app/config/.env` :

```ini
SECRET_KEY=une-longue-valeur-aleatoire-d-au-moins-32-caracteres
ENV=development
```

Pour générer une clé :

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

`backend/app/config/database.ini` :

```ini
[postgresql]
host=localhost
port=5432
database=aide
user=aide
password=mot_de_passe
```

Créez la base PostgreSQL correspondante, puis appliquez les migrations :

```bash
alembic upgrade head
```

Créez enfin un compte administrateur. Il n'existe volontairement aucune route HTTP pour cela ; la commande demande le mot de passe sans l'afficher :

```bash
python -m scripts.create_admin --username votre_pseudo

# ou, pour promouvoir un compte existant :
python -m scripts.create_admin --promote --username votre_pseudo
```

### 3. Frontend

```bash
cd frontend
npm install
```

## Lancer le projet

### Développement

Dans deux terminaux :

```bash
# Backend (depuis backend/)
fastapi dev main.py
```

```bash
# Frontend (depuis frontend/)
npm run dev
```

- Frontend : http://localhost:5173
- API : http://localhost:8000
- Documentation interactive de l'API : http://localhost:8000/docs

En mode `development`, le CORS n'autorise que `http://localhost:5173` et `http://127.0.0.1:5173`.

### Production locale

```bash
cd frontend && npm run build     # génère frontend/build/client
cd ../backend && fastapi run main.py
```

Le backend sert alors le frontend compilé (`/assets` et le reste du build), les cartes (`/maps`) et la documentation.

> **Cartes** : `main.py` monte le dossier `backend/documents/maps`, qui n'est pas versionné dans le dépôt. Créez-le (même vide) ou déposez-y vos exports de carte, sinon le backend refusera de démarrer.

## Tests

```bash
cd backend
pytest
```

Les tests utilisent une base SQLite en mémoire : aucune configuration PostgreSQL n'est nécessaire.

Côté frontend :

```bash
cd frontend
npm run lint
```

## Déploiement

1. Définir `ENV=production` dans `backend/app/config/.env` (la liste CORS est alors vide, le frontend étant servi par le même domaine que l'API).
2. Utiliser une `SECRET_KEY` longue et unique, jamais partagée.
3. Construire le frontend (`npm run build`) puis lancer `fastapi run main.py` derrière un reverse proxy HTTPS.
4. Appliquer les migrations (`alembic upgrade head`) à chaque mise à jour.
5. Les journaux sont écrits dans `backend/logs/aide.log`.

## Sécurité

- Les mots de passe sont hachés ; les sessions utilisent des JWT signés avec `SECRET_KEY`.
- Seul un administrateur peut approuver une faction ou créer un compte administrateur (via le script en ligne de commande).
- Un scan CodeQL et Dependabot tournent sur le dépôt.

Pour signaler une faille, ouvrez une issue sans détails sensibles ou contactez directement le mainteneur.

## Contribuer

1. Créez une branche à partir de `main`.
2. Lancez `pytest` (backend) et `npm run lint` (frontend) avant d'ouvrir une pull request.
3. Respectez le [code de conduite](CODE_OF_CONDUCT.md).

Rangement du frontend : un fichier va dans le dossier de son domaine (`factions`, `offers`, `currencies`, `transactions`, `admin`, `network`, `users`, `common`, `layout`). Deux fichiers de même nom mais de contenu différent gardent leur nom, c'est le dossier qui les distingue.

## Licence

Voir le fichier [LICENSE](LICENSE).
