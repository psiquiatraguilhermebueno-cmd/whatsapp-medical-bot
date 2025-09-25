# src/routes/admin_patient.py
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from uuid import uuid4

from src.models.user import db
from src.models.patient import Patient

# Este blueprint é registrado no main com url_prefix="/admin/api"
# Vamos aceitar rotas com e sem barra final para evitar 308/405.
admin_patient_bp = Blueprint("admin_patient_bp", __name__)

def _json_or_form(req):
    data = req.get_json(silent=True) or {}
    if not data:
        # fallback para form-urlencoded
        data = {
            "name": req.form.get("name"),
            "phone_e164": req.form.get("phone_e164"),
            "tags": req.form.get("tags"),
        }
    return data

# CREATE (POST) - aceita /admin/api/patients e /admin/api/patients/
@admin_patient_bp.route("/patients", methods=["POST"])
@admin_patient_bp.route("/patients/", methods=["POST"])
def create_patient_admin():
    data = _json_or_form(request)
    name = (data.get("name") or "").strip()
    phone = (data.get("phone_e164") or "").strip()
    tags = (data.get("tags") or "").strip() or None

    if not name or not phone:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "name and phone_e164 are required",
                    "fields": {"name": bool(name), "phone_e164": bool(phone)},
                }
            ),
            400,
        )

    # Evita duplicidade por telefone
    existing = Patient.query.filter_by(phone_e164=phone).first()
    if existing:
        return (
            jsonify({"ok": False, "error": "phone_e164 already exists", "patient": existing.to_dict()}),
            409,
        )

    # Patient.id é String -> usa UUID hex
    patient = Patient(
        id=uuid4().hex,
        name=name,
        phone_e164=phone,
        tags=tags,
        active=True,
    )
    try:
        db.session.add(patient)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"ok": False, "error": "integrity error (unique constraint?)"}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": f"db error: {e}"}), 500

    return jsonify({"ok": True, "patient": patient.to_dict()}), 201


# LIST (GET) - aceita /admin/api/patients e /admin/api/patients/
@admin_patient_bp.route("/patients", methods=["GET"])
@admin_patient_bp.route("/patients/", methods=["GET"])
def list_patients_admin():
    try:
        limit = int(request.args.get("limit", "50"))
        if limit <= 0 or limit > 200:
            limit = 50
    except Exception:
        limit = 50

    q = Patient.query.order_by(Patient.created_at.desc()).limit(limit).all()
    return jsonify({"ok": True, "items": [p.to_dict() for p in q], "count": len(q)}), 200
