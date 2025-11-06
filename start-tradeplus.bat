@echo off
REM TRADEPLUS - Script de inicio rápido para Windows PowerShell
REM Abre múltiples terminales y arranca todo

title TRADEPLUS - Setup Rápido
color 0A

cls
echo.
echo ============================================================
echo  TRADEPLUS - INICIO RÁPIDO
echo ============================================================
echo.
echo Este script abrirá 3 terminales PowerShell para:
echo   1. Backend (Puerto 5000)
echo   2. Frontend (Puerto 8080)
echo   3. Monitor/pruebas
echo.
echo Presiona ENTER para continuar...
pause

cd /d "%~dp0"

REM Terminal 1: Backend
echo.
echo Abriendo Terminal 1 - Backend...
start powershell -NoExit -Command "cd '%cd%\backend'; Write-Host 'Activando venv...' -ForegroundColor Cyan; .\venv\Scripts\Activate.ps1; Write-Host 'Ejecutando backend...' -ForegroundColor Green; python main.py"

REM Esperar un poco antes de abrir Terminal 2
timeout /t 3 /nobreak

REM Terminal 2: Frontend
echo Abriendo Terminal 2 - Frontend...
start powershell -NoExit -Command "cd '%cd%\frontend'; Write-Host 'Instalando dependencias (si es necesario)...' -ForegroundColor Cyan; npm install; Write-Host 'Ejecutando frontend...' -ForegroundColor Green; npm start"

REM Terminal 3: Monitor
echo Abriendo Terminal 3 - Monitor/Pruebas...
start powershell -NoExit -Command "cd '%cd%'; Write-Host '================================' -ForegroundColor Yellow; Write-Host 'TRADEPLUS - Terminal de Pruebas' -ForegroundColor Yellow; Write-Host '================================' -ForegroundColor Yellow; Write-Host 'URLs para probar:' -ForegroundColor Cyan; Write-Host '  - Frontend: http://localhost:8080' -ForegroundColor Green; Write-Host '  - Health:   http://localhost:5000/health' -ForegroundColor Green; Write-Host '' -ForegroundColor Gray; Write-Host 'Comandos útiles:' -ForegroundColor Cyan; Write-Host '  curl http://localhost:5000/health' -ForegroundColor Gray; Write-Host '  curl http://localhost:8080' -ForegroundColor Gray; Write-Host '' -ForegroundColor Gray;"

echo.
echo ✅ Tres terminales PowerShell abiertos
echo.
echo Esperando a que se inicialicen...
echo.
echo 🌐 Abre en tu navegador: http://localhost:8080
echo 🏥 Verifica salud:        http://localhost:5000/health
echo.
echo Presiona ENTER para cerrar esta ventana...
pause
