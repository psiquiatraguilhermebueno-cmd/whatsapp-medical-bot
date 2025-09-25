# src/main.py
import os
import sys
import logging
from datetime import datetime
from sqlalchemy import text

# --- PATH BASE (não alterar) ---
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify, send_from_directory  # noqa: E402
from flask_cors import CORS  # noqa: E402

# --- LOGGING BÁSICO ---
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("main")

# --- APP / CONFIG DB ---
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))
app.config["SECRET_KEY"] = os.getenv("APP_SECRET", "change-me")

# URL do banco (ajuste postgres:// -> postgresql://)
database_url = os.getenv("DATABASE_URL", "").strip()
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
if not database_url:
    database_url = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'app.db')}"
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Extensão do projeto
from src.models.user import db  # noqa: E402

CORS(app)

# ---------- BLUEPRINTS (núcleo do u-ETG + utilitários) ----------
from src.routes.user import user_bp  # noqa: E402
from src.routes.patient import patient_bp  # noqa: E402
from src.routes.reminder import reminder_bp  # noqa: E402
from src.routes.response import response_bp  # noqa: E402
from src.routes.scale import scale_bp  # noqa: E402
from src.routes.whatsapp import whatsapp_bp  # noqa: E402
from src.routes.telegram import telegram_bp  # noqa: E402
from src.routes.scheduler import scheduler_bp  # noqa: E402
from src.routes.iclinic import iclinic_bp  # noqa: E402

# ⚠️ MÓDULOS OPCIONAIS DESLIGADOS (evitar derrubar o boot)
# from src.routes.medication import medication_bp  # noqa: E402
# from src.routes.mood import mood_bp  # noqa: E402

# Admin APIs (REST usadas pela UI)
from src.routes.admin_tasks import admin_tasks_bp  # noqa: E402
from src.routes.admin_patient import admin_patient_bp  # noqa: E402

# Jobs / agendadores
from src.jobs.uetg_scheduler import init_scheduler  # noqa: E402

# Estado de boot
_MAIN_LOADED = False
_BOOT_ERROR = None


def _load_models_safely():
    """
    Importa MODELOS que participam do create_all(), de forma defensiva.
    Importante: sempre usar o alias Patient (tabela 'patients').
    """
    problems = []

    # Canônico: patients
    try:
        from src.models.patient import Patient  # noqa: F401
    except Exception as e:
        problems.append(f"patient model not loaded: {e}")

    # Núcleo que depende de patients
    try:
        from src.models.reminder import Reminder  # noqa: F401
    except Exception as e:
        problems.append(f"reminder model not loaded: {e}")

    try:
        from src.models.response import Response  # noqa: F401
    except Exception as e:
        problems.append(f"response model not loaded: {e}")

    try:
        from src.models.breathing_exercise import BreathingExercise  # noqa: F401
    except Exception as e:
        problems.append(f"breathing_exercise model not loaded: {e}")

    # ⚠️ NÃO importar campanhas, medication ou mood aqui.
    # Eles serão reintroduzidos depois que u-ETG estiver estável.

    if problems:
        for p in problems:
            logger.warning(p)


def _load_admin_blueprint():
    """Carrega a UI de Admin. Se falhar, deixa um endpoint de diagnóstico em /admin."""
    try:
        from src.admin.routes import admin_bp  # noqa: F401
        app.register_blueprint(admin_bp, url_prefix="/admin")
        logger.info("Admin UI loaded")
    except Exception as e:
        logger.warning(f"admin_bp not loaded: {e}")

        @app.route("/admin")
        @app.route("/admin/")
        def _admin_fallback():
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "Admin UI not loaded",
                        "hint": "verifique src/admin/routes/admin.py e dependências",
                        "detail": str(e),
                    }
                ),
                503,
            )


