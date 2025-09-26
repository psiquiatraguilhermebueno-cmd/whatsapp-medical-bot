import re
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, or_, cast, String

from src.models.user import db
from src.models.patient import Patient

admin_patient_bp = Blueprint("admin_patient_bp", __name__)

def _normalize_phone(s):
    digits = re.sub(r"\D+", "", s or "")
    return f"+{digits}" if digits else ""

@admin_patient_bp.route("/patients", methods=["GET"])
def list_patients():
    try:
        limit = int(request.args.get("limit", 10))
    except Exception:
        limit = 10
    q = (
        Patient.query.order_by(Patient.created_at.desc())
        .limit(max(1, min(limit, 100)))
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
    except IntegrityError as e:
        db.session.rollback()
        again = Patient.query.filter_by(phone_e164=phone).first()
        if again:
            return jsonify({"ok": True, "created": False, "patient": again.to_dict(), "hint": "already_exists"}), 200
        return jsonify({"ok": False, "error": "integrity_error", "detail": str(getattr(e, "orig", e))}), 409
    return jsonify({"ok": True, "created": True, "patient": p.to_dict()}), 201

@admin_patient_bp.route("/patients/<int:patient_id>", methods=["GET"])
def get_patient(patient_id):
    p = Patient.query.get(patient_id)
    if not p:
        return jsonify({"ok": False, "error": "not_found"}), 404
    return jsonify({"ok": True, "patient": p.to_dict()}), 200

@admin_patient_bp.route("/patients/<int:patient_id>", methods=["DELETE"])
def delete_patient(patient_id):
    p = Patient.query.get(patient_id)
    if not p:
        return jsonify({"ok": False, "error": "not_found"}), 404
    db.session.delete(p)
    db.session.commit()
    return jsonify({"ok": True, "deleted": True, "id": patient_id}), 200

@admin_patient_bp.route("/patients/search", methods=["GET"])
def search_patients():
    q = (request.args.get("q") or "").strip()
    try:
        limit = int(request.args.get("limit", 10))
    except Exception:
        limit = 10
    limit = max(1, min(limit, 50))
    if not q:
        return jsonify({"ok": True, "count": 0, "items": []})
    q_lower = q.lower()
    q_like_lower = f"%{q_lower}%"
    q_digits = re.sub(r"\D+", "", q)
    name_like = func.lower(func.coalesce(Patient.name, "")).like(q_like_lower)
    tags_like = func.lower(func.coalesce(Patient.tags, "")).like(q_like_lower)
    phone_text = cast(Patient.phone_e164, String)
    phone_clean = func.replace(func.replace(func.replace(func.coalesce(phone_text, ""), "+", ""), "-", ""), " ", "")
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
@admin_patient_bp.route("/patients/<int:patient_id>", methods=["PUT","PATCH"])
def update_patient(patient_id):
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return jsonify({"ok": False, "error": "invalid_json"}), 400

    p = Patient.query.get(patient_id)
    if not p:
        return jsonify({"ok": False, "error": "not_found"}), 404

    name = data.get("name")
    phone = data.get("phone_e164")
    tags = data.get("tags")
    active = data.get("active")

    if name is not None:
        p.name = (name or "").strip()

    if phone is not None:
        phone = _normalize_phone(phone)
        other = Patient.query.filter(Patient.phone_e164 == phone, Patient.id != p.id).first()
        if other:
            return jsonify({"ok": False, "error": "phone_in_use"}), 409
        p.phone_e164 = phone

    if tags is not None:
        p.tags = (tags or "").strip()

    if active is not None:
        p.active = bool(active)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"ok": False, "error": "could_not_update"}), 400

    return jsonify({"ok": True, "updated": True, "patient": p.to_dict()}), 200
@admin_patient_bp.route("/patients/export.csv", methods=["GET"])
def export_patients_csv():
    import csv, io
    rows = Patient.query.order_by(Patient.created_at.desc()).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id","name","phone_e164","tags","active","created_at"])
    for p in rows:
        w.writerow([
            p.id,
            p.name or "",
            p.phone_e164 or "",
            p.tags or "",
            1 if p.active else 0,
            p.created_at.isoformat() if getattr(p, "created_at", None) else "",
        ])
    from flask import Response
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition":"attachment; filename=patients.csv"}
    )
