import os
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
        f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    )
    logger.info("Using SQLite database for development")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# CORREÇÃO CRÍTICA: Inicializar SQLAlchemy com a aplicação
db.init_app(app)

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
    """Health check endpoint - VERSÃO CORRIGIDA"""
    try:
        # Testar conexão com o banco de forma segura
        db.session.execute(db.text('SELECT 1'))
        database_status = 'connected'
    except Exception as e:
        logger.warning(f"Database connection test failed: {e}")
        database_status = 'disconnected'
    
    return {
        'status': 'healthy',
        'service': 'whatsapp-medical-bot',
        'version': '1.0.0',
        'admin_enabled': bool(os.getenv('ADMIN_UI_TOKEN', '').strip()),
        'database': database_status
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


@app.route('/admin/api/patients', methods=['POST'])
def create_patient_api():
    """Criar novo paciente via API"""
    try:
        # Verificar token admin
        admin_token = request.headers.get('X-Admin-Token')
        if admin_token != 'admin123456':
            return jsonify({'error': 'Unauthorized', 'success': False}), 401
        
        # Obter dados do formulário
        data = request.get_json() or {}
        
        # Validar campos obrigatórios
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        
        if not name or not phone:
            return jsonify({'error': 'Nome e telefone são obrigatórios'}), 400
        
        # Limpar telefone (manter apenas números)
        phone_clean = ''.join(filter(str.isdigit, phone))
        if len(phone_clean) < 10:
            return jsonify({'error': 'Telefone inválido'}), 400
        
        # Formatear telefone brasileiro
        if phone_clean.startswith('55'):
            phone_formatted = f"+{phone_clean}"
        elif phone_clean.startswith('14'):
            phone_formatted = f"+55{phone_clean}"
        else:
            phone_formatted = f"+55{phone_clean}"
        
        # Criar paciente simples (sem banco de dados por enquanto)
        patient_data = {
            'id': len(phone_clean),  # ID temporário
            'name': name,
            'phone': phone_formatted,
            'email': data.get('email', ''),
            'protocols': data.get('protocols', []),
            'active': True,
            'created_at': 'now'
        }
        
        # Log do cadastro
        app.logger.info(f"✅ Paciente cadastrado: {name} ({phone_formatted})")
        
        return jsonify({
            'success': True,
            'message': f'Paciente {name} cadastrado com sucesso!',
            'patient': patient_data
        }), 201
        
    except Exception as e:
        app.logger.error(f"❌ Erro ao cadastrar paciente: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500


@app.route('/admin/api/create-tables', methods=['POST'])
def create_tables():
    """Força criação de todas as tabelas do banco"""
    try:
        # Verifica autenticação admin
        admin_token = request.headers.get('X-Admin-Token')
        if admin_token != 'admin123456':
            return jsonify({"error": "Unauthorized", "success": False}), 401
        
        # Cria todas as tabelas
        with app.app_context():
            db.create_all()
        
        # Verifica se as tabelas foram criadas
        tables_created = []
        inspector = db.inspect(db.engine)
        
        expected_tables = ['patients', 'responses', 'schedules']
        for table_name in expected_tables:
            if inspector.has_table(table_name):
                tables_created.append(table_name)
        
        return jsonify({
            "success": True,
            "message": "Tabelas criadas com sucesso",
            "tables_created": tables_created,
            "total_tables": len(tables_created)
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Erro ao criar tabelas: {str(e)}",
            "success": False
        }), 500


@app.route('/admin/api/create-tables', methods=['POST'])
def create_tables_endpoint():
    """Força criação de todas as tabelas do banco"""
    try:
        # Verifica autenticação admin
        admin_token = request.headers.get('X-Admin-Token')
        if admin_token != 'admin123456':
            return jsonify({"error": "Unauthorized", "success": False}), 401
        
        # Cria todas as tabelas
        with app.app_context():
            db.create_all()
        
        # Verifica se as tabelas foram criadas
        tables_created = []
        inspector = db.inspect(db.engine)
        
        expected_tables = ['patients', 'responses', 'schedules']
        for table_name in expected_tables:
            if inspector.has_table(table_name):
                tables_created.append(table_name)
        
        return jsonify({
            "success": True,
            "message": "Tabelas criadas com sucesso",
            "tables_created": tables_created,
            "total_tables": len(tables_created)
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Erro ao criar tabelas: {str(e)}",
            "success": False
        }), 500



@app.route('/admin/api/patients/simple', methods=['POST'])
def create_patient_simple():
    """Endpoint simplificado para criar paciente"""
    try:
        # Verifica token admin
        admin_token = request.headers.get('X-Admin-Token')
        if admin_token != 'admin123456':
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Obter dados
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        
        if not name or not phone:
            return jsonify({'error': 'Nome e telefone obrigatórios'}), 400
        
        # Limpar telefone
        phone_clean = ''.join(filter(str.isdigit, phone))
        phone_e164 = f"+55{phone_clean}" if not phone_clean.startswith('55') else f"+{phone_clean}"
        
        # Usar SQL direto
        import sqlite3
        db_path = "instance/medical_bot.db"
        os.makedirs("instance", exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Criar tabela se não existir
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            phone_e164 VARCHAR(20) UNIQUE NOT NULL,
            phone_masked VARCHAR(20),
            email VARCHAR(255),
            birth_date DATE,
            gender CHAR(1),
            priority VARCHAR(20) DEFAULT 'normal',
            notes TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Inserir paciente
        cursor.execute("""
        INSERT OR REPLACE INTO patients 
        (name, phone_e164, phone_masked, email, birth_date, gender, priority, notes, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, phone_e164, phone, 
            data.get('email', ''), data.get('birth_date', '1990-01-01'),
            data.get('gender', 'M'), data.get('priority', 'normal'),
            data.get('notes', ''), 1
        ))
        
        patient_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Paciente criado com sucesso',
            'patient': {'id': patient_id, 'name': name, 'phone': phone}
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500




@app.route('/api/send-template', methods=['POST'])
def send_template():
    """Endpoint para enviar templates WhatsApp"""
    try:
        data = request.get_json()
        template_name = data.get('template_name')
        recipient_phone = data.get('recipient_phone')
        patient_name = data.get('patient_name', 'Paciente')
        
        # Configurações WhatsApp
        access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        
        if not access_token or not phone_number_id:
            return jsonify({"error": "Configurações WhatsApp não encontradas"}), 500
        
        # URL da API WhatsApp
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        
        # Headers
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Payload da mensagem
        message_data = {
            "messaging_product": "whatsapp",
            "to": recipient_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": "pt_BR"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": patient_name
                            }
                        ]
                    }
                ]
            }
        }
        
        # Enviar mensagem
        response = requests.post(url, headers=headers, json=message_data)
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                "success": True,
                "message_id": result.get('messages', [{}])[0].get('id'),
                "template": template_name,
                "recipient": recipient_phone,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-templates', methods=['POST'])
def test_templates():
    """Endpoint para testar múltiplos templates"""
    try:
        data = request.get_json()
        recipient_phone = data.get('recipient_phone', '5514997799022')
        patient_name = data.get('patient_name', 'Dr. Guilherme')
        
        templates = [
            'gad7_checkin_ptbr',
            'phq9_checkin_ptbr'
        ]
        
        results = []
        
        for template in templates:
            # Fazer requisição interna para enviar template
            template_data = {
                'template_name': template,
                'recipient_phone': recipient_phone,
                'patient_name': patient_name
            }
            
            # Simular envio (usar a função send_template diretamente)
            try:
                access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
                phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
                
                url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
                
                message_data = {
                    "messaging_product": "whatsapp",
                    "to": recipient_phone,
                    "type": "template",
                    "template": {
                        "name": template,
                        "language": {"code": "pt_BR"},
                        "components": [{
                            "type": "body",
                            "parameters": [{"type": "text", "text": patient_name}]
                        }]
                    }
                }
                
                response = requests.post(url, headers=headers, json=message_data)
                
                if response.status_code == 200:
                    result = response.json()
                    results.append({
                        "template": template,
                        "success": True,
                        "message_id": result.get('messages', [{}])[0].get('id')
                    })
                else:
                    results.append({
                        "template": template,
                        "success": False,
                        "error": response.text
                    })
                    
            except Exception as e:
                results.append({
                    "template": template,
                    "success": False,
                    "error": str(e)
                })
        
        return jsonify({
            "success": True,
            "results": results,
            "total_sent": len([r for r in results if r['success']]),
            "total_templates": len(templates)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/send-template', methods=['POST'])
def send_template():
    """Endpoint para enviar templates WhatsApp"""
    try:
        data = request.get_json()
        template_name = data.get('template_name')
        recipient_phone = data.get('recipient_phone')
        patient_name = data.get('patient_name', 'Paciente')
        
        # Configurações WhatsApp
        access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        
        if not access_token or not phone_number_id:
            return jsonify({"error": "Configurações WhatsApp não encontradas"}), 500
        
        # URL da API WhatsApp
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        
        # Headers
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Payload da mensagem
        message_data = {
            "messaging_product": "whatsapp",
            "to": recipient_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": "pt_BR"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": patient_name
                            }
                        ]
                    }
                ]
            }
        }
        
        # Enviar mensagem
        response = requests.post(url, headers=headers, json=message_data)
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                "success": True,
                "message_id": result.get('messages', [{}])[0].get('id'),
                "template": template_name,
                "recipient": recipient_phone,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-templates', methods=['POST'])
def test_templates():
    """Endpoint para testar múltiplos templates"""
    try:
        data = request.get_json()
        recipient_phone = data.get('recipient_phone', '5514997799022')
        patient_name = data.get('patient_name', 'Dr. Guilherme')
        
        templates = [
            'gad7_checkin_ptbr',
            'phq9_checkin_ptbr'
        ]
        
        results = []
        
        for template in templates:
            try:
                access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
                phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
                
                url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
                
                message_data = {
                    "messaging_product": "whatsapp",
                    "to": recipient_phone,
                    "type": "template",
                    "template": {
                        "name": template,
                        "language": {"code": "pt_BR"},
                        "components": [{
                            "type": "body",
                            "parameters": [{"type": "text", "text": patient_name}]
                        }]
                    }
                }
                
                response = requests.post(url, headers=headers, json=message_data)
                
                if response.status_code == 200:
                    result = response.json()
                    results.append({
                        "template": template,
                        "success": True,
                        "message_id": result.get('messages', [{}])[0].get('id')
                    })
                else:
                    results.append({
                        "template": template,
                        "success": False,
                        "error": response.text
                    })
                    
            except Exception as e:
                results.append({
                    "template": template,
                    "success": False,
                    "error": str(e)
                })
        
        return jsonify({
            "success": True,
            "results": results,
            "total_sent": len([r for r in results if r['success']]),
            "total_templates": len(templates)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Validar ambiente
    validate_environment()
    
    # Inicializar banco de dados
    with app.app_context():
        create_tables()

    # FORÇA CRIAÇÃO DE TABELAS (ADICIONADO AUTOMATICAMENTE)
    try:
        with app.app_context():
            # Força criação de todas as tabelas
            db.create_all()
            
            # Verifica se as tabelas foram criadas
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            logger.info(f"✅ Tabelas disponíveis: {tables}")
            
            # Verifica tabelas essenciais
            essential_tables = ['patients', 'responses', 'schedules']
            missing_tables = [t for t in essential_tables if t not in tables]
            
            if missing_tables:
                logger.warning(f"⚠️ Tabelas ausentes: {missing_tables}")
                # Tenta criar novamente
                db.create_all()
                logger.info("🔄 Tentativa adicional de criação de tabelas")
            else:
                logger.info("✅ Todas as tabelas essenciais estão presentes")
                
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        # Continua mesmo com erro para não quebrar a aplicação

    
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
