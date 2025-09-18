import csv
import io
from typing import Dict, List, Optional
from datetime import datetime, date
from src.models.patient import Patient
from src.models.response import Response
from src.models.medication import Medication, MedicationConfirmation
from src.models.mood_chart import MoodChart
from src.models.user import db

class iClinicService:
    """Serviço de integração com iClinic via exportação/importação de dados"""
    
    def __init__(self):
        # Mapeamento de campos do bot para formato iClinic
        self.field_mapping = {
            'patient_code': 'id',
            'name': 'name',
            'birth_date': 'birth_date',
            'mobile_phone': 'phone_number',
            'email': 'email',
            'cpf': 'cpf',
            'active': 'is_active'
        }
    
    def export_patients_to_csv(self, patients: List[Patient] = None) -> str:
        """
        Exportar pacientes em formato CSV compatível com iClinic
        
        Args:
            patients: Lista de pacientes (se None, exporta todos os ativos)
            
        Returns:
            String contendo o CSV formatado
        """
        if patients is None:
            patients = Patient.query.filter_by(is_active=True).all()
        
        # Cabeçalhos conforme documentação iClinic
        headers = [
            'patient_code',
            'name',
            'birth_date',
            'mobile_phone',
            'email',
            'cpf',
            'active',
            'observation'
        ]
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escrever cabeçalho
        writer.writerow(headers)
        
        # Escrever dados dos pacientes
        for patient in patients:
            row = [
                patient.id,
                patient.name,
                patient.birth_date.strftime('%Y-%m-%d') if patient.birth_date else '',
                self._format_phone_for_iclinic(patient.phone_number),
                patient.email or '',
                patient.cpf or '',
                '1' if patient.is_active else '0',
                f'Paciente importado do sistema de lembretes médicos em {datetime.now().strftime("%d/%m/%Y")}'
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    def export_responses_to_csv(self, responses: List[Response] = None, days: int = 30) -> str:
        """
        Exportar respostas de escalas em formato CSV para análise no iClinic
        
        Args:
            responses: Lista de respostas (se None, exporta dos últimos 30 dias)
            days: Número de dias para buscar respostas (se responses for None)
            
        Returns:
            String contendo o CSV formatado
        """
        if responses is None:
            from datetime import timedelta
            start_date = datetime.now() - timedelta(days=days)
            responses = Response.query.filter(Response.created_at >= start_date).all()
        
        headers = [
            'patient_code',
            'patient_name',
            'scale_name',
            'score',
            'category',
            'is_alarming',
            'response_date',
            'response_time',
            'detailed_responses'
        ]
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escrever cabeçalho
        writer.writerow(headers)
        
        # Escrever dados das respostas
        for response in responses:
            patient = Patient.query.get(response.patient_id)
            if not patient:
                continue
            
            # Extrair dados da resposta
            response_data = response.response_data or {}
            scale_name = response_data.get('scale_name', 'Não especificado')
            
            # Formatar respostas detalhadas
            detailed_responses = self._format_detailed_responses(response_data)
            
            row = [
                patient.id,
                patient.name,
                scale_name,
                response.score or 0,
                response.category or '',
                '1' if response.is_alarming else '0',
                response.created_at.strftime('%Y-%m-%d'),
                response.created_at.strftime('%H:%M:%S'),
                detailed_responses
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    def export_medication_adherence_to_csv(self, patient_id: int = None, days: int = 30) -> str:
        """
        Exportar relatório de aderência medicamentosa em formato CSV
        
        Args:
            patient_id: ID do paciente (se None, exporta todos)
            days: Número de dias para análise
            
        Returns:
            String contendo o CSV formatado
        """
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        
        # Buscar confirmações de medicação
        query = MedicationConfirmation.query.filter(
            MedicationConfirmation.scheduled_time >= start_date
        )
        
        if patient_id:
            query = query.filter_by(patient_id=patient_id)
        
        confirmations = query.all()
        
        headers = [
            'patient_code',
            'patient_name',
            'medication_name',
            'dosage',
            'scheduled_date',
            'scheduled_time',
            'confirmed_date',
            'confirmed_time',
            'status',
            'adherence_percentage'
        ]
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escrever cabeçalho
        writer.writerow(headers)
        
        # Agrupar por paciente e medicação
        adherence_data = self._calculate_adherence_data(confirmations)
        
        for data in adherence_data:
            writer.writerow(data)
        
        return output.getvalue()
    
    def export_mood_trends_to_csv(self, patient_id: int = None, days: int = 30) -> str:
        """
        Exportar tendências de humor em formato CSV
        
        Args:
            patient_id: ID do paciente (se None, exporta todos)
            days: Número de dias para análise
            
        Returns:
            String contendo o CSV formatado
        """
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        
        query = MoodChart.query.filter(MoodChart.date >= start_date.date())
        
        if patient_id:
            query = query.filter_by(patient_id=patient_id)
        
        mood_charts = query.order_by(MoodChart.date.desc()).all()
        
        headers = [
            'patient_code',
            'patient_name',
            'date',
            'mood_level',
            'functioning_level',
            'sleep_quality',
            'sleep_hours',
            'anxiety_level',
            'irritability_level',
            'medications_taken',
            'significant_events',
            'notes'
        ]
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escrever cabeçalho
        writer.writerow(headers)
        
        # Escrever dados de humor
        for mood_chart in mood_charts:
            patient = Patient.query.get(mood_chart.patient_id)
            if not patient:
                continue
            
            row = [
                patient.id,
                patient.name,
                mood_chart.date.strftime('%Y-%m-%d'),
                mood_chart.mood_level or '',
                mood_chart.functioning_level or '',
                mood_chart.sleep_quality or '',
                mood_chart.sleep_hours or '',
                mood_chart.anxiety_level or '',
                mood_chart.irritability_level or '',
                '1' if mood_chart.medications_taken else '0',
                mood_chart.significant_events or '',
                mood_chart.notes or ''
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    def import_patient_from_iclinic_data(self, iclinic_data: Dict) -> Patient:
        """
        Importar dados de paciente do iClinic para o sistema
        
        Args:
            iclinic_data: Dicionário com dados do paciente do iClinic
            
        Returns:
            Objeto Patient criado ou atualizado
        """
        # Mapear campos do iClinic para o nosso sistema
        patient_data = {
            'name': iclinic_data.get('name'),
            'phone_number': self._format_phone_from_iclinic(iclinic_data.get('mobile_phone')),
            'email': iclinic_data.get('email'),
            'birth_date': self._parse_date(iclinic_data.get('birth_date')),
            'cpf': iclinic_data.get('cpf'),
            'is_active': iclinic_data.get('active', '1') == '1'
        }
        
        # Verificar se paciente já existe (por CPF ou telefone)
        existing_patient = None
        if patient_data['cpf']:
            existing_patient = Patient.query.filter_by(cpf=patient_data['cpf']).first()
        elif patient_data['phone_number']:
            existing_patient = Patient.query.filter_by(phone_number=patient_data['phone_number']).first()
        
        if existing_patient:
            # Atualizar paciente existente
            for key, value in patient_data.items():
                if value is not None:
                    setattr(existing_patient, key, value)
            
            db.session.commit()
            return existing_patient
        else:
            # Criar novo paciente
            patient = Patient(**patient_data)
            db.session.add(patient)
            db.session.commit()
            return patient
    
    def generate_integration_report(self, patient_id: int = None) -> Dict:
        """
        Gerar relatório consolidado para integração com iClinic
        
        Args:
            patient_id: ID do paciente (se None, gera para todos)
            
        Returns:
            Dicionário com dados consolidados
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'patients': [],
            'summary': {
                'total_patients': 0,
                'total_responses': 0,
                'total_medications': 0,
                'total_mood_entries': 0
            }
        }
        
        # Buscar pacientes
        if patient_id:
            patients = [Patient.query.get(patient_id)]
        else:
            patients = Patient.query.filter_by(is_active=True).all()
        
        for patient in patients:
            if not patient:
                continue
            
            # Dados do paciente
            patient_data = {
                'id': patient.id,
                'name': patient.name,
                'phone': patient.phone_number,
                'email': patient.email,
                'recent_responses': [],
                'medications': [],
                'mood_entries': []
            }
            
            # Respostas recentes (últimos 30 dias)
            from datetime import timedelta
            start_date = datetime.now() - timedelta(days=30)
            
            responses = Response.query.filter(
                Response.patient_id == patient.id,
                Response.created_at >= start_date
            ).order_by(Response.created_at.desc()).limit(10).all()
            
            for response in responses:
                response_data = response.response_data or {}
                patient_data['recent_responses'].append({
                    'scale': response_data.get('scale_name', 'Não especificado'),
                    'score': response.score,
                    'category': response.category,
                    'alarming': response.is_alarming,
                    'date': response.created_at.strftime('%Y-%m-%d %H:%M')
                })
            
            # Medicações ativas
            medications = Medication.query.filter_by(
                patient_id=patient.id,
                is_active=True
            ).all()
            
            for medication in medications:
                patient_data['medications'].append({
                    'name': medication.name,
                    'dosage': medication.dosage,
                    'frequency': medication.frequency,
                    'times': medication.times
                })
            
            # Registros de humor recentes
            mood_charts = MoodChart.query.filter(
                MoodChart.patient_id == patient.id,
                MoodChart.date >= start_date.date()
            ).order_by(MoodChart.date.desc()).limit(10).all()
            
            for mood_chart in mood_charts:
                patient_data['mood_entries'].append({
                    'date': mood_chart.date.strftime('%Y-%m-%d'),
                    'mood_level': mood_chart.mood_level,
                    'functioning_level': mood_chart.functioning_level,
                    'sleep_quality': mood_chart.sleep_quality
                })
            
            report['patients'].append(patient_data)
            
            # Atualizar sumário
            report['summary']['total_responses'] += len(patient_data['recent_responses'])
            report['summary']['total_medications'] += len(patient_data['medications'])
            report['summary']['total_mood_entries'] += len(patient_data['mood_entries'])
        
        report['summary']['total_patients'] = len(report['patients'])
        
        return report
    
    def _format_phone_for_iclinic(self, phone: str) -> str:
        """Formatar telefone para o padrão do iClinic"""
        if not phone:
            return ''
        
        # Remover caracteres não numéricos
        digits = ''.join(filter(str.isdigit, phone))
        
        # Formatar conforme padrão iClinic: (99) 99999-9999
        if len(digits) == 11:
            return f'({digits[:2]}) {digits[2:7]}-{digits[7:]}'
        elif len(digits) == 10:
            return f'({digits[:2]}) {digits[2:6]}-{digits[6:]}'
        
        return phone
    
    def _format_phone_from_iclinic(self, phone: str) -> str:
        """Formatar telefone do iClinic para o padrão do sistema"""
        if not phone:
            return ''
        
        # Remover caracteres não numéricos e adicionar código do país
        digits = ''.join(filter(str.isdigit, phone))
        
        if len(digits) == 11:
            return f'55{digits}'
        elif len(digits) == 10:
            return f'55{digits}'
        
        return phone
    
    def _parse_date(self, date_str: str) -> date:
        """Converter string de data para objeto date"""
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None
    
    def _format_detailed_responses(self, response_data: Dict) -> str:
        """Formatar respostas detalhadas para CSV"""
        if not response_data or 'responses' not in response_data:
            return ''
        
        responses = response_data['responses']
        formatted = []
        
        for i, response in enumerate(responses, 1):
            question = response.get('question', f'Pergunta {i}')
            answer = response.get('answer', 'Não respondido')
            formatted.append(f'{i}. {question}: {answer}')
        
        return ' | '.join(formatted)
    
    def _calculate_adherence_data(self, confirmations: List[MedicationConfirmation]) -> List[List]:
        """Calcular dados de aderência medicamentosa"""
        # Agrupar por paciente e medicação
        grouped = {}
        
        for confirmation in confirmations:
            patient = Patient.query.get(confirmation.patient_id)
            medication = Medication.query.get(confirmation.medication_id)
            
            if not patient or not medication:
                continue
            
            key = (patient.id, medication.id)
            
            if key not in grouped:
                grouped[key] = {
                    'patient': patient,
                    'medication': medication,
                    'confirmations': []
                }
            
            grouped[key]['confirmations'].append(confirmation)
        
        # Calcular aderência para cada grupo
        result = []
        
        for (patient_id, medication_id), data in grouped.items():
            patient = data['patient']
            medication = data['medication']
            confirmations = data['confirmations']
            
            total_scheduled = len(confirmations)
            total_confirmed = len([c for c in confirmations if c.status == 'confirmed'])
            
            adherence_percentage = (total_confirmed / total_scheduled * 100) if total_scheduled > 0 else 0
            
            for confirmation in confirmations:
                row = [
                    patient.id,
                    patient.name,
                    medication.name,
                    medication.dosage,
                    confirmation.scheduled_time.strftime('%Y-%m-%d'),
                    confirmation.scheduled_time.strftime('%H:%M:%S'),
                    confirmation.confirmed_time.strftime('%Y-%m-%d') if confirmation.confirmed_time else '',
                    confirmation.confirmed_time.strftime('%H:%M:%S') if confirmation.confirmed_time else '',
                    confirmation.status,
                    f'{adherence_percentage:.1f}%'
                ]
                result.append(row)
        
        return result

