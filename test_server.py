#!/usr/bin/env python3

print("=== TESTING SERVER ===")

try:
    print("1. Importing Flask...")
    from flask import Flask, jsonify
    from flask_cors import CORS
    print("   ✅ Flask imports OK")
    
    print("2. Creating Flask app...")
    app = Flask(__name__)
    CORS(app)
    print("   ✅ Flask app created")
    
    print("3. Defining health route...")
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({"status": "ok"})
    print("   ✅ Health route defined")
    
    print("4. Starting server...")
    app.run(debug=False, port=5004, host='127.0.0.1')
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
