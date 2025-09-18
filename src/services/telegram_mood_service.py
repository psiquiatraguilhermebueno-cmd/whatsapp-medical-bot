import logging
import os
from typing import Dict, List
from datetime import datetime, date, timedelta
from src.services.telegram_service import TelegramService
from src.models.patient import Patient
from src.models.mood_chart import MoodChart
from src.models.user import db

class TelegramMoodService:
    """Serviço para gerenciar registro de humor via Telegram"""
    
    def __init__(self):
        self.telegram_service = TelegramService(bot_token=os.getenv('TELEGRAM_BOT_TOKEN'))
        self.logger = logging.getLogger(__name__)
        
        # Estados de registro de humor ativos
        self.active_mood_charts = {}
    
    def start_mood_chart(self, chat_id: str, patient: Patient) -> Dict:
        """Iniciar registro de humor"""
        try:
            # Verificar se já registrou hoje
            today = date.today()
            existing_mood = MoodChart.query.filter_by(
                patient_id=patient.id,
                date=today
            ).first()
            
            if existing_mood:
                message = f"""😊 *Registro de Humor*

Você já registrou seu humor hoje!

📊 *Humor:* {existing_mood.mood_level}/10
😴 *Sono:* {existing_mood.sleep_quality or 'Não informado'}
💊 *Medicação:* {'Sim' if existing_mood.medication_taken else 'Não'}

Obrigado por manter seu registro em dia! 👏"""
                
                self.telegram_service.send_text_message(chat_id, message)
                return {"status": "already_registered", "action": "mood_already_registered"}
            
            # Inicializar estado do registro
            mood_state = {
                "patient_id": patient.id,
                "date": today.isoformat(),
                "step": "mood_level",
                "data": {},
                "started_at": datetime.now().isoformat()
            }
            
            self.active_mood_charts[chat_id] = mood_state
            
            # Enviar primeira pergunta
            return self._send_mood_level_question(chat_id)
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar registro de humor: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_mood_response(self, chat_id: str, callback_data: str, patient: Patient) -> Dict:
        """Processar resposta de humor"""
        try:
            if chat_id not in self.active_mood_charts:
                return self.start_mood_chart(chat_id, patient)
            
            state = self.active_mood_charts[chat_id]
            current_step = state["step"]
            
            if current_step == "mood_level":
                return self._handle_mood_level_response(chat_id, callback_data, state)
            elif current_step == "sleep_quality":
                return self._handle_sleep_quality_response(chat_id, callback_data, state)
            elif current_step == "medication_taken":
                return self._handle_medication_response(chat_id, callback_data, state)
            elif current_step == "notes":
                return self._handle_notes_response(chat_id, callback_data, state)
            else:
                return {"status": "error", "message": "Invalid step"}
                
        except Exception as e:
            self.logger.error(f"Erro ao processar resposta de humor: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_mood_level_question(self, chat_id: str) -> Dict:
        """Enviar pergunta sobre nível de humor"""
        message = """😊 *Registro de Humor Diário*

Como você está se sentindo hoje?

Escolha um número de 1 a 10:
• 1-3: Muito mal
• 4-6: Neutro/Ok
• 7-10: Muito bem"""
        
        buttons = []
        for i in range(1, 11):
            emoji = "😢" if i <= 3 else "😐" if i <= 6 else "😊"
            buttons.append({
                "text": f"{emoji} {i}",
                "callback_data": f"mood_level_{i}"
            })
        
        # Organizar botões em linhas de 5
        organized_buttons = []
        for i in range(0, len(buttons), 5):
            organized_buttons.extend(buttons[i:i+5])
        
        self.telegram_service.send_interactive_message(chat_id, message, organized_buttons)
        return {"status": "sent", "action": "mood_level_question_sent"}
    
    def _handle_mood_level_response(self, chat_id: str, callback_data: str, state: Dict) -> Dict:
        """Processar resposta do nível de humor"""
        try:
            # Extrair nível do callback_data
            mood_level = int(callback_data.split('_')[-1])
            
            state["data"]["mood_level"] = mood_level
            state["step"] = "sleep_quality"
            
            return self._send_sleep_quality_question(chat_id, mood_level)
            
        except Exception as e:
            self.logger.error(f"Erro ao processar nível de humor: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_sleep_quality_question(self, chat_id: str, mood_level: int) -> Dict:
        """Enviar pergunta sobre qualidade do sono"""
        mood_emoji = "😢" if mood_level <= 3 else "😐" if mood_level <= 6 else "😊"
        
        message = f"""😴 *Qualidade do Sono*

{mood_emoji} Humor registrado: {mood_level}/10

Como foi a qualidade do seu sono na noite passada?"""
        
        buttons = [
            {"text": "😴 Muito ruim", "callback_data": "sleep_quality_1"},
            {"text": "😕 Ruim", "callback_data": "sleep_quality_2"},
            {"text": "😐 Regular", "callback_data": "sleep_quality_3"},
            {"text": "😊 Bom", "callback_data": "sleep_quality_4"},
            {"text": "😴 Excelente", "callback_data": "sleep_quality_5"}
        ]
        
        self.telegram_service.send_interactive_message(chat_id, message, buttons)
        return {"status": "sent", "action": "sleep_quality_question_sent"}
    
    def _handle_sleep_quality_response(self, chat_id: str, callback_data: str, state: Dict) -> Dict:
        """Processar resposta da qualidade do sono"""
        try:
            # Extrair qualidade do sono
            sleep_quality = int(callback_data.split('_')[-1])
            
            sleep_labels = {
                1: "Muito ruim",
                2: "Ruim", 
                3: "Regular",
                4: "Bom",
                5: "Excelente"
            }
            
            state["data"]["sleep_quality"] = sleep_quality
            state["data"]["sleep_quality_label"] = sleep_labels.get(sleep_quality, "Não informado")
            state["step"] = "medication_taken"
            
            return self._send_medication_question(chat_id)
            
        except Exception as e:
            self.logger.error(f"Erro ao processar qualidade do sono: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_medication_question(self, chat_id: str) -> Dict:
        """Enviar pergunta sobre medicação"""
        message = """💊 *Medicação*

Você tomou sua medicação hoje conforme prescrito?"""
        
        buttons = [
            {"text": "✅ Sim, tomei tudo", "callback_data": "medication_taken_yes"},
            {"text": "⚠️ Tomei parcialmente", "callback_data": "medication_taken_partial"},
            {"text": "❌ Não tomei", "callback_data": "medication_taken_no"},
            {"text": "🚫 Não tenho medicação", "callback_data": "medication_taken_none"}
        ]
        
        self.telegram_service.send_interactive_message(chat_id, message, buttons)
        return {"status": "sent", "action": "medication_question_sent"}
    
    def _handle_medication_response(self, chat_id: str, callback_data: str, state: Dict) -> Dict:
        """Processar resposta sobre medicação"""
        try:
            medication_status = callback_data.split('_')[-1]
            
            medication_labels = {
                "yes": "Sim, tomei tudo",
                "partial": "Tomei parcialmente", 
                "no": "Não tomei",
                "none": "Não tenho medicação"
            }
            
            state["data"]["medication_taken"] = medication_status == "yes"
            state["data"]["medication_status"] = medication_labels.get(medication_status, "Não informado")
            
            # Finalizar registro
            return self._finish_mood_chart(chat_id, state)
            
        except Exception as e:
            self.logger.error(f"Erro ao processar medicação: {e}")
            return {"status": "error", "message": str(e)}
    
    def _finish_mood_chart(self, chat_id: str, state: Dict) -> Dict:
        """Finalizar registro de humor"""
        try:
            data = state["data"]
            
            # Criar registro no banco de dados
            mood_chart = MoodChart(
                patient_id=state["patient_id"],
                date=datetime.fromisoformat(state["date"]).date(),
                mood_level=data["mood_level"],
                sleep_quality=data["sleep_quality"],
                medication_taken=data["medication_taken"],
                notes=f"Sono: {data['sleep_quality_label']}, Medicação: {data['medication_status']}"
            )
            
            db.session.add(mood_chart)
            db.session.commit()
            
            # Enviar resumo para o paciente
            self._send_mood_chart_summary(chat_id, data)
            
            # Notificar administrador se necessário
            if data["mood_level"] <= 3 or not data["medication_taken"]:
                self._notify_admin_concerning_mood(state, data)
            
            # Limpar estado
            del self.active_mood_charts[chat_id]
            
            return {
                "status": "completed",
                "action": "mood_chart_finished",
                "mood_level": data["mood_level"],
                "chart_id": mood_chart.id
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao finalizar registro de humor: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_mood_chart_summary(self, chat_id: str, data: Dict) -> None:
        """Enviar resumo do registro de humor"""
        mood_level = data["mood_level"]
        sleep_quality_label = data["sleep_quality_label"]
        medication_status = data["medication_status"]
        
        mood_emoji = "😢" if mood_level <= 3 else "😐" if mood_level <= 6 else "😊"
        
        message = f"""✅ *Registro de Humor Concluído*

{mood_emoji} *Humor:* {mood_level}/10
😴 *Sono:* {sleep_quality_label}
💊 *Medicação:* {medication_status}
📅 *Data:* {datetime.now().strftime('%d/%m/%Y')}

Obrigado por manter seu registro em dia! Suas informações foram enviadas ao seu profissional de saúde.

"""
        
        if mood_level <= 3:
            message += """💙 *Lembre-se:* Você não está sozinho. Se precisar de apoio, entre em contato com seu profissional de saúde.

🆘 *Emergência:* CVV 188 (24h)"""
        else:
            message += "Continue cuidando bem de você! 💚"
        
        self.telegram_service.send_text_message(chat_id, message)
    
    def _notify_admin_concerning_mood(self, state: Dict, data: Dict) -> None:
        """Notificar administrador sobre humor preocupante"""
        try:
            patient = Patient.query.get(state["patient_id"])
            if not patient:
                return
            
            admin_chat_id = os.getenv('ADMIN_CHAT_ID')
            if not admin_chat_id:
                return
            
            mood_level = data["mood_level"]
            medication_taken = data["medication_taken"]
            
            concerns = []
            if mood_level <= 3:
                concerns.append(f"Humor baixo ({mood_level}/10)")
            if not medication_taken:
                concerns.append("Não tomou medicação")
            
            message = f"""⚠️ *Alerta - Registro de Humor*

👤 *Paciente:* {patient.name}
📊 *Preocupações:* {', '.join(concerns)}
😴 *Sono:* {data['sleep_quality_label']}
📅 *Data:* {datetime.now().strftime('%d/%m/%Y %H:%M')}

💡 *Sugestão:* Considere entrar em contato com o paciente."""
            
            # Enviar para todos os admins
            admin_ids = [id.strip() for id in admin_chat_id.split(',')]
            for admin_id in admin_ids:
                self.telegram_service.send_text_message(admin_id, message)
                
        except Exception as e:
            self.logger.error(f"Erro ao notificar admin sobre humor: {e}")
    
    def cancel_mood_chart(self, chat_id: str) -> Dict:
        """Cancelar registro de humor ativo"""
        if chat_id in self.active_mood_charts:
            del self.active_mood_charts[chat_id]
            
            self.telegram_service.send_text_message(
                chat_id,
                "❌ Registro de humor cancelado."
            )
            
            return {"status": "cancelled", "action": "mood_chart_cancelled"}
        
        return {"status": "error", "message": "No active mood chart"}
    
    def get_mood_history(self, patient_id: int, days: int = 7) -> List[Dict]:
        """Obter histórico de humor do paciente"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        mood_charts = MoodChart.query.filter(
            MoodChart.patient_id == patient_id,
            MoodChart.date >= start_date,
            MoodChart.date <= end_date
        ).order_by(MoodChart.date.desc()).all()
        
        return [
            {
                "date": chart.date.isoformat(),
                "mood_level": chart.mood_level,
                "sleep_quality": chart.sleep_quality,
                "medication_taken": chart.medication_taken,
                "notes": chart.notes
            }
            for chart in mood_charts
        ]

