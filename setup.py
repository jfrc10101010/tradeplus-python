#!/usr/bin/env python3
"""
Script de instalación y validación rápida de TRADEPLUS
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}: OK")
            return True
        else:
            print(f"❌ {description}: FALLÓ")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error ejecutando: {e}")
        return False

def main():
    print("=" * 60)
    print("🚀 TRADEPLUS - Setup Rápido")
    print("=" * 60)
    
    # Detectar OS
    is_windows = sys.platform == "win32"
    backend_dir = Path("backend")
    frontend_dir = Path("frontend")
    
    # 1. Validar estructura
    print("\n📁 Validando estructura...")
    required_dirs = [
        "backend/adapters",
        "backend/core",
        "frontend/js"
    ]
    required_files = [
        "backend/main.py",
        "backend/requirements.txt",
        "backend/.env",
        "frontend/package.json",
        "frontend/index.html",
        "README.md"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path}")
            all_exist = False
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            all_exist = False
    
    if not all_exist:
        print("\n❌ Estructura incompleta. Por favor verifica los archivos.")
        return False
    
    print("\n✅ Estructura completa y validada")
    
    # 2. Setup Backend
    print("\n" + "=" * 60)
    print("⚙️  Configurando Backend...")
    print("=" * 60)
    
    venv_dir = backend_dir / "venv"
    if venv_dir.exists():
        print("✅ venv ya existe")
    else:
        if run_command(
            f"cd backend && python -m venv venv",
            "Creando venv"
        ):
            print("✅ venv creado")
        else:
            print("❌ No se pudo crear venv")
            return False
    
    # Activar venv e instalar requirements
    if is_windows:
        pip_cmd = r"backend\venv\Scripts\pip"
        python_cmd = r"backend\venv\Scripts\python"
    else:
        pip_cmd = "backend/venv/bin/pip"
        python_cmd = "backend/venv/bin/python"
    
    if run_command(
        f"{pip_cmd} install --upgrade pip",
        "Actualizando pip"
    ):
        print("✅ pip actualizado")
    
    if run_command(
        f"{pip_cmd} install -r backend/requirements.txt",
        "Instalando dependencias Python"
    ):
        print("✅ Dependencias Python instaladas")
    
    # 3. Setup Frontend
    print("\n" + "=" * 60)
    print("⚙️  Configurando Frontend...")
    print("=" * 60)
    
    if run_command(
        "cd frontend && npm install",
        "Instalando dependencias Node"
    ):
        print("✅ Dependencias Node instaladas")
    
    # 4. Mostrar instrucciones finales
    print("\n" + "=" * 60)
    print("✅ Setup completado exitosamente")
    print("=" * 60)
    print("\n📖 Para iniciar TRADEPLUS:\n")
    print("Terminal 1 - Backend:")
    if is_windows:
        print(r"  cd backend && venv\Scripts\activate && python main.py")
    else:
        print("  cd backend && source venv/bin/activate && python main.py")
    print("\nTerminal 2 - Frontend:")
    print("  cd frontend && npm start")
    print("\n🌐 URLs:")
    print("  Frontend:   http://localhost:8080")
    print("  API Health: http://localhost:5000/health")
    print("  WebSocket:  ws://localhost:5000/ws")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
