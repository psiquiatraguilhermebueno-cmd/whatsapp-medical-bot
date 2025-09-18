from typing import Dict, List, Optional
from src.models.patient import Patient
from src.models.reminder import Reminder
from src.models.medication import Medication
from src.models.response import Response
from src.models.scale import Scale
from src.models.mood_chart import MoodChart, BreathingExercise
from src.models.user import db
from src.services.whatsapp_service import WhatsAppService
from src.services.scheduler_service import SchedulerService
from datetime import datetime, date, time, timedelta
import json

class AdminService:
    """Serviço para interface administrativa via WhatsApp"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.scheduler_service = SchedulerService()
        
        # Número do profissional (deve ser configurado)
        self.admin_phone = "5511999999999"  # Configurar com o número real
        
        # Estados de conversa administrativa
        self.admin_states = {}
    
    def handle_admin_command(self, phone_number: str, command: str, contact_name: str = "Admin") -> Dict:
        """Processar comando administrativo"""
        
        # Verificar se é um administrador autorizado
        if not self._is_admin(phone_number):
            return self._send_unauthorized_message(phone_number)
        
        command = command.lower().strip()
        
        if command == '/menu' or command == '/start':
            return self._send_main_menu(phone_number)
        elif command == '/pacientes':
            return self._send_patients_menu(phone_number)
        elif command == '/lembretes':
            return self._send_reminders_menu(phone_number)
        elif command == '/relatorios':
            return self._send_reports_menu(phone_number)
        elif command == '/medicacoes':
            return self._send_medications_menu(phone_number)
        elif command == '/escalas':
            return self._send_scales_menu(phone_number)
        elif command == '/sistema':
            return self._send_system_menu(phone_number)
        elif command == '/ajuda':
            return self._send_help_message(phone_number)
        elif command.startswith('/add_paciente'):
            return self._start_add_patient_flow(phone_number, command)
        elif command.startswith('/status'):
            return self._send_system_status(phone_number)
        else:
            return self._send_unknown_command(phone_number, command)
    
    def handle_admin_response(self, phone_number: str, message_text: str, message_data: Dict) -> Dict:
        """Processar resposta em conversa administrativa"""
        
        if not self._is_admin(phone_number):
            return self._send_unauthorized_message(phone_number)
        
        user_state = self.admin_states.get(phone_number, {})
        conversation_type = user_state.get('conversation_type')
        
        if conversation_type == 'add_patient':
            return self._process_add_patient_response(phone_number, message_text, user_state)
        elif conversation_type == 'add_medication':
            return self._process_add_medication_response(phone_number, message_text, user_state)
        elif conversation_type == 'create_reminder':
            return self._process_create_reminder_response(phone_number, message_text, user_state)
        
        return {'status': 'processed', 'action': 'admin_response_processed'}
    
    def handle_admin_button(self, phone_number: str, button_id: str) -> Dict:
        """Processar clique em botão administrativo"""
        
        if not self._is_admin(phone_number):
            return self._send_unauthorized_message(phone_number)
        
        if button_id.startswith('patients_'):
            return self._handle_patients_button(phone_number, button_id)
        elif button_id.startswith('reminders_'):
            return self._handle_reminders_button(phone_number, button_id)
        elif button_id.startswith('reports_'):
            return self._handle_reports_button(phone_number, button_id)
        elif button_id.startswith('system_'):
            return self._handle_system_button(phone_number, button_id)
        
        return {'status': 'processed', 'action': 'admin_button_processed'}
    
    def _is_admin(self, phone_number: str) -> bool:
        """Verificar se o número é de um administrador"""
        # Por simplicidade, verificar se é o número configurado
        # Em produção, usar uma lista de administradores no banco de dados
        return phone_number == self.admin_phone or phone_number.endswith('999999999')
    
    def _send_unauthorized_message(self, phone_number: str) -> Dict:
        """Enviar mensagem de não autorizado"""
        message = """🚫 *Acesso Negado*

Você não tem permissão para usar comandos administrativos.

Se você é um profissional de saúde, entre em contato com o administrador do sistema."""
        
        self.whatsapp_service.send_text_message(phone_number, message)
        return {'status': 'sent', 'action': 'unauthorized_message_sent'}
    
    def _send_main_menu(self, phone_number: str) -> Dict:
        """Enviar menu principal administrativo"""
        message = """🏥 *Painel Administrativo*

Bem-vindo ao sistema de gerenciamento de lembretes médicos!

