"""
Webhook integrado para WhatsApp com processamento automático
"""

import os
import re
import json
import logging
from datetime import datetime
import requests

from flask import Blueprint, request, jsonify

# DB e modelos
from sqlalchemy import text as sql_text
from src.models.user import db
from src.models.patient import Patient

# Processador genérico (mantido)
from src.services.response_processor import response_processor

logger = logging.getLogger(__name__)

whatsapp_bp = Blueprint('whatsapp', __name__)

# ---------- Helpers de envio ----------

def send_whatsapp_message(phone: str, message: str) -> bool:
    """Envia mensagem de texto via WhatsApp Business API"""
    try:
        access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')

        if not access_token or not phone_number_id:
            logger.error("Credenciais WhatsApp não configuradas")
            return False

        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": message}
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info(f"[WA] Mensagem enviada para {phone}")
            return True
        else:
            logger.error(f"[WA] Erro ao enviar: {resp.status_code} - {resp.text}")
            return False

    except Exception as e:
        logger.error(f"[WA] Exceção ao enviar: {e}")
        return False


def send_admin_alert(text: str) -> None:
    """Envia alerta para o admin (melhor esforço; não levanta exceção)"""
    admin_phone = os.getenv('ADMIN_PHONE_NUMBER')
    if not admin_phone:
        logger.warning("ADMIN_PHONE_NUMBER não configurado; alerta não enviado")
        return
    ok = send_whatsapp_message(admin_phone, text)
    if not ok:
        logger.error("Falha ao enviar alerta para admin")


def log_uetg_confirmation(phone: str, selected_time: str, patient_name: str) -> None:
    """Grava confirmação no banco (wa_campaign_runs)"""
    try:
        now_iso = datetime.now().isoformat(timespec='seconds')
        payload = json.dumps({
            "selected_time": selected_time,
            "patient_name": patient_name or ""
        })
        db.session.execute(
            sql_text("""
                INSERT INTO wa_campaign_runs
                    (campaign_id, run_at, phone_e164, payload, status)
                VALUES
                    (:cid, :run_at, :phone, :payload, :status)
            """),
            {
                "cid": "uetg-confirm",
                "run_at": now_iso,
                "phone": phone,
                "payload": payload,
                "status": "ok"
            }
        )
        db.session.commit()
        logger.info("[DB] u-ETG confirmação registrada em wa_campaign_runs")
    except Exception as e:
        logger.error(f"[DB] Falha ao registrar confirmação u-ETG: {e}")
        db.session.rollback()


def normalize_time_choice(text: str) -> str | None:
    """
    Aceita variações e normaliza para 'HH:MM'.
    Válidos: 12:15, 12h15, 12.15, 1215; idem 16:40 e 19:00.
    """
    s = re.sub(r"\s+", "", text or "").lower()
    s = s.replace("h", ":").replace(".", ":")
    # vira HH:MM se vier como 4 dígitos
    if re.fullmatch(r"\d{4}", s):
        s = f"{s[:2]}:{s[2:]}"
    valid = {"12:15", "16:40", "19:00"}
    return s if s in valid else None


def handle_uetg_selection(phone: str, text: str) -> bool:
    """
    Processa escolha de horário do u-ETG:
      - confirma para o paciente
      - avisa admin
      - registra no banco
    Retorna True se tratou a mensagem.
    """
    choice = normalize_time_choice(text)
    if not choice:
        return False

    # Tenta obter nome do paciente pelo telefone
    patient_name = None
    try:
        p = Patient.query.filter_by(phone_e164=phone).first()
        if p:
            patient_name = getattr(p, "name", None)
    except Exception as e:
        logger.warning(f"[DB] Falha ao buscar paciente por telefone: {e}")

    # Confirmação para paciente
    msg_patient = (
        "Confirmação u-ETG ✅\n\n"
        f"Horário escolhido: *{choice}* (hoje).\n"
        "Se precisar alterar, responda por aqui."
    )
    send_whatsapp_message(phone, msg_patient)

    # Alerta para o admin
    now_br = datetime.now().strftime("%d/%m %H:%M")
    who = f"{patient_name} ({phone})" if patient_name else phone
    msg_admin = (
        "u-ETG — confirmação recebida\n"
        f"Paciente: {who}\n"
        f"Escolha: {choice}\n"
        f"Carimbo: {now_br}"
    )
    send_admin_alert(msg_admin)

    # Registro no banco
    log_uetg_confirmation(phone, choice, patient_name or "")

    return True

# ---------- Webhook ----------

@whatsapp_bp.route('/api/whatsapp/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    """Webhook principal do WhatsApp"""
    if request.method == 'GET':
        return verify_webhook()
    elif request.method == 'POST':
        return handle_message()


def verify_webhook():
    """Verifica webhook do WhatsApp (GET challenge)"""
    try:
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if verify_token == os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN'):
            logger.info("Webhook verificado com sucesso")
            return challenge
        else:
            logger.warning("Token de verificação inválido")
            return "Token inválido", 403
    except Exception as e:
        logger.error(f"Erro na verificação do webhook: {e}")
        return "Erro interno", 500


def handle_message():
    """Processa mensagens recebidas (POST)"""
    try:
        data = request.get_json()
        if not data or 'entry' not in data:
            return jsonify({"status": "ok"})

        for entry in data['entry']:
            if 'changes' not in entry:
                continue
            for change in entry['changes']:
                if change.get('field') != 'messages':
                    continue

                value = change.get('value', {})
                messages = value.get('messages', [])
                for message in messages:
                    process_incoming_message(message, value)

        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        return jsonify({"status": "error"}), 500


def process_incoming_message(message: dict, value: dict):
    """Processa mensagem individual"""
    try:
        phone = message.get('from')
        msg_type = message.get('type')

        if msg_type != 'text':
            return

        text_body = (message.get('text', {}) or {}).get('body', '')
        text = (text_body or '').strip()

        if not phone or not text:
            return

        logger.info(f"Mensagem recebida de {phone}: {text}")

        # 1) Prioridade: laço de confirmação u-ETG
        if handle_uetg_selection(phone, text):
            return

        # 2) Caso contrário, segue o fluxo padrão
        response_text = response_processor.process_response(phone, text)
        if response_text:
            send_whatsapp_message(phone, response_text)

    except Exception as e:
        logger.error(f"Erro ao processar mensagem individual: {e}")
