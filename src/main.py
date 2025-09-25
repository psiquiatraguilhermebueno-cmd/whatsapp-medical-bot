# src/main.py
import os
import sys
import logging
from datetime import datetime
from sqlalchemy import text

# --- PATH BASE (não alterar) ---
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify, send_from_directory, render_template, redirect  # noqa: E402
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
    # fallback sqlite local
    database_url = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'app.db')}"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Extensão do projeto
from src.models.user import db  # noqa: E402

CORS(app)

# Flags de Admin e boot-state
_admin_loaded = False
_admin_load_error = None
_MAIN_LOADED = False
_BOOT_ERROR = None


def _load_models_safely():
    """
    Importa MODELOS que participam do create_all(), de forma defensiva.
    IMPORTANTE: usar o alias Patient de src.models.patient (tabela 'patients').
    """
    problems = []

    # Pacientes
    try:
        from src.models.patient import Patient  # noqa: F401
    except Exception as e:
        problems.append(f"patient model not loaded: {e}")

    # Dependentes de patients.id
    try:
        from src.models.reminder import Reminder  # noqa: F401
    except Exception as e:
        problems.append(f"reminder model not loaded: {e}")

    try:
        from src.models.response import Response  # noqa: F401
    except Exception as e:
        problems.append(f"response model not loaded: {e}")

    try:
        from src.models.medication import Medication  # noqa: F401
    except Exception as e:
        problems.append(f"medication model not loaded: {e}")

    # Exercício de respiração (usado por Reminder)
    try:
        from src.models.breathing_exercise import BreathingExercise  # noqa: F401
    except Exception as e:
        problems.append(f"breathing_exercise model not loaded: {e}")

    # Modelos opcionais (não derrubam boot)
    try:
        __import__("src.models.mood", fromlist=["*"])
    except Exception as e:
        logger.warning(f"mood model not loaded: {e}")

    # Campanhas (opcional; não derruba Admin)
    try:
        __import__("src.admin.models.campaign", fromlist=["*"])
    except Exception as e:
        logger.warning(f"campaign models not loaded: {e}")

    if problems:
        for p in problems:
            logger.warning(p)


def _register_api_blueprints():
    """Importa e registra blueprints de API com tolerância a falhas."""
    def _try(bp_import, prefix):
        try:
            bp = bp_import()
            app.register_blueprint(bp, url_prefix=prefix)
            logger.info(f"API blueprint loaded: {prefix}")
        except Exception as e:
            logger.warning(f"API blueprint NOT loaded ({prefix}): {e}")

    _try(lambda: __import__("src.routes.user", fromlist=["user_bp"]).user_bp, "/api/users")
    _try(lambda: __import__("src.routes.patient", fromlist=["patient_bp"]).patient_bp, "/api/patients")
    _try(lambda: __import__("src.routes.reminder", fromlist=["reminder_bp"]).reminder_bp, "/api/reminders")
    _try(lambda: __import__("src.routes.response", fromlist=["response_bp"]).response_bp, "/api/responses")
    _try(lambda: __import__("src.routes.scale", fromlist=["scale_bp"]).scale_bp, "/api/scales")
    _try(lambda: __import__("src.routes.whatsapp", fromlist=["whatsapp_bp"]).whatsapp_bp, "/api/whatsapp")
    _try(lambda: __import__("src.routes.telegram", fromlist=["telegram_bp"]).telegram_bp, "/api/telegram")
    _try(lambda: __import__("src.routes.medication", fromlist=["medication_bp"]).medication_bp, "/api/medications")
    _try(lambda: __import__("src.routes.mood", fromlist=["mood_bp"]).mood_bp, "/api/moods")
    _try(lambda: __import__("src.routes.scheduler", fromlist=["scheduler_bp"]).scheduler_bp, "/api/scheduler")
    _try(lambda: __import__("src.routes.iclinic", fromlist=["iclinic_bp"]).iclinic_bp, "/api/iclinic")
    _try(lambda: __import__("src.routes.admin_tasks", fromlist=["admin_tasks_bp"]).admin_tasks_bp, "/admin/api")
    _try(lambda: __import__("src.routes.admin_patient", fromlist=["admin_patient_bp"]).admin_patient_bp, "/admin/api")


def _load_admin_blueprint():
    """Carrega a UI de Admin. Se falhar, deixa um endpoint de diagnóstico em /admin."""
    global _admin_loaded, _admin_load_error
    try:
        admin_bp = __import__("src.admin.routes", fromlist=["admin_bp"]).admin_bp
        app.register_blueprint(admin_bp, url_prefix="/admin")
        _admin_loaded = True
        logger.info("Admin UI loaded")
    except Exception as e:
        _admin_load_error = str(e)
        _admin_loaded = False
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
                        "detail": _admin_load_error,
                    }
                ),
                503,
            )


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
            "admin_enabled": _admin_loaded,
        }
    )


def _boot_state_view():
    """Handler real do /ops/boot-state."""
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
        app.add_url_rule("/ops/boot-state", endpoint=endpoint_name, view_func=_boot_state_view)


# --- Catch-all para o Admin SPA (qualquer /admin/* que não seja /admin/api/*) ---
@app.route("/admin/<path:subpath>", methods=["GET"])
def admin_spa_catch_all(subpath):
    if subpath.startswith("api/"):
        return jsonify({"error": "Not Found"}), 404
    try:
        return render_template("admin/index.html"), 200
    except Exception:
        return redirect("/admin")


def _init_app():
    """Inicializa modelos, cria tabelas, agenda jobs e carrega Admin."""
    global _MAIN_LOADED, _BOOT_ERROR

    try:
        _load_models_safely()

        # Cria/garante tabelas
        try:
            db.create_all()
        except Exception:
            logger.error("⚠️ DB create_all falhou", exc_info=True)
            raise

        # Registra APIs com tolerância a falhas
        _register_api_blueprints()

        # Jobs (tolerante a falha)
        try:
            init_scheduler = __import__("src.jobs.uetg_scheduler", fromlist=["init_scheduler"]).init_scheduler
            init_scheduler()
            logger.info("u-ETG Scheduler initialized")
        except Exception:
            logger.exception("Error initializing u-ETG scheduler")

        # Admin UI
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


# Arquivos estáticos (se usar)
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)
