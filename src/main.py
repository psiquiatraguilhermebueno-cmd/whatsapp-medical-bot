# src/main.py
import os
import sys
import logging
from sqlalchemy import text

# Garante que "src" esteja no path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# ---- DB base
from src.models.user import db

# ---- Blueprints principais
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

# ---- Admin UI (import direto do módulo correto; se falhar, não derruba o app)
admin_bp = None
try:
    from src.admin.routes.admin import admin_bp  # o blueprint do Admin
except Exception as e:
    print(f"[BOOT][WARN] admin_bp not loaded: {e}")

# ---- Modelos que precisam existir antes do create_all()
# (1) tabela 'patient' (singular), usada por FKs de outros módulos
try:
    from src.models.patient import Patient
except Exception as e:
    print(f"[BOOT][WARN] patient model not loaded: {e}")

# (2) tabela 'patients' (plural), esperada pelo Admin
try:
    from src.models.patients import Patients
except Exception as e:
    print(f"[BOOT][WARN] patients model not loaded: {e}")

# (3) campanhas WhatsApp (nomes esperados pelo Admin: WACampaign*)
try:
    from src.admin.models.campaign import (
        WACampaign, WACampaignRecipient, WACampaignRun
    )
except Exception as e:
    print(f"[BOOT][WARN] campaign models not loaded: {e}")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))
app.config["SECRET_KEY"] = os.getenv("APP_SECRET", "change-me")

# ---- Config DB
database_url = os.getenv("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url or f"sqlite:///{os.path.join(os.path.dirname(__file__), 'app.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ---- Extensões
CORS(app)
db.init_app(app)

# ---- Cria as tabelas (idempotente)
with app.app_context():
    try:
        db.create_all()
        logger.info("✅ DB create_all executado: tabelas garantidas")
    except Exception:
        logger.exception("⚠️ DB create_all falhou")

# ---- Registra rotas
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

if admin_bp:
    app.register_blueprint(admin_bp, url_prefix="/admin")
else:
    @app.route("/admin")
    @app.route("/admin/")
    def admin_unavailable():
        return jsonify({
            "ok": False,
            "error": "Admin UI not loaded",
            "hint": "verifique src/admin/routes/admin.py e dependências"
        }), 503

@app.route("/")
def index():
    return jsonify({
        "service":"whatsapp-medical-bot",
        "status":"running",
        "version":"1.0.0",
        "admin_url":"/admin"
    })

@app.route("/health")
def health():
    try:
        with app.app_context():
            conn = db.engine.connect()
            conn.execute(text("SELECT 1"))
            conn.close()
        db_status = "connected"
    except Exception as e:
        logger.exception("DB health check failed")
        db_status = f"error: {e.__class__.__name__}"
    return jsonify({
        "service":"whatsapp-medical-bot",
        "status":"healthy",
        "version":"1.0.0",
        "database":db_status,
        "admin_enabled": bool(admin_bp)
    })

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

def _safe_import_schedulers():
    init_campaign_scheduler = None
    init_uetg_scheduler = None
    try:
        from src.admin.services.scheduler_service import init_campaign_scheduler as _ics
        init_campaign_scheduler = _ics
    except Exception as e:
        logger.warning(f"[BOOT][WARN] Campaign scheduler not loaded: {e}")
    try:
        from src.jobs.uetg_scheduler import init_scheduler as _iu
        init_uetg_scheduler = _iu
    except Exception as e:
        logger.warning(f"[BOOT][WARN] u-ETG scheduler not loaded: {e}")
    return init_campaign_scheduler, init_uetg_scheduler

if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
        except Exception:
            logger.exception("Error creating tables on startup")
        init_campaign_scheduler, init_uetg_scheduler = _safe_import_schedulers()
        if init_uetg_scheduler:
            try:
                init_uetg_scheduler()
                logger.info("✅ u-ETG Scheduler initialized")
            except Exception:
                logger.exception("Error initializing u-ETG scheduler")
        if init_campaign_scheduler:
            try:
                init_campaign_scheduler()
                logger.info("✅ Campaign Scheduler initialized")
            except Exception as e:
                logger.warning(f"Campaign scheduler disabled: {e}")
    port = int(os.getenv("PORT", 8080))
    debug = os.getenv("FLASK_ENV") == "development"
    logger.info(f"Starting on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)
