#!/usr/bin/env python3
"""
START-TRADEPLUS.PY - Inicia ambos servidores (Hub + Flask)
"""
import subprocess
import time
import sys
from pathlib import Path

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         🚀 INICIALIZANDO TRADEPLUS - DOS SERVIDORES         ║
║                                                              ║
║  1. Hub FastAPI (puerto 8000)                               ║
║     └─ Orquestador WebSockets privados                      ║
║     └─ Coinbase + Schwab                                    ║
║                                                              ║
║  2. Flask Dashboard (puerto 5000)                           ║
║     └─ Página de prueba: /test                              ║
║     └─ WebSockets en vivo                                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Cambia a directorio del proyecto
    project_root = Path(__file__).parent
    
    # Procesos
    hub_proc = None
    flask_proc = None
    
    try:
        print("\n⏳ Iniciando Hub FastAPI (puerto 8000)...")
        hub_proc = subprocess.Popen(
            [sys.executable, "-m", "hub.main"],
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        time.sleep(3)
        
        print("⏳ Iniciando Flask Dashboard (puerto 5000)...")
        flask_proc = subprocess.Popen(
            [sys.executable, "server.py"],
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║              ✅ AMBOS SERVIDORES INICIADOS                 ║
║                                                            ║
║  📊 Dashboard: http://localhost:5000/test                  ║
║  📡 API Hub:   http://localhost:8000/docs                  ║
║                                                            ║
║  Presiona Ctrl+C para detener                              ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
        """)
        
        # Mantener procesos activos
        while True:
            if hub_proc.poll() is not None:
                print("⚠️  Hub se detuvo inesperadamente")
                break
            if flask_proc.poll() is not None:
                print("⚠️  Flask se detuvo inesperadamente")
                break
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo servidores...")
        
        if flask_proc:
            flask_proc.terminate()
            flask_proc.wait(timeout=5)
        
        if hub_proc:
            hub_proc.terminate()
            hub_proc.wait(timeout=5)
        
        print("✅ Servidores detenidos correctamente")
        sys.exit(0)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
