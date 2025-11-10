"""
Test JWT WebSocket - Debug del payload
"""
import json
import base64
from hub.managers.coinbase_jwt_manager import CoinbaseJWTManager

def decode_jwt(token):
    """Decodificar JWT para ver su contenido"""
    parts = token.split('.')
    if len(parts) != 3:
        return None, None, None
    
    try:
        # Header
        header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
        
        # Payload
        payload_part = parts[1]
        payload_part += '=' * (4 - len(payload_part) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_part))
        
        return header, payload, parts[2][:20]
    except:
        return None, None, None

# Crear manager
jwt_mgr = CoinbaseJWTManager(config_path='hub')

# Generar JWT para REST API
print("\n=== JWT para REST API ===")
rest_jwt = jwt_mgr.generate_jwt()
header, payload, sig = decode_jwt(rest_jwt)
print("Header:", header)
print("Payload:", json.dumps(payload, indent=2))
print("Signature (primeras 20 chars):", sig)

# Generar JWT para WebSocket
print("\n=== JWT para WebSocket ===")
ws_jwt = jwt_mgr.generate_jwt_for_websocket()
header, payload, sig = decode_jwt(ws_jwt)
print("Header:", header)
print("Payload:", json.dumps(payload, indent=2))
print("Signature (primeras 20 chars):", sig)
