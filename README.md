# A.I.D.E

[![CodeQL](https://github.com/TheAveron/A.I.D.E/actions/workflows/codeql.yml/badge.svg)](https://github.com/TheAveron/A.I.D.E/actions/workflows/codeql.yml)

**Assistant Intelligent Dédié à l'Économie**

A.I.D.E est une application web full-stack qui gère l'économie virtuelle d'un serveur Minecraft roleplay : factions, monnaies, marché, transactions, réseau de transport, documentation et cartes du serveur.

- **Backend** : FastAPI + PostgreSQL (SQLAlchemy 2.0, Alembic, authentification JWT)
- **Frontend** : React 19 + TypeScript, React Router 8 (mode SPA) et Vite
- **Déploiement** : le backend sert lui-même le frontend compilé, les cartes et la documentation ; chaque release GitHub fournit le build du frontend, installé par `deploy.bat` / `deploy.sh`

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
│   ├── alembic.ini          # Réglages d'Alembic (sans identifiants : ils sont dans database.ini)
│   ├── app/
│   │   ├── api/             # Routeurs (auth, faction, offer, currencies, trains, ...)
│   │   ├── core/            # Paramètres, sécurité, erreurs, logs, limitation de débit
│   │   ├── crud/            # Accès aux données
│   │   ├── database/        # Connexion et modèles SQLAlchemy
│   │   └── schemas/         # Schémas Pydantic
│   ├── documents/           # Documentation Markdown (AgeOfSteam, CubeCrusaders)
│   ├── scripts/             # Utilitaires en ligne de commande (create_admin.py, deploy_helper.py)
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
├── deploy.bat / deploy.sh   # Mise à jour d'une installation à partir d'une release
└── .github/                 # CodeQL, Dependabot et build du frontend des releases
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

Créez la base PostgreSQL correspondante, puis appliquez les migrations. Elles se connectent avec `database.ini`, comme l'application : `backend/alembic.ini` ne contient aucun identifiant.

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

Une installation de production se met à jour à partir des **releases GitHub** : le code vient du tag de la release, le frontend déjà compilé vient du zip attaché à la release. La machine de déploiement n'a donc besoin ni de Node.js ni de npm.

### Publier une version

1. Fusionnez les changements dans `main`.
2. Publiez une release GitHub avec un tag `vX.Y.Z` (par exemple `v1.4.0`). Un tag avec un tiret (`v1.4.0-rc1`) est une pré-version : il n'est jamais déployé automatiquement.
3. Le workflow `.github/workflows/release-build.yml` compile le frontend et attache `AIDE_Front_X.Y.Z.zip` à la release. Comptez une à deux minutes : tant que le zip n'est pas là, le script de déploiement s'arrête sans rien modifier.

### Préparer la machine (une seule fois)

Suivez l'[installation](#installation) du backend (le frontend n'est pas nécessaire), puis :

- dans `backend/app/config/.env`, mettez `ENV=production` (la liste CORS est alors vide, le frontend étant servi par le même domaine que l'API) et une `SECRET_KEY` longue et unique, jamais partagée ;
- installez les outils clients de PostgreSQL : le déploiement sauvegarde la base avec `pg_dump`. Le script utilise, dans l'ordre : la variable d'environnement `PG_DUMP` (chemin complet de l'exécutable), le `PATH`, puis `C:\Program Files\PostgreSQL\*\bin` ;
- créez `backend/documents/maps` et déposez-y les exports de carte (voir [Cartes](#cartes)) ;
- lancez le backend derrière un reverse proxy HTTPS. Les journaux sont écrits dans `backend/logs/aide.log`.

### Mettre à jour

Depuis la racine du dépôt :

```bash
deploy.bat              # Windows (cmd) : dernière release publiée
./deploy.sh             # Linux, macOS ou Git Bash
```

Les scripts ne modifient rien tant que tout ce qui peut échouer n'a pas été vérifié :

| Étape | Ce que fait le script | Si elle échoue |
|---|---|---|
| 1 | Refuse de continuer si des fichiers suivis par git sont modifiés localement | rien n'est modifié |
| 2 | Prend la dernière **release publiée** (API GitHub), ou la version donnée en argument | rien n'est modifié |
| 3 | Vérifie `backend/.venv` et `backend/alembic.ini` | rien n'est modifié |
| 4 | Télécharge le zip du frontend et le prépare dans `frontend/build.new` | rien n'est modifié |
| 5 | Sauvegarde la base dans `backend/backups/` | rien n'est modifié |
| 6 | Pour un retour en arrière : redescend la base (voir ci-dessous) | le script indique la sauvegarde |
| 7 | `git checkout` du tag, `pip install`, `alembic upgrade head` | le script indique la sauvegarde |
| 8 | Remplace `frontend/build` par le nouveau build (l'ancien reste dans `frontend/build.old`) | le script dit quoi faire |

Une fois le script terminé, **relancez le backend** : arrêtez l'ancien processus, puis depuis `backend/`, venv activé :

```bash
fastapi run main.py
```

### Revenir à une version précédente

```bash
deploy.bat v1.3.2       # ou ./deploy.sh v1.3.2
```

Si la base contient des migrations que cette version ne connaît pas, le script la fait redescendre **avant** de changer de code (seul le code récent sait défaire ses propres migrations), puis installe l'ancienne version. Les migrations qui transforment des données ne sont pas toutes réversibles : par exemple, la 0019 transforme les marqueurs « gare » en vraies gares, et son retour en arrière ne recrée pas ces marqueurs. Pour retrouver exactement l'état d'avant, restaurez la sauvegarde.

### Sauvegardes

Chaque déploiement écrit `backend/backups/aide_<version>_<date>.dump` (format personnalisé de `pg_dump`, dossier ignoré par git). Ces fichiers ne sont jamais supprimés automatiquement : faites le ménage de temps en temps.

Pour restaurer une sauvegarde, backend arrêté :

```bash
pg_restore --clean --if-exists -h HOTE -p PORT -U UTILISATEUR -d BASE backend/backups/aide_v1.4.0_20261122-120000.dump
```

Une sauvegarde peut aussi être prise à la main, depuis `backend/` avec le venv activé :

```bash
python -m scripts.deploy_helper backup manuel
```

### Cartes

La carte du serveur actuel (`/actual`) est un export web de [uNmINeD](https://unmined.net/), déposé dans `backend/documents/maps/<dossier>`. Ce dossier n'est pas versionné : il faut le copier sur la machine de déploiement.

```bash
unmined-cli web render --world="chemin/du/monde" --output="backend/documents/maps/OAOS_zoom" --zoomin="2" --zoomout="7" --shadows="3d" --background="#313338"
```

- `--background` colore les chunks non générés ; sans lui ils sont noirs, et les tuiles étant en JPEG, cette couleur ne peut pas être changée après coup. Le site reprend la même couleur comme fond de carte.
- La première lettre du dossier donne la dimension : `O` pour l'Overworld, `N` pour le Nether, `E` pour l'End. Les gares affichées sont celles de cette dimension.
- Un nouveau dossier se déclare dans `frontend/src/app/utils/maps.ts` : `MAP_LABELS` pour son nom, et `CURRENT_MAP_VARIANTS` pour ajouter une dimension à `/actual` (le sélecteur de dimension apparaît dès qu'il y en a deux).

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
