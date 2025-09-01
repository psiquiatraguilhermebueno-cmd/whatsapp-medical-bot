# src/services/whatsapp_service.py
import os
import re
import json
import logging
from typing import Any, Dict, Optional, List

import requests

logger = logging.getLogger(__name__)

API_BASE = "https://graph.facebook.com/v20.0"

def _s(v, default: str = "") -> str:
    """strip seguro: se for string, .strip(); senão, default."""
    return v.strip() if isinstance(v, str) else default

def _clean_phone(pn: Optional[str]) -> str:
    """E.164 sem '+', apenas dígitos."""
    if not isinstance(pn, str):
        return ""
    pn = pn.strip()
    if pn.startswith("+"):
        pn = pn[1:]
    return re.sub(r"\D+", "", pn)

def _headers() -> Dict[str, str]:
    token = os.getenv("WHATSAPP_TOKEN") or os.getenv("WHATSAPP_ACCESS_TOKEN") or ""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

def _phone_id() -> str:
    # Principal e alternativo (você tem dois IDs)
    return (
        _s(os.getenv("WHATSAPP_PHONE_NUMBER_ID"))
        or _s(os.getenv("WABA_PHONE_ID"))
        or _s(os.getenv("ALT_WHATSAPP_PHONE_NUMBER_ID"))
        or _s(os.getenv("ALT_WABA_PHONE_ID"))
    )

class WhatsAppService:
    """Serviço de integração com WhatsApp Cloud API (robusto contra None)."""

    # ---------------- PARSE WEBHOOK ----------------

    def parse_webhook_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Devolve sempre:
        {
          "type": str, "from": str, "text": str, "message_id": str,
          "timestamp": str, "contact_name": str, "interactive": dict
        }
        """
        try:
            entry = (payload.get("entry") or [{}])[0]
            change = (entry.get("changes") or [{}])[0]
            value  = change.get("value") or {}

            messages = value.get("messages") or []
            if not messages:
                logger.debug("parse_webhook_message: sem 'messages' no payload")
                return {}

            msg = messages[0]

            msg_type = _s(msg.get("type"))
            frm      = _clean_phone(msg.get("from"))
            mid      = _s(msg.get("id") or msg.get("message_id"))
            ts       = _s(msg.get("timestamp"))

            # Nome do contato (se disponível)
            contacts = value.get("contacts") or []
            cname = ""
            if contacts and isinstance(contacts[0], dict):
                profile = contacts[0].get("profile") or {}
                cname = _s(profile.get("name"))

            # Texto pode vir como {"body": "..."} — padronizamos em string
            txt = msg.get("text")
            if isinstance(txt, dict):
                txt = _s(txt.get("body"))
            else:
                txt = _s(txt)

            # Interactive (button_reply / list_reply / nfm_reply) — garantir dict
            interactive = msg.get("interactive")
            if not isinstance(interactive, dict):
                interactive = {}

            out = {
                "type": msg_type,
                "from": frm,
                "text": txt,
                "message_id": mid,
                "timestamp": ts,
                "contact_name": cname,
                "interactive": interactive,
            }
            logger.debug("parse_webhook_message OUT: %s", json.dumps(out, ensure_ascii=False))
            return out

        except Exception as e:
            logger.error("parse_webhook_message error: %s", e, exc_info=True)
            # Retorne estrutura segura para não quebrar o handler
            return {
                "type": "",
                "from": "",
                "text": "",
                "message_id": "",
                "timestamp": "",
                "contact_name": "",
                "interactive": {},
            }

    # ---------------- READ STATUS ----------------

    def mark_message_as_read(self, message_id: Optional[str]) -> Dict[str, Any]:
        message_id = _s(message_id)
        pid = _phone_id()
        if not pid or not message_id:
            logger.debug("mark_message_as_read: faltando phone_id ou message_id")
            return {"ok": False, "error": "missing_parameters"}

        url = f"{API_BASE}/{pid}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        try:
            r = requests.post(url, headers=_headers(), data=json.dumps(payload), timeout=15)
            ok = 200 <= r.status_code < 300
            if not ok:
                logger.warning("mark_message_as_read falhou | status=%s | body=%s", r.status_code, r.text)
            return {"ok": ok, "status": r.status_code, "data": r.json() if ok else r.text}
        except Exception as e:
            logger.error("mark_message_as_read exception: %s", e, exc_info=True)
            return {"ok": False, "error": str(e)}

    # ---------------- SEND TEXT ----------------

    def send_text_message(self, to: Optional[str], body: Optional[str]) -> Dict[str, Any]:
        to = _clean_phone(to)
        body = _s(body) or " "
        pid = _phone_id()

        if not to or not pid:
            logger.error("send_text_message: parâmetros inválidos | to=%s pid=%s", to, pid)
            return {"ok": False, "error": "invalid_parameters"}

        url = f"{API_BASE}/{pid}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }
        try:
            r = requests.post(url, headers=_headers(), data=json.dumps(payload), timeout=15)
            ok = 200 <= r.status_code < 300
            if not ok:
                logger.error("WA send_text falhou | status=%s | body=%s", r.status_code, r.text)
            else:
                logger.info("WA send_text OK | to=%s", to)
            return {"ok": ok, "status": r.status_code, "data": r.json() if ok else r.text}
        except Exception as e:
            logger.error("send_text_message exception: %s", e, exc_info=True)
            return {"ok": False, "error": str(e)}

    # ---------------- SEND INTERACTIVE (BUTTONS) ----------------

    def send_interactive_message(
        self,
        to: Optional[str],
        header_text: Optional[str],
        body_text: Optional[str],
        buttons: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        to = _clean_phone(to)
        header_text = _s(header_text)
        body_text = _s(body_text) or " "
        pid = _phone_id()

        if not to or not pid:
            logger.error("send_interactive_message: parâmetros inválidos | to=%s pid=%s", to, pid)
            return {"ok": False, "error": "invalid_parameters"}

        # Sanitiza botões
        safe_buttons = []
        for b in (buttons or []):
            if not isinstance(b, dict):
                continue
            rid = _s(b.get("id"))
            ttl = _s(b.get("title"))
            if not rid and not ttl:
                continue
            safe_buttons.append({"type": "reply", "reply": {"id": rid or ttl or "opt", "title": ttl or rid or "Opção"}})

        interactive = {
            "type": "button",
            "body": {"text": body_text},
            "action": {"buttons": safe_buttons or [{"type":"reply","reply":{"id":"opt","title":"OK"}}]},
        }
        if header_text:
            interactive["header"] = {"type": "text", "text": header_text}

        url = f"{API_BASE}/{pid}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }

        try:
            r = requests.post(url, headers=_headers(), data=json.dumps(payload), timeout=15)
            ok = 200 <= r.status_code < 300
            if not ok:
                logger.error("WA send_buttons falhou | status=%s | body=%s", r.status_code, r.text)
            else:
                logger.info("WA send_buttons OK | to=%s", to)
            return {"ok": ok, "status": r.status_code, "data": r.json() if ok else r.text}
        except Exception as e:
            logger.error("send_interactive_message exception: %s", e, exc_info=True)
            return {"ok": False, "error": str(e)}
