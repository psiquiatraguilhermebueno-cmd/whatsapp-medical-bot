import logging
import os
from typing import Dict, List
from datetime import datetime, date
from src.services.whatsapp_service import WhatsAppService
from src.models.patient import Patient
from src.models.reminder import Reminder
from src.models.response import Response
from src.models.scale import Scale
from src.models.medication import Medication, MedicationConfirmation
from src.models.mood_chart import MoodChart
from src.models.user import db

class WhatsAppAdminService:
    """Serviço para interface administrativa via WhatsApp"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.logger = logging.getLogger(__name__)
        
        # Estados de conversa para fluxos administrativos
        self.conversation_states = {}
    
    def handle_command(self, phone_number: str, command: str, user_info: Dict) -> Dict:
        """Processar comando administrativo"""
        try:
            command = command.lower().strip()
            
            if command in ['/menu', 'menu']:
                return self._send_main_menu(phone_number)
            elif command in ['/pacientes', 'pacientes']:
                return self._send_patients_menu(phone_number)
            elif command in ['/lembretes', 'lembretes']:
                return self._send_reminders_menu(phone_number)
            elif command in ['/relatorios', 'relatorios']:
                return self._send_reports_menu(phone_number)
            elif command in ['/sistema', 'sistema']:
                return self._send_system_menu(phone_number)
            elif command in ['/status', 'status']:
                return self._send_quick_status(phone_number)
            elif command.startswith('/add_paciente'):
                return self._start_add_patient_flow(phone_number, command)
            else:
                return self._send_help_message(phone_number)
                
        except Exception as e:
            self.logger.error(f"Erro ao processar comando: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_callback(self, phone_number: str, callback_data: str, user_info: Dict) -> Dict:
        """Processar callback de botão administrativo"""
        try:
            if callback_data == 'admin_patients':
                return self._send_patients_menu(phone_number)
            elif callback_data == 'admin_reminders':
                return self._send_reminders_menu(phone_number)
            elif callback_data == 'admin_reports':
                return self._send_reports_menu(phone_number)
            elif callback_data == 'admin_system':
                return self._send_system_menu(phone_number)
            elif callback_data == 'admin_add_patient':
                return self._start_add_patient_flow(phone_number)
            elif callback_data == 'admin_list_patients':
                return self._list_patients(phone_number)
            elif callback_data == 'admin_patient_stats':
                return self._send_patient_statistics(phone_number)
            elif callback_data == 'admin_recent_responses':
                return self._send_recent_responses(phone_number)
            elif callback_data == 'admin_alerts':
                return self._send_alerts_summary(phone_number)
            elif callback_data == 'admin_medication_adherence':
                return self._send_medication_adherence(phone_number)
            elif callback_data == 'admin_system_status':
                return self._send_system_status(phone_number)
            elif callback_data == 'admin_backup_data':
                return self._backup_data(phone_number)
            elif callback_data.startswith('patient_details_'):
                patient_id = int(callback_data.split('_')[-1])
                return self._send_patient_details(phone_number, patient_id)
            else:
                return {"status": "processed", "action": "unknown_callback"}
                
        except Exception as e:
            self.logger.error(f"Erro ao processar callback: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_main_menu(self, phone_number: str) -> Dict:
        """Enviar menu principal administrativo"""
        message = """🏥 *Painel Administrativo*

Escolha uma opção para gerenciar o sistema:"""
        
        buttons = [
            {"id": "admin_patients", "title": "👥 Pacientes"},
            {"id": "admin_reminders", "title": "⏰ Lembretes"},
            {"id": "admin_reports", "title": "📊 Relatórios"}
        ]
        
        self.whatsapp_service.send_interactive_message(
            phone_number, 
            "Menu Principal", 
            message, 
            buttons
        )
        
        return {"status": "sent", "action": "main_menu_sent"}
    
    def _send_patients_menu(self, phone_number: str) -> Dict:
        """Enviar menu de gerenciamento de pacientes"""
        message = """👥 *Gerenciamento de Pacientes*

O que você gostaria de fazer?"""
        
        buttons = [
            {"id": "admin_add_patient", "title": "➕ Adicionar Paciente"},
            {"id": "admin_list_patients", "title": "📋 Listar Pacientes"},
            {"id": "admin_patient_stats", "title": "📊 Estatísticas"}
        ]
        
        self.whatsapp_service.send_interactive_message(
            phone_number, 
            "Gerenciar Pacientes", 
            message, 
            buttons
        )
        
        return {"status": "sent", "action": "patients_menu_sent"}
    
    def _send_reminders_menu(self, phone_number: str) -> Dict:
        """Enviar menu de gerenciamento de lembretes"""
        message = """⏰ *Gerenciamento de Lembretes*

