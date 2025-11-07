/**
 * DEBUG: Verificar conexión Python-Node.js
 * Ejecutar: node test/debug.js
 */

const { exec, spawn } = require('child_process');
const path = require('path');
const util = require('util');
const execPromise = util.promisify(exec);

console.log(`
╔════════════════════════════════════════════════════════════╗
║     DEBUG: Conexión Python-Node.js                         ║
║     Ejecutando diagnóstico...                              ║
╚════════════════════════════════════════════════════════════╝
`);

async function diagnose() {
    try {
        // TEST 1: ¿Python instalado?
        console.log('\n[1/4] Verificando Python...');
        const { stdout: pythonVer } = await execPromise('python --version');
        console.log(`✅ Python instalado: ${pythonVer.trim()}`);

        // TEST 2: ¿Módulos Python disponibles?
        console.log('\n[2/4] Verificando módulos Python...');
        const { stdout: modules } = await execPromise(
            'python -c "import sys; print(sys.path)"'
        );
        console.log(`✅ Python path: ${modules.substring(0, 100)}...`);

        // TEST 3: ¿Journal module importable?
        console.log('\n[3/4] Verificando journal module...');
        const hubPath = path.join(__dirname, '..', 'hub');
        const testScript = `
import sys
sys.path.insert(0, '${hubPath.replace(/\\/g, '\\\\')}')
try:
    from journal.journal_manager import JournalManager
    print("✅ JournalManager importado correctamente")
except Exception as e:
    print(f"❌ Error: {e}")
`;
        
        const { stdout: importTest } = await execPromise(
            `python -c "${testScript.replace(/"/g, '\\"')}"`,
            { maxBuffer: 10 * 1024 * 1024 }
        );
        console.log(`✅ ${importTest.trim()}`);

        // TEST 4: ¿API funciona?
        console.log('\n[4/4] Probando API Journal...');
        const apiScript = `
import sys
import json
sys.path.insert(0, '${hubPath.replace(/\\/g, '\\\\')}')
from journal.journal_manager import JournalManager

try:
    manager = JournalManager()
    result = manager.get_combined_journal(days=1)
    print(json.dumps({
        'success': True,
        'trades': len(result.get('trades', [])),
        'stats': result.get('stats', {})
    }))
except Exception as e:
    print(json.dumps({
        'success': False,
        'error': str(e)
    }))
`;

        const { stdout: apiResult } = await execPromise(
            `python -c "${apiScript.replace(/"/g, '\\"')}"`,
            { maxBuffer: 10 * 1024 * 1024, timeout: 15000 }
        );
        
        const result = JSON.parse(apiResult);
        if (result.success) {
            console.log(`✅ Journal Manager funciona: ${result.trades} trades encontrados`);
        } else {
            console.log(`❌ Error en Journal: ${result.error}`);
        }

        console.log(`
╔════════════════════════════════════════════════════════════╗
║     ✅ DIAGNÓSTICO COMPLETADO                              ║
╚════════════════════════════════════════════════════════════╝
        `);

    } catch (error) {
        console.error(`
❌ ERROR DETECTADO:
${error.message}

Posibles soluciones:
1. ¿Python está en PATH? Prueba: python --version
2. ¿Journal module existe? Verifica: hub/journal/
3. ¿Token managers funcionan? Verifica: hub/managers/
4. ¿Permisos correctos? Verifica: ls -la hub/journal/
        `);
    }
}

diagnose();
