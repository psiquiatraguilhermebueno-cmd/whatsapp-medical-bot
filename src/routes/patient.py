from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.patient import Patient

patient_bp = Blueprint('patient', __name__)

@patient_bp.route('/patients', methods=['GET'])
def get_patients():
    """Listar todos os pacientes"""
    patients = Patient.query.filter_by(is_active=True).all()
    return jsonify([patient.to_dict() for patient in patients])

@patient_bp.route('/patients/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Obter um paciente específico"""
    patient = Patient.query.get_or_404(patient_id)
    return jsonify(patient.to_dict())

@patient_bp.route('/patients', methods=['POST'])
def create_patient():
    """Criar um novo paciente"""
    data = request.get_json()
    
    if not data or 'name' not in data or 'phone_number' not in data:
        return jsonify({'error': 'Nome e número de telefone são obrigatórios'}), 400
    
    # Verificar se o número de telefone já existe
    existing_patient = Patient.query.filter_by(phone_number=data['phone_number']).first()
    if existing_patient:
        return jsonify({'error': 'Paciente com este número de telefone já existe'}), 400
    
    patient = Patient(
        name=data['name'],
        phone_number=data['phone_number'],
        iclinic_id=data.get('iclinic_id')
    )
    
    db.session.add(patient)
    db.session.commit()
    
    return jsonify(patient.to_dict()), 201

@patient_bp.route('/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    """Atualizar um paciente"""
    patient = Patient.query.get_or_404(patient_id)
    data = request.get_json()
    
    if 'name' in data:
        patient.name = data['name']
    if 'phone_number' in data:
        # Verificar se o novo número não está em uso por outro paciente
        existing_patient = Patient.query.filter_by(phone_number=data['phone_number']).first()
        if existing_patient and existing_patient.id != patient_id:
            return jsonify({'error': 'Número de telefone já está em uso'}), 400
        patient.phone_number = data['phone_number']
    if 'iclinic_id' in data:
        patient.iclinic_id = data['iclinic_id']
    if 'is_active' in data:
        patient.is_active = data['is_active']
    
    db.session.commit()
    return jsonify(patient.to_dict())

@patient_bp.route('/patients/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    """Desativar um paciente (soft delete)"""
    patient = Patient.query.get_or_404(patient_id)
    patient.is_active = False
    db.session.commit()
    return jsonify({'message': 'Paciente desativado com sucesso'})

@patient_bp.route('/patients/search', methods=['GET'])
def search_patients():
    """Buscar pacientes por nome ou telefone"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    patients = Patient.query.filter(
        db.or_(
            Patient.name.ilike(f'%{query}%'),
            Patient.phone_number.ilike(f'%{query}%')
        ),
        Patient.is_active == True
    ).all()
    
    return jsonify([patient.to_dict() for patient in patients])

