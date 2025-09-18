"""
Endpoints administrativos para controle manual do sistema u-ETG
"""

import os
from flask import Blueprint, request, jsonify
from src.jobs.uetg_scheduler import (
    plan_next_week,
    send_today,
    load_plan,
    load_confirmations,
)

admin_bp = Blueprint("admin", __name__)

# Token de segurança para endpoints administrativos
ADMIN_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "verify_123")


def verify_admin_token():
    """Verifica se o token de admin está correto"""
    token = request.args.get("token")
    if token != ADMIN_TOKEN:
        return False
    return True


@admin_bp.route("/cron/uetg/plan", methods=["POST"])
def force_plan():
    """Força o sorteio da próxima semana"""
    try:
        if not verify_admin_token():
            return jsonify({"error": "Token inválido"}), 403

        result = plan_next_week()

        if result:
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Sorteio realizado com sucesso",
                        "timestamp": plan_next_week.__name__,
                    }
                ),
                200,
            )
        else:
            return (
                jsonify({"status": "error", "message": "Erro ao realizar sorteio"}),
                500,
            )

    except Exception as e:
        return jsonify({"status": "error", "message": f"Erro interno: {str(e)}"}), 500


@admin_bp.route("/cron/uetg/send", methods=["POST"])
def force_send():
    """Força o envio do lembrete para hoje"""
    try:
        if not verify_admin_token():
            return jsonify({"error": "Token inválido"}), 403

        result = send_today()

        if result:
            return (
                jsonify(
                    {"status": "success", "message": "Lembrete enviado com sucesso"}
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "status": "info",
                        "message": "Hoje não é um dia sorteado ou erro no envio",
                    }
                ),
                200,
            )

    except Exception as e:
        return jsonify({"status": "error", "message": f"Erro interno: {str(e)}"}), 500


@admin_bp.route("/uetg/status", methods=["GET"])
def get_status():
    """Retorna o status atual do sistema u-ETG"""
    try:
        if not verify_admin_token():
            return jsonify({"error": "Token inválido"}), 403

        plan = load_plan()
        confirmations = load_confirmations()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "current_plan": plan,
                        "confirmations": confirmations,
                        "admin_phone": os.getenv("ADMIN_PHONE_NUMBER"),
                        "patient_phone": os.getenv("UETG_PATIENT_PHONE"),
                        "patient_name": os.getenv("UETG_PATIENT_NAME"),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": f"Erro interno: {str(e)}"}), 500


@admin_bp.route("/uetg/config", methods=["POST"])
def update_config():
    """Atualiza configurações do paciente u-ETG"""
    try:
        if not verify_admin_token():
            return jsonify({"error": "Token inválido"}), 403

        data = request.get_json()

        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400

        # Por enquanto, apenas retorna as configurações atuais
        # Em uma versão futura, poderia atualizar variáveis de ambiente

        return (
            jsonify(
                {
                    "status": "info",
                    "message": "Configurações são gerenciadas via variáveis de ambiente no Railway",
                    "current_config": {
                        "patient_phone": os.getenv("UETG_PATIENT_PHONE"),
                        "patient_name": os.getenv("UETG_PATIENT_NAME"),
                        "default_slot": os.getenv("UETG_DEFAULT_SLOT"),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": f"Erro interno: {str(e)}"}), 500


@admin_bp.route("/health", methods=["GET"])
def health_check():
    """Endpoint de health check"""
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "uETG Admin API",
                "timestamp": "2024-01-01T00:00:00Z",
            }
        ),
        200,
    )
