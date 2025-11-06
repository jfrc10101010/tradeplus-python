// coinbase-server.js - SERVIDOR COINBASE AISLADO
// ❌ NO TOCA NADA DE SCHWAB

const https = require('https');
const { sign } = require('jsonwebtoken');
const crypto = require('crypto');
const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

console.log('🚀 Iniciando servidor Coinbase aislado...');

// 🔐 CREDENCIALES COINBASE - DEL DOCUMENTO QUE ENCONTRASTE
const API_KEY = "organizations/60f9fe57-7692-4afa-a915-eedba4b90027/apiKeys/f8a591c0-fccc-4eb6-9d3f-6e42f7ab2c6e";
const SIGNING_KEY = `-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIFFB9yqMSLEvsI6xNlpFNgJo5AIsDq8arOKDyHXEs6tjoAoGCCqGSM49
AwEHoUQDQgAEBVnuU0a5qi+4YzqDWFD0KHM0gPIpZVt3d4VAFRJ9WeVS46DKUBkH
d2hPPXNv+oUVWM5RENslFPG/GTCh6jH+Rw==
-----END EC PRIVATE KEY-----`;

console.log('✅ Credenciales Coinbase cargadas');

// 🔐 Generar JWT Token
function generateJWT(method, requestPath) {
    const timestamp = Math.floor(Date.now() / 1000);
    
    const header = {
        alg: 'ES256',
        kid: API_KEY,
        typ: 'JWT',
        nonce: crypto.randomBytes(16).toString('hex')
    };

    const jwtUri = `${method} ${requestPath}`;

    const payload = {
        iss: 'cdp',
        nbf: timestamp,
        exp: timestamp + 120,
        sub: API_KEY,
        uri: jwtUri
    };

    return sign(payload, SIGNING_KEY, {
        algorithm: 'ES256',
        header: header
    });
}

// 🔐 Hacer request autenticado a Coinbase
function makeCoinbaseRequest(method, path, body = null) {
    return new Promise((resolve, reject) => {
        const token = generateJWT(method, path);

        const options = {
            hostname: 'api.coinbase.com',
            port: 443,
            path: path,
            method: method,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'User-Agent': 'HAIKU/5.0'
            }
        };

        const req = https.request(options, (response) => {
            let data = '';
            response.on('data', (chunk) => { data += chunk; });
            response.on('end', () => {
                try {
                    const parsed = JSON.parse(data);
                    if (response.statusCode >= 200 && response.statusCode < 300) {
                        resolve(parsed);
                    } else {
                        reject(new Error(`HTTP ${response.statusCode}: ${JSON.stringify(parsed)}`));
                    }
                } catch (e) {
                    reject(e);
                }
            });
        });

        req.on('error', reject);
        
        if (body) {
            req.write(JSON.stringify(body));
        }
        req.end();
    });
}

// ✅ ENDPOINT 1: Obtener cuentas Coinbase
app.get('/api/coinbase/accounts', async (req, res) => {
    try {
        console.log('📍 Solicitando cuentas Coinbase...');
        const data = await makeCoinbaseRequest('GET', '/api/v3/brokerage/accounts');
        console.log('✅ Cuentas obtenidas');
        res.json({ status: 'ok', data });
    } catch (error) {
        console.error('❌ Error:', error.message);
        res.status(500).json({ status: 'error', error: error.message });
    }
});

// ✅ ENDPOINT 2: Obtener órdenes
app.get('/api/coinbase/orders', async (req, res) => {
    try {
        console.log('📍 Solicitando órdenes Coinbase...');
        const data = await makeCoinbaseRequest('GET', '/api/v3/brokerage/orders/historical/batch');
        console.log('✅ Órdenes obtenidas');
        res.json({ status: 'ok', data });
    } catch (error) {
        console.error('❌ Error:', error.message);
        res.status(500).json({ status: 'error', error: error.message });
    }
});

// ✅ ENDPOINT 3: Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'ok',
        service: 'HAIKU Coinbase Server',
        version: '5.0',
        timestamp: new Date().toISOString()
    });
});

// Escuchar en puerto DIFERENTE al de Schwab (6000 en lugar de 5000)
const PORT = 6000;
app.listen(PORT, () => {
    console.log('');
    console.log('╔════════════════════════════════════════╗');
    console.log('║  🪙 HAIKU COINBASE SERVER v5.0         ║');
    console.log('╚════════════════════════════════════════╝');
    console.log('');
    console.log(`✅ Servidor escuchando en puerto ${PORT}`);
    console.log('');
    console.log('📍 Endpoints disponibles:');
    console.log(`   GET  http://localhost:${PORT}/api/coinbase/accounts`);
    console.log(`   GET  http://localhost:${PORT}/api/coinbase/orders`);
    console.log(`   GET  http://localhost:${PORT}/health`);
    console.log('');
    console.log('⚠️  Puerto DIFERENTE al de Schwab:5000');
    console.log('✅ Schwab sigue corriendo en puerto 5000');
    console.log('');
});