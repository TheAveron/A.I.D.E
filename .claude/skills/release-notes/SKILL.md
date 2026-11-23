---
name: release-notes
description: Prépare les notes de la prochaine release GitHub d'A.I.D.E (vX.Y.Z) à partir des PR fusionnées depuis le dernier tag, vérifie les numéros de version et donne la commande de publication sans la lancer.
argument-hint: "[vX.Y.Z]"
disable-model-invocation: true
allowed-tools: Bash(git log:*) Bash(git tag:*) Bash(git diff:*) Bash(git show:*) Bash(gh release list:*) Bash(gh release view:*) Bash(gh pr view:*) Bash(gh pr list:*)
---

# Notes de release

Version demandée : `$ARGUMENTS` (si vide, propose la suivante d'après le dernier tag et le contenu des PR : correctif → patch, fonctionnalité → mineure).

## 1. Ce qui a changé

- Dernière release **publiée** : `gh release list --limit 1` (c'est elle que `deploy.sh` compare, pas le dernier tag).
- PR fusionnées depuis : `git log --format='%s' <tag>..origin/main`. Les PR sont squashées, le numéro est à la fin du titre `(#NNN)`. Lis la description de chacune avec `gh pr view NNN` pour comprendre ce qu'elle change pour les joueurs.
- Migrations ajoutées : `git diff --name-only <tag>..origin/main -- backend/alembic/versions`. Pour chacune, lis `upgrade()` pour dire en une phrase ce qu'elle fait aux données.
- Autres points de déploiement à repérer dans le diff : `backend/requirements.txt` (nouvelle dépendance), nouvelles variables d'environnement ou clés de `database.ini`, nouveaux dossiers de stockage (non sauvegardés par `deploy.sh`), fichiers déplacés au démarrage.

## 2. Les numéros de version

La release ne doit pas partir si ces deux lignes ne portent pas la version demandée (c'est arrivé pour v1.5.0 et v1.6.0) :

- `backend/main.py` : `version = "X.Y.Z"`
- `frontend/package.json` : `"version": "X.Y.Z"` (et `package-lock.json`)

Si elles sont en retard, **arrête-toi** et propose une PR « Version X.Y.Z » qui ne change que ces lignes (`npm version --no-git-tag-version X.Y.Z` dans `frontend/`), sur le modèle de la PR #105.

## 3. Les notes

Même forme que les releases précédentes (`gh release view v1.6.0`), **en anglais** :

```markdown
## Highlights
- **Feature name** (`/page-address`): what players can now do, in one or two sentences.

## Deployment notes
- **Migration 00NN** (run by `deploy.sh`): what it does to the data.
- **New dependency** `name` (installed by `deploy.sh` through `requirements.txt`).

## What's Changed
* PR title by @author in https://github.com/TheAveron/A.I.D.E/pull/NNN

**Full Changelog**: https://github.com/TheAveron/A.I.D.E/compare/vA.B.C...vX.Y.Z
```

- `Highlights` : ce que voit un joueur ou un admin, groupé par thème (carte, réseau ferré, marché, factions, documents, administration). Pas de détails d'implémentation. Omets la section pour une release de pure maintenance.
- `Deployment notes` : seulement s'il y a quelque chose à faire ou à savoir au déploiement. Omets-la sinon.
- Titre de la release : `vX.Y.Z - <résumé court en anglais>`.

## 4. La publication

Écris les notes dans un fichier du scratchpad, montre-les, puis donne la commande **sans la lancer** :

```bash
gh release create vX.Y.Z --target main --title "vX.Y.Z - …" --notes-file <fichier>
```

La publication déclenche `release-build.yml`, qui ajoute `AIDE_Front_X.Y.Z.zip` à la release ; `deploy.sh` en a besoin. Un tag avec un tiret (`v1.7.0-rc1`) doit être publié avec `--prerelease`.