Escolha uma opção:"""
        
        # Para WhatsApp, vamos usar lista para mais opções
        sections = [{
            "title": "Lembretes",
            "rows": [
                {"id": "admin_create_reminder", "title": "➕ Criar Lembrete", "description": "Novo lembrete para paciente"},
                {"id": "admin_list_reminders", "title": "📋 Listar Lembretes", "description": "Ver lembretes ativos"},
                {"id": "admin_reminder_templates", "title": "📝 Templates", "description": "Gerenciar templates"}
            ]
        }]
        
        self.whatsapp_service.send_list_message(
            phone_number,
            "Gerenciar Lembretes",
            message,
            "Ver Opções",
            sections
        )
        
        return {"status": "sent", "action": "reminders_menu_sent"}
    
    def _send_reports_menu(self, phone_number: str) -> Dict:
        """Enviar menu de relatórios"""
        message = """📊 *Relatórios e Análises*

Selecione o tipo de relatório:"""
        
        buttons = [
            {"id": "admin_recent_responses", "title": "📋 Respostas Recentes"},
            {"id": "admin_alerts", "title": "🚨 Alertas"},
            {"id": "admin_medication_adherence", "title": "💊 Aderência"}
        ]
        
        self.whatsapp_service.send_interactive_message(
            phone_number, 
            "Relatórios", 
            message, 
            buttons
        )
        
        return {"status": "sent", "action": "reports_menu_sent"}
    
    def _send_system_menu(self, phone_number: str) -> Dict:
        """Enviar menu do sistema"""
        message = """⚙️ *Configurações do Sistema*

Opções de sistema:"""
        
        buttons = [
            {"id": "admin_system_status", "title": "📈 Status do Sistema"},
            {"id": "admin_backup_data", "title": "💾 Backup de Dados"},
            {"id": "admin_main_menu", "title": "🏠 Menu Principal"}
        ]
        
        self.whatsapp_service.send_interactive_message(
            phone_number, 
            "Sistema", 
            message, 
            buttons
        )
        
        return {"status": "sent", "action": "system_menu_sent"}
    
    def _send_quick_status(self, phone_number: str) -> Dict:
        """Enviar status rápido do sistema"""
        try:
            # Contar estatísticas básicas
            total_patients = Patient.query.filter_by(is_active=True).count()
            total_reminders = Reminder.query.filter_by(is_active=True).count()
            responses_today = Response.query.filter(
                Response.created_at >= date.today()
            ).count()
            
            # Alertas recentes (respostas com pontuação alta)
            recent_alerts = Response.query.filter(
                Response.created_at >= date.today(),
                Response.alert_triggered == True
            ).count()
            
            message = f"""📈 *Status Rápido do Sistema*

👥 *Pacientes Ativos:* {total_patients}
⏰ *Lembretes Ativos:* {total_reminders}
📋 *Respostas Hoje:* {responses_today}
🚨 *Alertas Hoje:* {recent_alerts}

📅 *Última Atualização:* {datetime.now().strftime('%d/%m/%Y %H:%M')}

Digite */menu* para ver mais opções."""
            
            self.whatsapp_service.send_text_message(phone_number, message)
            return {"status": "sent", "action": "quick_status_sent"}
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar status: {e}")
            return {"status": "error", "message": str(e)}
    
    def _start_add_patient_flow(self, phone_number: str, command: str = None) -> Dict:
        """Iniciar fluxo de adição de paciente"""
        # Verificar se foi passado nome no comando
        if command and len(command.split()) > 1:
            patient_name = ' '.join(command.split()[1:])
            return self._ask_patient_phone(phone_number, patient_name)
        
        # Iniciar fluxo perguntando o nome
        self.conversation_states[phone_number] = {
            "flow": "add_patient",
            "step": "name",
            "data": {}
        }
        
        message = """➕ *Adicionar Novo Paciente*

Por favor, digite o nome completo do paciente:"""
        
        self.whatsapp_service.send_text_message(phone_number, message)
        return {"status": "sent", "action": "add_patient_flow_started"}
    
    def _list_patients(self, phone_number: str) -> Dict:
        """Listar pacientes ativos"""
        try:
            patients = Patient.query.filter_by(is_active=True).order_by(Patient.name).limit(10).all()
            
            if not patients:
                message = """👥 *Lista de Pacientes*

Nenhum paciente cadastrado ainda.

Use */add_paciente Nome* para adicionar o primeiro paciente."""
                
                self.whatsapp_service.send_text_message(phone_number, message)
                return {"status": "sent", "action": "empty_patients_list"}
            
            message = "👥 *Pacientes Ativos*\n\n"
            
            for i, patient in enumerate(patients, 1):
                # Contar respostas recentes
                recent_responses = Response.query.filter(
                    Response.patient_id == patient.id,
                    Response.created_at >= date.today()
                ).count()
                
                status_emoji = "🟢" if recent_responses > 0 else "⚪"
                
                message += f"{status_emoji} *{i}. {patient.name}*\n"
                message += f"   📱 {patient.whatsapp_phone or 'Não informado'}\n"
                message += f"   📊 {recent_responses} respostas hoje\n\n"
            
            if len(patients) == 10:
                message += "📝 *Mostrando primeiros 10 pacientes*"
            
            self.whatsapp_service.send_text_message(phone_number, message)
            return {"status": "sent", "action": "patients_list_sent"}
            
        except Exception as e:
            self.logger.error(f"Erro ao listar pacientes: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_recent_responses(self, phone_number: str) -> Dict:
        """Enviar relatório de respostas recentes"""
        try:
            # Buscar respostas das últimas 24 horas
            recent_responses = Response.query.filter(
                Response.created_at >= date.today()
            ).order_by(Response.created_at.desc()).limit(10).all()
            
            if not recent_responses:
                message = """📋 *Respostas Recentes*