# ---------- Registro dos blueprints de API ----------
app.register_blueprint(user_bp, url_prefix="/api/users")
app.register_blueprint(patient_bp, url_prefix="/api/patients")
app.register_blueprint(reminder_bp, url_prefix="/api/reminders")
app.register_blueprint(response_bp, url_prefix="/api/responses")
app.register_blueprint(scale_bp, url_prefix="/api/scales")
app.register_blueprint(whatsapp_bp, url_prefix="/api/whatsapp")
app.register_blueprint(telegram_bp, url_prefix="/api/telegram")
app.register_blueprint(scheduler_bp, url_prefix="/api/scheduler")
app.register_blueprint(iclinic_bp, url_prefix="/api/iclinic")
app.register_blueprint(admin_tasks_bp, url_prefix="/admin/api")
app.register_blueprint(admin_patient_bp, url_prefix="/admin/api")

# ⚠️ Desligado por ora
# app.register_blueprint(medication_bp, url_prefix="/api/medications")
# app.register_blueprint(mood_bp, url_prefix="/api/moods")


# ---------- Rotas básicas ----------
@app.route("/")
def index():
    return jsonify(
        {
            "service": "whatsapp-medical-bot",
            "status": "running",
            "version": "1.0.0",
            "admin_url": "/admin",
        }
    )


@app.route("/health")
def health():
    try:
        with app.app_context():
            conn = db.engine.connect()
            conn.execute(text("SELECT 1"))
            conn.close()
        db_status = "connected"
        status = "healthy"
    except Exception as e:
        logger.exception("DB health check failed")
        db_status = f"error: {e.__class__.__name__}"
        status = "degraded"

    return jsonify(
        {
            "service": "whatsapp-medical-bot",
            "status": status,
            "version": "1.0.0",
            "database": db_status,
        }
    )


def _boot_state():
    """/ops/boot-state (sem decorator para evitar conflitos de endpoint)."""
    if _MAIN_LOADED:
        return jsonify(
            {
                "main_loaded": True,
                "source": "main_boot",
                "last_attempt": datetime.utcnow().isoformat() + "Z",
            }
        )
    else:
        err = _BOOT_ERROR or "unknown"
        return jsonify(
            {
                "main_loaded": False,
                "source": "exception",
                "error_type": getattr(err, "__class__", type("E", (), {})).__name__
                if hasattr(err, "__class__")
                else "Exception",
                "summary": str(err),
                "file": "src/main.py",
                "line": 0,
                "last_attempt": datetime.utcnow().isoformat() + "Z",
            }
        )


def _register_boot_state_route():
    """Registra /ops/boot-state de forma idempotente."""
    endpoint_name = "ops_boot_state"
    if endpoint_name not in app.view_functions:
        app.add_url_rule("/ops/boot-state", endpoint=endpoint_name, view_func=_boot_state)


def _init_app():
    """Inicializa modelos, cria tabelas, agenda jobs e carrega Admin."""
    global _MAIN_LOADED, _BOOT_ERROR
    try:
        _load_models_safely()

        try:
            db.create_all()
        except Exception:
            logging.error("⚠️ DB create_all falhou", exc_info=True)
            raise

        try:
            init_scheduler()
            logger.info("u-ETG Scheduler initialized")
        except Exception:
            logger.exception("Error initializing u-ETG scheduler")

        _load_admin_blueprint()

        _MAIN_LOADED = True
        _BOOT_ERROR = None
        logger.info("Main app initialized successfully")
    except Exception as e:
        _MAIN_LOADED = False
        _BOOT_ERROR = e
        logger.exception("Main app failed to initialize")
    finally:
        _register_boot_state_route()


# ---------- Entrada ----------
if __name__ == "__main__":
    db.init_app(app)
    with app.app_context():
        _init_app()
    port = int(os.getenv("PORT", "8080"))
    debug = os.getenv("FLASK_ENV") == "development"
    logger.info(f"Starting on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)
else:
    db.init_app(app)
    with app.app_context():
        _init_app()


# Arquivos estáticos
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)