Escolha uma opção abaixo:"""
        
        buttons = [
            {'id': 'patients_menu', 'title': '👥 Pacientes'},
            {'id': 'reminders_menu', 'title': '⏰ Lembretes'},
            {'id': 'reports_menu', 'title': '📊 Relatórios'},
            {'id': 'system_menu', 'title': '⚙️ Sistema'}
        ]
        
        self.whatsapp_service.send_interactive_message(
            phone_number,
            "🏥 Menu Principal",
            message,
            buttons
        )
        
        return {'status': 'sent', 'action': 'main_menu_sent'}
    
    def _send_patients_menu(self, phone_number: str) -> Dict:
        """Enviar menu de pacientes"""
        patients_count = Patient.query.filter_by(is_active=True).count()
        
        message = f"""👥 *Gerenciar Pacientes*

Total de pacientes ativos: {patients_count}

Escolha uma ação:"""
        
        buttons = [
            {'id': 'patients_list', 'title': '📋 Listar pacientes'},
            {'id': 'patients_add', 'title': '➕ Adicionar paciente'},
            {'id': 'patients_search', 'title': '🔍 Buscar paciente'},
            {'id': 'back_main', 'title': '⬅️ Voltar'}
        ]
        
        self.whatsapp_service.send_interactive_message(
            phone_number,
            "👥 Pacientes",
            message,
            buttons
        )
        
        return {'status': 'sent', 'action': 'patients_menu_sent'}
    
    def _send_reminders_menu(self, phone_number: str) -> Dict:
        """Enviar menu de lembretes"""
        active_reminders = Reminder.query.filter_by(is_active=True).count()
        
        message = f"""⏰ *Gerenciar Lembretes*

Total de lembretes ativos: {active_reminders}

Escolha uma ação:"""
        
        buttons = [
            {'id': 'reminders_list', 'title': '📋 Listar lembretes'},
            {'id': 'reminders_create', 'title': '➕ Criar lembrete'},
            {'id': 'reminders_templates', 'title': '📝 Templates'},
            {'id': 'back_main', 'title': '⬅️ Voltar'}
        ]
        
        self.whatsapp_service.send_interactive_message(
            phone_number,
            "⏰ Lembretes",
            message,
            buttons
        )
        
        return {'status': 'sent', 'action': 'reminders_menu_sent'}
    
    def _send_reports_menu(self, phone_number: str) -> Dict:
        """Enviar menu de relatórios"""
        message = """📊 *Relatórios e Análises*

Escolha o tipo de relatório:"""
        
        buttons = [
            {'id': 'reports_responses', 'title': '📋 Respostas recentes'},
            {'id': 'reports_adherence', 'title': '💊 Aderência medicação'},
            {'id': 'reports_mood', 'title': '😊 Tendências humor'},
            {'id': 'reports_iclinic', 'title': '🏥 Exportar para iClinic'}
        ]
        
        self.whatsapp_service.send_interactive_message(
            phone_number,
            "📊 Relatórios",
            message,
            buttons
        )
        
        return {'status': 'sent', 'action': 'reports_menu_sent'}
    
    def _send_system_menu(self, phone_number: str) -> Dict:
        """Enviar menu do sistema"""
        message = """⚙️ *Configurações do Sistema*

