#!/usr/bin/env python3
"""
Cria versão limpa e funcional do main.py
"""

def create_clean_main():
    """
    Cria main.py limpo e funcional
    """
    
    clean_main = '''import os
import sys
import logging

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
import requests
from datetime import datetime
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.patient import patient_bp
from src.routes.reminder import reminder_bp
from src.routes.response import response_bp
from src.routes.scale import scale_bp
from src.routes.whatsapp import whatsapp_bp
from src.routes.telegram import telegram_bp
from src.routes.medication import medication_bp
from src.routes.mood import mood_bp
from src.routes.scheduler import scheduler_bp
from src.routes.iclinic import iclinic_bp
from src.routes.admin_tasks import admin_tasks_bp
from src.routes.admin_patient import admin_patient_bp
from src.admin.routes import admin_bp
from src.admin.services.scheduler_service import init_campaign_scheduler
from src.jobs.uetg_scheduler import init_scheduler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))
app.config["SECRET_KEY"] = "asdf#FGSgvasgf$5$WGT"

# Configuração do banco de dados
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Fix postgres:// to postgresql:// for SQLAlchemy 1.4+
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    logger.info("Using PostgreSQL database from DATABASE_URL")
else:
    # SQLite para desenvolvimento
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{os.path.join(os.path.dirname(__file__), 'app.db')}"
    )
    logger.info("Using SQLite database for development")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializar extensões
CORS(app)
db.init_app(app)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix="/api/users")
app.register_blueprint(patient_bp, url_prefix="/api/patients")
app.register_blueprint(reminder_bp, url_prefix="/api/reminders")
app.register_blueprint(response_bp, url_prefix="/api/responses")
app.register_blueprint(scale_bp, url_prefix="/api/scales")
app.register_blueprint(whatsapp_bp, url_prefix="/api/whatsapp")
app.register_blueprint(telegram_bp, url_prefix="/api/telegram")
app.register_blueprint(medication_bp, url_prefix="/api/medications")
app.register_blueprint(mood_bp, url_prefix="/api/moods")
app.register_blueprint(scheduler_bp, url_prefix="/api/scheduler")
app.register_blueprint(iclinic_bp, url_prefix="/api/iclinic")
app.register_blueprint(admin_tasks_bp, url_prefix="/admin/api")
app.register_blueprint(admin_patient_bp, url_prefix="/admin/api")
app.register_blueprint(admin_bp, url_prefix="/admin")

@app.route("/")
def index():
    """Página inicial"""
    return jsonify({
        "service": "whatsapp-medical-bot",
        "status": "running",
        "version": "1.0.0",
        "admin_url": "/admin"
    })

@app.route("/health")
def health():
    """Health check endpoint"""
    try:
        # Testar conexão com banco
        with app.app_context():
            db.engine.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"
    
    return jsonify({
        "service": "whatsapp-medical-bot",
        "status": "healthy",
        "version": "1.0.0",
        "database": db_status,
        "admin_enabled": True
    })

@app.route("/static/<path:filename>")
def static_files(filename):
    """Servir arquivos estáticos"""
    return send_from_directory(app.static_folder, filename)

if __name__ == "__main__":
    # Criar tabelas na inicialização
    with app.app_context():
        try:
            db.create_all()
            logger.info("✅ Database tables created/verified")
        except Exception as e:
            logger.error(f"⚠️ Error creating tables: {e}")
    
    # Inicializar scheduler u-ETG
    try:
        with app.app_context():
            init_scheduler()
            logger.info("✅ u-ETG Scheduler initialized")
    except Exception as e:
        logger.error(f"⚠️ Error initializing u-ETG scheduler: {e}")
        logger.warning("⚠️ Application will continue without automatic scheduler")
    
    # Inicializar scheduler de campanhas
    try:
        with app.app_context():
            init_campaign_scheduler()
            logger.info("✅ Campaign Scheduler initialized")
    except Exception as e:
        logger.error(f"Failed to initialize campaign scheduler: {e}")
        logger.warning("Campaign scheduler disabled - manual execution only")
    
    # Iniciar aplicação
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    
    logger.info(f"Starting WhatsApp Medical Bot on port {port}")
    logger.info(f"Admin UI available at: http://localhost:{port}/admin")
    logger.info(f"Health check: http://localhost:{port}/health")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
'''
    
    # Salvar main.py limpo
    with open('src/main.py', 'w', encoding='utf-8') as f:
        f.write(clean_main)
    
    print("✅ main.py limpo criado")
    return True

if __name__ == "__main__":
    create_clean_main()