Nenhuma resposta registrada hoje.

Os pacientes receberão lembretes automáticos conforme programado."""
                
                self.whatsapp_service.send_text_message(phone_number, message)
                return {"status": "sent", "action": "empty_responses_report"}
            
            message = "📋 *Respostas das Últimas 24h*\n\n"
            
            for response in recent_responses:
                patient = Patient.query.get(response.patient_id)
                scale = Scale.query.get(response.scale_id)
                
                alert_emoji = "🚨" if response.alert_triggered else "✅"
                time_str = response.created_at.strftime('%H:%M')
                
                message += f"{alert_emoji} *{patient.name if patient else 'Paciente'}*\n"
                message += f"   📊 {scale.name if scale else 'Escala'}: {response.total_score} pts\n"
                message += f"   🕐 {time_str}\n\n"
            
            self.whatsapp_service.send_text_message(phone_number, message)
            return {"status": "sent", "action": "recent_responses_sent"}
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar respostas recentes: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_alerts_summary(self, phone_number: str) -> Dict:
        """Enviar resumo de alertas"""
        try:
            # Buscar alertas das últimas 24 horas
            alerts = Response.query.filter(
                Response.created_at >= date.today(),
                Response.alert_triggered == True
            ).order_by(Response.created_at.desc()).all()
            
            if not alerts:
                message = """🚨 *Alertas Recentes*

✅ Nenhum alerta nas últimas 24 horas.

Todos os pacientes estão com pontuações dentro dos parâmetros normais."""
                
                self.whatsapp_service.send_text_message(phone_number, message)
                return {"status": "sent", "action": "no_alerts_report"}
            
            message = f"🚨 *Alertas - {len(alerts)} encontrado(s)*\n\n"
            
            for alert in alerts:
                patient = Patient.query.get(alert.patient_id)
                scale = Scale.query.get(alert.scale_id)
                
                time_str = alert.created_at.strftime('%H:%M')
                
                message += f"⚠️ *{patient.name if patient else 'Paciente'}*\n"
                message += f"   📊 {scale.name if scale else 'Escala'}: {alert.total_score} pts\n"
                message += f"   🕐 {time_str}\n"
                message += f"   💡 Considere contato direto\n\n"
            
            self.whatsapp_service.send_text_message(phone_number, message)
            return {"status": "sent", "action": "alerts_summary_sent"}
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar alertas: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_help_message(self, phone_number: str) -> Dict:
        """Enviar mensagem de ajuda"""
        message = """❓ *Comandos Disponíveis*

📋 */menu* - Menu principal
👥 */pacientes* - Gerenciar pacientes
⏰ */lembretes* - Gerenciar lembretes
📊 */relatorios* - Ver relatórios
⚙️ */sistema* - Configurações
📈 */status* - Status rápido

➕ */add_paciente Nome* - Adicionar paciente rapidamente

💡 *Dica:* Use */menu* para navegar com botões interativos."""
        
        self.whatsapp_service.send_text_message(phone_number, message)
        return {"status": "sent", "action": "help_message_sent"}
    
    def _send_system_status(self, phone_number: str) -> Dict:
        """Enviar status detalhado do sistema"""
        try:
            # Estatísticas gerais
            total_patients = Patient.query.count()
            active_patients = Patient.query.filter_by(is_active=True).count()
            total_reminders = Reminder.query.count()
            active_reminders = Reminder.query.filter_by(is_active=True).count()
            total_responses = Response.query.count()
            
            # Estatísticas de hoje
            responses_today = Response.query.filter(
                Response.created_at >= date.today()
            ).count()
            alerts_today = Response.query.filter(
                Response.created_at >= date.today(),
                Response.alert_triggered == True
            ).count()
            
            message = f"""📈 *Status Detalhado do Sistema*

👥 *Pacientes:*
   • Total: {total_patients}
   • Ativos: {active_patients}

⏰ *Lembretes:*
   • Total: {total_reminders}
   • Ativos: {active_reminders}

📊 *Respostas:*
   • Total: {total_responses}
   • Hoje: {responses_today}
   • Alertas hoje: {alerts_today}

🕐 *Última atualização:* {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

✅ Sistema operacional"""
            
            self.whatsapp_service.send_text_message(phone_number, message)
            return {"status": "sent", "action": "system_status_sent"}
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar status do sistema: {e}")
            return {"status": "error", "message": str(e)}

