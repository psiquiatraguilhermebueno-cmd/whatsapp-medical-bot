from typing import Dict, List
from src.models.patient import Patient
from src.models.medication import Medication, MedicationConfirmation
from src.models.user import db
from src.services.whatsapp_service import WhatsAppService
from datetime import datetime, date, time
import json

class MedicationService:
    """Serviço para gerenciar lembretes de medicação"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
    
    def send_medication_reminder(self, patient: Patient, medication: Medication) -> Dict:
        """Enviar lembrete de medicação"""
        current_time = datetime.now().strftime('%H:%M')
        
        message = f"""💊 *Lembrete de Medicação*

⏰ *Horário:* {current_time}
💊 *Medicamento:* {medication.name}
📏 *Dosagem:* {medication.dosage}

{medication.instructions if medication.instructions else ''}

Por favor, confirme quando tomar o medicamento."""
        
        # Criar botões de confirmação
        buttons = [
            {'id': f'med_confirm_{medication.id}', 'title': '✅ Tomei agora'},
            {'id': f'med_delay_{medication.id}', 'title': '⏰ Lembrar em 15min'},
            {'id': f'med_skip_{medication.id}', 'title': '❌ Pular esta dose'}
        ]
        
        result = self.whatsapp_service.send_interactive_message(
            patient.phone_number,
            "💊 Hora do Medicamento",
            message,
            buttons
        )
        
        # Criar registro de confirmação pendente
        confirmation = MedicationConfirmation(
            medication_id=medication.id,
            patient_id=patient.id,
            scheduled_time=datetime.now(),
            status='pending'
        )
        db.session.add(confirmation)
        db.session.commit()
        
        return {
            'status': 'sent',
            'action': 'medication_reminder_sent',
            'medication_id': medication.id,
            'confirmation_id': confirmation.id
        }
    
    def handle_medication_button(self, patient: Patient, button_id: str) -> Dict:
        """Processar resposta de botão de medicação"""
        parts = button_id.split('_')
        action = parts[1]  # confirm, delay, skip
        medication_id = int(parts[2])
        
        medication = Medication.query.get(medication_id)
        if not medication:
            return {'status': 'error', 'message': 'Medicação não encontrada'}
        
        # Buscar confirmação pendente
        confirmation = MedicationConfirmation.query.filter_by(
            medication_id=medication_id,
            patient_id=patient.id,
            status='pending'
        ).order_by(MedicationConfirmation.created_at.desc()).first()
        
        if action == 'confirm':
            return self._confirm_medication(patient, medication, confirmation)
        elif action == 'delay':
            return self._delay_medication(patient, medication, confirmation)
        elif action == 'skip':
            return self._skip_medication(patient, medication, confirmation)
        
        return {'status': 'error', 'message': 'Ação não reconhecida'}
    
    def _confirm_medication(self, patient: Patient, medication: Medication, confirmation: MedicationConfirmation) -> Dict:
        """Confirmar que o medicamento foi tomado"""
        if confirmation:
            confirmation.status = 'confirmed'
            confirmation.confirmed_time = datetime.now()
            db.session.commit()
        
        message = f"""✅ *Medicação Confirmada*

💊 {medication.name} - {medication.dosage}
⏰ Confirmado às {datetime.now().strftime('%H:%M')}

Ótimo! Continue seguindo seu tratamento. 👍"""
        
        self.whatsapp_service.send_text_message(patient.phone_number, message)
        
        return {'status': 'confirmed', 'action': 'medication_confirmed'}
    
    def _delay_medication(self, patient: Patient, medication: Medication, confirmation: MedicationConfirmation) -> Dict:
        """Atrasar lembrete de medicação"""
        message = f"""⏰ *Lembrete Adiado*

💊 {medication.name}
🔔 Você receberá um novo lembrete em 15 minutos.

Não se esqueça! 😊"""
        
        self.whatsapp_service.send_text_message(patient.phone_number, message)
        
        # Aqui você implementaria a lógica para reagendar o lembrete
        # Por exemplo, adicionar uma tarefa para enviar em 15 minutos
        
        return {'status': 'delayed', 'action': 'medication_delayed'}
    
    def _skip_medication(self, patient: Patient, medication: Medication, confirmation: MedicationConfirmation) -> Dict:
        """Pular dose de medicação"""
        if confirmation:
            confirmation.status = 'missed'
            confirmation.notes = 'Pulado pelo paciente'
            db.session.commit()
        
        message = f"""❌ *Dose Pulada*

💊 {medication.name}
📝 Registrado como dose pulada.

