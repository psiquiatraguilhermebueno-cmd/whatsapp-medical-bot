from typing import Dict, List
from src.models.patient import Patient
from src.models.mood_chart import MoodChart
from src.models.user import db
from src.services.whatsapp_service import WhatsAppService
from datetime import datetime, date, timedelta
import json

class MoodService:
    """Serviço para gerenciar o afetivograma (registro de humor)"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
    
    def start_mood_registration(self, patient: Patient) -> Dict:
        """Iniciar registro de humor diário"""
        today = date.today()
        
        # Verificar se já foi registrado hoje
        existing_entry = MoodChart.query.filter_by(
            patient_id=patient.id,
            date=today
        ).first()
        
        if existing_entry:
            return self._show_today_mood(patient, existing_entry)
        
        # Iniciar novo registro
        message = """😊 *Registro de Humor Diário*

Vou ajudar você a registrar como está se sentindo hoje. Isso é baseado no método NIMH Life Chart.

Vamos começar com seu nível de humor atual."""
        
        self.whatsapp_service.send_text_message(patient.phone_number, message)
        
        return self._ask_mood_level(patient)
    
    def _ask_mood_level(self, patient: Patient) -> Dict:
        """Perguntar sobre o nível de humor"""
        message = """📊 *Nível de Humor*

Como você descreveria seu humor hoje?

Escala de -3 a +3:
• -3: Depressão severa
• -2: Depressão moderada  
• -1: Depressão leve
• 0: Humor normal/estável
• +1: Hipomania leve
• +2: Hipomania moderada
• +3: Mania severa"""
        
        # Criar botões para níveis de humor
        buttons = [
            {'id': 'mood_-3', 'title': '-3 Depressão severa'},
            {'id': 'mood_-2', 'title': '-2 Depressão moderada'},
            {'id': 'mood_-1', 'title': '-1 Depressão leve'},
            {'id': 'mood_0', 'title': '0 Normal/estável'}
        ]
        
        self.whatsapp_service.send_interactive_message(
            patient.phone_number,
            "😊 Nível de Humor",
            message,
            buttons
        )
        
        # Enviar segunda parte dos botões
        buttons2 = [
            {'id': 'mood_1', 'title': '+1 Hipomania leve'},
            {'id': 'mood_2', 'title': '+2 Hipomania moderada'},
            {'id': 'mood_3', 'title': '+3 Mania severa'}
        ]
        
        self.whatsapp_service.send_interactive_message(
            patient.phone_number,
            "😊 Nível de Humor (cont.)",
            "Ou escolha um dos níveis elevados:",
            buttons2
        )
        
        return {'status': 'sent', 'action': 'mood_level_asked'}
    
    def handle_mood_button(self, patient: Patient, button_id: str) -> Dict:
        """Processar resposta de botão de humor"""
        if button_id.startswith('mood_'):
            mood_level = int(button_id.replace('mood_', ''))
            return self._ask_functioning_level(patient, mood_level)
        elif button_id.startswith('func_'):
            functioning_level = int(button_id.replace('func_', ''))
            return self._ask_sleep_quality(patient, functioning_level)
        elif button_id.startswith('sleep_'):
            sleep_quality = int(button_id.replace('sleep_', ''))
            return self._ask_anxiety_level(patient, sleep_quality)
        elif button_id.startswith('anxiety_'):
            anxiety_level = int(button_id.replace('anxiety_', ''))
            return self._finish_mood_registration(patient, anxiety_level)
        
        return {'status': 'error', 'message': 'Botão não reconhecido'}
    
    def _ask_functioning_level(self, patient: Patient, mood_level: int) -> Dict:
        """Perguntar sobre nível de funcionamento"""
        mood_description = self._get_mood_description(mood_level)
        
        message = f"""✅ Humor registrado: {mood_description}

🎯 *Nível de Funcionamento*

Como está sua capacidade de realizar atividades diárias hoje?

Escala de 0 a 100:
• 0-25: Muito prejudicado
• 26-50: Moderadamente prejudicado
• 51-75: Levemente prejudicado  
• 76-100: Funcionamento normal"""
        
        buttons = [
            {'id': 'func_15', 'title': '0-25 Muito prejudicado'},
            {'id': 'func_40', 'title': '26-50 Moderadamente'},
            {'id': 'func_65', 'title': '51-75 Levemente'},
            {'id': 'func_90', 'title': '76-100 Normal'}
        ]
        
        self.whatsapp_service.send_interactive_message(
            patient.phone_number,
            "🎯 Funcionamento",
            message,
            buttons
        )
        
        # Salvar mood_level temporariamente
        self._save_temp_data(patient, 'mood_level', mood_level)
        
        return {'status': 'sent', 'action': 'functioning_asked'}
    
    def _ask_sleep_quality(self, patient: Patient, functioning_level: int) -> Dict:
        """Perguntar sobre qualidade do sono"""
        message = f"""✅ Funcionamento registrado: {functioning_level}%

