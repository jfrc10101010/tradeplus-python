#!/usr/bin/env python3
"""
VALIDACION FASE 2 CON REGENERACION DE TOKENS
Regenera tokens FRESCOS y luego valida ambos WebSockets
"""
import asyncio
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
import time

def regenerate_tokens():
    """Regenerar tokens OAuth de Schwab y JWT de Coinbase"""
    print("\n" + "="*80)
    print("PASO 1: REGENERANDO TOKENS (FRESCOS)")
    print("="*80)
    
    try:
        # Regenerar token Schwab
        print("\n[1/2] Regenerando token OAuth de Schwab...")
        result = subprocess.run([sys.executable, "generate_token.py"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✓ Token Schwab regenerado exitosamente")
        else:
            print(f"✗ Error regenerando token Schwab:\n{result.stderr}")
            return False
        
        # Esperar 2 segundos
        time.sleep(2)
        
        print("\n[2/2] Regenerando JWT de Coinbase...")
        # El JWT se regenera automáticamente en connect(), pero podemos validar que el archivo existe
        jwt_file = Path("hub/coinbase_current_jwt.json")
        if jwt_file.exists():
            with open(jwt_file) as f:
                jwt_data = json.load(f)
            print(f"✓ JWT actual válido hasta: {jwt_data.get('expires', 'unknown')}")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("✗ Timeout regenerando tokens")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Ejecutar regeneración + validación"""
    print("\n" + "="*80)
    print("VALIDACION FASE 2 CON TOKENS FRESCOS")
    print("="*80)
    
    # Paso 1: Regenerar tokens
    if not regenerate_tokens():
        print("\n[FAIL] No se pudieron regenerar los tokens")
        sys.exit(1)
    
    # Paso 2: Esperar 3 segundos para asegurar que los tokens estén listos
    print("\nEsperando 3 segundos antes de validar...")
    time.sleep(3)
    
    # Paso 3: Ejecutar validación
    print("\n" + "="*80)
    print("PASO 2: EJECUTANDO VALIDACION CON TOKENS FRESCOS")
    print("="*80)
    
    result = subprocess.run([sys.executable, "validate_fase2_real.py"], 
                          capture_output=False, text=True)
    
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
