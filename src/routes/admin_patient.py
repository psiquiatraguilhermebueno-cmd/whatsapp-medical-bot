# src/routes/admin_patient.py
# (coloque exatamente neste caminho)

import os
import re
import logging
from typing import Dict, Any

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError

from src.models.user import db
from src.models.patient import Patient

logger = logging.getLogger(__name__)

# Este blueprint será montado em main.py com url_prefix="/admin/api"
admin_patient_bp = Blueprint("admin_patient", __name__)

# -----------------------
# Helpers
# -----------------------

def _clean_phone(phone: str) -> str:
    """
    Normaliza telefone para dígitos somente, formato E.164 sem o '+'
    Ex.: "+55 (11) 91234-5678" -> "5511912345678"
    """
    if not isinstance(phone, str):
        return ""
    phone = phone.strip()
    if phone.startswith("+"):
        phone = phone[1:]
    return re.sub(r"\D+", "", phone)

def _extract_payload(req) -> Dict[str, Any]:
    """
    Aceita JSON e form urlencoded (fallback).
    Campos: name, phone, tags (opcional), active (opcional)
    """
    data: Dict[str, Any] = {}
    try:
        if req.is_json:
            data = req.get_json(silent=True) or {}
    except Exception:
        data = {}

    if not data:
        form = req.form or {}
        data = {
            "name": form.get("name", ""),
            "phone": form.get("phone", ""),
            "tags": form.get("tags", ""),
            "active": form.get("active", ""),
        }

    # normaliza tipos
    if not isinstance(data.get("name", ""), str):
        data["name"] = str(data.get("name", ""))
    if not isinstance(data.get("phone", ""), str):
        data["phone"] = str(data.get("phone", ""))
    if not isinstance(data.get("tags", ""), str):
        data["tags"] = str(data.get("tags", ""))

    # ativa por padrão; strings como "false", "0", "no" desativam
    if isinstance(data.get("active"), str):
        data["active"] = data["active"].lower() not in ("false", "0", "no", "off", "")
    if "active" not in data:
        data["active"] = True

    return data

def _ok(payload: Dict[str, Any], status: int = 200):
    return jsonify(payload), status

def _fail(reason: str, detail: str = "", status: int = 400):
    body = {"ok": False, "reason": reason}
    if detail:
        body["detail"] = detail
    return jsonify(body), status

# -----------------------
# Rotas
# -----------------------

@admin_patient_bp.route("/patients/add", methods=["POST"])
def add_patient():
    """
    Alinha com o front: POST /admin/api/patients/add
    Upsert por whatsapp_phone (E.164 sem '+').
    """
    try:
        data = _extract_payload(request)
        name = (data.get("name") or "").strip()
        phone_raw = (data.get("phone") or "").strip()
        tags = (data.get("tags") or "").strip()
        active = bool(data.get("active", True))

        if not name:
            return _fail("validation_error", "Nome é obrigatório", 400)
        if not phone_raw:
            return _fail("validation_error", "Telefone é obrigatório", 400)

        phone_clean = _clean_phone(phone_raw)
        if not phone_clean or len(phone_clean) < 10:
            return _fail("validation_error", "Telefone inválido", 400)

        # Upsert por whatsapp_phone
        patient = Patient.query.filter_by(whatsapp_phone=phone_clean).first()
        created = False
        if patient:
            patient.name = name
            patient.is_active = active
        else:
            patient = Patient(
                name=name,
                whatsapp_phone=phone_clean,
                is_active=active,
            )
            db.session.add(patient)
            created = True

        db.session.commit()

        masked = f"****{phone_clean[-4:]}" if len(phone_clean) >= 4 else "****"
        logger.info("Patient %s: %s (%s)", "created" if created else "updated", name, masked)

        return _ok(
            {
                "ok": True,
                "action": "created" if created else "updated",
                "patient": {
                    "id": patient.id,
                    "name": patient.name,
                    "phone_masked": masked,
                    "is_active": patient.is_active,
                },
            },
            200,
        )

    except SQLAlchemyError as sqle:
        db.session.rollback()
        logger.exception("DB error on add_patient")
        return _fail("db_insert_failed", sqle.__class__.__name__, 500)
    except Exception as e:
        logger.exception("Unexpected error on add_patient")
        return _fail("unexpected_error", e.__class__.__name__, 500)


@admin_patient_bp.route("/patients/status", methods=["GET"])
def patients_status():
    """Diagnóstico simples para o painel."""
    try:
        total = Patient.query.count()
        actives = Patient.query.filter_by(is_active=True).count()
        return _ok({"ok": True, "stats": {"total": total, "active": actives}})
    except Exception as e:
        logger.exception("Status error")
        return _fail("unexpected_error", e.__class__.__name__, 500)