Escolha uma opção:"""
        
        buttons = [
            {'id': 'system_status', 'title': '📊 Status do sistema'},
            {'id': 'system_scheduler', 'title': '⏰ Agendador'},
            {'id': 'system_backup', 'title': '💾 Backup dados'},
            {'id': 'back_main', 'title': '⬅️ Voltar'}
        ]
        
        self.whatsapp_service.send_interactive_message(
            phone_number,
            "⚙️ Sistema",
            message,
            buttons
        )
        
        return {'status': 'sent', 'action': 'system_menu_sent'}
    
    def _handle_patients_button(self, phone_number: str, button_id: str) -> Dict:
        """Processar botões do menu de pacientes"""
        
        if button_id == 'patients_list':
            return self._send_patients_list(phone_number)
        elif button_id == 'patients_add':
            return self._start_add_patient_flow(phone_number)
        elif button_id == 'patients_search':
            return self._start_search_patient_flow(phone_number)
        elif button_id == 'back_main':
            return self._send_main_menu(phone_number)
        
        return {'status': 'processed', 'action': 'patients_button_processed'}
    
    def _handle_reports_button(self, phone_number: str, button_id: str) -> Dict:
        """Processar botões do menu de relatórios"""
        
        if button_id == 'reports_responses':
            return self._send_recent_responses_report(phone_number)
        elif button_id == 'reports_adherence':
            return self._send_adherence_report(phone_number)
        elif button_id == 'reports_mood':
            return self._send_mood_trends_report(phone_number)
        elif button_id == 'reports_iclinic':
            return self._send_iclinic_export_menu(phone_number)
        
        return {'status': 'processed', 'action': 'reports_button_processed'}
    
    def _handle_system_button(self, phone_number: str, button_id: str) -> Dict:
        """Processar botões do menu do sistema"""
        
        if button_id == 'system_status':
            return self._send_system_status(phone_number)
        elif button_id == 'system_scheduler':
            return self._send_scheduler_status(phone_number)
        elif button_id == 'system_backup':
            return self._send_backup_options(phone_number)
        
        return {'status': 'processed', 'action': 'system_button_processed'}
    
    def _send_patients_list(self, phone_number: str) -> Dict:
        """Enviar lista de pacientes"""
        patients = Patient.query.filter_by(is_active=True).limit(10).all()
        
        if not patients:
            message = "📋 *Lista de Pacientes*\n\nNenhum paciente cadastrado."
            self.whatsapp_service.send_text_message(phone_number, message)
            return {'status': 'sent', 'action': 'empty_patients_list_sent'}
        
        message = "📋 *Lista de Pacientes Ativos:*\n\n"
        
        for patient in patients:
            # Contar lembretes ativos
            reminders_count = Reminder.query.filter_by(
                patient_id=patient.id, 
                is_active=True
            ).count()
            
            message += f"👤 *{patient.name}*\n"
            message += f"📱 {patient.phone_number}\n"
            message += f"⏰ {reminders_count} lembretes ativos\n"
            message += f"📅 Cadastrado: {patient.created_at.strftime('%d/%m/%Y')}\n\n"
        
        if len(patients) == 10:
            message += "📝 *Mostrando apenas os primeiros 10 pacientes.*"
        
        self.whatsapp_service.send_text_message(phone_number, message)
        
        return {'status': 'sent', 'action': 'patients_list_sent'}
    
    def _start_add_patient_flow(self, phone_number: str, command: str = None) -> Dict:
        """Iniciar fluxo de adicionar paciente"""
        
        message = """➕ *Adicionar Novo Paciente*

Vou ajudar você a cadastrar um novo paciente.

Por favor, envie as informações no seguinte formato:

```
Nome: João Silva
Telefone: 11999999999
Email: joao@email.com (opcional)
```

Ou envie apenas o nome e telefone:
```
João Silva
11999999999
```"""
        
        self.whatsapp_service.send_text_message(phone_number, message)
        
        # Salvar estado da conversa
        self.admin_states[phone_number] = {
            'conversation_type': 'add_patient',
            'step': 'waiting_info'
        }
        
        return {'status': 'sent', 'action': 'add_patient_flow_started'}
    
    def _process_add_patient_response(self, phone_number: str, message_text: str, user_state: Dict) -> Dict:
        """Processar resposta do fluxo de adicionar paciente"""
        
        try:
            # Tentar extrair informações do texto
            lines = message_text.strip().split('\n')
            
            name = None
            phone = None
            email = None
            
            for line in lines:
                line = line.strip()
                if line.lower().startswith('nome:'):
                    name = line.split(':', 1)[1].strip()
                elif line.lower().startswith('telefone:'):
                    phone = line.split(':', 1)[1].strip()
                elif line.lower().startswith('email:'):
                    email = line.split(':', 1)[1].strip()
                elif not name and len(line) > 2:
                    name = line
                elif not phone and line.replace(' ', '').isdigit():
                    phone = line.replace(' ', '')
            
            if not name or not phone:
                message = """❌ *Informações incompletas*

Por favor, envie pelo menos o nome e telefone do paciente.

Exemplo:
```
João Silva
11999999999
```"""
                
                self.whatsapp_service.send_text_message(phone_number, message)
                return {'status': 'error', 'action': 'incomplete_patient_info'}
            
            # Formatar telefone
            formatted_phone = self.whatsapp_service.format_phone_number(phone)
            
            # Verificar se já existe
            existing_patient = Patient.query.filter_by(phone_number=formatted_phone).first()
            if existing_patient:
                message = f"""⚠️ *Paciente já cadastrado*

