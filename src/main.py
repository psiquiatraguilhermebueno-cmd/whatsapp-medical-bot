import os
import sys
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
from src.routes.admin_tasks import admin_bp
from src.jobs.uetg_scheduler import init_scheduler

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Habilitar CORS para todas as rotas
CORS(app)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(patient_bp, url_prefix='/api')
app.register_blueprint(reminder_bp, url_prefix='/api')
app.register_blueprint(response_bp, url_prefix='/api')
app.register_blueprint(scale_bp, url_prefix='/api')
app.register_blueprint(whatsapp_bp, url_prefix='/api/whatsapp')
app.register_blueprint(telegram_bp, url_prefix='/api/telegram')
app.register_blueprint(medication_bp, url_prefix='/api')
app.register_blueprint(mood_bp, url_prefix='/api')
app.register_blueprint(scheduler_bp, url_prefix='/api/scheduler')
app.register_blueprint(iclinic_bp, url_prefix='/api/iclinic')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

# uncomment if you need to use database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Importar modelos para criação das tabelas
from src.models.user import User
from src.models.patient import Patient
from src.models.reminder import Reminder
from src.models.response import Response
from src.models.scale import Scale
from src.models.medication import Medication, MedicationConfirmation
from src.models.mood_chart import MoodChart
from src.models.breathing_exercise import BreathingExercise

db.init_app(app)
with app.app_context():
    db.create_all()
    # Inicializar escalas padrão
    from src.utils.scale_initializer import initialize_scales
    initialize_scales()
    # # Inicializar exercícios de respiração
    # from src.utils.breathing_exercises_initializer import initialize_breathing_exercises
    # initialize_breathing_exercises()

# Inicializar scheduler u-ETG (se não estiver desabilitado)
if os.getenv('DISABLE_SCHEDULER') != '1':
    try:
        init_scheduler()
    except Exception as e:
        print(f"⚠️ Erro ao inicializar scheduler u-ETG: {e}")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

