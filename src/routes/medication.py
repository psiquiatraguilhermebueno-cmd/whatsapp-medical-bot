from flask import Blueprint, request, jsonify
from src.models.medication import Medication, MedicationConfirmation
from src.models.patient import Patient
from src.models.user import db
from datetime import datetime, date, time

medication_bp = Blueprint('medication', __name__)

@medication_bp.route('/medications', methods=['GET'])
def get_medications():
    """Listar todas as medicações"""
    try:
        patient_id = request.args.get('patient_id')
        
        query = Medication.query
        if patient_id:
            query = query.filter_by(patient_id=patient_id)
        
        medications = query.all()
        return jsonify([med.to_dict() for med in medications]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@medication_bp.route('/medications', methods=['POST'])
def create_medication():
    """Criar nova medicação"""
    try:
        data = request.get_json()
        
        required_fields = ['patient_id', 'name', 'dosage', 'frequency', 'times', 'start_date']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Campos obrigatórios: patient_id, name, dosage, frequency, times, start_date'}), 400
        
        # Verificar se o paciente existe
        patient = Patient.query.get(data['patient_id'])
        if not patient:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        # Converter data de string para date
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = None
        if data.get('end_date'):
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        medication = Medication(
            patient_id=data['patient_id'],
            name=data['name'],
            dosage=data['dosage'],
            frequency=data['frequency'],
            times=data['times'],
            instructions=data.get('instructions'),
            start_date=start_date,
            end_date=end_date
        )
        
        db.session.add(medication)
        db.session.commit()
        
        return jsonify(medication.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@medication_bp.route('/medications/<int:medication_id>', methods=['GET'])
def get_medication(medication_id):
    """Obter medicação específica"""
    try:
        medication = Medication.query.get(medication_id)
        if not medication:
            return jsonify({'error': 'Medicação não encontrada'}), 404
        
        return jsonify(medication.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@medication_bp.route('/medications/<int:medication_id>', methods=['PUT'])
def update_medication(medication_id):
    """Atualizar medicação"""
    try:
        medication = Medication.query.get(medication_id)
        if not medication:
            return jsonify({'error': 'Medicação não encontrada'}), 404
        
        data = request.get_json()
        
        # Atualizar campos permitidos
        if 'name' in data:
            medication.name = data['name']
        if 'dosage' in data:
            medication.dosage = data['dosage']
        if 'frequency' in data:
            medication.frequency = data['frequency']
        if 'times' in data:
            medication.times = data['times']
        if 'instructions' in data:
            medication.instructions = data['instructions']
        if 'start_date' in data:
            medication.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if 'end_date' in data:
            medication.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data['end_date'] else None
        if 'is_active' in data:
            medication.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify(medication.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@medication_bp.route('/medications/<int:medication_id>', methods=['DELETE'])
def delete_medication(medication_id):
    """Deletar medicação"""
    try:
        medication = Medication.query.get(medication_id)
        if not medication:
            return jsonify({'error': 'Medicação não encontrada'}), 404
        
        db.session.delete(medication)
        db.session.commit()
        
        return jsonify({'message': 'Medicação deletada com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@medication_bp.route('/medications/<int:medication_id>/confirmations', methods=['GET'])
def get_medication_confirmations(medication_id):
    """Obter confirmações de uma medicação"""
    try:
        medication = Medication.query.get(medication_id)
        if not medication:
            return jsonify({'error': 'Medicação não encontrada'}), 404
        
        confirmations = MedicationConfirmation.query.filter_by(medication_id=medication_id).all()
        return jsonify([conf.to_dict() for conf in confirmations]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@medication_bp.route('/confirmations', methods=['POST'])
def create_confirmation():
    """Criar confirmação de medicação"""
    try:
        data = request.get_json()
        
        required_fields = ['medication_id', 'patient_id', 'scheduled_time']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Campos obrigatórios: medication_id, patient_id, scheduled_time'}), 400
        
        # Verificar se a medicação existe
        medication = Medication.query.get(data['medication_id'])
        if not medication:
            return jsonify({'error': 'Medicação não encontrada'}), 404
        
        # Verificar se o paciente existe
        patient = Patient.query.get(data['patient_id'])
        if not patient:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        scheduled_time = datetime.fromisoformat(data['scheduled_time'])
        confirmed_time = None
        if data.get('confirmed_time'):
            confirmed_time = datetime.fromisoformat(data['confirmed_time'])
        
        confirmation = MedicationConfirmation(
            medication_id=data['medication_id'],
            patient_id=data['patient_id'],
            scheduled_time=scheduled_time,
            confirmed_time=confirmed_time,
            status=data.get('status', 'pending'),
            notes=data.get('notes')
        )
        
        db.session.add(confirmation)
        db.session.commit()
        
        return jsonify(confirmation.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@medication_bp.route('/confirmations/<int:confirmation_id>', methods=['PUT'])
def update_confirmation(confirmation_id):
    """Atualizar confirmação de medicação"""
    try:
        confirmation = MedicationConfirmation.query.get(confirmation_id)
        if not confirmation:
            return jsonify({'error': 'Confirmação não encontrada'}), 404
        
        data = request.get_json()
        
        if 'status' in data:
            confirmation.status = data['status']
        if 'confirmed_time' in data:
            confirmation.confirmed_time = datetime.fromisoformat(data['confirmed_time']) if data['confirmed_time'] else None
        if 'notes' in data:
            confirmation.notes = data['notes']
        
        db.session.commit()
        
        return jsonify(confirmation.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@medication_bp.route('/patients/<int:patient_id>/adherence', methods=['GET'])
def get_adherence_report(patient_id):
    """Obter relatório de aderência de um paciente"""
    try:
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        days = int(request.args.get('days', 7))
        
        from src.services.medication_service import MedicationService
        medication_service = MedicationService()
        
        report = medication_service.get_medication_adherence_report(patient, days)
        
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@medication_bp.route('/patients/<int:patient_id>/medications/active', methods=['GET'])
def get_active_medications(patient_id):
    """Obter medicações ativas de um paciente"""
    try:
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        medications = Medication.query.filter_by(
            patient_id=patient_id,
            is_active=True
        ).all()
        
        return jsonify([med.to_dict() for med in medications]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