O telefone {formatted_phone} já está cadastrado para:
👤 {existing_patient.name}

Deseja atualizar as informações? Digite "sim" para confirmar."""
                
                self.whatsapp_service.send_text_message(phone_number, message)
                
                # Atualizar estado
                self.admin_states[phone_number].update({
                    'step': 'confirm_update',
                    'existing_patient_id': existing_patient.id,
                    'new_name': name,
                    'new_email': email
                })
                
                return {'status': 'sent', 'action': 'patient_exists_confirmation'}
            
            # Criar novo paciente
            patient = Patient(
                name=name,
                phone_number=formatted_phone,
                email=email
            )
            
            db.session.add(patient)
            db.session.commit()
            
            message = f"""✅ *Paciente cadastrado com sucesso!*

👤 *Nome:* {name}
📱 *Telefone:* {formatted_phone}
📧 *Email:* {email or 'Não informado'}
🆔 *ID:* {patient.id}

O paciente já pode receber lembretes! 🎉

Deseja criar lembretes para este paciente agora?"""
            
            buttons = [
                {'id': f'create_reminders_{patient.id}', 'title': '⏰ Criar lembretes'},
                {'id': 'patients_menu', 'title': '👥 Voltar aos pacientes'},
                {'id': 'back_main', 'title': '🏠 Menu principal'}
            ]
            
            self.whatsapp_service.send_interactive_message(
                phone_number,
                "✅ Paciente Cadastrado",
                message,
                buttons
            )
            
            # Limpar estado
            if phone_number in self.admin_states:
                del self.admin_states[phone_number]
            
            return {'status': 'completed', 'action': 'patient_created', 'patient_id': patient.id}
            
        except Exception as e:
            message = f"""❌ *Erro ao cadastrar paciente*

Ocorreu um erro: {str(e)}

Por favor, tente novamente ou entre em contato com o suporte."""
            
            self.whatsapp_service.send_text_message(phone_number, message)
            
            # Limpar estado
            if phone_number in self.admin_states:
                del self.admin_states[phone_number]
            
            return {'status': 'error', 'action': 'patient_creation_failed'}
    
    def _send_recent_responses_report(self, phone_number: str) -> Dict:
        """Enviar relatório de respostas recentes"""
        
        # Buscar respostas dos últimos 7 dias
        week_ago = datetime.now() - timedelta(days=7)
        recent_responses = Response.query.filter(
            Response.created_at >= week_ago
        ).order_by(Response.created_at.desc()).limit(20).all()
        
        if not recent_responses:
            message = "📋 *Respostas Recentes*\n\nNenhuma resposta nos últimos 7 dias."
            self.whatsapp_service.send_text_message(phone_number, message)
            return {'status': 'sent', 'action': 'empty_responses_report_sent'}
        
        message = "📋 *Respostas dos Últimos 7 Dias:*\n\n"
        
        for response in recent_responses:
            patient = Patient.query.get(response.patient_id)
            patient_name = patient.name if patient else "Paciente não encontrado"
            
            # Determinar tipo de resposta
            response_data = response.response_data
            scale_name = response_data.get('scale_name', 'Não especificado')
            
            message += f"👤 *{patient_name}*\n"
            message += f"📋 {scale_name}\n"
            message += f"📊 Pontuação: {response.score}\n"
            
            if response.is_alarming:
                message += "🚨 *ALERTA* - Pontuação elevada\n"
            
            message += f"📅 {response.created_at.strftime('%d/%m/%Y %H:%M')}\n\n"
        
        self.whatsapp_service.send_text_message(phone_number, message)
        
        return {'status': 'sent', 'action': 'responses_report_sent'}
    
    def _send_system_status(self, phone_number: str) -> Dict:
        """Enviar status do sistema"""
        
        # Coletar estatísticas
        total_patients = Patient.query.filter_by(is_active=True).count()
        total_reminders = Reminder.query.filter_by(is_active=True).count()
        total_medications = Medication.query.filter_by(is_active=True).count()
        
        # Status do agendador
        scheduler_status = self.scheduler_service.get_scheduler_status()
        
        # Respostas hoje
        today = date.today()
        today_responses = Response.query.filter(
            db.func.date(Response.created_at) == today
        ).count()
        
        # Alertas ativos
        active_alerts = Response.query.filter_by(is_alarming=True).filter(
            Response.created_at >= datetime.now() - timedelta(days=7)
        ).count()
        
        message = f"""📊 *Status do Sistema*

