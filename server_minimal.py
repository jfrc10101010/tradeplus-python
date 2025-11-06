from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

print("=== SERVIDOR MINIMAL INICIADO ===")

@app.route('/api/health', methods=['GET'])
def health():
    print("Health endpoint llamado")
    return jsonify({"status": "ok"})

@app.route('/api/test', methods=['GET'])
def test():
    print("Test endpoint llamado")
    return jsonify({"status": "test working"})

if __name__ == '__main__':
    print("=== INICIANDO SERVIDOR EN PUERTO 5002 ===")
    app.run(debug=True, port=5002, host='127.0.0.1')