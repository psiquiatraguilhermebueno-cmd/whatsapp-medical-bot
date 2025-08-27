from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.scale import Scale

scale_bp = Blueprint('scale', __name__)

@scale_bp.route('/scales', methods=['GET'])
def get_scales():
    """Listar todas as escalas"""
    scales = Scale.query.all()
    return jsonify([scale.to_dict() for scale in scales])

@scale_bp.route('/scales/<int:scale_id>', methods=['GET'])
def get_scale(scale_id):
    """Obter uma escala específica"""
    scale = Scale.query.get_or_404(scale_id)
    return jsonify(scale.to_dict())

@scale_bp.route('/scales/name/<string:scale_name>', methods=['GET'])
def get_scale_by_name(scale_name):
    """Obter uma escala pelo nome"""
    scale = Scale.query.filter_by(name=scale_name).first_or_404()
    return jsonify(scale.to_dict())

@scale_bp.route('/scales', methods=['POST'])
def create_scale():
    """Criar uma nova escala"""
    data = request.get_json()
    
    required_fields = ['name', 'title', 'questions', 'scoring_rules', 'alarm_threshold']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Campos obrigatórios: name, title, questions, scoring_rules, alarm_threshold'}), 400
    
    # Verificar se a escala já existe
    existing_scale = Scale.query.filter_by(name=data['name']).first()
    if existing_scale:
        return jsonify({'error': 'Escala com este nome já existe'}), 400
    
    scale = Scale(
        name=data['name'],
        title=data['title'],
        description=data.get('description'),
        questions=data['questions'],
        scoring_rules=data['scoring_rules'],
        alarm_threshold=data['alarm_threshold']
    )
    
    db.session.add(scale)
    db.session.commit()
    
    return jsonify(scale.to_dict()), 201

@scale_bp.route('/scales/<int:scale_id>', methods=['PUT'])
def update_scale(scale_id):
    """Atualizar uma escala"""
    scale = Scale.query.get_or_404(scale_id)
    data = request.get_json()
    
    if 'title' in data:
        scale.title = data['title']
    if 'description' in data:
        scale.description = data['description']
    if 'questions' in data:
        scale.questions = data['questions']
    if 'scoring_rules' in data:
        scale.scoring_rules = data['scoring_rules']
    if 'alarm_threshold' in data:
        scale.alarm_threshold = data['alarm_threshold']
    
    db.session.commit()
    return jsonify(scale.to_dict())

@scale_bp.route('/scales/<int:scale_id>', methods=['DELETE'])
def delete_scale(scale_id):
    """Deletar uma escala"""
    scale = Scale.query.get_or_404(scale_id)
    db.session.delete(scale)
    db.session.commit()
    return jsonify({'message': 'Escala deletada com sucesso'})

@scale_bp.route('/scales/<string:scale_name>/calculate', methods=['POST'])
def calculate_scale_score(scale_name):
    """Calcular a pontuação de uma escala baseada nas respostas"""
    scale = Scale.query.filter_by(name=scale_name).first_or_404()
    data = request.get_json()
    
    if not data or 'responses' not in data:
        return jsonify({'error': 'Campo obrigatório: responses'}), 400
    
    responses = data['responses']
    
    # Calcular pontuação baseada nas regras da escala
    total_score = 0
    for i, response in enumerate(responses):
        if i < len(scale.questions):
            total_score += response
    
    # Verificar se é alarmante
    is_alarming = total_score >= scale.alarm_threshold
    
    # Determinar categoria baseada nas regras de pontuação
    category = 'unknown'
    for rule in scale.scoring_rules:
        if rule['min_score'] <= total_score <= rule['max_score']:
            category = rule['category']
            break
    
    result = {
        'scale_name': scale_name,
        'total_score': total_score,
        'max_score': len(scale.questions) * 3,  # Assumindo escala 0-3
        'category': category,
        'is_alarming': is_alarming,
        'responses': responses
    }
    
    return jsonify(result)

