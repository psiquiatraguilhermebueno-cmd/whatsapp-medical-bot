#!/usr/bin/env python3
"""
WhatsApp Medical Reminder Bot
Ponto de entrada principal para deploy
"""

import os
import sys

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

