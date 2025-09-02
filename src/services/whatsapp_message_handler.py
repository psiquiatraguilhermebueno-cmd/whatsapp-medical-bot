import traceback
import logging
import os
from typing import Dict, Any
from src.services.whatsapp_service import WhatsAppService
from src.services.whatsapp_admin_service import WhatsAppAdminService
from src.services.whatsapp_questionnaire_service import WhatsAppQuestionnaireService
from src.services.whatsapp_scheduler_service import WhatsAppSchedulerService
from src.services.whatsapp_mood_service import WhatsAppMoodService
from src.models.patient import Patient
from src.models.breathing_exercise import BreathingExercise
from src.models.user import db


class WhatsAppMessageHandler:
    """Handler principal para processar mensagens do WhatsApp"""

    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.admin_service = WhatsAppAdminService()
        self.questionnaire_service = WhatsAppQuestionnaireService()
        self.scheduler_service = WhatsAppSchedulerService()
        self.mood_service = WhatsAppMoodService()
        self.logger = logging.getLogger(__name__)

        # Número do administrador (configurado via variável de ambiente)
        self.admin_phone = os.getenv("ADMIN_PHONE_NUMBER")

    def handle_webhook(self, webhook_data: Dict) -> Dict:
        """
        Processar webhook do WhatsApp

        Args:
            webhook_data: Dados do webhook

        Returns:
            Resultado do processamento
        """
        try:
            # Processar mensagem
            message_data = self.whatsapp_service.parse_webhook_message(webhook_data)
            if not message_data:
                return {"status": "ignored", "reason": "Invalid webhook data"}

            # Marcar mensagem como lida
            if message_data.get("message_id"):
                self.whatsapp_service.mark_message_as_read(message_data["message_id"])

            # Extrair informações do usuário
            # === user_info normalizado + bypass global u-ETG ===
            user_info = {
                "phone_number": _clean_phone(message_data.get("from")),
                "name": message_data.get("contact_name") or "Usuário",
                "message_id": message_data.get("message_id"),
                "timestamp": message_data.get("timestamp"),
            }
            phone_number = _clean_phone(user_info.get("phone_number"))

            # BYPASS GLOBAL u-ETG: processa slot_* antes de qualquer guard/roteamento
            if message_data.get("type") == "interactive":
                try:
                    response_id, _title = self._normalize_interactive(message_data.get("interactive") or {})
                except Exception:
                    response_id = ""

                # Mapas de slots + mapeamento canônico
                slot_ids    = {"slot_0730", "slot_1215", "slot_1900"}
                slot_titles = {"07:30": "slot_0730", "12:15": "slot_1215", "19:00": "slot_1900"}
                normalized_id = slot_titles.get(response_id, response_id)

                if normalized_id in slot_ids or str(normalized_id).startswith("slot_"):
                    # autocadastro idempotente
                    patient = self._get_or_create_patient({"phone_number": phone_number, "name": user_info.get("name")})
                    try:
                        if patient and getattr(patient, "is_active", None) is False:
                            patient.is_active = True
                            db.session.commit()
                    except Exception:
                        pass

                    # log opcional (ajuda no diagnóstico)
                    try:
                        self.logger.warning("PATH|BYPASS_GLOBAL|from=%s|slot=%s", phone_number, normalized_id)
                    except Exception:
                        pass

                    return self._handle_uetg_slot_callback(phone_number, normalized_id, patient)



            # Verificar se é mensagem de texto
            if message_data.get("type") == "text":
                return self._handle_text_message(
                    phone_number, message_data.get("text", ""), user_info
                )

            # Verificar se é resposta interativa (botão ou lista)
            elif message_data.get("type") == "interactive":
                return self._handle_interactive_message(
                    phone_number, message_data.get("interactive", {}), user_info
                )

            # Outros tipos de mensagem
            else:
                self.whatsapp_service.send_text_message(
                    phone_number,
                    "Desculpe, não consigo processar este tipo de mensagem. Use apenas texto ou os botões fornecidos.",
                )
                return {"status": "processed", "action": "unsupported_message_type"}

       except Exception as e:
    import traceback
    print(f"Erro ao processar mensagem: {e}")
    print(traceback.format_exc())
    return {"status": "error", "message": str(e)}

    def _handle_text_message(
        self, phone_number: str, message_text: str, user_info: Dict
    ) -> Dict:
        """Processar mensagem de texto"""
        try:
            # Verificar se é comando administrativo
            if self._is_admin(phone_number):
                return self._handle_admin_command(phone_number, message_text, user_info)

            # Verificar comandos básicos
            if message_text.lower() in ["/start", "oi", "olá", "menu"]:
                return self._send_welcome_message(phone_number, user_info)

            # Para pacientes, resposta padrão
            patient = self._get_or_create_patient(user_info)
            if patient:
                self.whatsapp_service.send_text_message(
                    phone_number,
                    "Mensagem recebida! Se você está respondendo a um questionário, use os botões fornecidos.",
                )
                return {"status": "processed", "action": "patient_response_received"}

            return {"status": "processed", "action": "text_message_handled"}

        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem de texto: {e}")
            return {"status": "error", "message": str(e)}

