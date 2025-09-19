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

