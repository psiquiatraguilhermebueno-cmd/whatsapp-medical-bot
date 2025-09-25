from flask import Blueprint, request, jsonify
from sqlalchemy import or_, func
from datetime import datetime
import re

from src.models.user import db
from src.admin.models.patient import Patient

admin_patient_bp = Blueprint("admin_patient_bp", __name__)

def _normalize_phone(s):
    s = str(s or "")
    digits = re.sub(r"\D+", "", s)
    if not digits:
        return ""
    if s.startswith("+"):
        return "+" + digits
    return "+" + digits

@admin_patient_bp.route("/patients", methods=["GET"])
def list_patients():
    try:
        limit = int(request.args.get("limit", 20))
    except Exception:
        limit = 20
    rows = (
        Patient.query.order_by(Patient.created_at.desc()).limit(limit).all()
    )
    return jsonify({"ok": True, "count": len(rows), "items": [p.to_dict() for p in rows]})

@admin_patient_bp.route("/patients", methods=["POST"])
def create_patient():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return jsonify({"ok": False, "error": "invalid_json"}), 400

    name = (data.get("name") or "").strip()
    phone = _normalize_phone(data.get("phone_e164"))
    tags = (data.get("tags") or "").strip()

    if not name or not phone:
        return jsonify({"ok": False, "error": "name_and_phone_required"}), 400

    existing = Patient.query.filter_by(phone_e164=phone).first()
    if existing:
        return jsonify({"ok": True, "created": False, "patient": existing.to_dict(), "hint": "already_exists"}), 200

    p = Patient(
        name=name,
        phone_e164=phone,
        tags=tags,
        active=True,
        created_at=datetime.utcnow(),
    )
    db.session.add(p)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        again = Patient.query.filter_by(phone_e164=phone).first()
        if again:
            return jsonify({"ok": True, "created": False, "patient": again.to_dict(), "hint": "already_exists"}), 200
        return jsonify({"ok": False, "error": "could_not_create"}), 400

    return jsonify({"ok": True, "created": True, "patient": p.to_dict()}), 201

@admin_patient_bp.route("/patients/search", methods=["GET"])
def search_patients():
    q = (request.args.get("q") or "").strip()
    try:
        limit = int(request.args.get("limit", 20))
    except Exception:
        limit = 20

    if not q:
        return jsonify({"ok": True, "count": 0, "items": []})

    q_lower = q.lower()
    q_like_lower = f"%{q_lower}%"
    q_digits = re.sub(r"\D+", "", q)

    name_like = func.lower(func.coalesce(Patient.name, "")).like(q_like_lower)
    tags_like = func.lower(func.coalesce(Patient.tags, "")).like(q_like_lower)

    phone_clean = func.replace(
        func.replace(func.replace(func.coalesce(Patient.phone_e164, ""), "+", ""), "-", ""), " ", ""
    )
    filters = [name_like, tags_like]
    if q_digits:
        filters.append(phone_clean.like(f"%{q_digits}%"))

    rows = (
        Patient.query.filter(or_(*filters))
        .order_by(Patient.created_at.desc())
        .limit(limit)
        .all()
    )
    return jsonify({"ok": True, "count": len(rows), "items": [p.to_dict() for p in rows]})
