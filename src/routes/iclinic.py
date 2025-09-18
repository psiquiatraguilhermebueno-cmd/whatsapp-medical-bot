from flask import Blueprint, request, jsonify, send_file
from src.services.iclinic_service import iClinicService
from src.models.patient import Patient
from src.models.response import Response
from src.models.user import db
from datetime import datetime
import io
import json

iclinic_bp = Blueprint('iclinic', __name__)

# Instância do serviço iClinic
iclinic_service = iClinicService()

@iclinic_bp.route('/export/patients', methods=['GET'])
def export_patients():
    """Exportar pacientes em formato CSV compatível com iClinic"""
    try:
        patient_ids = request.args.get('patient_ids')
        
        if patient_ids:
            # Exportar pacientes específicos
            ids = [int(id.strip()) for id in patient_ids.split(',')]
            patients = Patient.query.filter(Patient.id.in_(ids)).all()
        else:
            # Exportar todos os pacientes ativos
            patients = None
        
        csv_content = iclinic_service.export_patients_to_csv(patients)
        
        # Criar arquivo em memória
        output = io.BytesIO()
        output.write(csv_content.encode('utf-8'))
        output.seek(0)
        
        filename = f'pacientes_iclinic_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@iclinic_bp.route('/export/responses', methods=['GET'])
def export_responses():
    """Exportar respostas de escalas em formato CSV"""
    try:
        days = int(request.args.get('days', 30))
        patient_id = request.args.get('patient_id')
        
        responses = None
        if patient_id:
            from datetime import timedelta
            start_date = datetime.now() - timedelta(days=days)
            responses = Response.query.filter(
                Response.patient_id == int(patient_id),
                Response.created_at >= start_date
            ).all()
        
        csv_content = iclinic_service.export_responses_to_csv(responses, days)
        
        # Criar arquivo em memória
        output = io.BytesIO()
        output.write(csv_content.encode('utf-8'))
        output.seek(0)
        
        filename = f'respostas_escalas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@iclinic_bp.route('/export/medication-adherence', methods=['GET'])
def export_medication_adherence():
    """Exportar relatório de aderência medicamentosa"""
    try:
        days = int(request.args.get('days', 30))
        patient_id = request.args.get('patient_id')
        
        patient_id = int(patient_id) if patient_id else None
        
        csv_content = iclinic_service.export_medication_adherence_to_csv(patient_id, days)
        
        # Criar arquivo em memória
        output = io.BytesIO()
        output.write(csv_content.encode('utf-8'))
        output.seek(0)
        
        filename = f'aderencia_medicamentosa_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@iclinic_bp.route('/export/mood-trends', methods=['GET'])
def export_mood_trends():
    """Exportar tendências de humor"""
    try:
        days = int(request.args.get('days', 30))
        patient_id = request.args.get('patient_id')
        
        patient_id = int(patient_id) if patient_id else None
        
        csv_content = iclinic_service.export_mood_trends_to_csv(patient_id, days)
        
        # Criar arquivo em memória
        output = io.BytesIO()
        output.write(csv_content.encode('utf-8'))
        output.seek(0)
        
        filename = f'tendencias_humor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@iclinic_bp.route('/import/patient', methods=['POST'])
