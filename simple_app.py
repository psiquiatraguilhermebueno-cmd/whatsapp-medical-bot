#!/usr/bin/env python3
"""
Aplicação simples para testar se o Railway está funcionando
"""

import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'whatsapp-medical-bot',
        'version': '1.0.0'
    })

@app.route('/')
def home():
    return jsonify({
        'message': 'WhatsApp Medical Bot API',
        'status': 'running'
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
