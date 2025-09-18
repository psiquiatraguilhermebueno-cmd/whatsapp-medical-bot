import os
import re
from flask import Blueprint, request, jsonify
from src.models.patient import Patient
from src.models.user import db

admin_patient_bp = Blueprint('admin_patient', __name__)

def _clean_phone(phone: str) -> str:
    """Limpar telefone para formato E.164 sem +"""
    if not isinstance(phone, str):
        return ""
    phone = phone.strip()
    if phone.startswith("+"):
        phone = phone[1:]
    return re.sub(r"\D+", "", phone)

def _validate_admin_secret(request):
    """Validar secret administrativo"""
    app_secret = os.getenv('APP_SECRET', '').strip()
    if not app_secret:
        return False
    
    admin_secret = request.headers.get('X-Admin-Secret', '').strip()
    return admin_secret == app_secret

@admin_patient_bp.route('/api/admin/patient/register', methods=['POST'])
def register_patient():
    """Cadastrar ou atualizar paciente"""
    try:
        # Validar secret
        if not _validate_admin_secret(request):
            return jsonify({
                'ok': False,
                'error': 'Unauthorized - Invalid X-Admin-Secret'
            }), 401
        
        data = request.get_json() or {}
        
        # Validar dados obrigatórios
        phone = data.get('phone', '').strip()
        name = data.get('name', '').strip()
        
        if not phone:
            return jsonify({
                'ok': False,
                'error': 'Phone number is required'
            }), 400
            
        if not name:
            return jsonify({
                'ok': False,
                'error': 'Name is required'
            }), 400
        
        # Limpar telefone
        phone_clean = _clean_phone(phone)
        if not phone_clean:
            return jsonify({
                'ok': False,
                'error': 'Invalid phone number format'
            }), 400
        
        # Buscar ou criar paciente
        patient = Patient.query.filter_by(whatsapp_phone=phone_clean).first()
        
        if patient:
            # Atualizar paciente existente
            patient.name = name
            patient.is_active = data.get('active', True)
            action = 'updated'
        else:
            # Criar novo paciente
            patient = Patient(
                name=name,
                whatsapp_phone=phone_clean,
                is_active=data.get('active', True)
            )
            db.session.add(patient)
            action = 'created'
        
        db.session.commit()
        
        # Log sem dados sensíveis
        phone_masked = f"****{phone_clean[-4:]}" if len(phone_clean) >= 4 else "****"
        print(f"Patient {action}: {name} - {phone_masked}")
        
        return jsonify({
            'ok': True,
            'action': action,
            'patient': {
                'id': patient.id,
                'name': patient.name,
                'phone_masked': phone_masked,
                'is_active': patient.is_active
            }
        })
        
    except Exception as e:
        print(f"Error in register_patient: {e}")
        return jsonify({
            'ok': False,
            'error': 'Internal server error'
        }), 500

@admin_patient_bp.route('/api/admin/seed-patient', methods=['POST'])
def seed_patient():
    """Ativar paciente admin rapidamente"""
    try:
        # Validar secret
        if not _validate_admin_secret(request):
            return jsonify({
                'ok': False,
                'error': 'Unauthorized - Invalid X-Admin-Secret'
            }), 401
        
        # Número do admin (configurável)
        admin_phone = os.getenv('ADMIN_PHONE_NUMBER', '5514997799022').strip()
        admin_phone_clean = _clean_phone(admin_phone)
        
        if not admin_phone_clean:
            return jsonify({
                'ok': False,
                'error': 'ADMIN_PHONE_NUMBER not configured'
            }), 500
        
        # Buscar ou criar paciente admin
        patient = Patient.query.filter_by(whatsapp_phone=admin_phone_clean).first()
        
        if patient:
            # Reativar se existir
            patient.is_active = True
            action = 'reactivated'
        else:
            # Criar novo
            patient = Patient(
                name='Dr. Admin',
                whatsapp_phone=admin_phone_clean,
                is_active=True
            )
            db.session.add(patient)
            action = 'created'
        
        db.session.commit()
        
        # Log mascarado
        phone_masked = f"****{admin_phone_clean[-4:]}" if len(admin_phone_clean) >= 4 else "****"
        print(f"Admin patient {action}: {phone_masked}")
        
        return jsonify({
            'ok': True,
            'action': action,
            'patient': {
                'id': patient.id,
                'name': patient.name,
                'phone_masked': phone_masked,
                'is_active': patient.is_active
            }
        })
        
    except Exception as e:
        print(f"Error in seed_patient: {e}")
        return jsonify({
            'ok': False,
            'error': 'Internal server error'
        }), 500

@admin_patient_bp.route('/api/admin/patient/status', methods=['GET'])
def patient_status():
    """Verificar status de pacientes"""
    try:
        # Validar secret
        if not _validate_admin_secret(request):
            return jsonify({
                'ok': False,
                'error': 'Unauthorized - Invalid X-Admin-Secret'
            }), 401
        
        # Contar pacientes
        total_patients = Patient.query.count()
        active_patients = Patient.query.filter_by(is_active=True).count()
        
        # Admin phone
        admin_phone = os.getenv('ADMIN_PHONE_NUMBER', '').strip()
        admin_phone_clean = _clean_phone(admin_phone)
        admin_registered = False
        
        if admin_phone_clean:
            admin_patient = Patient.query.filter_by(whatsapp_phone=admin_phone_clean).first()
            admin_registered = admin_patient is not None and admin_patient.is_active
        
        return jsonify({
            'ok': True,
            'stats': {
                'total_patients': total_patients,
                'active_patients': active_patients,
                'admin_registered': admin_registered,
                'admin_phone_configured': bool(admin_phone_clean)
            }
        })
        
    except Exception as e:
        print(f"Error in patient_status: {e}")
        return jsonify({
            'ok': False,
            'error': 'Internal server error'
        }), 500

