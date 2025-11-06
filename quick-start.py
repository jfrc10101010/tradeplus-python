#!/usr/bin/env python3
"""
QUICK LAUNCHER - Arranca todo TRADEPLUS en segundos
Uso: python quick-start.py
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def start_terminal_command(title, command, cwd=None):
    """Abre nueva terminal PowerShell con comando"""
    if cwd is None:
        cwd = os.getcwd()
    
    ps_command = f'Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd \'{cwd}\'; {command}"'
    try:
        subprocess.Popen(
            ["powershell", "-Command", ps_command],
            shell=False
        )
        return True
    except Exception as e:
        print(f"Error abriendo terminal: {e}")
        return False

def main():
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("=" * 70)
    print("🚀 TRADEPLUS - QUICK START")
    print("=" * 70)
    
    print("\n📋 Se abrirán 3 terminales automáticamente...\n")
    
    # Terminal 1: Backend
    print("1️⃣  Abriendo Backend (puerto 5000)...")
    backend_cmd = r"""
    Write-Host '═══════════════════════════════════' -ForegroundColor Cyan;
    Write-Host '🚀 TRADEPLUS BACKEND' -ForegroundColor Cyan;
    Write-Host '═══════════════════════════════════' -ForegroundColor Cyan;
    Write-Host '';
    Write-Host 'Activando venv...' -ForegroundColor Yellow;
    .\venv\Scripts\Activate.ps1;
    Write-Host 'Ejecutando backend...' -ForegroundColor Green;
    Write-Host '';
    python main.py;
    """
    start_terminal_command("Backend", backend_cmd.replace("\n", "; "), f"{project_dir}\\backend")
    time.sleep(2)
    
    # Terminal 2: Frontend
    print("2️⃣  Abriendo Frontend (puerto 8080)...")
    frontend_cmd = r"""
    Write-Host '═══════════════════════════════════' -ForegroundColor Cyan;
    Write-Host '🌐 TRADEPLUS FRONTEND' -ForegroundColor Cyan;
    Write-Host '═══════════════════════════════════' -ForegroundColor Cyan;
    Write-Host '';
    Write-Host 'Instalando/verificando npm...' -ForegroundColor Yellow;
    npm install 2>&1 | Out-Null;
    Write-Host 'Ejecutando frontend...' -ForegroundColor Green;
    Write-Host '';
    npm start;
    """
    start_terminal_command("Frontend", frontend_cmd.replace("\n", "; "), f"{project_dir}\\frontend")
    time.sleep(2)
    
    # Terminal 3: Monitor
    print("3️⃣  Abriendo Monitor/Pruebas...")
    monitor_cmd = r"""
    Write-Host '═══════════════════════════════════' -ForegroundColor Yellow;
    Write-Host '📊 TRADEPLUS - MONITOR' -ForegroundColor Yellow;
    Write-Host '═══════════════════════════════════' -ForegroundColor Yellow;
    Write-Host '';
    Write-Host '🌐 URLs:' -ForegroundColor Cyan;
    Write-Host '   • Frontend:   http://localhost:8080' -ForegroundColor Green;
    Write-Host '   • API Health: http://localhost:5000/health' -ForegroundColor Green;
    Write-Host '   • WebSocket:  ws://localhost:5000/ws' -ForegroundColor Green;
    Write-Host '';
    Write-Host '💡 Comandos útiles:' -ForegroundColor Cyan;
    Write-Host '   curl http://localhost:5000/health' -ForegroundColor Gray;
    Write-Host '   curl http://localhost:8080' -ForegroundColor Gray;
    Write-Host '';
    Write-Host '⏱️  Esperando inicio (30 segundos)...' -ForegroundColor Yellow;
    Start-Sleep -Seconds 3;
    Write-Host '';
    Write-Host '✅ TRADEPLUS está iniciando!' -ForegroundColor Green;
    Write-Host '';
    Write-Host 'Abre en tu navegador: http://localhost:8080' -ForegroundColor Yellow;
    Write-Host '';
    """
    start_terminal_command("Monitor", monitor_cmd.replace("\n", "; "), str(project_dir))
    
    print("\n" + "=" * 70)
    print("✅ TRES TERMINALES ABIERTAS")
    print("=" * 70)
    print("\n⏱️  Esperando inicio (30 segundos)...")
    
    for i in range(30, 0, -1):
        print(f"\r⏳ {i}s", end="", flush=True)
        time.sleep(1)
    
    print("\n\n" + "=" * 70)
    print("🎉 TRADEPLUS DEBE ESTAR CORRIENDO")
    print("=" * 70)
    print("\n🌐 Abre: http://localhost:8080\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelado")
        sys.exit(1)
