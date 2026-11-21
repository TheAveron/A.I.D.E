#!/usr/bin/env bash
# Déploiement d'A.I.D.E à partir d'une release GitHub.
# Usage : ./deploy.sh            -> dernière release stable
#         ./deploy.sh v1.3.0     -> version précise (rollback inclus)
set -euo pipefail

REPO="TheAveron/A.I.D.E"
cd "$(dirname "$0")"

git fetch --tags --prune
TAG="${1:-$(git tag --list 'v[0-9]*' --sort=-v:refname | grep -v -- '-' | head -1)}"
ASSET="AIDE_Front_${TAG#v}.zip"
echo "Déploiement de $TAG ($ASSET)"
git checkout "$TAG"

# Backend
cd backend
# Linux/macOS : .venv/bin/activate, Windows (Git Bash) : .venv/Scripts/activate
if [ -f .venv/Scripts/activate ]; then
  source .venv/Scripts/activate
else
  source .venv/bin/activate
fi
pip install -r requirements.txt
alembic upgrade head
cd ..

# Frontend (build fourni par la release)
TMP="$(mktemp -d)"
curl -fL "https://github.com/$REPO/releases/download/$TAG/$ASSET" -o "$TMP/front.zip"
python -m zipfile -e "$TMP/front.zip" "$TMP/out"   # python est toujours la (venv actif), contrairement a unzip
test -f "$TMP/out/build/client/index.html"   # garde-fou avant de toucher à l'existant

rm -rf frontend/build.old
[ -d frontend/build ] && mv frontend/build frontend/build.old
mv "$TMP/out/build" frontend/build
rm -rf "$TMP"

echo "Déploiement de $TAG terminé."
echo "Relance maintenant le backend : arrête l'ancien processus (Ctrl+C), puis depuis backend/ :"
echo "  Linux : source .venv/bin/activate && fastapi run main.py"
echo "  Windows : .venv\\Scripts\\activate && fastapi run main.py"
