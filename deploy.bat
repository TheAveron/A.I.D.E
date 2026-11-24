@echo off
setlocal
REM cmd relit ce fichier ligne apres ligne pendant qu'il s'execute, a la position
REM ou il s'etait arrete. Le git checkout plus bas remplace deploy.bat par celui
REM de la version deployee : la suite serait lue au milieu d'un autre fichier
REM (c'est ce qui sautait la migration). Le script s'execute donc depuis une
REM copie dans %TEMP%, que le checkout ne touche pas. Le "& exit /b" doit rester
REM sur la meme ligne que le call : cette ligne est lue en entier avant le call.
if /i "%~f0"=="%TEMP%\aide_deploy_run.bat" goto :main
set "AIDE_ROOT=%~dp0"
copy /y "%~f0" "%TEMP%\aide_deploy_run.bat" >nul || exit /b 1
call "%TEMP%\aide_deploy_run.bat" %* & exit /b

:main
setlocal enabledelayedexpansion
REM Deploiement d'A.I.D.E a partir d'une release GitHub (Windows, cmd).
REM Usage : deploy.bat            -> derniere release publiee
REM         deploy.bat v1.3.0     -> version precise (rollback inclus)
REM
REM Tout ce qui peut echouer (version, zip du frontend, venv, sauvegarde de la
REM base) est fait AVANT de toucher au code, a la base ou au site en place :
REM un echec a ces etapes laisse l'installation telle quelle.
REM
REM Prerequis sur la machine : backend\.venv,
REM backend\app\config\database.ini et pg_dump (dans le PATH, ou son chemin
REM complet dans la variable PG_DUMP).

set REPO=TheAveron/A.I.D.E
cd /d "%AIDE_ROOT%"

REM --- 1. Le depot : aucune modification locale qu'un checkout ecraserait ---
git diff --quiet HEAD
if errorlevel 1 (
  echo Des fichiers suivis par git sont modifies localement, deploiement annule :
  git status --short --untracked-files=no
  exit /b 1
)
git fetch --tags --prune --force || exit /b 1

REM --- 2. La version : la derniere release PUBLIEE, pas le dernier tag ---
if "%~1"=="" (
  for /f "delims=" %%t in ('powershell -NoProfile -Command "(Invoke-RestMethod https://api.github.com/repos/%REPO%/releases/latest).tag_name"') do set TAG=%%t
) else (
  set TAG=%~1
)
if not defined TAG (
  echo Impossible de trouver la derniere release : passe la version en argument, ex. deploy.bat v1.3.2
  exit /b 1
)
git rev-parse --verify --quiet "refs/tags/!TAG!" >nul
if errorlevel 1 (
  echo Le tag !TAG! n'existe pas.
  exit /b 1
)
set ASSET=AIDE_Front_!TAG:~1!.zip
echo Deploiement de !TAG! ^(!ASSET!^)

REM --- 3. Les prerequis du backend ---
if not exist backend\.venv\Scripts\activate.bat (
  echo backend\.venv est introuvable : cree le venv avant de deployer.
  exit /b 1
)
if not exist backend\alembic.ini (
  echo backend\alembic.ini est introuvable : restaure-le avec git checkout -- backend\alembic.ini
  exit /b 1
)
call backend\.venv\Scripts\activate.bat

REM --- 4. Le frontend, prepare a cote de celui en place ---
set TMP_DIR=%TEMP%\aide_deploy
if exist "%TMP_DIR%" rmdir /s /q "%TMP_DIR%"
mkdir "%TMP_DIR%\out"
curl.exe -fL "https://github.com/%REPO%/releases/download/!TAG!/!ASSET!" -o "%TMP_DIR%\front.zip"
if errorlevel 1 (
  echo Le build du frontend n'est pas encore sur la release : reessaie dans quelques minutes.
  exit /b 1
)
tar -xf "%TMP_DIR%\front.zip" -C "%TMP_DIR%\out" || exit /b 1
if not exist "%TMP_DIR%\out\build\client\index.html" (
  echo Structure du zip inattendue, rien n'a ete modifie.
  exit /b 1
)
if exist frontend\build.new rmdir /s /q frontend\build.new
robocopy "%TMP_DIR%\out\build" frontend\build.new /E /NFL /NDL /NJH /NJS >nul
if errorlevel 8 exit /b 1
rmdir /s /q "%TMP_DIR%"

REM --- 5. La base : ou aller, puis une sauvegarde ---
REM Le helper de la version installee, ou celui de la version deployee si
REM l'installee est trop ancienne pour en avoir un
set "AIDE_BACKEND=%CD%\backend"
set "HELPER=%CD%\backend\scripts\deploy_helper.py"
if not exist "!HELPER!" (
  set "HELPER=%TEMP%\aide_deploy_helper.py"
  git show "!TAG!:backend/scripts/deploy_helper.py" > "!HELPER!"
  if errorlevel 1 (
    echo Ni la version installee ni !TAG! n'ont de scripts\deploy_helper.py, rien n'a ete modifie.
    exit /b 1
  )
)
pushd backend
REM Avec le code ACTUEL : lui seul sait defaire ses propres migrations
set DOWN=
for /f "delims=" %%r in ('python "!HELPER!" downgrade-target !TAG!') do set DOWN=%%r
if not defined DOWN (
  echo Impossible de comparer la base a !TAG!, rien n'a ete modifie.
  exit /b 1
)
set BACKUP=
for /f "delims=" %%b in ('python "!HELPER!" backup !TAG!') do set BACKUP=%%b
if not defined BACKUP (
  echo Sauvegarde de la base impossible, rien n'a ete modifie.
  exit /b 1
)
echo Base sauvegardee : !BACKUP!

REM --- 6. Retour en arriere : la base redescend avant le changement de code ---
if not "!DOWN!"=="none" (
  echo La base redescend a la revision !DOWN! pour !TAG!.
  alembic downgrade !DOWN!
  if errorlevel 1 (
    echo Echec du downgrade. Restaure la sauvegarde : !BACKUP!
    exit /b 1
  )
)
popd

REM --- 7. Le code et le backend ---
REM alembic.ini est versionne apres la v1.3.2, ignore avant : une copie locale
REM non suivie bloquerait le checkout, et une version plus ancienne n'en a pas.
copy /y backend\alembic.ini "%TEMP%\aide_alembic.ini" >nul
git ls-files --error-unmatch backend/alembic.ini >nul 2>&1
if errorlevel 1 del backend\alembic.ini
git checkout --quiet !TAG!
if errorlevel 1 (
  if not exist backend\alembic.ini copy /y "%TEMP%\aide_alembic.ini" backend\alembic.ini >nul
  echo Echec du checkout de !TAG!. Sauvegarde de la base : !BACKUP!
  exit /b 1
)
if not exist backend\alembic.ini copy /y "%TEMP%\aide_alembic.ini" backend\alembic.ini >nul
del "%TEMP%\aide_alembic.ini"
pushd backend
pip install -r requirements.txt
if errorlevel 1 (
  echo Echec de pip install. Sauvegarde de la base : !BACKUP!
  exit /b 1
)
REM fastapi and older fastapi-cli releases both install the `fastapi` script:
REM upgrading fastapi-cli removes it. Reinstall fastapi to put it back.
if not exist "%VIRTUAL_ENV%\Scripts\fastapi.exe" (
  set "FASTAPI_REQ="
  for /f "usebackq delims=" %%L in (`findstr /i /b "fastapi==" requirements.txt`) do set "FASTAPI_REQ=%%L"
  pip install --force-reinstall --no-deps "!FASTAPI_REQ!"
  if errorlevel 1 (
    echo Echec de la reinstallation de fastapi. Sauvegarde de la base : !BACKUP!
    exit /b 1
  )
)
alembic upgrade head
if errorlevel 1 (
  echo Echec de la migration. Restaure la sauvegarde : !BACKUP!
  exit /b 1
)
popd

REM --- 8. Le frontend : echange des dossiers ---
if exist frontend\build.old rmdir /s /q frontend\build.old
if exist frontend\build (
  ren frontend\build build.old
  if errorlevel 1 (
    echo frontend\build est verrouille : arrete le backend, puis renomme frontend\build.new en frontend\build.
    exit /b 1
  )
)
ren frontend\build.new build || exit /b 1

echo.
echo Deploiement de !TAG! termine. Sauvegarde de la base : !BACKUP!
echo Relance maintenant le backend : arrete l'ancien processus ^(Ctrl+C^), puis depuis backend\ :
echo   .venv\Scripts\activate ^&^& fastapi run main.py
