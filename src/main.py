import os
import sys
import logging

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
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
        f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    )
    logger.info("Using SQLite database for development")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Habilitar CORS para todas as rotas
CORS(app)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix="/api")
app.register_blueprint(patient_bp, url_prefix="/api")
app.register_blueprint(reminder_bp, url_prefix="/api")
app.register_blueprint(response_bp, url_prefix="/api")
app.register_blueprint(scale_bp, url_prefix="/api")
app.register_blueprint(whatsapp_bp, url_prefix="/api/whatsapp")
app.register_blueprint(telegram_bp, url_prefix="/api/telegram")
app.register_blueprint(medication_bp, url_prefix="/api")
app.register_blueprint(mood_bp, url_prefix="/api")
app.register_blueprint(scheduler_bp, url_prefix="/api/scheduler")
app.register_blueprint(iclinic_bp, url_prefix="/api/iclinic")
app.register_blueprint(admin_tasks_bp, url_prefix="/api/admin")
app.register_blueprint(admin_patient_bp, url_prefix="/api/admin")
app.register_blueprint(admin_bp)  # Admin UI sem prefix

# Importar modelos para criação das tabelas
from src.models.user import User
from src.models.patient import Patient
from src.models.reminder import Reminder
from src.models.response import Response
from src.models.scale import Scale
from src.models.medication import Medication, MedicationConfirmation
from src.models.mood_chart import MoodChart
from src.models.breathing_exercise import BreathingExercise
from src.admin.models.patient import AdminPatient
from src.admin.models.campaign import WACampaign, WACampaignRecipient, WACampaignRun

def validate_environment():
    """Validar variáveis de ambiente essenciais"""
    required_vars = [
        'WHATSAPP_ACCESS_TOKEN',
        'WHATSAPP_PHONE_NUMBER_ID',
        'APP_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var, '').strip()
        if not value:
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Some features may not work properly")
    else:
        logger.info("All required environment variables are configured")
    
    # Verificar token admin
    admin_token = os.getenv('ADMIN_UI_TOKEN', '').strip()
    if not admin_token:
        logger.warning("ADMIN_UI_TOKEN not configured - Admin UI will not be accessible")
        logger.warning("Set ADMIN_UI_TOKEN environment variable to enable admin access")
    else:
        logger.info("Admin UI token configured - Admin interface available at /admin")

def create_tables():
    """Criar tabelas do banco de dados"""
    try:
        db.create_all()
        logger.info("Database tables created successfully")
        
        # Inicializar dados padrão
        initialize_default_data()
        
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

def initialize_default_data():
    """Inicializar dados padrão do sistema"""
    try:
        # Inicializar escalas padrão
        from src.utils.scale_initializer import initialize_scales
        initialize_scales()
        
        # Seed inicial do admin se necessário
        seed_admin_patient()
        
        logger.info("Default data initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing default data: {e}")

def seed_admin_patient():
    """Criar paciente admin se necessário"""
    try:
        admin_phone = os.getenv('ADMIN_PHONE_NUMBER', '5514997799022').strip()
        if admin_phone.startswith('+'):
            admin_phone = admin_phone[1:]
        
        existing_admin = AdminPatient.query.filter_by(phone_e164=admin_phone).first()
        if not existing_admin:
            admin_patient = AdminPatient(
                name='Dr. Admin',
                phone_e164=admin_phone,
                active=True
            )
            db.session.add(admin_patient)
            db.session.commit()
            logger.info(f"Admin patient created: ****{admin_phone[-4:]}")
        
    except Exception as e:
        logger.error(f"Error seeding admin patient: {e}")
        db.session.rollback()

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'whatsapp-medical-bot',
        'version': '1.0.0',
        'admin_enabled': bool(os.getenv('ADMIN_UI_TOKEN', '').strip()),
        'database': 'connected' if db.engine else 'disconnected'
    }

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    """Servir arquivos estáticos"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return {
            'message': 'WhatsApp Medical Bot API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'webhook': '/api/whatsapp/webhook',
                'admin': '/admin'
            }
        }

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, "index.html")
        else:
            return {
                'message': 'WhatsApp Medical Bot API',
                'version': '1.0.0',
                'endpoints': {
                    'health': '/health',
                    'webhook': '/api/whatsapp/webhook',
                    'admin': '/admin'
                }
            }

if __name__ == "__main__":
    # Validar ambiente
    validate_environment()
    
    # Inicializar banco de dados
    with app.app_context():
        create_tables()
    
    # Inicializar scheduler u-ETG (existente)
    if os.getenv("DISABLE_SCHEDULER") != "1":
        try:
            from src.jobs.uetg_scheduler import validate_config
            
            if validate_config():
                init_scheduler()
                logger.info("✅ u-ETG Scheduler initialized")
            else:
                logger.warning("⚠️ u-ETG scheduler not started due to invalid configuration")
        except Exception as e:
            logger.error(f"⚠️ Error initializing u-ETG scheduler: {e}")
            logger.warning("⚠️ Application will continue without automatic scheduler")
    
    # Inicializar scheduler de campanhas (novo)
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

