from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

print("=== SERVIDOR SIMPLE SIN DEBUG ===")

@app.route('/api/health', methods=['GET'])
def health():
    print("Health endpoint llamado")
    return jsonify({"status": "ok", "message": "Server working!"})

if __name__ == '__main__':
    print("=== INICIANDO SERVIDOR EN PUERTO 5003 ===")
    app.run(debug=False, port=5003, host='127.0.0.1')