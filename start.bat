@echo off
setlocal
REM Lancement d'A.I.D.E en production (Windows) : Caddy (HTTPS, ports 80/443)
REM puis le backend sur 127.0.0.1:8000. Ne deploie rien : deploy.bat se lance
REM a part, backend arrete.
REM
REM Caddy est cherche dans l'ordre : service Windows "caddy", variable CADDY
REM (chemin complet de caddy.exe), PATH, puis C:\caddy\caddy.exe.

cd /d "%~dp0"

REM --- 1. Les prerequis : rien n'est lance s'il en manque un ---
if not exist backend\.venv\Scripts\activate.bat (
  echo backend\.venv est introuvable : cree le venv ^(voir README, Installation^).
  goto :fail
)
if not exist backend\app\config\.env (
  echo backend\app\config\.env est introuvable ^(voir README, Installation^).
  goto :fail
)
if not exist backend\app\config\database.ini (
  echo backend\app\config\database.ini est introuvable ^(voir README, Installation^).
  goto :fail
)
if not exist frontend\build\client\index.html (
  echo frontend\build est introuvable ou incomplet : lance deploy.bat, ou renomme frontend\build.new en frontend\build.
  goto :fail
)
if not exist backend\documents\maps (
  echo backend\documents\maps est introuvable : cree le dossier, meme vide.
  goto :fail
)
if not exist Caddyfile (
  echo Caddyfile est introuvable a la racine du depot.
  goto :fail
)
findstr /i /r /c:"^ENV=production" backend\app\config\.env >nul
if errorlevel 1 echo Attention : ENV=production n'est pas dans backend\app\config\.env.

REM --- 2. Caddy ---
REM Installe comme service : on le demarre s'il est arrete.
sc.exe query caddy >nul 2>&1
if errorlevel 1 goto :caddy_exe
sc.exe query caddy | find "RUNNING" >nul
if not errorlevel 1 (
  echo Caddy tourne deja ^(service Windows^).
  goto :backend
)
echo Demarrage du service Caddy...
sc.exe start caddy >nul
if errorlevel 1 (
  echo Impossible de demarrer le service Caddy : relance ce script en administrateur, ou "sc.exe start caddy".
  goto :fail
)
goto :backend

:caddy_exe
REM Sans service : caddy.exe dans une fenetre a part.
set "CADDY_EXE=%CADDY%"
if not defined CADDY_EXE for /f "delims=" %%c in ('where caddy 2^>nul') do if not defined CADDY_EXE set "CADDY_EXE=%%c"
if not defined CADDY_EXE if exist C:\caddy\caddy.exe set "CADDY_EXE=C:\caddy\caddy.exe"
if not defined CADDY_EXE (
  echo caddy.exe est introuvable : installe-le dans C:\caddy\ ^(voir README, HTTPS^) ou donne son chemin dans la variable CADDY.
  goto :fail
)
tasklist /fi "imagename eq caddy.exe" | find /i "caddy.exe" >nul
if not errorlevel 1 (
  echo Caddy tourne deja.
  goto :backend
)
REM Avant Caddy, le backend etait lance avec --port=80 : il bloquerait Caddy.
netstat -ano | findstr /r /c:"TCP *[^ ]*:80 " >nul
if not errorlevel 1 (
  echo Le port 80 est deja occupe, sans doute par l'ancien backend lance avec --port=80 : arrete-le d'abord.
  echo Programme qui l'occupe : netstat -ano ^| findstr :80 donne son PID, tasklist /fi "pid eq PID" son nom.
  goto :fail
)
"%CADDY_EXE%" validate --config Caddyfile --adapter caddyfile >nul 2>&1
if errorlevel 1 (
  echo Le Caddyfile est invalide :
  "%CADDY_EXE%" validate --config Caddyfile --adapter caddyfile
  goto :fail
)
echo Demarrage de Caddy dans une nouvelle fenetre...
start "A.I.D.E - Caddy (HTTPS)" "%CADDY_EXE%" run --config "%~dp0Caddyfile"

:backend
REM --- 3. Le backend, dans cette fenetre (Ctrl+C pour l'arreter) ---
netstat -ano | findstr /r /c:"TCP *[^ ]*:8000 " >nul
if not errorlevel 1 (
  echo Le port 8000 est deja occupe : le backend tourne sans doute deja dans une autre fenetre.
  goto :fail
)
cd backend
call .venv\Scripts\activate.bat
echo Demarrage du backend sur 127.0.0.1:8000 : https://cubecrusader.serveminecraft.net
REM Tout sur une ligne : cmd lit la ligne entiere avant de l'executer. Si
REM start.bat est modifie pendant que le backend tourne (git checkout de
REM deploy.bat), cmd ne relit pas la suite au milieu du nouveau fichier.
python -m fastapi run main.py --host 127.0.0.1 --port 8000 & echo. & echo Backend arrete. Caddy tourne toujours : ferme sa fenetre ^(ou "sc.exe stop caddy"^) pour arreter le site. & pause & exit /b

:fail
echo.
echo Lancement interrompu.
pause
exit /b 1
