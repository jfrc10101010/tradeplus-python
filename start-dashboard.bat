@echo off
REM Iniciar WebSocket Dashboard - Schwab + Coinbase
REM
REM Este script inicia el dashboard en http://localhost:8000
REM Presiona CTRL+C para detener

cd /d "%~dp0"

echo.
echo ================================================================================
echo                    WebSocket Dashboard - TradePlus
echo ================================================================================
echo.
echo   URL: http://localhost:8000
echo.
echo   Secciones:
echo     - Schwab: Saldo, Posiciones, Compra/Venta (actualiza cada 5s)
echo     - Coinbase: Wallets, Saldos, Disponible (actualiza cada 5s)
echo.
echo   Presiona CTRL+C para detener
echo.
echo ================================================================================
echo.

python websocket_dashboard.py

pause
