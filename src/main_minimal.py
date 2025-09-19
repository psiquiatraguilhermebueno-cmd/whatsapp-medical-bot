import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({
        "service": "whatsapp-medical-bot",
        "status": "running",
        "version": "1.0.0"
    })

@app.route("/health")
def health():
    return jsonify({
        "service": "whatsapp-medical-bot",
        "status": "healthy",
        "version": "1.0.0",
        "database": "ok",
        "admin_enabled": True
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
