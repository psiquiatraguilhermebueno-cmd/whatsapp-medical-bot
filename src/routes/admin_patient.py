# src/routes/admin_patient.py
import os
import re
import logging
from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from src.models.user import db
from src.models.patient import Patient

logger = logging.getLogger(__name__)

# OBS: este blueprint é registrado no main com url_prefix="/admin/api"
# Por isso, as rotas abaixo são RELATIVAS (ex.: "/patients").
admin_patient_bp = Blueprint("admin_patient", __name__)

# ----------------- helpers -----------------

def _clean_phone(phone: str) -> str:
    """
    Normaliza telefone para dígitos (formato aceito pelo WhatsApp webhook: 5511999999999).
    Ex.: "+55 (11) 91211-3050" -> "5511912113050"
    """
    if not isinstance(phone, str):
        return ""
    return re.sub(r"\D+", "", phone)

def _validate_admin_secret(req) -> bool:
    """Valida X-Admin-Secret contra APP_SECRET (variável de ambiente)."""
    app_secret = (os.getenv("APP_SECRET") or "").strip()
    if not app_secret:
        return False
    admin_secret = (req.headers.get("X-Admin-Secret") or "").strip()
    return admin_secret == app_secret

def _to_dict(p: Patient) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "phone_number": p.phone_number,
        "whatsapp_phone": p.whatsapp_phone,
        "is_active": bool(getattr(p, "is_active", True)),
        "created_at": p.created_at.isoformat() if getattr(p, "created_at", None) else None,
        "updated_at": p.updated_at.isoformat() if getattr(p, "updated_at", None) else None,
    }

# ----------------- rotas -----------------

@admin_patient_bp.route("/patients", methods=["GET"])
def list_patients():
    """Lista últimos pacientes (até 200)."""
    if not _validate_admin_secret(request):
        return jsonify({"ok": False, "error": "Unauthorized - Invalid X-Admin-Secret"}), 401
    rows = Patient.query.order_by(Patient.created_at.desc()).limit(200).all()
    return jsonify({"ok": True, "patients": [_to_dict(p) for p in rows]})

@admin_patient_bp.route("/patients", methods=["POST"])
def upsert_patient():
    """
    Cria/atualiza paciente por telefone (upsert).
    Aceita JSON ou form. Campos: name (obrigatório), phone (obrigatório).
    Não duplica: se existir por phone_number OU whatsapp_phone, atualiza.
    """
    try:
        if not _validate_admin_secret(request):
            return jsonify({"ok": False, "error": "Unauthorized - Invalid X-Admin-Secret"}), 401

        data = request.get_json(silent=True) or request.form.to_dict() or {}
        name = (data.get("name") or "").strip()
        raw_phone = (data.get("phone") or data.get("phone_e164") or "").strip()

        if not name:
            return jsonify({"ok": False, "reason": "validation", "detail": "name_required"}), 400
        phone = _clean_phone(raw_phone)
        if not phone:
            return jsonify({"ok": False, "reason": "validation", "detail": "invalid_phone"}), 400

        # upsert por qualquer um dos campos de telefone
        existing = (
            Patient.query.filter(
                or_(Patient.phone_number == phone, Patient.whatsapp_phone == phone)
            )
            .order_by(Patient.id.asc())
            .first()
        )

        if existing:
            existing.name = name
            existing.phone_number = phone
            existing.whatsapp_phone = phone
            if hasattr(existing, "is_active"):
                existing.is_active = True
            db.session.commit()
            logger.info("Updated patient id=%s phone=%s", existing.id, phone)
            return jsonify({"ok": True, "mode": "updated", "patient": _to_dict(existing)})

        p = Patient(
            name=name,
            phone_number=phone,
            whatsapp_phone=phone,
            is_active=True,
        )
        db.session.add(p)
        db.session.commit()
        logger.info("Created patient id=%s phone=%s", p.id, phone)
        return jsonify({"ok": True, "mode": "created", "patient": _to_dict(p)})

    except Exception as e:
        logger.exception("db_insert_failed")
        return jsonify({"ok": False, "reason": "db_insert_failed", "detail": str(e)}), 500

@admin_patient_bp.route("/patient/register", methods=["POST"])
def register_patient_compat():
    """
    Compatibilidade com versões antigas do Admin que chamavam /api/admin/patient/register.
    Neste projeto o blueprint é prefixado por /admin/api, então a rota final é:
    POST /admin/api/patient/register
    """
    return upsert_patient()

@admin_patient_bp.route("/patients/status", methods=["GET"])
def patient_status():
    """Estatísticas simples e checagem do admin cadastrado."""
    if not _validate_admin_secret(request):
        return jsonify({"ok": False, "error": "Unauthorized - Invalid X-Admin-Secret"}), 401

    total = Patient.query.count()
    active = Patient.query.filter_by(is_active=True).count()

    admin_phone_cfg = (os.getenv("ADMIN_PHONE_NUMBER") or "").strip()
    admin_clean = _clean_phone(admin_phone_cfg)
    admin_registered = False
    if admin_clean:
        admin_row = Patient.query.filter(
            or_(Patient.phone_number == admin_clean, Patient.whatsapp_phone == admin_clean)
        ).first()
        admin_registered = bool(admin_row and getattr(admin_row, "is_active", True))

    return jsonify({
        "ok": True,
        "stats": {
            "total_patients": total,
            "active_patients": active,
            "admin_registered": admin_registered,
            "admin_phone_configured": bool(admin_clean),
        }
    })

@admin_patient_bp.route("/seed-patient", methods=["POST"])
def seed_patient():
    """(Utilitário) Garante paciente ADMIN ativo a partir de ADMIN_PHONE_NUMBER."""
    try:
        if not _validate_admin_secret(request):
            return jsonify({"ok": False, "error": "Unauthorized - Invalid X-Admin-Secret"}), 401

        admin_phone_cfg = (os.getenv("ADMIN_PHONE_NUMBER") or "").strip()
        admin_clean = _clean_phone(admin_phone_cfg)
        if not admin_clean:
            return jsonify({"ok": False, "reason": "config", "detail": "ADMIN_PHONE_NUMBER missing/invalid"}), 500

        existing = Patient.query.filter(
            or_(Patient.phone_number == admin_clean, Patient.whatsapp_phone == admin_clean)
        ).first()

        if existing:
            if hasattr(existing, "is_active"):
                existing.is_active = True
            mode = "reactivated"
            p = existing
        else:
            p = Patient(
                name="Dr. Admin",
                phone_number=admin_clean,
                whatsapp_phone=admin_clean,
                is_active=True,
            )
            db.session.add(p)
            mode = "created"

        db.session.commit()
        logger.info("Admin patient %s (id=%s phone=%s)", mode, p.id, admin_clean)
        mask = ("****" + admin_clean[-4:]) if len(admin_clean) >= 4 else "****"
        return jsonify({"ok": True, "mode": mode, "patient": _to_dict(p), "phone_masked": mask})

    except Exception as e:
        logger.exception("seed_failed")
        return jsonify({"ok": False, "reason": "seed_failed", "detail": str(e)}), 500
