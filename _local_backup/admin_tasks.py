import os
from flask import Blueprint, request, jsonify
from src.jobs.uetg_scheduler import plan_next_week, send_today

admin_bp = Blueprint('admin_bp', __name__)

def _auth_ok(req):
    token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'verify_123')
    return req.args.get('token') == token

@admin_bp.route('/cron/uetg/plan', methods=['POST'])
def cron_plan():
    if not _auth_ok(request):
        return jsonify({"error":"forbidden"}), 403
    plan_next_week()
    return jsonify({"status":"planned"})

@admin_bp.route('/cron/uetg/send', methods=['POST'])
def cron_send():
    if not _auth_ok(request):
        return jsonify({"error":"forbidden"}), 403
    send_today()
    return jsonify({"status":"sent_try"})
