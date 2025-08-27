import logging
import os
from typing import Dict, List
from datetime import datetime, timedelta
from src.services.telegram_service import TelegramService
from src.models.patient import Patient
from src.models.reminder import Reminder
from src.models.response import Response
from src.models.medication import Medication
from src.models.user import db

class TelegramAdminService:
    """Serviço de interface administrativa via Telegram"""
    
    def __init__(self):
        self.telegram_service = TelegramService(bot_token=os.getenv('TELEGRAM_BOT_TOKEN'))
        self.logger = logging.getLogger(__name__)
        
        # Estados de conversa para fluxos complexos
        self.conversation_states = {}
    
    def handle_command(self, chat_id: str, command: str, user_info: Dict) -> Dict:
        """Processar comando administrativo"""
        command = command.lower().strip()
        
        if command == '/start' or command == '/menu':
            return self._send_main_menu(chat_id)
        elif command == '/pacientes':
            return self._send_patients_menu(chat_id)
        elif command == '/lembretes':
            return self._send_reminders_menu(chat_id)
        elif command == '/relatorios':
            return self._send_reports_menu(chat_id)
        elif command == '/sistema':
            return self._send_system_menu(chat_id)
        elif command == '/status':
            return self._send_quick_status(chat_id)
        elif command == '/add_paciente':
            return self._start_add_patient_flow(chat_id)
        elif command == '/ajuda' or command == '/help':
            return self._send_admin_help(chat_id)
        else:
            return self._send_unknown_command(chat_id, command)
    
    def handle_text(self, chat_id: str, text: str, user_info: Dict) -> Dict:
        """Processar texto administrativo"""
        # Verificar se está em fluxo de conversa
        if chat_id in self.conversation_states:
            return self._handle_conversation_flow(chat_id, text)
        
        # Texto livre sem contexto
        self.telegram_service.send_text_message(
            chat_id,
            "Use /menu para acessar o painel administrativo ou /ajuda para ver os comandos disponíveis."
        )
        return {"status": "processed", "action": "free_text_handled"}
    
    def handle_callback(self, chat_id: str, callback_data: str, user_info: Dict) -> Dict:
        """Processar callback administrativo"""
        if callback_data.startswith('patients_'):
            return self._handle_patients_callback(chat_id, callback_data)
        elif callback_data.startswith('reminders_'):
            return self._handle_reminders_callback(chat_id, callback_data)
        elif callback_data.startswith('reports_'):
            return self._handle_reports_callback(chat_id, callback_data)
        elif callback_data.startswith('system_'):
            return self._handle_system_callback(chat_id, callback_data)
        elif callback_data == 'main_menu':
            return self._send_main_menu(chat_id)
        else:
            return {"status": "processed", "action": "unknown_callback"}
    
    def _send_main_menu(self, chat_id: str) -> Dict:
        """Enviar menu principal administrativo"""
        message = """🏥 *Painel Administrativo*

Bem-vindo ao sistema de gerenciamento do Bot de Lembretes Médicos.

Escolha uma opção:"""
        
        buttons = [
            {"text": "👥 Pacientes", "callback_data": "patients_menu"},
            {"text": "⏰ Lembretes", "callback_data": "reminders_menu"},
            {"text": "📊 Relatórios", "callback_data": "reports_menu"},
            {"text": "⚙️ Sistema", "callback_data": "system_menu"}
        ]
        
        self.telegram_service.send_interactive_message(chat_id, message, buttons)
        return {"status": "sent", "action": "main_menu_sent"}
    
    def _send_patients_menu(self, chat_id: str) -> Dict:
        """Enviar menu de pacientes"""
        # Contar pacientes
        total_patients = Patient.query.filter_by(is_active=True).count()
        pending_patients = Patient.query.filter_by(is_active=False).count()
        
        message = f"""👥 *Gerenciar Pacientes*

📊 *Estatísticas:*
• Pacientes ativos: {total_patients}
• Aguardando aprovação: {pending_patients}

Escolha uma ação:"""
        
        buttons = [
            {"text": "📋 Listar pacientes", "callback_data": "patients_list"},
            {"text": "➕ Adicionar paciente", "callback_data": "patients_add"},
            {"text": "🔍 Buscar paciente", "callback_data": "patients_search"},
            {"text": "⏳ Pacientes pendentes", "callback_data": "patients_pending"},
            {"text": "🔙 Menu principal", "callback_data": "main_menu"}
        ]
        
        self.telegram_service.send_interactive_message(chat_id, message, buttons)
        return {"status": "sent", "action": "patients_menu_sent"}
    
    def _send_reminders_menu(self, chat_id: str) -> Dict:
        """Enviar menu de lembretes"""
        # Contar lembretes
        active_reminders = Reminder.query.filter_by(is_active=True).count()
        
        message = f"""⏰ *Gerenciar Lembretes*

📊 *Estatísticas:*
• Lembretes ativos: {active_reminders}

Escolha uma ação:"""
        
        buttons = [
            {"text": "📋 Listar lembretes", "callback_data": "reminders_list"},
            {"text": "➕ Criar lembrete", "callback_data": "reminders_create"},
            {"text": "📝 Templates", "callback_data": "reminders_templates"},
            {"text": "⏸️ Pausar/Retomar", "callback_data": "reminders_toggle"},
            {"text": "🔙 Menu principal", "callback_data": "main_menu"}
        ]
        
        self.telegram_service.send_interactive_message(chat_id, message, buttons)
        return {"status": "sent", "action": "reminders_menu_sent"}
    
    def _send_reports_menu(self, chat_id: str) -> Dict:
        """Enviar menu de relatórios"""
        message = """📊 *Relatórios e Análises*

Escolha o tipo de relatório:"""
        
        buttons = [
            {"text": "📋 Respostas recentes", "callback_data": "reports_responses"},
            {"text": "💊 Aderência medicação", "callback_data": "reports_adherence"},
            {"text": "😊 Tendências humor", "callback_data": "reports_mood"},
            {"text": "🏥 Exportar para iClinic", "callback_data": "reports_iclinic"},
            {"text": "🔙 Menu principal", "callback_data": "main_menu"}
        ]
        
        self.telegram_service.send_interactive_message(chat_id, message, buttons)
        return {"status": "sent", "action": "reports_menu_sent"}
    
    def _send_system_menu(self, chat_id: str) -> Dict:
        """Enviar menu do sistema"""
        message = """⚙️ *Configurações do Sistema*

Escolha uma opção:"""
        
        buttons = [
            {"text": "📊 Status do sistema", "callback_data": "system_status"},
            {"text": "🔄 Status agendador", "callback_data": "system_scheduler"},
            {"text": "💾 Backup dados", "callback_data": "system_backup"},
            {"text": "🔧 Configurações", "callback_data": "system_config"},
            {"text": "🔙 Menu principal", "callback_data": "main_menu"}
        ]
        
        self.telegram_service.send_interactive_message(chat_id, message, buttons)
        return {"status": "sent", "action": "system_menu_sent"}
    
    def _send_quick_status(self, chat_id: str) -> Dict:
        """Enviar status rápido do sistema"""
        # Estatísticas básicas
        total_patients = Patient.query.filter_by(is_active=True).count()
        active_reminders = Reminder.query.filter_by(is_active=True).count()
        
        # Respostas recentes (últimas 24h)
        yesterday = datetime.now() - timedelta(days=1)
        recent_responses = Response.query.filter(Response.created_at >= yesterday).count()
        
        message = f"""📊 *Status Rápido do Sistema*

👥 *Pacientes ativos:* {total_patients}
⏰ *Lembretes ativos:* {active_reminders}
📋 *Respostas (24h):* {recent_responses}

🤖 *Bot:* Funcionando
⏱️ *Agendador:* Ativo
📅 *Última atualização:* {datetime.now().strftime('%d/%m/%Y %H:%M')}

Use /menu para acessar o painel completo."""
        
        self.telegram_service.send_text_message(chat_id, message)
        return {"status": "sent", "action": "quick_status_sent"}
    
    def _handle_patients_callback(self, chat_id: str, callback_data: str) -> Dict:
        """Processar callbacks do menu de pacientes"""
        if callback_data == "patients_list":
            return self._send_patients_list(chat_id)
        elif callback_data == "patients_add":
            return self._start_add_patient_flow(chat_id)
        elif callback_data == "patients_search":
            return self._start_search_patient_flow(chat_id)
        elif callback_data == "patients_pending":
            return self._send_pending_patients(chat_id)
        
        return {"status": "processed", "action": "patients_callback_handled"}
    
    def _handle_reminders_callback(self, chat_id: str, callback_data: str) -> Dict:
        """Processar callbacks do menu de lembretes"""
        if callback_data == "reminders_list":
            return self._send_reminders_list(chat_id)
        elif callback_data == "reminders_create":
            return self._start_create_reminder_flow(chat_id)
        elif callback_data == "reminders_templates":
            return self._send_reminder_templates(chat_id)
        
        return {"status": "processed", "action": "reminders_callback_handled"}
    
    def _handle_reports_callback(self, chat_id: str, callback_data: str) -> Dict:
        """Processar callbacks do menu de relatórios"""
        if callback_data == "reports_responses":
            return self._send_recent_responses_report(chat_id)
        elif callback_data == "reports_adherence":
            return self._send_adherence_report(chat_id)
        elif callback_data == "reports_mood":
            return self._send_mood_report(chat_id)
        elif callback_data == "reports_iclinic":
            return self._send_iclinic_export_menu(chat_id)
        
        return {"status": "processed", "action": "reports_callback_handled"}
    
    def _handle_system_callback(self, chat_id: str, callback_data: str) -> Dict:
        """Processar callbacks do menu do sistema"""
        if callback_data == "system_status":
            return self._send_detailed_system_status(chat_id)
        elif callback_data == "system_scheduler":
            return self._send_scheduler_status(chat_id)
        elif callback_data == "system_backup":
            return self._create_system_backup(chat_id)
        
        return {"status": "processed", "action": "system_callback_handled"}
    
    def _send_patients_list(self, chat_id: str) -> Dict:
        """Enviar lista de pacientes"""
        patients = Patient.query.filter_by(is_active=True).order_by(Patient.name).limit(10).all()
        
        if not patients:
            message = "📋 *Lista de Pacientes*\n\nNenhum paciente ativo encontrado."
        else:
            message = "📋 *Lista de Pacientes Ativos*\n\n"
            for i, patient in enumerate(patients, 1):
                last_response = Response.query.filter_by(patient_id=patient.id).order_by(Response.created_at.desc()).first()
                last_response_date = last_response.created_at.strftime('%d/%m') if last_response else 'Nunca'
                
                message += f"{i}. *{patient.name}*\n"
                message += f"   📱 Chat: `{patient.telegram_chat_id}`\n"
                message += f"   📅 Última resposta: {last_response_date}\n\n"
            
            if len(patients) == 10:
                message += "_(Mostrando apenas os primeiros 10 pacientes)_"
        
        buttons = [{"text": "🔙 Menu pacientes", "callback_data": "patients_menu"}]
        self.telegram_service.send_interactive_message(chat_id, message, buttons)
        return {"status": "sent", "action": "patients_list_sent"}
    
    def _send_recent_responses_report(self, chat_id: str) -> Dict:
        """Enviar relatório de respostas recentes"""
        # Últimas 7 dias
        week_ago = datetime.now() - timedelta(days=7)
        responses = Response.query.filter(Response.created_at >= week_ago).order_by(Response.created_at.desc()).limit(10).all()
        
        if not responses:
            message = "📋 *Respostas Recentes (7 dias)*\n\nNenhuma resposta encontrada."
        else:
            message = "📋 *Respostas Recentes (7 dias)*\n\n"
            for response in responses:
                patient = Patient.query.get(response.patient_id)
                if patient:
                    response_data = response.response_data or {}
                    scale_name = response_data.get('scale_name', 'Questionário')
                    
                    message += f"👤 *{patient.name}*\n"
                    message += f"📊 {scale_name} - Pontuação: {response.score or 'N/A'}\n"
                    message += f"📅 {response.created_at.strftime('%d/%m/%Y %H:%M')}\n"
                    
                    if response.is_alarming:
                        message += "🚨 *ALERTA: Pontuação preocupante*\n"
                    
                    message += "\n"
        
        buttons = [{"text": "🔙 Menu relatórios", "callback_data": "reports_menu"}]
        self.telegram_service.send_interactive_message(chat_id, message, buttons)
        return {"status": "sent", "action": "responses_report_sent"}
    
    def _send_iclinic_export_menu(self, chat_id: str) -> Dict:
        """Enviar menu de exportação para iClinic"""
        message = """🏥 *Exportação para iClinic*

Escolha o tipo de dados para exportar:

📋 *Pacientes:* Lista de pacientes cadastrados
📊 *Respostas:* Resultados de escalas clínicas
💊 *Medicações:* Relatório de aderência
😊 *Humor:* Registros de afetivograma

Os arquivos serão gerados em formato CSV compatível com o iClinic."""
        
        buttons = [
            {"text": "👥 Exportar pacientes", "callback_data": "iclinic_export_patients"},
            {"text": "📋 Exportar respostas", "callback_data": "iclinic_export_responses"},
            {"text": "💊 Exportar medicações", "callback_data": "iclinic_export_medications"},
            {"text": "😊 Exportar humor", "callback_data": "iclinic_export_mood"},
            {"text": "🔙 Menu relatórios", "callback_data": "reports_menu"}
        ]
        
        self.telegram_service.send_interactive_message(chat_id, message, buttons)
        return {"status": "sent", "action": "iclinic_export_menu_sent"}
    
    def _start_add_patient_flow(self, chat_id: str) -> Dict:
        """Iniciar fluxo de adicionar paciente"""
        self.conversation_states[chat_id] = {
            "flow": "add_patient",
            "step": "name",
            "data": {}
        }
        
        message = """➕ *Adicionar Novo Paciente*

Por favor, envie as informações do paciente no seguinte formato:

```
Nome: João da Silva
Chat ID: 123456789
Telefone: 11987654321
Email: joao@email.com
```

Ou envie apenas o nome e eu te guiarei passo a passo.

Digite /cancelar para cancelar."""
        
        self.telegram_service.send_text_message(chat_id, message)
        return {"status": "sent", "action": "add_patient_flow_started"}
    
    def _handle_conversation_flow(self, chat_id: str, text: str) -> Dict:
        """Processar fluxo de conversa"""
        if text.lower() == '/cancelar':
            del self.conversation_states[chat_id]
            self.telegram_service.send_text_message(chat_id, "Operação cancelada.")
            return self._send_main_menu(chat_id)
        
        state = self.conversation_states[chat_id]
        
        if state["flow"] == "add_patient":
            return self._handle_add_patient_flow(chat_id, text, state)
        
        return {"status": "processed", "action": "conversation_flow_handled"}
    
    def _handle_add_patient_flow(self, chat_id: str, text: str, state: Dict) -> Dict:
        """Processar fluxo de adicionar paciente"""
        # Tentar parsear formato completo
        if "Nome:" in text and "Chat ID:" in text:
            return self._parse_complete_patient_data(chat_id, text)
        
        # Fluxo passo a passo
        if state["step"] == "name":
            state["data"]["name"] = text
            state["step"] = "chat_id"
            
            self.telegram_service.send_text_message(
                chat_id,
                f"✅ Nome: {text}\n\nAgora envie o Chat ID do Telegram do paciente:"
            )
            return {"status": "processed", "action": "name_collected"}
        
        elif state["step"] == "chat_id":
            state["data"]["chat_id"] = text
            
            # Criar paciente
            return self._create_patient_from_data(chat_id, state["data"])
        
        return {"status": "processed", "action": "add_patient_step_handled"}
    
    def _parse_complete_patient_data(self, chat_id: str, text: str) -> Dict:
        """Parsear dados completos do paciente"""
        data = {}
        
        for line in text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if 'nome' in key:
                    data['name'] = value
                elif 'chat' in key:
                    data['chat_id'] = value
                elif 'telefone' in key:
                    data['phone'] = value
                elif 'email' in key:
                    data['email'] = value
        
        if 'name' in data and 'chat_id' in data:
            return self._create_patient_from_data(chat_id, data)
        else:
            self.telegram_service.send_text_message(
                chat_id,
                "❌ Formato inválido. Nome e Chat ID são obrigatórios."
            )
            return {"status": "error", "action": "invalid_patient_format"}
    
    def _create_patient_from_data(self, chat_id: str, data: Dict) -> Dict:
        """Criar paciente a partir dos dados coletados"""
        try:
            # Verificar se já existe
            existing = Patient.query.filter_by(telegram_chat_id=data['chat_id']).first()
            if existing:
                self.telegram_service.send_text_message(
                    chat_id,
                    f"❌ Já existe um paciente com Chat ID {data['chat_id']}: {existing.name}"
                )
                del self.conversation_states[chat_id]
                return {"status": "error", "action": "patient_already_exists"}
            
            # Criar novo paciente
            patient = Patient(
                name=data['name'],
                telegram_chat_id=data['chat_id'],
                phone_number=data.get('phone'),
                email=data.get('email'),
                is_active=True
            )
            
            db.session.add(patient)
            db.session.commit()
            
            message = f"""✅ *Paciente adicionado com sucesso!*

👤 *Nome:* {patient.name}
📱 *Chat ID:* {patient.telegram_chat_id}
📞 *Telefone:* {patient.phone_number or 'Não informado'}
📧 *Email:* {patient.email or 'Não informado'}

O paciente já pode interagir com o bot."""
            
            self.telegram_service.send_text_message(chat_id, message)
            del self.conversation_states[chat_id]
            
            return {"status": "success", "action": "patient_created", "patient_id": patient.id}
            
        except Exception as e:
            self.logger.error(f"Erro ao criar paciente: {e}")
            self.telegram_service.send_text_message(
                chat_id,
                f"❌ Erro ao criar paciente: {str(e)}"
            )
            del self.conversation_states[chat_id]
            return {"status": "error", "action": "patient_creation_failed"}
    
    def _send_unknown_command(self, chat_id: str, command: str) -> Dict:
        """Enviar mensagem para comando desconhecido"""
        message = f"❓ Comando não reconhecido: `{command}`\n\nUse /menu para acessar o painel administrativo."
        self.telegram_service.send_text_message(chat_id, message)
        return {"status": "sent", "action": "unknown_command_sent"}
    
    def _send_admin_help(self, chat_id: str) -> Dict:
        """Enviar ajuda administrativa"""
        message = """🏥 *Ajuda - Painel Administrativo*

*Comandos principais:*
/menu - Painel administrativo principal
/pacientes - Gerenciar pacientes
/lembretes - Gerenciar lembretes
/relatorios - Ver relatórios e análises
/sistema - Configurações do sistema
/status - Status rápido do sistema

*Comandos rápidos:*
/add_paciente - Adicionar paciente rapidamente

*Navegação:*
Use os botões interativos para navegar pelos menus ou digite os comandos diretamente.

*Dúvidas?*
Entre em contato com o suporte técnico."""
        
        self.telegram_service.send_text_message(chat_id, message)
        return {"status": "sent", "action": "admin_help_sent"}

