#!/usr/bin/env bash
# Déploiement d'A.I.D.E à partir d'une release GitHub.
# Usage : ./deploy.sh            -> dernière release publiée
#         ./deploy.sh v1.3.0     -> version précise (rollback inclus)
#
# Tout ce qui peut échouer (version, zip du frontend, venv, sauvegarde de la
# base) est fait AVANT de toucher au code, à la base ou au site en place : un
# échec à ces étapes laisse l'installation telle quelle.
#
# Prérequis sur la machine : backend/.venv,
# backend/app/config/database.ini et pg_dump (dans le PATH, ou son chemin
# complet dans la variable PG_DUMP).
set -euo pipefail

# Tout le script est dans main(), appelée à la dernière ligne : bash lit la
# fonction en entier avant de l'exécuter. Le git checkout plus bas remplace
# deploy.sh par celui de la version déployée ; sans cela, la suite pourrait
# être lue dans le nouveau fichier, à la mauvaise position.
main() {

REPO="TheAveron/A.I.D.E"
cd "$(dirname "$0")"

fail() {
  echo "$*" >&2
  exit 1
}

# --- 1. Le dépôt : aucune modification locale qu'un checkout écraserait ---
if ! git diff --quiet HEAD; then
  echo "Des fichiers suivis par git sont modifiés localement, déploiement annulé :" >&2
  git status --short --untracked-files=no >&2
  exit 1
fi
git fetch --tags --prune --force

# --- 2. La version : la dernière release PUBLIÉE, pas le dernier tag ---
if [ -n "${1:-}" ]; then
  TAG="$1"
else
  TAG="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
    | grep -o '"tag_name": *"[^"]*"' | head -1 | sed -E 's/.*"([^"]+)"$/\1/' || true)"
fi
[ -n "$TAG" ] || fail "Impossible de trouver la dernière release : passe la version en argument (ex. ./deploy.sh v1.3.2)."
git rev-parse --verify --quiet "refs/tags/$TAG" >/dev/null || fail "Le tag $TAG n'existe pas."
ASSET="AIDE_Front_${TAG#v}.zip"
echo "Déploiement de $TAG ($ASSET)"

# --- 3. Les prérequis du backend ---
# Linux/macOS : .venv/bin/activate, Windows (Git Bash) : .venv/Scripts/activate
if [ -f backend/.venv/Scripts/activate ]; then
  source backend/.venv/Scripts/activate
elif [ -f backend/.venv/bin/activate ]; then
  source backend/.venv/bin/activate
else
  fail "backend/.venv est introuvable : crée le venv avant de déployer."
fi
[ -f backend/alembic.ini ] || fail "backend/alembic.ini est introuvable : restaure-le avec git checkout -- backend/alembic.ini"

# --- 4. Le frontend, préparé à côté de celui en place ---
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fL "https://github.com/$REPO/releases/download/$TAG/$ASSET" -o "$TMP/front.zip" \
  || fail "Le build du frontend n'est pas encore sur la release : réessaie dans quelques minutes."
python -m zipfile -e "$TMP/front.zip" "$TMP/out"   # python est là (venv actif), contrairement à unzip
[ -f "$TMP/out/build/client/index.html" ] || fail "Structure du zip inattendue, rien n'a été modifié."
rm -rf frontend/build.new
mv "$TMP/out/build" frontend/build.new

# --- 5. La base : où aller, puis une sauvegarde ---
cd backend
# Avec le code ACTUEL : lui seul sait défaire ses propres migrations
DOWN="$(python -m scripts.deploy_helper downgrade-target "$TAG")" \
  || fail "Impossible de comparer la base à $TAG, rien n'a été modifié."
BACKUP="$(python -m scripts.deploy_helper backup "$TAG")" \
  || fail "Sauvegarde de la base impossible, rien n'a été modifié."
echo "Base sauvegardée : $BACKUP"

# --- 6. Retour en arrière : la base redescend avant le changement de code ---
if [ "$DOWN" != "none" ]; then
  echo "La base redescend à la révision $DOWN pour $TAG."
  alembic downgrade "$DOWN" || fail "Échec du downgrade. Restaure la sauvegarde : $BACKUP"
fi
cd ..

# --- 7. Le code et le backend ---
# alembic.ini est versionné après la v1.3.2, ignoré avant : une copie locale
# non suivie bloquerait le checkout, et une version plus ancienne n'en a pas.
cp backend/alembic.ini "$TMP/alembic.ini"
git ls-files --error-unmatch backend/alembic.ini >/dev/null 2>&1 || rm backend/alembic.ini
if ! git checkout --quiet "$TAG"; then
  [ -f backend/alembic.ini ] || cp "$TMP/alembic.ini" backend/alembic.ini
  fail "Échec du checkout de $TAG. Sauvegarde de la base : $BACKUP"
fi
[ -f backend/alembic.ini ] || cp "$TMP/alembic.ini" backend/alembic.ini
cd backend
pip install -r requirements.txt || fail "Échec de pip install. Sauvegarde de la base : $BACKUP"
alembic upgrade head || fail "Échec de la migration. Restaure la sauvegarde : $BACKUP"
cd ..

# --- 8. Le frontend : échange des dossiers ---
rm -rf frontend/build.old
if [ -d frontend/build ]; then mv frontend/build frontend/build.old; fi
mv frontend/build.new frontend/build

echo
echo "Déploiement de $TAG terminé. Sauvegarde de la base : $BACKUP"
echo "Relance maintenant le backend : arrête l'ancien processus (Ctrl+C), puis depuis backend/ :"
echo "  Linux : source .venv/bin/activate && fastapi run main.py"
echo "  Windows : .venv\\Scripts\\activate && fastapi run main.py"
}

main "$@"
exit