😴 *Qualidade do Sono*

Como foi seu sono na noite passada?"""
        
        buttons = [
            {'id': 'sleep_1', 'title': '1 - Muito ruim'},
            {'id': 'sleep_2', 'title': '2 - Ruim'},
            {'id': 'sleep_3', 'title': '3 - Regular'},
            {'id': 'sleep_4', 'title': '4 - Bom'},
            {'id': 'sleep_5', 'title': '5 - Excelente'}
        ]
        
        self.whatsapp_service.send_interactive_message(
            patient.phone_number,
            "😴 Sono",
            message,
            buttons
        )
        
        # Salvar functioning_level temporariamente
        self._save_temp_data(patient, 'functioning_level', functioning_level)
        
        return {'status': 'sent', 'action': 'sleep_asked'}
    
    def _ask_anxiety_level(self, patient: Patient, sleep_quality: int) -> Dict:
        """Perguntar sobre nível de ansiedade"""
        sleep_desc = ['', 'muito ruim', 'ruim', 'regular', 'bom', 'excelente'][sleep_quality]
        
        message = f"""✅ Sono registrado: {sleep_desc}

😰 *Nível de Ansiedade*

Qual seu nível de ansiedade hoje?

Escala de 0 a 10:
• 0: Nenhuma ansiedade
• 5: Ansiedade moderada
• 10: Ansiedade extrema"""
        
        buttons = [
            {'id': 'anxiety_0', 'title': '0 - Nenhuma'},
            {'id': 'anxiety_2', 'title': '1-2 - Baixa'},
            {'id': 'anxiety_5', 'title': '3-5 - Moderada'},
            {'id': 'anxiety_8', 'title': '6-8 - Alta'},
            {'id': 'anxiety_10', 'title': '9-10 - Extrema'}
        ]
        
        self.whatsapp_service.send_interactive_message(
            patient.phone_number,
            "😰 Ansiedade",
            message,
            buttons
        )
        
        # Salvar sleep_quality temporariamente
        self._save_temp_data(patient, 'sleep_quality', sleep_quality)
        
        return {'status': 'sent', 'action': 'anxiety_asked'}
    
    def _finish_mood_registration(self, patient: Patient, anxiety_level: int) -> Dict:
        """Finalizar registro de humor"""
        # Recuperar dados temporários
        temp_data = self._get_temp_data(patient)
        mood_level = temp_data.get('mood_level', 0)
        functioning_level = temp_data.get('functioning_level', 50)
        sleep_quality = temp_data.get('sleep_quality', 3)
        
        # Criar registro no banco de dados
        mood_chart = MoodChart(
            patient_id=patient.id,
            date=date.today(),
            mood_level=mood_level,
            functioning_level=functioning_level,
            sleep_quality=sleep_quality,
            anxiety_level=anxiety_level
        )
        
        db.session.add(mood_chart)
        db.session.commit()
        
        # Enviar resumo
        mood_desc = self._get_mood_description(mood_level)
        anxiety_desc = self._get_anxiety_description(anxiety_level)
        
        message = f"""✅ *Registro de Humor Concluído!*

📊 *Resumo de hoje:*
• 😊 Humor: {mood_desc}
• 🎯 Funcionamento: {functioning_level}%
• 😴 Sono: {sleep_quality}/5
• 😰 Ansiedade: {anxiety_level}/10 ({anxiety_desc})

Obrigado por registrar! Seus dados ajudam no acompanhamento do seu tratamento. 📈"""
        
        self.whatsapp_service.send_text_message(patient.phone_number, message)
        
        # Limpar dados temporários
        self._clear_temp_data(patient)
        
        return {
            'status': 'completed',
            'action': 'mood_registration_finished',
            'mood_level': mood_level,
            'functioning_level': functioning_level
        }
    
    def _show_today_mood(self, patient: Patient, mood_entry: MoodChart) -> Dict:
        """Mostrar registro de humor já existente para hoje"""
        mood_desc = mood_entry.get_mood_description()
        anxiety_desc = self._get_anxiety_description(mood_entry.anxiety_level)
        
        message = f"""📊 *Seu humor hoje já foi registrado:*

