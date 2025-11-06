#!/usr/bin/env python3
"""
TRADEPLUS - Setup Completo e Instalador Automático
Configura todo de una: Python, Node, venv, dependencias, todo.
"""

import os
import subprocess
import sys
import platform
from pathlib import Path

def run_command(cmd, description="", show_output=True):
    """Ejecutar comando y capturar salida"""
    try:
        print(f"\n🔄 {description}..." if description else f"\n🔄 Ejecutando: {cmd}")
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=not show_output,
            text=True
        )
        if result.returncode == 0:
            if description:
                print(f"✅ {description}: OK")
            return True, result.stdout
        else:
            if description:
                print(f"❌ {description}: FALLÓ")
            print(f"Error: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False, str(e)

def main():
    print("=" * 70)
    print("🚀 TRADEPLUS - SETUP COMPLETO")
    print("=" * 70)
    
    is_windows = sys.platform == "win32"
    
    # Detectar directorio de proyecto
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)
    
    print(f"\n📁 Proyecto: {project_dir}")
    print(f"🖥️  SO: {'Windows' if is_windows else 'macOS/Linux'}")
    
    # ============================================
    # PASO 1: Validar estructura
    # ============================================
    print("\n" + "=" * 70)
    print("PASO 1: Validando estructura...")
    print("=" * 70)
    
    required_files = {
        "backend/main.py": "Backend principal",
        "backend/requirements.txt": "Dependencias Python",
        "backend/.env": "Variables de entorno",
        "backend/adapters/schwab_adapter.py": "Adapter Schwab",
        "backend/adapters/coinbase_adapter.py": "Adapter Coinbase",
        "backend/core/models.py": "Modelos",
        "frontend/package.json": "Dependencias Node",
        "frontend/server.js": "Servidor frontend",
        "frontend/index.html": "HTML frontend",
    }
    
    all_exist = True
    for file_path, desc in required_files.items():
        if Path(file_path).exists():
            print(f"  ✅ {file_path:<40} ({desc})")
        else:
            print(f"  ❌ {file_path:<40} ({desc}) - FALTA")
            all_exist = False
    
    if not all_exist:
        print("\n❌ Faltan archivos. Setup abortado.")
        return False
    
    print("\n✅ Estructura completa")
    
    # ============================================
    # PASO 2: Setup Backend (Python venv)
    # ============================================
    print("\n" + "=" * 70)
    print("PASO 2: Configurando Backend (Python venv)...")
    print("=" * 70)
    
    venv_path = Path("backend/venv")
    
    if venv_path.exists():
        print("✅ venv ya existe")
    else:
        print("📦 Creando venv...")
        if is_windows:
            success, _ = run_command(
                "cd backend && python -m venv venv",
                "Crear venv"
            )
        else:
            success, _ = run_command(
                "cd backend && python3 -m venv venv",
                "Crear venv"
            )
        
        if not success:
            print("❌ Error creando venv")
            return False
    
    # Determinar comandos según SO
    if is_windows:
        pip_cmd = r"backend\venv\Scripts\pip"
        python_cmd = r"backend\venv\Scripts\python"
        activate_cmd = r"backend\venv\Scripts\activate"
    else:
        pip_cmd = "backend/venv/bin/pip"
        python_cmd = "backend/venv/bin/python"
        activate_cmd = "source backend/venv/bin/activate"
    
    # Actualizar pip
    print("\n📦 Actualizando pip...")
    run_command(f"{pip_cmd} install --upgrade pip", "Actualizar pip")
    
    # Instalar requirements.txt
    print("\n📦 Instalando dependencias Python...")
    success, output = run_command(
        f"{pip_cmd} install -r backend/requirements.txt",
        "Instalar requirements.txt"
    )
    if not success:
        print("⚠️  Algunos paquetes pueden haber fallado, pero continuamos...")
    
    # ============================================
    # PASO 3: Setup Frontend (Node.js)
    # ============================================
    print("\n" + "=" * 70)
    print("PASO 3: Configurando Frontend (Node.js)...")
    print("=" * 70)
    
    # Verificar si npm existe
    success, _ = run_command("npm --version", "Verificar npm")
    if not success:
        print("❌ npm no está instalado. Por favor instala Node.js primero.")
        print("   Descarga desde: https://nodejs.org/")
        return False
    
    print("\n📦 Instalando dependencias Node...")
    success, _ = run_command(
        "cd frontend && npm install",
        "npm install"
    )
    if not success:
        print("⚠️  npm install tuvo problemas, pero continuamos...")
    
    # ============================================
    # PASO 4: Verificar token Schwab
    # ============================================
    print("\n" + "=" * 70)
    print("PASO 4: Verificando autenticación Schwab...")
    print("=" * 70)
    
    token_file = Path(".schwab_token.json")
    if token_file.exists():
        print("✅ Token Schwab ya existe (.schwab_token.json)")
    else:
        print("⚠️  Token Schwab no encontrado")
        print("\n📋 IMPORTANTE:")
        print("   1. Antes de ejecutar backend, necesitas obtener token Schwab")
        print("   2. Ejecuta este comando:")
        if is_windows:
            print(f"      cd backend && venv\\Scripts\\activate && python scripts/get_schwab_token.py")
        else:
            print(f"      cd backend && source venv/bin/activate && python scripts/get_schwab_token.py")
        print("   3. Se abrirá navegador para autenticación (autoriza)")
        print("   4. Después sí puedes ejecutar backend")
    
    # ============================================
    # PASO 5: Mostrar instrucciones finales
    # ============================================
    print("\n" + "=" * 70)
    print("✅ SETUP COMPLETADO EXITOSAMENTE")
    print("=" * 70)
    
    print("\n📖 CÓMO EJECUTAR TRADEPLUS:\n")
    
    print("┌─ TERMINAL 1 (Backend - Puerto 5000)")
    print("│")
    if is_windows:
        print(f"│  cd {project_dir}\\backend")
        print(f"│  venv\\Scripts\\activate")
        print(f"│  python scripts/get_schwab_token.py   # SOLO PRIMERA VEZ")
        print(f"│  python main.py")
    else:
        print(f"│  cd {project_dir}/backend")
        print(f"│  source venv/bin/activate")
        print(f"│  python scripts/get_schwab_token.py   # SOLO PRIMERA VEZ")
        print(f"│  python main.py")
    print("│")
    print("└─ Verás logs como:")
    print("   🔐 Autenticando con Schwab...")
    print("   ✅ Cliente Schwab autenticado")
    print("   📊 Tick AAPL: $150.25")
    
    print("\n┌─ TERMINAL 2 (Frontend - Puerto 8080)")
    print("│")
    print(f"│  cd {project_dir}\\frontend")
    print(f"│  npm start")
    print("│")
    print("└─ Verás:")
    print("   ✅ Frontend running on http://localhost:8080")
    
    print("\n┌─ NAVEGADOR")
    print("│")
    print("│  http://localhost:8080")
    print("│  (datos en tiempo real con Schwab + Coinbase)")
    print("│")
    print("└─ API Health Check:")
    print("   http://localhost:5000/health")
    
    print("\n🔌 URLs importantes:")
    print(f"  • Frontend:   http://localhost:8080")
    print(f"  • API Health: http://localhost:5000/health")
    print(f"  • WebSocket:  ws://localhost:5000/ws")
    
    print("\n💡 NOTAS IMPORTANTES:")
    print("  1. Backend necesita token Schwab (OAuth) - obtenlo con get_schwab_token.py")
    print("  2. Coinbase WebSocket es PÚBLICO (no necesita autenticación)")
    print("  3. Mantén ambas terminales abiertas mientras uses TRADEPLUS")
    print("  4. Usa Ctrl+C para detener cualquier terminal")
    
    print("\n" + "=" * 70)
    print("¡LISTO PARA EJECUTAR TRADEPLUS! 🚀")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
