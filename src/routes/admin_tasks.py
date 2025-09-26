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
    p = Patient.query.get(patient_id)
    if not p:
        return jsonify({"ok": False, "error": "not_found"}), 404
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or f"Olá {p.name}, esta é uma mensagem de teste.").strip()

    delivered = False
    detail = None

    # Tenta enviar usando serviços existentes, mas sem quebrar se não houver
    for mod_name in ("src.services.whatsapp_admin_service", "src.services.whatsapp_service"):
        try:
            m = import_module(mod_name)
            for fn_name in ("send_text", "send_message", "send_whatsapp_message"):
                fn = getattr(m, fn_name, None)
                if callable(fn):
                    fn(p.phone_e164, text)
                    delivered = True
                    break
            if delivered:
                break
            # tenta classe de serviço comum
            for cls_name in ("WhatsappAdminService", "WhatsAppAdminService", "WhatsappService", "WhatsAppService"):
                cls = getattr(m, cls_name, None)
                if cls:
                    try:
                        svc = cls()
                        if hasattr(svc, "send_message"):
                            svc.send_message(p.phone_e164, text)
                            delivered = True
                            break
                    except Exception as e:
                        detail = str(e)
            if delivered:
                break
        except Exception as e:
            detail = str(e)

    return jsonify({
        "ok": True,
        "delivered": delivered,
        "patient": p.to_dict(),
        "text": text,
        "detail": detail
    }), 200
