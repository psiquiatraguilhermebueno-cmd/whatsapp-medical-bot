from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

# Criar blueprint
admin_tasks_bp = Blueprint('admin_tasks', __name__)

@admin_tasks_bp.route('/health', methods=['GET'])
def health():
    """Health check para admin tasks"""
    return jsonify({
        'status': 'ok',
        'service': 'admin_tasks'
    })

@admin_tasks_bp.route('/test', methods=['GET'])
def test():
    """Endpoint de teste"""
    return jsonify({
        'message': 'Admin tasks funcionando!',
        'status': 'success'
    })

@admin_tasks_bp.route('/force-uetg-plan', methods=['POST'])
def force_uetg_plan():
    """Forçar planejamento u-ETG"""
    try:
        from src.jobs.uetg_scheduler import force_plan
        result = force_plan()
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Planejamento u-ETG executado com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Falha no planejamento u-ETG'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in force u-ETG plan: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_tasks_bp.route('/force-uetg-send', methods=['POST'])
def force_uetg_send():
    """Forçar envio u-ETG"""
    try:
        from src.jobs.uetg_scheduler import force_send
        result = force_send()
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Envio u-ETG executado com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Falha no envio u-ETG'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in force u-ETG send: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_tasks_bp.route("/_routes", methods=["GET"])
def _list_routes():
    from flask import current_app, jsonify
    rules = []
    for r in current_app.url_map.iter_rules():
        methods = sorted([m for m in r.methods if m not in ("HEAD","OPTIONS")])
        rules.append({"rule": str(r), "endpoint": r.endpoint, "methods": methods})
    rules = sorted(rules, key=lambda x: x["rule"])
    return jsonify({"ok": True, "routes": rules})
from flask import request, jsonify
from importlib import import_module
from src.models.patient import Patient



@admin_tasks_bp.route("/patients/<int:patient_id>/send-test", methods=["POST"])
def admin_send_test_message(patient_id):
    from flask import request, jsonify
    from src.models.patient import Patient
    p = Patient.query.get(patient_id)
    if not p:
        return jsonify({"ok": False, "error": "not_found"}), 404
    text = (request.get_json(silent=True) or {}).get("text") or "Mensagem de teste ✅"
    try:
        from src.services.whatsapp_admin_service import WhatsAppService
        svc = WhatsAppService()
        if hasattr(svc, "send_text_message"):
            svc.send_text_message(p.phone_e164, text)
        elif hasattr(svc, "send_message"):
            svc.send_message(p.phone_e164, text)
        else:
            return jsonify({"ok": False, "error": "no_send_method"}), 500
        return jsonify({"ok": True, "delivered": True, "patient": p.to_dict(), "text": text}), 200
    except Exception as e:
        return jsonify({"ok": True, "delivered": False, "patient": p.to_dict(), "text": text, "detail": str(e)}), 200



@admin_tasks_bp.route("/admin/api/force-uetg-plan", methods=["POST"])
def force_uetg_plan():
    from flask import jsonify
    import importlib
    try:
        m = importlib.import_module("src.jobs.uetg_scheduler")
    except Exception as e:
        return jsonify({"success": False, "error": f"import_module: {e}"}), 200
    fn = getattr(m, "plan_next_week", None) or getattr(m, "force_plan", None) or getattr(m, "plan", None)
    if not callable(fn):
        return jsonify({"success": False, "error": "no_plan_function", "candidates": [n for n in dir(m) if "plan" in n]}), 200
    try:
        rv = fn()
        return jsonify({"success": True, "result": str(rv) if rv is not None else None}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 200


@admin_tasks_bp.route("/admin/api/force-uetg-send", methods=["POST"])
def force_uetg_send():
    from flask import jsonify
    import importlib
    try:
        m = importlib.import_module("src.jobs.uetg_scheduler")
    except Exception as e:
        return jsonify({"success": False, "error": f"import_module: {e}"}), 200
    fn = getattr(m, "send_today", None) or getattr(m, "force_send", None) or getattr(m, "send", None)
    if not callable(fn):
        return jsonify({"success": False, "error": "no_send_function", "candidates": [n for n in dir(m) if "send" in n or "dispatch" in n]}), 200
    try:
        rv = fn()
        return jsonify({"success": True, "result": str(rv) if rv is not None else None}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 200