⚠️ Lembre-se: é importante manter a regularidade do tratamento. Se tiver dúvidas, consulte seu médico."""
        
        self.whatsapp_service.send_text_message(patient.phone_number, message)
        
        return {'status': 'skipped', 'action': 'medication_skipped'}
    
    def send_medication_status(self, patient: Patient) -> Dict:
        """Enviar status das medicações do paciente"""
        medications = Medication.query.filter_by(
            patient_id=patient.id,
            is_active=True
        ).all()
        
        if not medications:
            message = """💊 *Suas Medicações*

Você não tem medicações cadastradas no momento.

Se você deveria ter medicações cadastradas, entre em contato com seu profissional de saúde."""
            
            self.whatsapp_service.send_text_message(patient.phone_number, message)
            return {'status': 'sent', 'action': 'no_medications'}
        
        # Construir lista de medicações
        message = "💊 *Suas Medicações Ativas:*\n\n"
        
        for med in medications:
            times_str = ", ".join(med.times)
            message += f"🔹 *{med.name}*\n"
            message += f"   📏 {med.dosage}\n"
            message += f"   ⏰ {times_str}\n"
            message += f"   📅 {med.frequency}\n\n"
        
        message += "✅ Continue seguindo seu tratamento conforme orientado!"
        
        self.whatsapp_service.send_text_message(patient.phone_number, message)
        
        return {'status': 'sent', 'action': 'medication_status_sent'}
    
    def process_medication_confirmation(self, patient: Patient, message_text: str, user_state: Dict) -> Dict:
        """Processar confirmação de medicação via texto"""
        medication_id = user_state.get('medication_id')
        
        if not medication_id:
            return {'status': 'error', 'message': 'ID da medicação não encontrado'}
        
        medication = Medication.query.get(medication_id)
        if not medication:
            return {'status': 'error', 'message': 'Medicação não encontrada'}
        
        # Processar resposta
        response_lower = message_text.lower()
        
        if any(word in response_lower for word in ['sim', 'tomei', 'ok', 'confirmado']):
            return self._confirm_medication_text(patient, medication, message_text)
        elif any(word in response_lower for word in ['não', 'nao', 'ainda não', 'depois']):
            return self._delay_medication_text(patient, medication)
        else:
            # Resposta não reconhecida
            message = """Não entendi sua resposta. 

Por favor, responda:
• "Sim" ou "Tomei" para confirmar
• "Não" ou "Depois" para adiar
• "Pular" para pular esta dose"""
            
            self.whatsapp_service.send_text_message(patient.phone_number, message)
            return {'status': 'error', 'action': 'unclear_response'}
    
    def _confirm_medication_text(self, patient: Patient, medication: Medication, notes: str = "") -> Dict:
        """Confirmar medicação via resposta de texto"""
        # Buscar confirmação pendente
        confirmation = MedicationConfirmation.query.filter_by(
            medication_id=medication.id,
            patient_id=patient.id,
            status='pending'
        ).order_by(MedicationConfirmation.created_at.desc()).first()
        
        if confirmation:
            confirmation.status = 'confirmed'
            confirmation.confirmed_time = datetime.now()
            confirmation.notes = notes
            db.session.commit()
        
        message = f"""✅ *Confirmado!*

💊 {medication.name} tomado às {datetime.now().strftime('%H:%M')}

Obrigado por confirmar! 👍"""
        
        self.whatsapp_service.send_text_message(patient.phone_number, message)
        
        return {'status': 'confirmed', 'action': 'medication_confirmed_text'}
    
    def _delay_medication_text(self, patient: Patient, medication: Medication) -> Dict:
        """Atrasar medicação via resposta de texto"""
        message = f"""⏰ *Entendido!*

💊 {medication.name}
🔔 Vou lembrar você novamente em 15 minutos.

Não se esqueça! 😊"""
        
        self.whatsapp_service.send_text_message(patient.phone_number, message)
        
        return {'status': 'delayed', 'action': 'medication_delayed_text'}
    
    def get_medication_adherence_report(self, patient: Patient, days: int = 7) -> Dict:
        """Gerar relatório de aderência à medicação"""
        from datetime import timedelta
        
        start_date = datetime.now() - timedelta(days=days)
        
        confirmations = MedicationConfirmation.query.filter(
            MedicationConfirmation.patient_id == patient.id,
            MedicationConfirmation.created_at >= start_date
        ).all()
        
        total_scheduled = len(confirmations)
        confirmed = len([c for c in confirmations if c.status == 'confirmed'])
        missed = len([c for c in confirmations if c.status == 'missed'])
        
        adherence_rate = (confirmed / total_scheduled * 100) if total_scheduled > 0 else 0
        
        return {
            'total_scheduled': total_scheduled,
            'confirmed': confirmed,
            'missed': missed,
            'adherence_rate': round(adherence_rate, 1),
            'period_days': days
        }

