@echo off
setlocal enabledelayedexpansion
REM Deploiement d'A.I.D.E a partir d'une release GitHub (Windows, cmd).
REM Usage : deploy.bat            -> derniere release stable
REM         deploy.bat v1.3.0     -> version precise (rollback inclus)

set REPO=TheAveron/A.I.D.E
cd /d "%~dp0"

git fetch --tags --prune || exit /b 1

if "%~1"=="" (
  for /f "delims=" %%t in ('git tag --list "v[0-9]*" --sort=-v:refname ^| findstr /v /c:"-"') do (
    if not defined TAG set TAG=%%t
  )
) else (
  set TAG=%~1
)
if not defined TAG (
  echo Aucun tag trouve.
  exit /b 1
)

set ASSET=AIDE_Front_!TAG:~1!.zip
echo Deploiement de !TAG! (!ASSET!)
git checkout !TAG! || exit /b 1

REM --- Backend ---
cd backend
call .venv\Scripts\activate.bat
pip install -r requirements.txt || exit /b 1
alembic upgrade head || exit /b 1
cd ..

REM --- Frontend (build fourni par la release) ---
set TMP_DIR=%TEMP%\aide_deploy
if exist "%TMP_DIR%" rmdir /s /q "%TMP_DIR%"
mkdir "%TMP_DIR%\out"
curl.exe -fL "https://github.com/%REPO%/releases/download/!TAG!/!ASSET!" -o "%TMP_DIR%\front.zip" || exit /b 1
tar -xf "%TMP_DIR%\front.zip" -C "%TMP_DIR%\out" || exit /b 1
if not exist "%TMP_DIR%\out\build\client\index.html" (
  echo Structure du zip inattendue, frontend inchange.
  exit /b 1
)

if exist frontend\build.old rmdir /s /q frontend\build.old
if exist frontend\build ren frontend\build build.old
robocopy "%TMP_DIR%\out\build" frontend\build /E /NFL /NDL /NJH /NJS >nul
if errorlevel 8 exit /b 1
rmdir /s /q "%TMP_DIR%"

echo.
echo Deploiement de !TAG! termine.
echo Relance maintenant le backend : arrete l'ancien processus (Ctrl+C), puis depuis backend\ :
echo   .venv\Scripts\activate ^&^& fastapi run main.py
