from flask import Blueprint, request, jsonify
from src.services.scheduler_service import SchedulerService
from datetime import time

scheduler_bp = Blueprint('scheduler', __name__)

# Instância global do agendador
scheduler_service = SchedulerService()

@scheduler_bp.route('/start', methods=['POST'])
def start_scheduler():
    """Iniciar o agendador"""
    try:
        scheduler_service.start_scheduler()
        return jsonify({'message': 'Agendador iniciado com sucesso'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scheduler_bp.route('/stop', methods=['POST'])
def stop_scheduler():
    """Parar o agendador"""
    try:
        scheduler_service.stop_scheduler()
        return jsonify({'message': 'Agendador parado com sucesso'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scheduler_bp.route('/status', methods=['GET'])
def get_scheduler_status():
    """Obter status do agendador"""
    try:
        status = scheduler_service.get_scheduler_status()
        return jsonify(status), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scheduler_bp.route('/reminders', methods=['POST'])
def create_reminder():
    """Criar um novo lembrete agendado"""
    try:
        data = request.get_json()
        
        required_fields = ['patient_id', 'reminder_type', 'title', 'scheduled_time']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Campos obrigatórios: patient_id, reminder_type, title, scheduled_time'}), 400
        
        # Converter horário de string para time
        scheduled_time = time.fromisoformat(data['scheduled_time'])
        
        reminder = scheduler_service.create_reminder(
            patient_id=data['patient_id'],
            reminder_type=data['reminder_type'],
            title=data['title'],
            scheduled_time=scheduled_time,
            frequency=data.get('frequency', 'daily'),
            description=data.get('description'),
            scale_type=data.get('scale_type'),
            medication_id=data.get('medication_id'),
            breathing_exercise_id=data.get('breathing_exercise_id'),
            custom_schedule=data.get('custom_schedule')
        )
        
        return jsonify(reminder.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scheduler_bp.route('/reminders/bulk', methods=['POST'])
def create_bulk_reminders():
    """Criar múltiplos lembretes de uma vez"""
    try:
        data = request.get_json()
        
        if 'reminders' not in data or not isinstance(data['reminders'], list):
            return jsonify({'error': 'Campo obrigatório: reminders (lista)'}), 400
        
        created_reminders = []
        
        for reminder_data in data['reminders']:
            required_fields = ['patient_id', 'reminder_type', 'title', 'scheduled_time']
            if not all(field in reminder_data for field in required_fields):
                continue  # Pular lembretes inválidos
            
            try:
                scheduled_time = time.fromisoformat(reminder_data['scheduled_time'])
                
                reminder = scheduler_service.create_reminder(
                    patient_id=reminder_data['patient_id'],
                    reminder_type=reminder_data['reminder_type'],
                    title=reminder_data['title'],
                    scheduled_time=scheduled_time,
                    frequency=reminder_data.get('frequency', 'daily'),
                    description=reminder_data.get('description'),
                    scale_type=reminder_data.get('scale_type'),
                    medication_id=reminder_data.get('medication_id'),
                    breathing_exercise_id=reminder_data.get('breathing_exercise_id'),
                    custom_schedule=reminder_data.get('custom_schedule')
                )
                
                created_reminders.append(reminder.to_dict())
                
            except Exception as e:
                print(f"Erro ao criar lembrete: {e}")
                continue
        
        return jsonify({
            'message': f'{len(created_reminders)} lembretes criados com sucesso',
            'reminders': created_reminders
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scheduler_bp.route('/reminders/templates', methods=['GET'])
def get_reminder_templates():
    """Obter templates de lembretes pré-definidos"""
    try:
        templates = {
            'scale_reminders': [
                {
                    'reminder_type': 'scale',
                    'scale_type': 'PHQ-9',
                    'title': 'Questionário PHQ-9 - Depressão',
                    'description': 'Avaliação semanal dos sintomas de depressão',
                    'frequency': 'weekly',
                    'suggested_time': '09:00'
                },
                {
                    'reminder_type': 'scale',
                    'scale_type': 'GAD-7',
                    'title': 'Questionário GAD-7 - Ansiedade',
                    'description': 'Avaliação semanal dos sintomas de ansiedade',
                    'frequency': 'weekly',
                    'suggested_time': '10:00'
                },
                {
                    'reminder_type': 'scale',
                    'scale_type': 'MDQ',
                    'title': 'Questionário MDQ - Transtorno Bipolar',
                    'description': 'Triagem para episódios de mania/hipomania',
                    'frequency': 'monthly',
                    'suggested_time': '11:00'
                }
            ],
            'mood_reminders': [
                {
                    'reminder_type': 'mood_chart',
                    'title': 'Registro de Humor Diário',
                    'description': 'Registre como você está se sentindo hoje',
                    'frequency': 'daily',
                    'suggested_time': '20:00'
                }
            ],
            'breathing_reminders': [
                {
                    'reminder_type': 'breathing',
                    'title': 'Exercício de Respiração Matinal',
                    'description': 'Comece o dia com um exercício de respiração',
                    'frequency': 'daily',
                    'suggested_time': '08:00'
                },
                {
                    'reminder_type': 'breathing',
                    'title': 'Pausa para Respirar',
                    'description': 'Momento de relaxamento no meio do dia',
                    'frequency': 'daily',
                    'suggested_time': '15:00'
                }
            ],
            'motivational_reminders': [
                {
                    'reminder_type': 'motivational',
                    'title': 'Mensagem Motivacional',
                    'description': 'Você é mais forte do que imagina! Continue cuidando de si mesmo.',
                    'frequency': 'daily',
                    'suggested_time': '12:00'
                }
            ]
        }
        
        return jsonify(templates), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scheduler_bp.route('/reminders/patient/<int:patient_id>', methods=['GET'])
def get_patient_reminders(patient_id):
    """Obter lembretes de um paciente específico"""
    try:
        from src.models.reminder import Reminder
        
        reminders = Reminder.query.filter_by(patient_id=patient_id).all()
        return jsonify([reminder.to_dict() for reminder in reminders]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scheduler_bp.route('/reminders/<int:reminder_id>/toggle', methods=['PUT'])
def toggle_reminder(reminder_id):
    """Ativar/desativar um lembrete"""
    try:
        from src.models.reminder import Reminder
        from src.models.user import db
        
        reminder = Reminder.query.get(reminder_id)
        if not reminder:
            return jsonify({'error': 'Lembrete não encontrado'}), 404
        
        reminder.is_active = not reminder.is_active
        db.session.commit()
        
        status = 'ativado' if reminder.is_active else 'desativado'
        return jsonify({
            'message': f'Lembrete {status} com sucesso',
            'reminder': reminder.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scheduler_bp.route('/test-reminder', methods=['POST'])
def test_reminder():
    """Testar envio de lembrete imediatamente"""
    try:
        data = request.get_json()
        
        if 'reminder_id' not in data:
            return jsonify({'error': 'Campo obrigatório: reminder_id'}), 400
        
        from src.models.reminder import Reminder
        
        reminder = Reminder.query.get(data['reminder_id'])
        if not reminder:
            return jsonify({'error': 'Lembrete não encontrado'}), 404
        
        # Enviar lembrete imediatamente para teste
        scheduler_service._send_reminder(reminder)
        
        return jsonify({'message': 'Lembrete de teste enviado com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

