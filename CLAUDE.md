# A.I.D.E — notes pour Claude

Site du serveur Minecraft Cube Crusader (saison actuelle : Age of Steam).
Backend FastAPI + PostgreSQL (`backend/`), frontend React 19 + React Router 8 en mode SPA (`frontend/`).
Le README décrit l'installation ; ce fichier liste les conventions et les pièges du projet.

## Langues

- **Interface, documentation, descriptions de PR : français.**
- **Code, commentaires, messages d'erreur de l'API, messages de commit : anglais.** Le frontend affiche le `detail` des erreurs tel quel (`utils/apierror.ts`) : ne pas mélanger les langues côté API.

## Vérifier avant de dire « c'est fait »

```bash
cd backend && .venv/bin/python -m pytest -q -p no:warnings   # ~3 min, SQLite en mémoire
cd frontend && npx tsc --noEmit -p . && npx eslint .
```

Pour voir le site réel : `npm run build` dans `frontend/`, puis le backend sert `frontend/build/client` (il n'y a pas de proxy Vite). Un changement du frontend ou de `public/` n'est visible qu'après un nouveau build.

Pour un test connecté, créer un compte temporaire directement en base (mot de passe aléatoire jamais affiché, jeton via `create_access_token`), puis **le supprimer** à la fin, avec ses données. La base locale est celle de l'utilisateur.

## Backend

- **Tests** : fixture `env` de `tests/test_hardening.py` (SQLite, `env.client`, `env.h("alice")` pour les en-têtes). Ajouter les routeurs nécessaires dans une fixture dérivée (voir `tests/test_trains.py`, `tests/test_schematics.py`).
- **CodeQL refuse les effets de bord dans un `assert`** (`py/side-effect-in-assert`) : jamais `assert client.put(...).status_code == 200`. Écrire `r = client.put(...)` puis `assert r.status_code == 200`.
- **Fichiers gzip dans les tests** : `gzip.compress(data, mtime=0)`, sinon deux appels donnent des octets différents.
- **Migrations** : numérotées `00NN_nom.py` dans `alembic/versions/`, `down_revision` = la précédente.
- **Rôles globaux** (`admin`, `train_admin`, `money_admin`) indépendants : être admin ne fait pas de quelqu'un un admin trains. Une action d'un membre de l'équipe sur ce qui appartient à un autre joueur s'inscrit au journal (`crud/audit.py`).
- **Noms de documents** : le nom de fichier passe par `normalize()` (minuscules, sans accents, chiffres ni ponctuation, `_` conservé). `Normes-2.md` serait introuvable.
- **Fichiers envoyés par les joueurs** : jamais confiance au nom ni au contenu. Stockage sous un nom aléatoire, vérification par le contenu (voir `core/nbt.py`, `crud/schematic.py`).

## Frontend : pièges CSS récurrents

Plusieurs règles globales visent des **balises** et s'appliquent partout :

- `header { position: fixed; height: … }` (barre du haut) et `nav { flex: 1; justify-content: space-between; … }` dans `layout/header.css` : **ne pas utiliser `<header>` ni `<nav>` pour autre chose** sans neutraliser ces règles (`PageHeader` est une `<div>`, `.section-tabs` annule celles de `nav`).
- `section { min-height: calc(100dvh - …) }` dans `components/sections.css` : une `<section>` prend toute la hauteur de l'écran.
- `div` est en `flex-direction: column` (`base/layout.css`) : préciser `flex-direction: row` quand il le faut.
- `.snippet-container ul/li` transforme les listes des cartes en lignes bordées : surcharger avec un sélecteur plus précis (`.snippet-container .ma-liste`).
- `layout/grid.css` est chargé après les composants : à spécificité égale, ses règles (dont « carte seule centrée sur 2 colonnes ») l'emportent.
- Un élément placé dans un composant hérite de ses sélecteurs descendants. Exemple : un `<dialog>` dans `.page-header` recevait la taille de `.page-header h1`. Cibler précisément (`.page-header-text h1`).

## Frontend : conventions

- **Thèmes** : attribut `data-theme` sur `<html>`, couleurs en variables CSS. En thème clair, `--primary` (vert) et `--secondary` (jaune) sont pâles : pour du texte coloré, utiliser `--success-fg` ou une couleur assombrie avec `color-mix`. Une image chargée par `<img>` (SVG compris) ne voit pas ces variables : lui donner son propre fond clair.
- **Lint `react-refresh/only-export-components`** : un fichier de composant ou de page n'exporte que des composants. Les fonctions utilitaires vont dans `utils/`.
- **Adresses** : le site et l'API partagent l'origine, sans préfixe `/api`. Le middleware de `main.py` renvoie `index.html` aux navigateurs, mais une nouvelle page doit quand même avoir une adresse distincte des routes d'API (ex. pages `/schematiques`, API `/schematics`).
- **Navigation** : toutes les sections et leurs pages sont décrites dans `utils/navigation.ts` (`NAV_SECTIONS`). Le menu, les onglets de section et la page d'accueil le lisent : ajouter une page = ajouter une ligne là.
- **Composants communs à réutiliser** :
  - `components/common/page_header.tsx` : en-tête de page (icône et couleur de la section, `h1`, description, actions).
  - `components/common/form_dialog.tsx` : formulaire de création dans un `<dialog>` natif, derrière un bouton. Ne pas laisser un formulaire de création ouvert en permanence sous une liste.
  - `components/common/markdown_table.tsx` : tableaux Markdown pleine largeur qui défilent sur mobile.
- **Requêtes authentifiées** : `useApiGet` (`utils/useapiget.ts`). Une image ou un fichier réservé aux comptes connectés ne peut pas être une simple URL dans `<img>` ou `<a>` (pas d'en-tête `Authorization`) : passer par axios en `blob` (voir `hooks/schematics/schematics.ts`).
- **Animations** : seulement dans `@media (prefers-reduced-motion: no-preference)`, sur `opacity` et `transform`/`translate`. Rien ne doit bouger en continu.

## Domaine

- **Les schematics sont indépendants du réseau ferré.** Le seul lien est le badge « conforme aux normes ferroviaires », attribué par un admin trains. Ne pas les ranger avec les trains, lignes et gares : ni dans les menus, ni dans l'administration, ni dans ce que voit un admin trains dans le journal.
- Les normes ferroviaires sont dans `backend/documents/AgeOfSteam/normes_ferroviaires.md`, leurs schémas dans `frontend/public/images/docs/ferroviaire/`.
- « Projets » = marqueurs de carte de type `city` (« Ville / Projet »).
- Le nombre de joueurs inscrits exclut les comptes `admin`.

## Git

- Partir de `main` à jour ; une branche par sujet ; messages de commit en anglais, avec un titre court et un corps qui explique le pourquoi.
- Les PR sont fusionnées sur GitHub en un seul commit (*squash*) : `git branch -d` refuse alors de supprimer la branche locale. Vérifier que la PR est fusionnée (`gh pr list --state merged --head <branche>`) avant de faire `git branch -D`.