def _handle_interactive_message(self, phone_number: str, interactive_data: Dict[str, Any], user_info: Dict[str, Any]) -> Dict[str, Any]:
    """Processar mensagem interativa (botões/listas) com bypass explícito p/ u-ETG."""
    try:
        pn = _clean_phone(phone_number or "")

        # 1) Normalização robusta do payload
        try:
            self.logger.debug("RAW INTERACTIVE: %s", json.dumps(interactive_data, ensure_ascii=False))
        except Exception:
            pass

        data = interactive_data or {}
        itype = _s(data.get("type"))
        br = data.get("button_reply") or {}
        lr = data.get("list_reply") or {}
        nfm = data.get("nfm_reply") or {}

        rid, title = "", ""
        if itype == "button_reply":
            rid = _s(br.get("id")); title = _s(br.get("title"))
        elif itype == "list_reply":
            rid = _s(lr.get("id")); title = _s(lr.get("title"))
        elif itype == "nfm_reply":
            title = _s(nfm.get("body"))
            rid = _s(nfm.get("response_json")) or title

        response_id = rid or title
        if not response_id:
            self.logger.error("Interactive sem id/title")
            self.whatsapp_service.send_text_message(pn, "Recebi seu clique, mas não identifiquei a opção. Pode tentar novamente?")
            return {"status": "error", "message": "No response ID or title"}

        self.logger.info("Interactive click | from=%s | resp=%s | title=%s", pn, response_id, title or "-")

        # 2) Mapas fixos de slots u-ETG
        slot_ids    = {"slot_0730", "slot_1215", "slot_1900"}
        slot_titles = {"07:30": "slot_0730", "12:15": "slot_1215", "19:00": "slot_1900"}

        # aceitar 1215 / 12h15 / 12:15 → canônico
        hhmm_digits = re.fullmatch(r"\s*(\d{3,4})\s*", response_id or "")
        if hhmm_digits and ":" not in response_id:
            num = hhmm_digits.group(1)
            response_id = f"{int(num[:-2]):02d}:{num[-2:]}" if len(num) == 3 else f"{num[:2]}:{num[2:]}"
        m = re.search(r"(\d{1,2})[:hH]?(\d{2})", response_id or "")
        if m and response_id not in slot_titles and response_id not in slot_ids:
            candidate = f"{int(m.group(1)):02d}:{m.group(2)}"
            response_id = slot_titles.get(candidate, response_id)

        normalized_id = slot_titles.get(response_id, response_id)

        # 3) AUTO-CADASTRO silencioso (idempotente)
        try:
            patient = self._get_or_create_patient({"phone_number": pn, "name": user_info.get("name")})
            try:
                if patient and getattr(patient, "is_active", None) is False:
                    patient.is_active = True
                    db.session.commit()
            except Exception:
                pass
        except Exception:
            self.logger.warning("Auto-cadastro no clique falhou (segue fluxo).", exc_info=True)
            patient = None

        # 4) BYPASS EXPLÍCITO: se for u-ETG, processa AGORA e NÃO passa por guards
        if normalized_id in slot_ids or str(normalized_id).startswith("slot_"):
            return self._handle_uetg_slot_callback(pn, normalized_id, patient)

        # 5) Admin callbacks
        if self._is_admin(pn):
            return self._handle_admin_callback(pn, response_id, user_info)

        # 6) Questionários
        if response_id.startswith(("start_questionnaire_", "questionnaire_")):
            if patient:
                return self._handle_questionnaire_callback(pn, response_id, patient)

        # 7) Medicação
        if response_id.startswith("medication_"):
            if patient:
                return self._handle_medication_callback(pn, response_id, patient)

        # 8) Humor
        if response_id.startswith(("mood_", "start_mood_")):
            if patient:
                return self._handle_mood_callback(pn, response_id, patient)

        # 9) Respiração
        if response_id.startswith(("breathing_", "start_breathing_")):
            if patient:
                return self._handle_breathing_callback(pn, response_id, patient)

        # 10) Lembretes
        if response_id.startswith(("snooze_", "skip_")):
            if patient:
                return self._handle_reminder_action(pn, response_id, patient)

        # 11) Fallback neutro
        self.whatsapp_service.send_text_message(pn, "Opção recebida. Já anotei aqui. ✅")
        return {"status": "processed", "action": "interactive_handled"}

    except Exception as e:
        self.logger.error("Erro no interactive: %s", e)
        self.logger.debug(traceback.format_exc())
        try:
            self.whatsapp_service.send_text_message(_clean_phone(phone_number), "❌ Erro ao processar seu clique. Tente outra vez.")
        except Exception:
            pass
        return {"status": "error", "message": str(e)}