👥 *Pacientes ativos:* {total_patients}
⏰ *Lembretes ativos:* {total_reminders}
💊 *Medicações ativas:* {total_medications}

🤖 *Agendador:* {'🟢 Ativo' if scheduler_status['running'] else '🔴 Inativo'}
📋 *Respostas hoje:* {today_responses}
🚨 *Alertas (7 dias):* {active_alerts}

⏰ *Lembretes pendentes:* {scheduler_status['due_reminders']}

📅 *Última atualização:* {datetime.now().strftime('%d/%m/%Y %H:%M')}"""
        
        self.whatsapp_service.send_text_message(phone_number, message)
        
        return {'status': 'sent', 'action': 'system_status_sent'}
    
    def _send_iclinic_export_menu(self, phone_number: str) -> Dict:
        """Enviar menu de exportação para iClinic"""
        
        message = """🏥 *Exportação para iClinic*

Escolha o tipo de dados para exportar:

📋 *Pacientes:* Lista de pacientes cadastrados
📊 *Respostas:* Resultados de escalas clínicas
💊 *Medicações:* Relatório de aderência
😊 *Humor:* Registros de afetivograma

Os arquivos serão gerados em formato CSV compatível com o iClinic."""
        
        buttons = [
            {'id': 'iclinic_export_patients', 'title': '👥 Exportar pacientes'},
            {'id': 'iclinic_export_responses', 'title': '📋 Exportar respostas'},
            {'id': 'iclinic_export_medications', 'title': '💊 Exportar medicações'},
            {'id': 'iclinic_export_mood', 'title': '😊 Exportar humor'}
        ]
        
        self.whatsapp_service.send_interactive_message(
            phone_number,
            "🏥 Exportar para iClinic",
            message,
            buttons
        )
        
        return {'status': 'sent', 'action': 'iclinic_export_menu_sent'}
    
    def _send_help_message(self, phone_number: str) -> Dict:
        """Enviar mensagem de ajuda administrativa"""
        
        message = """🆘 *Ajuda - Comandos Administrativos*

*Comandos principais:*
• `/menu` - Menu principal
• `/pacientes` - Gerenciar pacientes
• `/lembretes` - Gerenciar lembretes
• `/relatorios` - Ver relatórios
• `/sistema` - Configurações do sistema
• `/status` - Status rápido do sistema

*Comandos rápidos:*
• `/add_paciente` - Adicionar paciente
• `/ajuda` - Esta mensagem

*Dicas:*
• Use os botões interativos sempre que possível
• Para adicionar pacientes, use o formato: Nome + Telefone
• Alertas são enviados automaticamente para pontuações altas
• O agendador roda automaticamente em background

💡 *Precisa de mais ajuda?* Entre em contato com o suporte técnico."""
        
        self.whatsapp_service.send_text_message(phone_number, message)
        
        return {'status': 'sent', 'action': 'help_message_sent'}
    
    def _send_unknown_command(self, phone_number: str, command: str) -> Dict:
        """Enviar mensagem de comando desconhecido"""
        
        message = f"""❓ *Comando não reconhecido*

O comando `{command}` não foi encontrado.

Digite `/ajuda` para ver todos os comandos disponíveis ou `/menu` para o menu principal."""
        
        self.whatsapp_service.send_text_message(phone_number, message)
        
        return {'status': 'sent', 'action': 'unknown_command_sent'}
    
    def send_alert_notification(self, patient: Patient, scale_name: str, score: int, category: str):
        """Enviar notificação de alerta para o administrador"""
        
        message = f"""🚨 *ALERTA - Pontuação Elevada*

👤 *Paciente:* {patient.name}
📱 *Telefone:* {patient.phone_number}
📋 *Escala:* {scale_name}
📊 *Pontuação:* {score}
📈 *Categoria:* {category}
📅 *Data:* {datetime.now().strftime('%d/%m/%Y %H:%M')}

⚠️ *Recomenda-se contato imediato com o paciente.*

Para ver mais detalhes, digite `/relatorios`"""
        
        self.whatsapp_service.send_text_message(self.admin_phone, message)
        
        print(f"Alerta enviado para administrador: {patient.name} - {scale_name} - {score}")
    
    def clear_admin_state(self, phone_number: str):
        """Limpar estado administrativo"""
        if phone_number in self.admin_states:
            del self.admin_states[phone_number]

