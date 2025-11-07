/**
 * ╔═══════════════════════════════════════════════════════════════╗
 * ║     Test Server - Journal Module en Tiempo Real (REPARADO)   ║
 * ║     TRADEPLUS V5.0 - Multi-Broker Test Interface            ║
 * ║     Puerto: 8080 | PM2: "journal-test"                      ║
 * ╚═══════════════════════════════════════════════════════════════╝
 */

const express = require('express');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

const app = express();
const PORT = 8080;

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Logging
const logFile = path.join(__dirname, '..', 'logs', 'server.log');
function log(msg) {
    const timestamp = new Date().toISOString();
    const logMsg = `[${timestamp}] ${msg}\n`;
    console.log(logMsg);
    try {
        fs.appendFileSync(logFile, logMsg);
    } catch (e) {
        // Silent fail si no puede escribir log
    }
}

// Almacenamiento en memoria para datos
let journalCache = {
    combined: null,
    timestamp: null,
    updatedAt: null,
    error: null
};

/**
 * FUNCIÓN CORE: Ejecuta Python de forma segura
 */
async function fetchJournalData() {
    return new Promise((resolve, reject) => {
        try {
            const projectRoot = path.join(__dirname, '..');
            const hubPath = path.join(projectRoot, 'hub');
            
            const pythonScript = `
import sys
import json
sys.path.insert(0, '${hubPath.replace(/\\/g, '\\\\')}')

try:
    from journal.journal_manager import JournalManager
    manager = JournalManager()
    result = manager.get_combined_journal(days=7)
    print(json.dumps(result, indent=2, default=str))
except Exception as e:
    import traceback
    error = {
        'error': str(e),
        'type': type(e).__name__,
        'traceback': traceback.format_exc()
    }
    print(json.dumps(error))
`;

            log('📍 Ejecutando Python para obtener journal...');

            // Usar spawn en lugar de exec para mejor manejo
            // ⚠️ CRÍTICO: cwd debe ser projectRoot (donde está .env)
            const python = spawn('python', ['-c', pythonScript], {
                cwd: projectRoot,
                timeout: 30000,
                maxBuffer: 10 * 1024 * 1024,
                windowsHide: true  // Ocultar ventana CMD en Windows
            });

            let stdout = '';
            let stderr = '';

            // Capturar stdout
            python.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            // Capturar stderr
            python.stderr.on('data', (data) => {
                stderr += data.toString();
                log(`⚠️ Python stderr: ${data}`);
            });

            // Manejar finalización
            python.on('close', (code) => {
                if (code !== 0) {
                    log(`❌ Python terminó con código ${code}`);
                    if (stderr) {
                        reject(new Error(`Python error: ${stderr}`));
                    } else {
                        reject(new Error(`Python process exited con código ${code}`));
                    }
                    return;
                }

                try {
                    if (!stdout) {
                        reject(new Error('No output from Python'));
                        return;
                    }

                    const data = JSON.parse(stdout);

                    if (data.error) {
                        log(`❌ Error en Journal: ${data.error}`);
                        reject(new Error(data.error));
                        return;
                    }

                    log(`✅ Journal actualizado: ${data.stats?.total_trades || 0} trades`);
                    resolve(data);

                } catch (parseErr) {
                    log(`❌ Error parseando JSON: ${parseErr.message}`);
                    log(`📄 Output: ${stdout.substring(0, 500)}`);
                    reject(parseErr);
                }
            });

            // Timeout manual
            setTimeout(() => {
                python.kill();
                reject(new Error('Python script timeout (30s)'));
            }, 35000);

        } catch (error) {
            log(`❌ Error en fetchJournalData: ${error.message}`);
            reject(error);
        }
    });
}

/**
 * Obtener datos de un broker específico
 */
async function fetchBrokerData(broker) {
    return new Promise((resolve, reject) => {
        try {
            const projectRoot = path.join(__dirname, '..');
            const hubPath = path.join(projectRoot, 'hub');
            
            const pythonScript = `
import sys
import json
sys.path.insert(0, '${hubPath.replace(/\\/g, '\\\\')}')

try:
    from journal.journal_manager import JournalManager
    manager = JournalManager()
    result = manager.get_trades_by_broker('${broker}', days=7)
    print(json.dumps(result, indent=2, default=str))
except Exception as e:
    import traceback
    error = {
        'error': str(e),
        'type': type(e).__name__,
        'traceback': traceback.format_exc()
    }
    print(json.dumps(error))
`;

            const python = spawn('python', ['-c', pythonScript], {
                cwd: projectRoot,
                timeout: 30000,
                maxBuffer: 10 * 1024 * 1024,
                windowsHide: true  // Ocultar ventana CMD en Windows
            });

            let stdout = '';
            let stderr = '';

            python.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            python.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            python.on('close', (code) => {
                if (code !== 0) {
                    if (stderr) {
                        reject(new Error(`Python error: ${stderr}`));
                    } else {
                        reject(new Error(`Python process exited con código ${code}`));
                    }
                    return;
                }

                try {
                    if (!stdout) {
                        reject(new Error('No output from Python'));
                        return;
                    }

                    const data = JSON.parse(stdout);

                    if (data.error) {
                        reject(new Error(data.error));
                        return;
                    }

                    resolve(data);

                } catch (parseErr) {
                    reject(parseErr);
                }
            });

            setTimeout(() => {
                python.kill();
                reject(new Error('Python script timeout (30s)'));
            }, 35000);

        } catch (error) {
            reject(error);
        }
    });
}

