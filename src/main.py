import os
import sys
import logging
from sqlalchemy import text

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from datetime import datetime

# Project extensions and blueprints
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))
app.config["SECRET_KEY"] = os.getenv("APP_SECRET", "change-me")

database_url = os.getenv("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url or f"sqlite:///{os.path.join(os.path.dirname(__file__), 'app.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app)
db.init_app(app)

# Register blueprints
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
    return jsonify({"service":"whatsapp-medical-bot","status":"running","version":"1.0.0","admin_url":"/admin"})

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
    return jsonify({"service":"whatsapp-medical-bot","status":"healthy","version":"1.0.0","database":db_status,"admin_enabled":True})

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created/verified")
        except Exception:
            logger.exception("Error creating tables")
        try:
            init_scheduler()
            logger.info("u-ETG Scheduler initialized")
        except Exception:
            logger.exception("Error initializing u-ETG scheduler")
        try:
            init_campaign_scheduler()
            logger.info("Campaign Scheduler initialized")
        except Exception as e:
            logger.warning(f"Campaign scheduler disabled: {e}")
    port = int(os.getenv("PORT", 8080))
    debug = os.getenv("FLASK_ENV") == "development"
    logger.info(f"Starting on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)
