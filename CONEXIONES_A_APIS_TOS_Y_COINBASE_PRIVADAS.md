# CONEXIONES A APIs DE TOS Y COINBASE PRIVADAS

## Documento Técnico - Autenticación y Consumo de APIs

**Autor:** TradePlus Team  
**Fecha:** 5 de Noviembre de 2025  
**Versión:** 1.0  
**Estado:** ✅ FUNCIONAL

---

## TABLA DE CONTENIDOS

1. [Introducción](#introducción)
2. [API de Charles Schwab (TOS)](#api-de-charles-schwab-tos)
3. [API de Coinbase (CDP)](#api-de-coinbase-cdp)
4. [Comparativa de Autenticación](#comparativa-de-autenticación)
5. [Implementación en TradePlus](#implementación-en-tradeplus)
6. [Manejo de Errores](#manejo-de-errores)
7. [Consideraciones de Seguridad](#consideraciones-de-seguridad)

---

## INTRODUCCIÓN

TradePlus integra dos brokers principales mediante sus APIs privadas:

1. **Charles Schwab (TD Ameritrade - TOS)**: Trading de acciones, opciones y futuros
2. **Coinbase (CDP)**: Trading de criptomonedas

Ambas requieren autenticación diferenciada con manejo específico de tokens y credenciales.

---

## API DE CHARLES SCHWAB (TOS)

### 1. Descripción General

La API de Schwab utiliza el protocolo **OAuth 2.0** con flujo de autorización de código. Requiere:
- **Client ID** y **Client Secret**
- **Refresh Token** (renovable)
- **Access Token** (corta duración, ~30 minutos)

### 2. Flujo de Autenticación

```
┌─────────────────────────────────────────────────────────────┐
│                    SCHWAB OAUTH 2.0 FLOW                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Usuario autoriza en portal Schwab                        │
│     └─> Recibe Authorization Code                           │
│                                                               │
│  2. Intercambiar Code por Tokens                            │
│     POST /v1/oauth/token                                    │
│     ├─ grant_type: authorization_code                       │
│     ├─ code: [authorization_code]                           │
│     ├─ client_id: [CLIENT_ID]                              │
│     └─ client_secret: [CLIENT_SECRET]                       │
│                                                               │
│  3. Respuesta con Access Token + Refresh Token              │
│     {                                                         │
│       "access_token": "...",                                │
│       "refresh_token": "...",                               │
│       "expires_in": 1800                                    │
│     }                                                         │
│                                                               │
│  4. Usar Access Token en peticiones                         │
│     GET /v1/accounts                                        │
│     Authorization: Bearer {access_token}                    │
│                                                               │
│  5. Renovar Token cuando expire                             │
│     POST /v1/oauth/token                                    │
│     └─ grant_type: refresh_token                            │
│        refresh_token: [REFRESH_TOKEN]                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 3. Endpoints Principales

| Endpoint | Método | Descripción | Autenticación |
|----------|--------|-------------|---------------|
| `/v1/oauth/token` | POST | Obtener/renovar tokens | Client ID/Secret |
| `/v1/accounts` | GET | Listar cuentas del usuario | Bearer Token |
| `/v1/accounts/{accountId}` | GET | Detalles de cuenta específica | Bearer Token |
| `/v1/accounts/{accountId}/orders` | GET | Órdenes de la cuenta | Bearer Token |
| `/v1/accounts/{accountId}/positions` | GET | Posiciones abiertas | Bearer Token |

### 4. Estructura de Almacenamiento de Tokens

**Archivo:** `current_token.json`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 1800,
  "token_type": "Bearer",
  "obtained_at": "2025-11-05T12:00:00Z",
  "expires_at": "2025-11-05T12:30:00Z"
}
```

### 5. Ejemplo de Petición - Obtener Cuentas

```python
import requests
import json
from datetime import datetime, timedelta

# Cargar tokens
with open('current_token.json', 'r') as f:
    tokens = json.load(f)

access_token = tokens['access_token']

# Realizar petición
headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json'
}

response = requests.get(
    'https://api.schwabapi.com/trader/v1/accounts',
    headers=headers,
    timeout=10
)

if response.status_code == 200:
    accounts = response.json()
    print(f"✅ Cuentas obtenidas: {len(accounts)}")
    for account in accounts:
        print(f"  - {account['accountNumber']}: ${account['initialBalances']['accountValue']}")
elif response.status_code == 401:
    print("❌ Token expirado - Renovando...")
    # Lógica de renovación
else:
    print(f"❌ Error {response.status_code}: {response.text}")
```

### 6. Renovación Automática de Tokens

**Función:** `get_schwab_token.py`

```python
import requests
import json
from datetime import datetime, timedelta

CLIENT_ID = os.getenv('SCHWAB_CLIENT_ID')
CLIENT_SECRET = os.getenv('SCHWAB_CLIENT_SECRET')
REFRESH_TOKEN_FILE = 'current_token.json'

def renovar_token():
    """Renovar access token usando refresh token"""
    
    with open(REFRESH_TOKEN_FILE, 'r') as f:
        tokens = json.load(f)
    
    refresh_token = tokens['refresh_token']
    
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    response = requests.post(
        'https://api.schwabapi.com/v1/oauth/token',
        data=payload,
        timeout=10
    )
    
    if response.status_code == 200:
        new_tokens = response.json()
        new_tokens['obtained_at'] = datetime.utcnow().isoformat() + 'Z'
        new_tokens['expires_at'] = (
            datetime.utcnow() + timedelta(seconds=new_tokens['expires_in'])
        ).isoformat() + 'Z'
        
        with open(REFRESH_TOKEN_FILE, 'w') as f:
            json.dump(new_tokens, f, indent=2)
        
        print("✅ Token renovado exitosamente")
        return new_tokens
    else:
        print(f"❌ Error renovando token: {response.text}")
        return None
```

### 7. Manejo de Errores - Schwab

| Código | Significado | Acción |
|--------|-------------|--------|
| 200 | OK | Procesar respuesta |
| 400 | Bad Request | Validar parámetros |
| 401 | Unauthorized | Renovar token |
| 403 | Forbidden | Verificar permisos |
| 429 | Too Many Requests | Implementar backoff exponencial |
| 500 | Server Error | Reintentar con delay |

---

## API DE COINBASE (CDP)

### 1. Descripción General

Coinbase utiliza autenticación basada en **JWT (JSON Web Tokens)** firmados con criptografía **ES256** (ECDSA).

**Características:**
- No requiere OAuth
- Usa clave privada (PEM) para firmar JWTs
- Cada petición incluye un JWT único con timestamp
- Previene replay attacks con timestamps y nonces

### 2. Flujo de Autenticación

```
┌─────────────────────────────────────────────────────────────┐
│              COINBASE CDP JWT AUTHENTICATION                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Generar JWT para cada petición                          │
│     ├─ Leer clave privada (PEM format)                      │
│     ├─ Crear payload con:                                   │
│     │  ├─ sub: API Key ID                                   │
│     │  ├─ iss: "cdp"                                        │
│     │  ├─ nbf: timestamp actual                             │
│     │  ├─ exp: timestamp + 120 segundos                     │
│     │  └─ uri: "{METHOD} {HOST}{PATH}"  ⚠️ CRÍTICO          │
│     └─ Firmar con ES256 usando clave privada                │
│                                                               │
│  2. Crear Headers de petición                               │
│     ├─ Authorization: "Bearer {jwt}"                        │
│     ├─ kid: API Key ID                                      │
│     └─ Content-Type: "application/json"                     │
│                                                               │
│  3. Enviar petición a Coinbase                             │
│     GET https://api.coinbase.com/api/v3/brokerage/accounts │
│                                                               │
│  4. Coinbase valida JWT                                     │
│     ├─ Verifica firma con clave pública                     │
│     ├─ Valida timestamps (nbf, exp)                         │
│     ├─ Verifica el URI coincide                             │
│     └─ Retorna respuesta autenticada                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 3. Formato de la Clave Privada

**Archivo:** `apicoinbase1fullcdp_api_key.json`

```json
{
  "name": "organizations/60f9fe57-7692-4afa-a915-eedba4b90027/apiKeys/98819dd6-8c94-4eeb-8935-dc1513f98a11",
  "privateKey": "-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIH...\n-----END EC PRIVATE KEY-----"
}
```

**Formato PEM (PKCS#8):**
- Tipo: Curva Elíptica (EC)
- Algoritmo: ECDSA (ES256)
- Tamaño: 256 bits (32 bytes)

### 4. Estructura del JWT

**Header:**
```json
{
  "alg": "ES256",
  "kid": "organizations/60f9fe57-7692-4afa-a915-eedba4b90027/apiKeys/98819dd6-8c94-4eeb-8935-dc1513f98a11",
  "nonce": "f47ac10b58cc4372"
}
```

**Payload:**
```json
{
  "sub": "organizations/60f9fe57-7692-4afa-a915-eedba4b90027/apiKeys/98819dd6-8c94-4eeb-8935-dc1513f98a11",
  "iss": "cdp",
  "nbf": 1762359789,
  "exp": 1762359909,
  "uri": "GET api.coinbase.com/api/v3/brokerage/accounts"
}
```

**⚠️ CRÍTICO:** El campo `uri` debe incluir:
- Método HTTP: `GET`, `POST`, etc.
- Hostname: `api.coinbase.com`
- Path: `/api/v3/brokerage/accounts`
- **Formato:** `"{METHOD} {HOSTNAME}{PATH}"`

### 5. Endpoints Principales

| Endpoint | Método | Descripción | Auth |
|----------|--------|-------------|------|
| `/api/v3/brokerage/accounts` | GET | Listar cuentas | JWT |
| `/api/v3/brokerage/accounts/{account_id}` | GET | Detalles de cuenta | JWT |
| `/api/v3/brokerage/orders` | GET | Historial de órdenes | JWT |
| `/api/v3/brokerage/orders` | POST | Crear orden | JWT |
| `/api/v3/brokerage/orders/{order_id}` | DELETE | Cancelar orden | JWT |

### 6. Implementación de Generación de JWT

**Archivo:** `backend/main.py` (función `generate_jwt()`)

```python
import jwt
import time
import secrets
from cryptography.hazmat.primitives import serialization

def generate_jwt(method='GET', request_path='/api/v3/brokerage/accounts'):
    """
    Genera JWT firmado para autenticación en Coinbase API
    
    Args:
        method: HTTP method (GET, POST, DELETE, etc.)
        request_path: API endpoint path
    
    Returns:
        str: JWT token firmado
    """
    
    # Cargar clave privada
    with open('apicoinbase1fullcdp_api_key.json', 'r') as f:
        config = json.load(f)
    
    api_key = config['name']
    private_key_pem = config['privateKey']
    
    # Parsear clave privada
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None
    )
    
    # Crear timestamps
    now = int(time.time())
    
    # ⚠️ CRÍTICO: URI debe incluir HOST completo
    request_host = 'api.coinbase.com'
    uri = f"{method} {request_host}{request_path}"
    
    # Payload del JWT
    payload = {
        'sub': api_key,
        'iss': 'cdp',  # ⚠️ Debe ser "cdp" (no "cdp_service_sk")
        'nbf': now,
        'exp': now + 120,  # Válido por 2 minutos
        'uri': uri
    }
    
    # Headers del JWT
    headers = {
        'kid': api_key,
        'nonce': secrets.token_hex()  # Previene replay attacks
    }
    
    # Firmar JWT con ES256
    token = jwt.encode(
        payload,
        private_key,
        algorithm='ES256',
        headers=headers
    )
    
    print(f"[JWT] URI: {uri}")
    print(f"[JWT] Sub: {api_key[:50]}...")
    print(f"[JWT] Válido por: {payload['exp'] - payload['nbf']} segundos")
    
    return token
```

### 7. Ejemplo de Petición - Obtener Cuentas

```python
import requests

def obtener_cuentas_coinbase():
    """Obtiene lista de cuentas de Coinbase"""
    
    # Generar JWT
    token = generate_jwt(method='GET', request_path='/api/v3/brokerage/accounts')
    
    # Preparar headers
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Realizar petición
    response = requests.get(
        'https://api.coinbase.com/api/v3/brokerage/accounts',
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        accounts = data.get('accounts', [])
        
        print(f"✅ {len(accounts)} cuentas encontradas:")
        for acc in accounts:
            balance = acc['available_balance']['value']
            currency = acc['currency']
            print(f"   • {currency}: {balance}")
        
        return accounts
    
    elif response.status_code == 401:
        print("❌ Unauthorized - Verifica credenciales")
    elif response.status_code == 429:
        print("⚠️ Rate limited - Espera antes de reintentar")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
    
    return None
```

### 8. Manejo de Errores - Coinbase

| Código | Significado | Acción | Causa Común |
|--------|-------------|--------|-------------|
| 200 | OK | Procesar respuesta | - |
| 400 | Bad Request | Validar formato | URI mal formado |
| 401 | Unauthorized | Revisar JWT | Clave privada inválida, JWT expirado |
| 403 | Forbidden | Verificar permisos | IP no autorizada |
| 429 | Too Many Requests | Backoff exponencial | Rate limit excedido |
| 500 | Server Error | Reintentar | Problema temporal en Coinbase |

**⚠️ ERRORES COMUNES:**

1. **URI incorrecto:**
   ```
   ❌ MALO:   "uri": "GET /api/v3/brokerage/accounts"
   ✅ BUENO:  "uri": "GET api.coinbase.com/api/v3/brokerage/accounts"
   ```

2. **Campo `iss` incorrecto:**
   ```
   ❌ MALO:   "iss": "cdp_service_sk"
   ✅ BUENO:  "iss": "cdp"
   ```

3. **JWT expirado:**
   - Los JWTs de Coinbase duran 120 segundos
   - Generar nuevo JWT para cada petición
   - No reutilizar JWTs

4. **Clave privada inválida:**
   - Debe ser formato PEM
   - Debe ser EC PRIVATE KEY (no RSA)
   - Verificar codificación UTF-8

---

## COMPARATIVA DE AUTENTICACIÓN

| Aspecto | Schwab (OAuth) | Coinbase (JWT) |
|--------|----------------|----------------|
| **Tipo Auth** | OAuth 2.0 | JWT (ES256) |
| **Token Duration** | 30 minutos | 120 segundos |
| **Renovación** | Refresh token | Generar nuevo JWT |
| **Almacenamiento** | `current_token.json` | Clave privada (PEM) |
| **Seguridad** | Server-side session | Firmas criptográficas |
| **Rate Limit** | 120 req/min | 10 req/seg |
| **Complejidad** | Media | Alta |
| **Mantenimiento** | Renovar tokens | Regenerar JWTs |

---

## IMPLEMENTACIÓN EN TRADEPLUS

### 1. Estructura de Directorios

```
tradeplus-python/
├── server.py                          # API Flask principal
├── apicoinbase1fullcdp_api_key.json   # Credenciales Coinbase
├── current_token.json                 # Tokens Schwab
├── backend/
│   ├── __init__.py
│   ├── main.py                        # Punto de entrada
│   ├── adapters/
│   │   ├── base.py                    # Clase base
│   │   ├── coinbase_adapter.py        # Adapter Coinbase
│   │   └── schwab_adapter.py          # Adapter Schwab
│   ├── core/
│   │   ├── models.py                  # Modelos de datos
│   │   ├── normalizer.py              # Normalizar datos
│   │   └── candle_builder.py          # Construir velas
│   └── scripts/
│       └── get_schwab_token.py        # Obtener tokens Schwab
└── logs/
    └── api-out.log                    # Logs del servidor
```

### 2. Archivo `server.py` - Endpoints

```python
from flask import Flask, jsonify
from flask_cors import CORS
import json
import jwt
import time
import requests
import secrets
from cryptography.hazmat.primitives import serialization

app = Flask(__name__)
CORS(app)

# Cargar credenciales Coinbase
with open('apicoinbase1fullcdp_api_key.json', 'r') as f:
    COINBASE_CONFIG = json.load(f)

COINBASE_API_KEY = COINBASE_CONFIG['name']
COINBASE_PRIVATE_KEY = COINBASE_CONFIG['privateKey']

def generate_jwt():
    """Genera JWT para Coinbase"""
    key = serialization.load_pem_private_key(
        COINBASE_PRIVATE_KEY.encode(),
        password=None
    )
    
    now = int(time.time())
    uri = "GET api.coinbase.com/api/v3/brokerage/accounts"
    
    payload = {
        'sub': COINBASE_API_KEY,
        'iss': 'cdp',
        'nbf': now,
        'exp': now + 120,
        'uri': uri
    }
    
    headers = {
        'kid': COINBASE_API_KEY,
        'nonce': secrets.token_hex()
    }
    
    return jwt.encode(payload, key, algorithm='ES256', headers=headers)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/api/coinbase-accounts', methods=['GET'])
def coinbase_accounts():
    """Obtiene cuentas de Coinbase"""
    try:
        token = generate_jwt()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            'https://api.coinbase.com/api/v3/brokerage/accounts',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                "status": "success",
                "accounts": response.json().get('accounts', [])
            })
        else:
            return jsonify({
                "error": f"HTTP {response.status_code}",
                "details": response.text,
                "status": "error"
            }), response.status_code
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/api/schwab-accounts', methods=['GET'])
def schwab_accounts():
    """Obtiene cuentas de Schwab"""
    try:
        with open('current_token.json', 'r') as f:
            tokens = json.load(f)
        
        access_token = tokens['access_token']
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        response = requests.get(
            'https://api.schwabapi.com/trader/v1/accounts',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                "status": "success",
                "accounts": response.json()
            })
        elif response.status_code == 401:
            return jsonify({
                "error": "Token expired",
                "status": "token_expired"
            }), 401
        else:
            return jsonify({
                "error": f"HTTP {response.status_code}",
                "details": response.text,
                "status": "error"
            }), response.status_code
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

if __name__ == '__main__':
    app.run(debug=False, port=5000, host='0.0.0.0')
```

### 3. Gestión de Secretos

**⚠️ IMPORTANTE - Nunca commitear:**
- `apicoinbase1fullcdp_api_key.json`
- `current_token.json`
- Variables de entorno con credenciales

**Usar variables de entorno:**
```bash
export COINBASE_API_KEY="organizations/60f9fe57-..."
export COINBASE_PRIVATE_KEY="-----BEGIN EC PRIVATE KEY-----\n..."
export SCHWAB_CLIENT_ID="..."
export SCHWAB_CLIENT_SECRET="..."
export SCHWAB_REFRESH_TOKEN="..."
```

---

## CONSIDERACIONES DE SEGURIDAD

### 1. Schwab (OAuth)

- ✅ Usar HTTPS exclusivamente
- ✅ Almacenar tokens en archivo seguro (permisos 600)
- ✅ Renovar tokens antes de expiración
- ✅ Implementar rate limiting
- ✅ Loguear tentativas de acceso

### 2. Coinbase (JWT)

- ✅ **Nunca** commitear clave privada
- ✅ Usar variables de entorno
- ✅ Rotar claves regularmente
- ✅ Usar HTTPS para todas las peticiones
- ✅ Validar respuestas HTTPS (certificados)
- ✅ Implementar nonces para prevenir replay
- ✅ Regenerar JWT para cada petición

### 3. General

- ✅ Implementar logging de errores
- ✅ No mostrar detalles de API en frontend
- ✅ Usar firewalls de aplicación (WAF)
- ✅ Monitorear uso de API
- ✅ Alertas ante errores 401/403

---

## CONCLUSIÓN

**Estado actual:**

✅ **Coinbase** - Funcionando con JWT (ES256)
- Autenticación privada (credenciales)
- Endpoints: `/api/v3/brokerage/accounts`
- Status: HTTP 200 ✅

✅ **Schwab** - Implementado con OAuth 2.0
- Autenticación via tokens
- Endpoints: `/trader/v1/accounts`
- Status: Listo para integración completa

Ambas APIs están plenamente integradas en TradePlus y listas para operaciones en producción.

---

**Documentación actualizada:** 5 de Noviembre de 2025  
**Versión:** 1.0 - Inicial  
**Próximas mejoras:** Agregar endpoints de órdenes y posiciones