def import_patient():
    """Importar dados de paciente do iClinic"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados do paciente são obrigatórios'}), 400
        
        patient = iclinic_service.import_patient_from_iclinic_data(data)
        
        return jsonify({
            'message': 'Paciente importado com sucesso',
            'patient': patient.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@iclinic_bp.route('/import/patients/bulk', methods=['POST'])
def import_patients_bulk():
    """Importar múltiplos pacientes do iClinic"""
    try:
        data = request.get_json()
        
        if not data or 'patients' not in data:
            return jsonify({'error': 'Lista de pacientes é obrigatória'}), 400
        
        imported_patients = []
        errors = []
        
        for patient_data in data['patients']:
            try:
                patient = iclinic_service.import_patient_from_iclinic_data(patient_data)
                imported_patients.append(patient.to_dict())
            except Exception as e:
                errors.append({
                    'patient_data': patient_data,
                    'error': str(e)
                })
        
        return jsonify({
            'message': f'{len(imported_patients)} pacientes importados com sucesso',
            'imported_patients': imported_patients,
            'errors': errors
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@iclinic_bp.route('/report/integration', methods=['GET'])
def get_integration_report():
    """Gerar relatório consolidado para integração"""
    try:
        patient_id = request.args.get('patient_id')
        patient_id = int(patient_id) if patient_id else None
        
        report = iclinic_service.generate_integration_report(patient_id)
        
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@iclinic_bp.route('/report/integration/download', methods=['GET'])
def download_integration_report():
    """Baixar relatório de integração em formato JSON"""
    try:
        patient_id = request.args.get('patient_id')
        patient_id = int(patient_id) if patient_id else None
        
        report = iclinic_service.generate_integration_report(patient_id)
        
        # Criar arquivo JSON em memória
        output = io.BytesIO()
        json_content = json.dumps(report, indent=2, ensure_ascii=False)
        output.write(json_content.encode('utf-8'))
        output.seek(0)
        
        filename = f'relatorio_integracao_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        return send_file(
            output,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@iclinic_bp.route('/sync/patient/<int:patient_id>', methods=['POST'])
def sync_patient_data():
    """Sincronizar dados específicos de um paciente"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados de sincronização são obrigatórios'}), 400
        
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        # Atualizar dados do paciente com informações do iClinic
        updated_fields = []
        
        if 'name' in data and data['name']:
            patient.name = data['name']
            updated_fields.append('name')
        
        if 'email' in data and data['email']:
            patient.email = data['email']
            updated_fields.append('email')
        
        if 'birth_date' in data and data['birth_date']:
            patient.birth_date = iclinic_service._parse_date(data['birth_date'])
            updated_fields.append('birth_date')
        
        if 'cpf' in data and data['cpf']:
            patient.cpf = data['cpf']
            updated_fields.append('cpf')
        
        if updated_fields:
            db.session.commit()
        
        return jsonify({
            'message': 'Dados do paciente sincronizados com sucesso',
            'updated_fields': updated_fields,
            'patient': patient.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@iclinic_bp.route('/templates/csv', methods=['GET'])
def get_csv_templates():
    """Obter templates de CSV para importação no iClinic"""
    try:
        templates = {
            'patients': {
                'description': 'Template para importação de pacientes no iClinic',
                'headers': [
                    'patient_code',
                    'name',
                    'birth_date',
                    'mobile_phone',
                    'email',
                    'cpf',
                    'active',
                    'observation'
                ],
                'example_row': [
                    '1',
                    'João Silva',
                    '1990-01-15',
                    '(11) 99999-9999',
                    'joao@email.com',
                    '12345678901',
                    '1',
                    'Paciente importado do sistema de lembretes'
                ]
            },
            'responses': {
                'description': 'Template para respostas de escalas clínicas',
                'headers': [
                    'patient_code',
                    'patient_name',
                    'scale_name',
                    'score',
                    'category',
                    'is_alarming',
                    'response_date',
                    'response_time',
                    'detailed_responses'
                ],
                'example_row': [
                    '1',
                    'João Silva',
                    'PHQ-9',
                    '12',
                    'Moderada',
                    '0',
                    '2025-08-26',
                    '14:30:00',
                    '1. Pouco interesse: Vários dias | 2. Sentindo-se deprimido: Mais da metade dos dias'
                ]
            }
        }
        
        return jsonify(templates), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@iclinic_bp.route('/status', methods=['GET'])
def get_integration_status():
    """Obter status da integração com iClinic"""
    try:
        # Estatísticas básicas
        total_patients = Patient.query.filter_by(is_active=True).count()
        
        from datetime import timedelta
        week_ago = datetime.now() - timedelta(days=7)
        recent_responses = Response.query.filter(Response.created_at >= week_ago).count()
        
        status = {
            'integration_type': 'CSV Export/Import',
            'status': 'active',
            'last_export': None,  # Seria atualizado quando houver exports
            'statistics': {
                'total_patients': total_patients,
                'recent_responses_7_days': recent_responses,
                'available_exports': [
                    'patients',
                    'responses',
                    'medication_adherence',
                    'mood_trends'
                ]
            },
            'features': {
                'patient_export': True,
                'response_export': True,
                'medication_tracking': True,
                'mood_tracking': True,
                'bulk_import': True,
                'real_time_sync': False,  # Não disponível via CSV
                'webhooks': False  # Não disponível no iClinic
            }
        }
        
        return jsonify(status), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

