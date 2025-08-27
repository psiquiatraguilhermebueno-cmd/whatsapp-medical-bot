from flask import Blueprint, request, jsonify
from datetime import datetime, time, timedelta
from src.models.user import db
from src.models.reminder import Reminder
from src.models.patient import Patient

reminder_bp = Blueprint('reminder', __name__)

@reminder_bp.route('/reminders', methods=['GET'])
def get_reminders():
    """Listar todos os lembretes"""
    patient_id = request.args.get('patient_id')
    
    query = Reminder.query.filter_by(is_active=True)
    if patient_id:
        query = query.filter_by(patient_id=patient_id)
    
    reminders = query.all()
    return jsonify([reminder.to_dict() for reminder in reminders])

@reminder_bp.route('/reminders/<int:reminder_id>', methods=['GET'])
def get_reminder(reminder_id):
    """Obter um lembrete específico"""
    reminder = Reminder.query.get_or_404(reminder_id)
    return jsonify(reminder.to_dict())

@reminder_bp.route('/reminders', methods=['POST'])
def create_reminder():
    """Criar um novo lembrete"""
    data = request.get_json()
    
    required_fields = ['patient_id', 'reminder_type', 'title', 'frequency', 'scheduled_time']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Campos obrigatórios: patient_id, reminder_type, title, frequency, scheduled_time'}), 400
    
    # Verificar se o paciente existe
    patient = Patient.query.get(data['patient_id'])
    if not patient:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    # Converter scheduled_time para objeto time
    try:
        scheduled_time = datetime.strptime(data['scheduled_time'], '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'Formato de horário inválido. Use HH:MM'}), 400
    
    # Calcular próxima data de envio
    next_send_date = calculate_next_send_date(data['frequency'], scheduled_time)
    
    reminder = Reminder(
        patient_id=data['patient_id'],
        reminder_type=data['reminder_type'],
        scale_type=data.get('scale_type'),
        title=data['title'],
        description=data.get('description'),
        frequency=data['frequency'],
        scheduled_time=scheduled_time,
        next_send_date=next_send_date
    )
    
    db.session.add(reminder)
    db.session.commit()
    
    return jsonify(reminder.to_dict()), 201

@reminder_bp.route('/reminders/<int:reminder_id>', methods=['PUT'])
def update_reminder(reminder_id):
    """Atualizar um lembrete"""
    reminder = Reminder.query.get_or_404(reminder_id)
    data = request.get_json()
    
    if 'title' in data:
        reminder.title = data['title']
    if 'description' in data:
        reminder.description = data['description']
    if 'frequency' in data:
        reminder.frequency = data['frequency']
    if 'scheduled_time' in data:
        try:
            reminder.scheduled_time = datetime.strptime(data['scheduled_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Formato de horário inválido. Use HH:MM'}), 400
    if 'is_active' in data:
        reminder.is_active = data['is_active']
    if 'scale_type' in data:
        reminder.scale_type = data['scale_type']
    
    # Recalcular próxima data de envio se necessário
    if 'frequency' in data or 'scheduled_time' in data:
        reminder.next_send_date = calculate_next_send_date(reminder.frequency, reminder.scheduled_time)
    
    db.session.commit()
    return jsonify(reminder.to_dict())

@reminder_bp.route('/reminders/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    """Desativar um lembrete"""
    reminder = Reminder.query.get_or_404(reminder_id)
    reminder.is_active = False
    db.session.commit()
    return jsonify({'message': 'Lembrete desativado com sucesso'})

@reminder_bp.route('/reminders/due', methods=['GET'])
def get_due_reminders():
    """Obter lembretes que devem ser enviados agora"""
    now = datetime.utcnow()
    due_reminders = Reminder.query.filter(
        Reminder.is_active == True,
        Reminder.next_send_date <= now
    ).all()
    
    return jsonify([reminder.to_dict() for reminder in due_reminders])

def calculate_next_send_date(frequency, scheduled_time):
    """Calcular a próxima data de envio baseada na frequência"""
    now = datetime.utcnow()
    today = now.date()
    
    # Criar datetime com o horário agendado para hoje
    next_datetime = datetime.combine(today, scheduled_time)
    
    # Se o horário de hoje já passou, começar amanhã
    if next_datetime <= now:
        if frequency == 'daily':
            next_datetime += timedelta(days=1)
        elif frequency == 'weekly':
            next_datetime += timedelta(days=7)
        elif frequency == 'monthly':
            next_datetime += timedelta(days=30)
        elif frequency == 'once':
            next_datetime += timedelta(days=1)
    
    return next_datetime

