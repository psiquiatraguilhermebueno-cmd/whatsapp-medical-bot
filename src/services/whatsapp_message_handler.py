# src/services/whatsapp_message_handler.py
import os
import re
import json
import logging
import traceback
from typing import Dict, Any, Optional, Tuple

from src.services.whatsapp_service import WhatsAppService
from src.services.whatsapp_admin_service import WhatsAppAdminService
from src.services.whatsapp_questionnaire_service import WhatsAppQuestionnaireService
from src.services.whatsapp_scheduler_service import WhatsAppSchedulerService
from src.services.whatsapp_mood_service import WhatsAppMoodService
from src.models.patient import Patient
from src.models.breathing_exercise import BreathingExercise
from src.models.user import db


def _clean_phone(pn: Optional[str]) -> str:
    """Normaliza telefone para E.164 sem '+', apenas dígitos."""
    if not isinstance(pn, str):
        return ""
    pn = pn.strip()
    if pn.startswith("+"):
        pn = pn[1:]
    return re.sub(r"\D+", "", pn)


class WhatsAppMessageHandler:
    """Handler principal para processar mensagens do WhatsApp."""

    # Mapas estáveis de horários (para u-ETG)
    SLOT_ID_MAP = {
        "07:30": "slot_0730",
        "12:15": "slot_1215",
        "19:00": "slot_1900",
    }
    REVERSE_SLOT_ID_MAP = {v: k for k, v in SLOT_ID_MAP.items()}
    TIME_RE = re.compile(r"^\s*(\d{1,2})[:hH]?(\d{2})\s*$")  # "12:15", "12h15", "1215" (via pré-processamento)

    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.admin_service = WhatsAppAdminService()
        self.questionnaire_service = WhatsAppQuestionnaireService()
        self.scheduler_service = WhatsAppSchedulerService()
        self.mood_service = WhatsAppMoodService()
        self.logger = logging.getLogger(__name__)

        # Número(s) do administrador (config via variável de ambiente)
        # Suporta múltiplos separados por vírgula.
        self.admin_phone = os.getenv("ADMIN_PHONE_NUMBER") or os.getenv("ADMIN_NUMBER") or ""
        self._admin_set = {
            _clean_phone(p) for p in (self.admin_phone.split(",") if self.admin_phone else [])
            if _clean_phone(p)
        }

    # ------------- ENTRYPOINT -------------

    def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa o webhook do WhatsApp.

        Returns:
            dict com status/ação
        """
        try:
            # Parse padrão do seu serviço (mantido)
            message_data = self.whatsapp_service.parse_webhook_message(webhook_data)
            if not message_data:
                return {"status": "ignored", "reason": "Invalid webhook data"}

            # Marcar mensagem como lida (se aplicável)
            if message_data.get("message_id"):
                try:
                    self.whatsapp_service.mark_message_as_read(message_data["message_id"])
                except Exception:
                    # Não derruba o fluxo por falha de "read"
                    self.logger.warning("Falha ao marcar mensagem como lida", exc_info=True)

            # Extrair infos do usuário
            user_info = {
                "phone_number": _clean_phone(message_data.get("from")),
                "name": message_data.get("contact_name") or "Usuário",
                "message_id": message_data.get("message_id"),
                "timestamp": message_data.get("timestamp"),
            }
            phone_number = user_info["phone_number"]

            msg_type = (message_data.get("type") or "").strip().lower()

            if msg_type == "text":
                return self._handle_text_message(phone_number, message_data.get("text", "") or "", user_info)

            elif msg_type == "interactive":
                return self._handle_interactive_message(phone_number, message_data.get("interactive", {}) or {}, user_info)

            else:
                # Tipos não suportados—responder de forma amigável
                self.whatsapp_service.send_text_message(
                    phone_number,
                    "Desculpe, não consigo processar este tipo de mensagem. Use texto ou os botões fornecidos. ✅"
                )
                return {"status": "processed", "action": "unsupported_message_type"}

        except Exception as e:
            self.logger.error("Erro ao processar webhook: %s", e)
            self.logger.debug(traceback.format_exc())
            return {"status": "error", "message": str(e)}

    # ------------- TEXT -------------

    def _handle_text_message(self, phone_number: str, message_text: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Processar mensagem de texto."""
        try:
            txt = (message_text or "").strip().lower()

            # Admin: comandos
            if self._is_admin(phone_number):
                return self._handle_admin_command(phone_number, txt, user_info)

            # Comandos básicos
            if txt in {"/start", "oi", "olá", "ola", "menu"}:
                return self._send_welcome_message(phone_number, user_info)

            # Paciente: resposta padrão
            patient = self._get_or_create_patient(user_info)
            if patient:
                self.whatsapp_service.send_text_message(
                    phone_number,
                    "Mensagem recebida! Se você está respondendo a um questionário, use os botões fornecidos. ✅"
                )
                return {"status": "processed", "action": "patient_response_received"}

            return {"status": "processed", "action": "text_message_handled"}

        except Exception as e:
            self.logger.error("Erro ao processar mensagem de texto: %s", e)
            self.logger.debug(traceback.format_exc())
            return {"status": "error", "message": str(e)}

    # ------------- INTERACTIVE -------------

    def _normalize_interactive(self, interactive: Dict[str, Any]) -> Tuple[str, str]:
        """
        Aceita button_reply, list_reply e nfm_reply.
        Retorna (response_id_normalizado, title_visto).
        """
        # Log bruto (útil para debug em produção)
        try:
            self.logger.debug("RAW INTERACTIVE: %s", json.dumps(interactive, ensure_ascii=False))
        except Exception:
            pass

        itype = (interactive.get("type") or "").strip()

        rid, title = "", ""
        if itype == "button_reply":
            br = interactive.get("button_reply") or {}
            rid = (br.get("id") or "").strip()
            title = (br.get("title") or "").strip()

        elif itype == "list_reply":
            lr = interactive.get("list_reply") or {}
            rid = (lr.get("id") or "").strip()
            title = (lr.get("title") or "").strip()

        elif itype == "nfm_reply":
            # Alguns fluxos "native flow" chegam assim
            nfm = interactive.get("nfm_reply") or {}
            title = (nfm.get("body") or "").strip()
            rid = (nfm.get("response_json") or "").strip() or title

        # Fallback: usar título quando id vazio
        response = (rid or title or "").strip()

        # Pré-processar para regex (permitir "12h15", "1215")
        # Se vier "1215" puro, vamos transformar em "12:15" para checar no mapa
        digits = re.fullmatch(r"\s*(\d{3,4})\s*", response or "")
        if digits and not response.count(":"):
            num = digits.group(1)
            if len(num) == 3:  # 815 -> 08:15
                response = f"{int(num[:-2]):02d}:{num[-2:]}"
            elif len(num) == 4:  # 1215 -> 12:15
                response = f"{num[:2]}:{num[2:]}"

        # Mapear título exato -> slot_id
        if response in self.SLOT_ID_MAP:
            response = self.SLOT_ID_MAP[response]

        # Se ainda não mapeou e há horário no rid/title, tenta regex
        if response not in self.REVERSE_SLOT_ID_MAP:
            candidate = rid or title
            if candidate:
                m = self.TIME_RE.match(candidate.replace(" ", ""))
                if m:
                    hhmm = f"{int(m.group(1)):02d}:{m.group(2)}"
                    response = self.SLOT_ID_MAP.get(hhmm, response)

        return response, title

    def _handle_interactive_message(self, phone_number: str, interactive_data: Dict[str, Any], user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Processar mensagem interativa (botões/listas/flows)."""
        try:
            phone_number = _clean_phone(phone_number)
            response_id, title = self._normalize_interactive(interactive_data)

            if not response_id:
                self.logger.error("Nenhum ID/título encontrado na resposta interativa")
                self.whatsapp_service.send_text_message(
                    phone_number, "Recebi seu clique, mas não identifiquei a opção. Pode tentar novamente? 🙏"
                )
                return {"status": "error", "message": "No response ID or title"}

            self.logger.info("Interactive click | from=%s | resp=%s | title=%s",
                             phone_number, response_id, title or "-")

            # 1) Slots u-ETG (IDs estáveis slot_0730/1215/1900)
            if response_id in self.REVERSE_SLOT_ID_MAP or response_id.startswith("slot_"):
                patient = self._get_or_create_patient(user_info)
                return self._handle_uetg_slot_callback(phone_number, response_id, patient)

            # 2) Admin callbacks
            if self._is_admin(phone_number):
                return self._handle_admin_callback(phone_number, response_id, user_info)

            # 3) Questionários
            if response_id.startswith("start_questionnaire_") or response_id.startswith("questionnaire_"):
                patient = self._get_or_create_patient(user_info)
                if patient:
                    return self._handle_questionnaire_callback(phone_number, response_id, patient)

            # 4) Medicação
            if response_id.startswith("medication_"):
                patient = self._get_or_create_patient(user_info)
                if patient:
                    return self._handle_medication_callback(phone_number, response_id, patient)

            # 5) Humor
            if response_id.startswith("mood_") or response_id.startswith("start_mood_"):
                patient = self._get_or_create_patient(user_info)
                if patient:
                    return self._handle_mood_callback(phone_number, response_id, patient)

            # 6) Respiração
            if response_id.startswith("breathing_") or response_id.startswith("start_breathing_"):
                patient = self._get_or_create_patient(user_info)
                if patient:
                    return self._handle_breathing_callback(phone_number, response_id, patient)

            # 7) Lembretes
            if response_id.startswith("snooze_") or response_id.startswith("skip_"):
                patient = self._get_or_create_patient(user_info)
                if patient:
                    return self._handle_reminder_action(phone_number, response_id, patient)

            # Fallback amigável
            self.logger.info("Resposta interativa não reconhecida: %s", response_id)
            self.whatsapp_service.send_text_message(
                phone_number,
                "Opção recebida. Já anotei aqui e te retorno em seguida. ✅"
            )
            return {"status": "processed", "action": "interactive_handled"}

        except Exception as e:
            self.logger.error("Erro ao processar mensagem interativa: %s", e)
            self.logger.debug(traceback.format_exc())
            self.whatsapp_service.send_text_message(
                _clean_phone(phone_number),
                "❌ Ocorreu um erro ao processar seu clique. Tente novamente em instantes."
            )
            return {"status": "error", "message": str(e)}

    # ------------- ADMIN -------------

    def _handle_admin_command(self, phone_number: str, command: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Processar comando administrativo."""
        return self.admin_service.handle_command(phone_number, command, user_info)

    def _handle_admin_callback(self, phone_number: str, callback_data: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Processar callback administrativo."""
        return self.admin_service.handle_callback(phone_number, callback_data, user_info)

    # ------------- QUESTIONÁRIO / MEDICAÇÃO / HUMOR / RESPIRAÇÃO / LEMBRETES -------------

    def _handle_questionnaire_callback(self, phone_number: str, callback_data: str, patient: Patient) -> Dict[str, Any]:
        """Processar callback de questionário."""
        if callback_data.startswith("start_questionnaire_"):
            scale_name = callback_data.replace("start_questionnaire_", "", 1)
            return self.questionnaire_service.start_questionnaire(phone_number, scale_name, patient)
        elif callback_data.startswith("questionnaire_answer_"):
            return self.questionnaire_service.handle_response(phone_number, callback_data, patient)
        else:
            return {"status": "processed", "action": "questionnaire_callback_handled"}

    def _handle_medication_callback(self, phone_number: str, callback_data: str, patient: Patient) -> Dict[str, Any]:
        """Processar callback de medicação."""
        return self.scheduler_service.handle_medication_confirmation(phone_number, callback_data, patient)

    def _handle_mood_callback(self, phone_number: str, callback_data: str, patient: Patient) -> Dict[str, Any]:
        """Processar callback de humor."""
        if callback_data == "start_mood_chart":
            return self.mood_service.start_mood_chart(phone_number, patient)
        elif callback_data.startswith("mood_"):
            return self.mood_service.handle_mood_response(phone_number, callback_data, patient)
        else:
            return {"status": "processed", "action": "mood_callback_handled"}

    def _handle_breathing_callback(self, phone_number: str, callback_data: str, patient: Patient) -> Dict[str, Any]:
        """Processar callback de exercício de respiração."""
        if callback_data.startswith("start_breathing_"):
            try:
                exercise_id = int(callback_data.split("_")[-1])
            except Exception:
                self.whatsapp_service.send_text_message(phone_number, "❌ Exercício inválido.")
                return {"status": "error", "message": "Invalid breathing ID"}
            return self._start_breathing_exercise(phone_number, exercise_id, patient)
        else:
            return {"status": "processed", "action": "breathing_callback_handled"}

    def _handle_reminder_action(self, phone_number: str, callback_data: str, patient: Patient) -> Dict[str, Any]:
        """Processar ações de lembrete (snooze, skip)."""
        if callback_data.startswith("snooze_"):
            return self.scheduler_service.handle_reminder_snooze(phone_number, callback_data, patient)
        elif callback_data.startswith("skip_"):
            return self.scheduler_service.handle_reminder_skip(phone_number, callback_data, patient)
        else:
            return {"status": "processed", "action": "reminder_action_handled"}

    # ------------- U-ETG -------------

    def _handle_uetg_slot_callback(self, phone_number: str, response_id: str, patient: Optional[Patient]) -> Dict[str, Any]:
        """Processar clique nos botões de horário u-ETG (tolerante a diferenças de assinatura)."""
        try:
            if not response_id:
                self.logger.error("Response ID inválido para u-ETG")
                self.whatsapp_service.send_text_message(phone_number, "❌ Opção inválida. Tente novamente.")
                return {"status": "error", "action": "invalid_response_id"}

            if not patient or not getattr(patient, "name", None):
                self.logger.error("Paciente inválido para u-ETG")
                self.whatsapp_service.send_text_message(phone_number, "❌ Paciente não identificado.")
                return {"status": "error", "action": "invalid_patient"}

            patient_name = (patient.name or "Paciente").strip()
            phone_clean = _clean_phone(phone_number)

            # Descobrir horário humano, se possível
            human_time = self.REVERSE_SLOT_ID_MAP.get(response_id)
            if not human_time:
                # Tenta extrair por regex de dentro do ID (ex.: HORARIO_1215)
                m = re.search(r"(\d{1,2})[:hH]?(\d{2})", response_id or "")
                if m:
                    human_time = f"{int(m.group(1)):02d}:{m.group(2)}"

            self.logger.info("Processando slot u-ETG | user=%s | resp=%s | time=%s",
                             phone_clean, response_id, human_time or "-")

            # Import tardio (evita ciclos)
            from src.jobs.uetg_scheduler import process_button_click  # noqa: E402

            ok = None
            # 1) Assinatura estilo: process_button_click(user_id, response_id, request_id="")
            try:
                ok = process_button_click(user_id=phone_clean, response_id=response_id, request_id="uETG-webhook")
            except TypeError:
                pass
            except Exception:
                self.logger.warning("Assinatura (user_id, response_id, request_id) falhou", exc_info=True)

            # 2) Assinatura estilo: process_button_click(response_id, phone_number, patient_name)
            if ok is None:
                try:
                    ok = process_button_click(response_id, phone_clean, patient_name)
                except TypeError:
                    pass
                except Exception:
                    self.logger.warning("Assinatura (resp_id, phone, name) falhou", exc_info=True)

            # 3) Assinatura estilo: process_button_click(phone_number, response_id)
            if ok is None:
                try:
                    ok = process_button_click(phone_clean, response_id)
                except TypeError:
                    pass
                except Exception:
                    self.logger.warning("Assinatura (phone, resp_id) falhou", exc_info=True)

            # Se a função não retorna booleano, considerar sucesso ao não lançar exceção
            if ok is None:
                ok = True

            if ok:
                msg = f"⏰ Horário confirmado: {human_time or 'horário escolhido'}. Obrigado! ✅"
                self.whatsapp_service.send_text_message(phone_clean, msg)
                self.logger.info("u-ETG horário confirmado | user=%s | time=%s", phone_clean, human_time or "-")
                return {"status": "processed", "action": "uetg_slot_confirmed"}
            else:
                self.logger.error("Erro ao confirmar slot u-ETG: %s", response_id)
                self.whatsapp_service.send_text_message(
                    phone_clean, "❌ Erro ao confirmar horário. Tente novamente."
                )
                return {"status": "error", "action": "uetg_slot_error"}

        except Exception as e:
            self.logger.error("Erro ao processar confirmação u-ETG: %s", e)
            self.logger.debug(traceback.format_exc())
            self.whatsapp_service.send_text_message(
                _clean_phone(phone_number), "❌ Erro interno. Tente novamente mais tarde."
            )
            return {"status": "error", "message": str(e)}

    # ------------- BOAS-VINDAS -------------

    def _send_welcome_message(self, phone_number: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Enviar mensagem de boas-vindas."""
        name = user_info.get("name", "") or ""

        if self._is_admin(phone_number):
            message = (
                f"👋 Olá{f', {name}' if name else ''}!\n\n"
                "🏥 *Painel Administrativo - Bot de Lembretes Médicos*\n\n"
                "Comandos:\n"
                "📋 */menu* — Menu principal\n"
                "👥 */pacientes* — Gerenciar pacientes\n"
                "⏰ */lembretes* — Gerenciar lembretes\n"
                "📊 */relatorios* — Ver relatórios\n"
                "⚙️ */sistema* — Configurações\n"
                "📈 */status* — Status rápido\n"
            )
        else:
            message = (
                f"👋 Olá{f', {name}' if name else ''}!\n\n"
                "🏥 *Bot de Lembretes Médicos*\n\n"
                "Posso ajudar com:\n"
                "• 📋 Questionários de saúde\n"
                "• 💊 Lembretes de medicação\n"
                "• 😊 Registro de humor\n"
                "• 🫁 Exercícios de respiração\n\n"
                "Aguarde os lembretes automáticos ou digite *menu* para ver opções."
            )

        self.whatsapp_service.send_text_message(_clean_phone(phone_number), message)
        return {"status": "sent", "action": "welcome_message_sent"}

    # ------------- PACIENTE / ADMIN CHECK -------------

    def _get_or_create_patient(self, user_info: Dict[str, Any]) -> Optional[Patient]:
        """Obter ou criar paciente por phone_number."""
        phone_number = _clean_phone(user_info.get("phone_number"))
        if not phone_number:
            return None

        patient = Patient.query.filter_by(whatsapp_phone=phone_number).first()
        if not patient:
            patient = Patient(
                name=user_info.get("name", f"Paciente {phone_number[-4:]}"),
                whatsapp_phone=phone_number,
                is_active=True,
            )
            db.session.add(patient)
            db.session.commit()
        return patient

    def _is_admin(self, phone_number: str) -> bool:
        """Verifica se o número é admin (robusto contra None e múltiplos)."""
        try:
            pn = _clean_phone(phone_number)
            if not pn:
                return False
            # Recarrega admins se env mudou durante o runtime
            if not self._admin_set:
                raw = os.getenv("ADMIN_PHONE_NUMBER") or os.getenv("ADMIN_NUMBER") or ""
                self._admin_set = {_clean_phone(p) for p in raw.split(",") if _clean_phone(p)}
            return pn in self._admin_set
        except Exception as e:
            self.logger.error("_is_admin error: %s\n%s", e, traceback.format_exc())
            return False

    # ------------- RESPIRAÇÃO -------------

    def _start_breathing_exercise(self, phone_number: str, exercise_id: int, patient: Patient) -> Dict[str, Any]:
        """Iniciar exercício de respiração."""
        try:
            exercise = BreathingExercise.query.get(exercise_id)
            if not exercise:
                self.whatsapp_service.send_text_message(_clean_phone(phone_number), "❌ Exercício de respiração não encontrado.")
                return {"status": "error", "message": "Exercise not found"}

            message = (
                f"🫁 *{exercise.name}*\n\n"
                f"{exercise.description}\n\n"
                f"📝 *Instruções:*\n{exercise.instructions}\n\n"
                f"⏱️ *Duração:* {exercise.duration_minutes} minutos\n\n"
                "Vamos começar? Encontre um local confortável e siga as instruções."
            )
            buttons = [
                {"id": f"breathing_start_audio_{exercise_id}", "title": "🎵 Iniciar com áudio"},
                {"id": f"breathing_start_text_{exercise_id}", "title": "📝 Apenas instruções"},
                {"id": "breathing_cancel", "title": "❌ Cancelar"},
            ]
            self.whatsapp_service.send_interactive_message(_clean_phone(phone_number), "Exercício de Respiração", message, buttons)
            return {"status": "sent", "action": "breathing_exercise_started"}

        except Exception as e:
            self.logger.error("Erro ao iniciar exercício de respiração: %s", e)
            self.logger.debug(traceback.format_exc())
            return {"status": "error", "message": str(e)}

    # ------------- ADMIN NOTIFY -------------

    def notify_admin(self, message: str) -> Dict[str, Any]:
        """Enviar notificação para administrador(es)."""
        raw_admins = self.admin_phone or os.getenv("ADMIN_PHONE_NUMBER") or os.getenv("ADMIN_NUMBER") or ""
        admin_phones = [_clean_phone(p) for p in raw_admins.split(",") if _clean_phone(p)]
        if not admin_phones:
            self.logger.warning("Admin phone não configurado")
            return {"status": "error", "message": "Admin phone not configured"}

        try:
            for admin_phone in admin_phones:
                self.whatsapp_service.send_text_message(admin_phone, message)
            return {"status": "sent", "action": "admin_notified"}
        except Exception as e:
            self.logger.error("Erro ao notificar admin: %s", e)
            self.logger.debug(traceback.format_exc())
            return {"status": "error", "message": str(e)}
