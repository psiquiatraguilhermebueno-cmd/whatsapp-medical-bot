from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.response import Response
from src.models.reminder import Reminder
from src.models.patient import Patient

response_bp = Blueprint('response', __name__)

@response_bp.route('/responses', methods=['GET'])
def get_responses():
    """Listar todas as respostas"""
    patient_id = request.args.get('patient_id')
    reminder_id = request.args.get('reminder_id')
    
    query = Response.query
    if patient_id:
        query = query.filter_by(patient_id=patient_id)
    if reminder_id:
        query = query.filter_by(reminder_id=reminder_id)
    
    responses = query.order_by(Response.created_at.desc()).all()
    return jsonify([response.to_dict() for response in responses])

@response_bp.route('/responses/<int:response_id>', methods=['GET'])
def get_response(response_id):
    """Obter uma resposta específica"""
    response = Response.query.get_or_404(response_id)
    return jsonify(response.to_dict())

@response_bp.route('/responses', methods=['POST'])
def create_response():
    """Criar uma nova resposta"""
    data = request.get_json()
    
    required_fields = ['patient_id', 'reminder_id']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Campos obrigatórios: patient_id, reminder_id'}), 400
    
    # Verificar se o paciente e lembrete existem
    patient = Patient.query.get(data['patient_id'])
    if not patient:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    reminder = Reminder.query.get(data['reminder_id'])
    if not reminder:
        return jsonify({'error': 'Lembrete não encontrado'}), 404
    
    response = Response(
        patient_id=data['patient_id'],
        reminder_id=data['reminder_id'],
        response_data=data.get('response_data'),
        media_url=data.get('media_url'),
        text_response=data.get('text_response'),
        score=data.get('score'),
        is_alarming=data.get('is_alarming', False)
    )
    
    db.session.add(response)
    db.session.commit()
    
    return jsonify(response.to_dict()), 201

@response_bp.route('/responses/<int:response_id>', methods=['PUT'])
def update_response(response_id):
    """Atualizar uma resposta"""
    response = Response.query.get_or_404(response_id)
    data = request.get_json()
    
    if 'response_data' in data:
        response.response_data = data['response_data']
    if 'media_url' in data:
        response.media_url = data['media_url']
    if 'text_response' in data:
        response.text_response = data['text_response']
    if 'score' in data:
        response.score = data['score']
    if 'is_alarming' in data:
        response.is_alarming = data['is_alarming']
    
    db.session.commit()
    return jsonify(response.to_dict())

@response_bp.route('/responses/alarming', methods=['GET'])
def get_alarming_responses():
    """Obter respostas com pontuações alarmantes"""
    responses = Response.query.filter_by(is_alarming=True).order_by(Response.created_at.desc()).all()
    return jsonify([response.to_dict() for response in responses])

@response_bp.route('/responses/patient/<int:patient_id>/latest', methods=['GET'])
def get_patient_latest_responses(patient_id):
    """Obter as últimas respostas de um paciente"""
    limit = request.args.get('limit', 10, type=int)
    
    responses = Response.query.filter_by(patient_id=patient_id).order_by(
        Response.created_at.desc()
    ).limit(limit).all()
    
    return jsonify([response.to_dict() for response in responses])

@response_bp.route('/responses/stats', methods=['GET'])
def get_response_stats():
    """Obter estatísticas das respostas"""
    total_responses = Response.query.count()
    alarming_responses = Response.query.filter_by(is_alarming=True).count()
    
    # Estatísticas por tipo de lembrete
    scale_responses = db.session.query(
        Reminder.scale_type,
        db.func.count(Response.id).label('count'),
        db.func.avg(Response.score).label('avg_score')
    ).join(Response).filter(
        Reminder.scale_type.isnot(None)
    ).group_by(Reminder.scale_type).all()
    
    stats = {
        'total_responses': total_responses,
        'alarming_responses': alarming_responses,
        'alarming_percentage': (alarming_responses / total_responses * 100) if total_responses > 0 else 0,
        'scale_stats': [
            {
                'scale_type': stat.scale_type,
                'count': stat.count,
                'avg_score': round(stat.avg_score, 2) if stat.avg_score else 0
            }
            for stat in scale_responses
        ]
    }
    
    return jsonify(stats)