• 😊 Humor: {mood_desc}
• 🎯 Funcionamento: {mood_entry.functioning_level}%
• 😴 Sono: {mood_entry.sleep_quality}/5
• 😰 Ansiedade: {mood_entry.anxiety_level}/10 ({anxiety_desc})

Registrado às {mood_entry.created_at.strftime('%H:%M')}

Você pode registrar novamente amanhã! 📅"""
        
        self.whatsapp_service.send_text_message(patient.phone_number, message)
        
        return {'status': 'sent', 'action': 'existing_mood_shown'}
    
    def process_mood_response(self, patient: Patient, message_text: str, user_state: Dict) -> Dict:
        """Processar resposta de humor via texto"""
        step = user_state.get('mood_step', 'mood_level')
        
        try:
            value = int(message_text.strip())
        except ValueError:
            message = "Por favor, digite apenas um número válido."
            self.whatsapp_service.send_text_message(patient.phone_number, message)
            return {'status': 'error', 'action': 'invalid_number'}
        
        if step == 'mood_level':
            if -3 <= value <= 3:
                return self._ask_functioning_level(patient, value)
            else:
                message = "Por favor, digite um número entre -3 e +3."
                self.whatsapp_service.send_text_message(patient.phone_number, message)
                return {'status': 'error', 'action': 'invalid_range'}
        
        # Implementar outros steps conforme necessário
        return {'status': 'processed', 'action': 'mood_response_processed'}
    
    def get_mood_trend_report(self, patient: Patient, days: int = 7) -> Dict:
        """Gerar relatório de tendência de humor"""
        start_date = date.today() - timedelta(days=days)
        
        mood_entries = MoodChart.query.filter(
            MoodChart.patient_id == patient.id,
            MoodChart.date >= start_date
        ).order_by(MoodChart.date.desc()).all()
        
        if not mood_entries:
            return {'status': 'no_data', 'message': 'Nenhum registro encontrado'}
        
        # Calcular médias
        avg_mood = sum(entry.mood_level for entry in mood_entries) / len(mood_entries)
        avg_functioning = sum(entry.functioning_level for entry in mood_entries) / len(mood_entries)
        avg_anxiety = sum(entry.anxiety_level or 0 for entry in mood_entries) / len(mood_entries)
        
        return {
            'period_days': days,
            'total_entries': len(mood_entries),
            'avg_mood': round(avg_mood, 1),
            'avg_functioning': round(avg_functioning, 1),
            'avg_anxiety': round(avg_anxiety, 1),
            'entries': [entry.to_dict() for entry in mood_entries]
        }
    
    def _get_mood_description(self, mood_level: int) -> str:
        """Obter descrição do nível de humor"""
        descriptions = {
            -3: "Depressão severa",
            -2: "Depressão moderada",
            -1: "Depressão leve",
            0: "Humor normal/estável",
            1: "Hipomania leve",
            2: "Hipomania moderada",
            3: "Mania severa"
        }
        return descriptions.get(mood_level, "Não definido")
    
    def _get_anxiety_description(self, anxiety_level: int) -> str:
        """Obter descrição do nível de ansiedade"""
        if anxiety_level == 0:
            return "nenhuma"
        elif 1 <= anxiety_level <= 2:
            return "baixa"
        elif 3 <= anxiety_level <= 5:
            return "moderada"
        elif 6 <= anxiety_level <= 8:
            return "alta"
        else:
            return "extrema"
    
    def _save_temp_data(self, patient: Patient, key: str, value):
        """Salvar dados temporários"""
        # Implementação simples usando variável de classe
        # Em produção, usar Redis ou banco de dados
        if not hasattr(self, 'temp_data'):
            self.temp_data = {}
        
        if patient.phone_number not in self.temp_data:
            self.temp_data[patient.phone_number] = {}
        
        self.temp_data[patient.phone_number][key] = value
    
    def _get_temp_data(self, patient: Patient) -> Dict:
        """Recuperar dados temporários"""
        if not hasattr(self, 'temp_data'):
            return {}
        
        return self.temp_data.get(patient.phone_number, {})
    
    def _clear_temp_data(self, patient: Patient):
        """Limpar dados temporários"""
        if hasattr(self, 'temp_data') and patient.phone_number in self.temp_data:
            del self.temp_data[patient.phone_number]