/**
 * RUTAS API
 */

// GET /api/journal - Journal combinado completo
app.get('/api/journal', async (req, res) => {
    try {
        const data = await fetchJournalData();
        
        journalCache.combined = data;
        journalCache.timestamp = data.timestamp;
        journalCache.updatedAt = new Date();
        journalCache.error = null;

        res.json(data);

    } catch (error) {
        log(`❌ Error en GET /api/journal: ${error.message}`);
        journalCache.error = error.message;

        res.status(500).json({
            error: error.message,
            trades: [],
            stats: {},
            timestamp: new Date().toISOString()
        });
    }
});

// GET /api/journal/stats - Solo estadísticas
app.get('/api/journal/stats', async (req, res) => {
    try {
        const data = await fetchJournalData();
        res.json({
            stats: data.stats || {},
            timestamp: data.timestamp
        });
    } catch (error) {
        res.status(500).json({
            error: error.message,
            stats: {}
        });
    }
});

// GET /api/journal/broker/:name - Datos de un broker específico
app.get('/api/journal/broker/:name', async (req, res) => {
    try {
        const broker = req.params.name;
        const data = await fetchBrokerData(broker);
        res.json(data);
    } catch (error) {
        res.status(500).json({
            error: error.message,
            trades: []
        });
    }
});

// GET /api/health - Health check
app.get('/api/health', (req, res) => {
    res.json({
        status: 'healthy',
        uptime: process.uptime(),
        port: PORT,
        timestamp: new Date().toISOString()
    });
});

// GET /api/status - Estado completo
app.get('/api/status', (req, res) => {
    res.json({
        status: 'online',
        uptime: process.uptime(),
        port: PORT,
        cache: {
            hasData: !!journalCache.combined,
            lastUpdate: journalCache.updatedAt,
            cacheAge: journalCache.updatedAt ? 
                Math.round((Date.now() - journalCache.updatedAt) / 1000) + 's' : 'N/A',
            error: journalCache.error
        },
        timestamp: new Date().toISOString()
    });
});

// POST /api/refresh - Fuerza refresh manual
app.post('/api/refresh', async (req, res) => {
    try {
        const data = await fetchJournalData();
        res.json({
            success: true,
            message: 'Journal actualizado exitosamente',
            stats: data.stats,
            trades: data.trades.length
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// GET /api/debug - Info de debug
app.get('/api/debug', (req, res) => {
    res.json({
        version: '1.0.0',
        node_version: process.version,
        platform: process.platform,
        cwd: process.cwd(),
        env: {
            NODE_ENV: process.env.NODE_ENV,
            PYTHONPATH: process.env.PYTHONPATH
        },
        logs: logFile
    });
});

// GET / - Redirigir a índice
app.get('/', (req, res) => {
    res.redirect('/index.html');
});

/**
 * ERROR HANDLER
 */
app.use((err, req, res, next) => {
    log(`❌ Express error: ${err.message}`);
    res.status(500).json({ error: err.message });
});

/**
 * INICIAR SERVIDOR
 */
app.listen(PORT, () => {
    // Crear carpeta de logs si no existe
    try {
        const logsDir = path.join(__dirname, '..', 'logs');
        if (!fs.existsSync(logsDir)) {
            fs.mkdirSync(logsDir, { recursive: true });
        }
    } catch (e) {
        console.error('Error creando carpeta logs:', e);
    }

    log(`
╔════════════════════════════════════════════════════════════╗
║     TRADEPLUS V5.0 - JOURNAL TEST SERVER                  ║
║     🚀 Puerto: ${PORT}                                          ║
║     📍 http://localhost:${PORT}                               ║
║     🔄 Datos en VIVO desde Schwab + Coinbase              ║
║     📊 Dashboard: http://localhost:${PORT}/dashboard         ║
╚════════════════════════════════════════════════════════════╝
    `);

    // Cargar datos iniciales
    fetchJournalData()
        .then(() => log('✅ Datos iniciales cargados'))
        .catch(err => log(`⚠️ Error inicial: ${err.message}`));

    // Actualizar cada 30 segundos
    setInterval(() => {
        fetchJournalData()
            .catch(err => log(`⚠️ Error en refresh: ${err.message}`));
    }, 30000);
});

module.exports = app;
