from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from sqlalchemy.exc import IntegrityError

from src.models.user import db
from src.models.patient import Patient

admin_patient_bp = Blueprint("admin_patient_bp", __name__)

def _normalize_phone(raw: str) -> str:
    if not raw:
        return ""
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("55"):
        digits = "+" + digits
    elif raw.startswith("+"):
        return raw
    else:
        digits = "+55" + digits
    return digits

@admin_patient_bp.route("/patients", methods=["GET"])
def list_patients():
    try:
        limit = int(request.args.get("limit", 20))
    except Exception:
        limit = 20
    q = (
        Patient.query
        .order_by(Patient.created_at.desc())
        .limit(max(1, min(limit, 200)))
        .all()
    )
    return jsonify({"ok": True, "count": len(q), "items": [p.to_dict() for p in q]})

@admin_patient_bp.route("/patients", methods=["POST"])
def create_patient():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return jsonify({"ok": False, "error": "invalid_json"}), 400

    name = (data.get("name") or "").strip()
    phone = _normalize_phone(data.get("phone_e164") or "")
    tags = (data.get("tags") or "").strip()

    if not name or not phone:
        return jsonify({"ok": False, "error": "name and phone_e164 are required"}), 400

    existing = Patient.query.filter_by(phone_e164=phone).first()
    if existing:
        return jsonify({"ok": True, "created": False, "patient": existing.to_dict(), "hint": "already_exists"}), 200

    new_patient = Patient(
        id=uuid.uuid4().hex,
        name=name,
        phone_e164=phone,
        tags=tags,
        active=True,
        created_at=datetime.utcnow(),
    )
    db.session.add(new_patient)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        again = Patient.query.filter_by(phone_e164=phone).first()
        if again:
            return jsonify({"ok": True, "created": False, "patient": again.to_dict(), "hint": "already_exists"}), 200
        return jsonify({"ok": False, "error": "could_not_create"}), 400

    return jsonify({"ok": True, "created": True, "patient": new_patient.to_dict()}), 201
