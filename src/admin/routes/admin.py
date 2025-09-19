import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from sqlalchemy import desc, func
from src.admin.models.campaign import WACampaign, WACampaignRecipient, WACampaignRun
from src.admin.models.patient import AdminPatient
from src.admin.services.campaign_service import CampaignService
from src.admin.services.whatsapp_service import AdminWhatsAppService
from src.models.user import db

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../templates')

# Configuração
ADMIN_TOKEN = os.getenv('ADMIN_UI_TOKEN', '').strip()

def require_auth(f):
    """Decorator para exigir autenticação admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar token no header
        token = request.headers.get('X-Admin-Token', '').strip()
        
        # Verificar token na sessão (para páginas web)
        if not token:
            token = session.get('admin_token', '').strip()
        
        # Verificar token nos cookies
        if not token:
            token = request.cookies.get('admin_token', '').strip()
        
        if not ADMIN_TOKEN:
            return jsonify({'error': 'Admin token not configured'}), 500
            
        if not token or token != ADMIN_TOKEN:
            if request.is_json or request.path.startswith('/admin/api/'):
                return jsonify({'error': 'Unauthorized'}), 401
            else:
                return redirect(url_for('admin.login'))
        
        return f(*args, **kwargs)
    return decorated_function

# Páginas Web
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        
        if not ADMIN_TOKEN:
            flash('Sistema não configurado', 'error')
            return render_template('login.html')
        
        if token == ADMIN_TOKEN:
            session['admin_token'] = token
            flash('Login realizado com sucesso', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Token inválido', 'error')
    
    return render_template('login.html')

@admin_bp.route('/logout')
def logout():
    """Logout"""
    session.pop('admin_token', None)
    flash('Logout realizado com sucesso', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@require_auth
def dashboard():
    """Dashboard principal"""
    return render_template('dashboard.html')

@admin_bp.route('/campaigns')
@require_auth
def campaigns():
    """Lista de campanhas"""
    return render_template('campaigns.html')

@admin_bp.route('/campaigns/new')
@require_auth
def new_campaign():
    """Nova campanha"""
    return render_template('campaign_form.html')

@admin_bp.route('/campaigns/<campaign_id>')
@require_auth
def campaign_detail(campaign_id):
    """Detalhes da campanha"""
    return render_template('campaign_detail.html', campaign_id=campaign_id)

@admin_bp.route('/patients')
@require_auth
def patients():
    """Lista de pacientes"""
    return render_template('patients.html')

@admin_bp.route('/patients/new')
@require_auth
def new_patient():
    """Novo paciente"""
    return render_template('patient_form.html')

@admin_bp.route('/logs')
@require_auth
def logs():
    """Logs do sistema"""
    return render_template('logs.html')

@admin_bp.route('/health')
@require_auth
def health():
    """Health check"""
    return render_template('health.html')

@admin_bp.route('/settings')
@require_auth
def settings():
    """Configurações"""
    return render_template('settings.html')

# API Endpoints
@admin_bp.route('/api/stats')
@require_auth
def api_stats():
    """Estatísticas básicas para sidebar"""
    try:
        campaigns_count = WACampaign.query.count()
        patients_count = AdminPatient.query.filter_by(active=True).count()
        
        return jsonify({
            'success': True,
            'campaigns_count': campaigns_count,
            'patients_count': patients_count
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/dashboard/stats')
@require_auth
def api_dashboard_stats():
    """Estatísticas detalhadas do dashboard"""
    try:
        # Contadores básicos
        total_campaigns = WACampaign.query.count()
        active_campaigns = WACampaign.query.filter_by(status='active').count()
        total_patients = AdminPatient.query.count()
        active_patients = AdminPatient.query.filter_by(active=True).count()
        
        # Mensagens hoje
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        messages_today = WACampaignRun.query.filter(
            WACampaignRun.run_at >= today_start,
            WACampaignRun.run_at <= today_end
        ).count()
        
        # Taxa de sucesso hoje
        success_today = WACampaignRun.query.filter(
            WACampaignRun.run_at >= today_start,
            WACampaignRun.run_at <= today_end,
            WACampaignRun.status == 'ok'
        ).count()
        
        success_rate = round((success_today / messages_today * 100) if messages_today > 0 else 0, 1)
        
        # Próxima execução
        campaign_service = CampaignService()
        next_execution = None
        next_campaign = None
        
        active_campaigns_list = WACampaign.query.filter_by(status='active').all()
        earliest_execution = None
        earliest_campaign = None
        
        for campaign in active_campaigns_list:
            executions = campaign_service.get_next_executions(campaign, limit=1)
            if executions:
                if not earliest_execution or executions[0] < earliest_execution:
                    earliest_execution = executions[0]
                    earliest_campaign = campaign.name
        
        if earliest_execution:
            next_execution = earliest_execution.strftime('%d/%m %H:%M')
            next_campaign = earliest_campaign
        
        return jsonify({
            'success': True,
            'stats': {
                'total_campaigns': total_campaigns,
                'active_campaigns': active_campaigns,
                'total_patients': total_patients,
                'active_patients': active_patients,
                'messages_today': messages_today,
                'success_rate': success_rate,
                'next_execution': next_execution,
                'next_campaign': next_campaign
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/dashboard/recent')
@require_auth
def api_dashboard_recent():
    """Atividade recente para dashboard"""
    try:
        # Campanhas recentes
        recent_campaigns = WACampaign.query.order_by(desc(WACampaign.created_at)).limit(5).all()
        
        # Execuções recentes
        recent_runs = db.session.query(
            WACampaignRun,
            WACampaign.name.label('campaign_name')
        ).join(WACampaign).order_by(desc(WACampaignRun.run_at)).limit(10).all()
        
        # Formatar dados
        campaigns_data = []
        for campaign in recent_campaigns:
            campaigns_data.append({
                'id': str(campaign.id),
                'name': campaign.name,
                'template_name': campaign.template_name,
                'frequency': campaign.frequency,
                'status': campaign.status
            })
        
        runs_data = []
        for run, campaign_name in recent_runs:
            # Mascarar telefone
            phone_masked = f"****{run.phone_e164[-4:]}" if len(run.phone_e164) >= 4 else "****"
            
            runs_data.append({
                'id': run.id,
                'campaign_name': campaign_name,
                'phone_masked': phone_masked,
                'run_at': run.run_at.isoformat() if run.run_at else None,
                'status': run.status
            })
        
        return jsonify({
            'success': True,
            'recent_campaigns': campaigns_data,
            'recent_runs': runs_data
        })
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/test-template', methods=['POST'])
@require_auth
def api_test_template():
    """Testar envio de template"""
    try:
        # Número do admin
        admin_phone = os.getenv('ADMIN_PHONE_NUMBER', '5514997799022').strip()
        if admin_phone.startswith('+'):
            admin_phone = admin_phone[1:]
        
        # Serviço WhatsApp
        whatsapp_service = AdminWhatsAppService()
        
        if not whatsapp_service.validate_credentials():
            return jsonify({
                'success': False,
                'error': 'WhatsApp credentials not configured'
            }), 500
        
        # Enviar template de teste
        result = whatsapp_service.send_template(
            phone_e164=admin_phone,
            template_name='uetg_paciente_agenda_ptbr',
            lang_code='pt_BR',
            params={
                '1': 'Admin',
                '2': datetime.now().strftime('%d/%m/%Y')
            }
        )
        
        if result['success']:
            logger.info(f"Test template sent successfully to admin")
            return jsonify({
                'success': True,
                'message': 'Template de teste enviado com sucesso',
                'message_id': result.get('message_id')
            })
        else:
            logger.error(f"Test template failed: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Erro desconhecido')
            }), 400
            
    except Exception as e:
        logger.error(f"Error testing template: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/campaigns', methods=['GET'])
@require_auth
def api_campaigns_list():
    """Listar campanhas"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        campaigns = WACampaign.query.order_by(desc(WACampaign.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        campaigns_data = []
        campaign_service = CampaignService()
        
        for campaign in campaigns.items:
            # Próximas execuções
            next_executions = campaign_service.get_next_executions(campaign, limit=3)
            next_executions_formatted = [
                exec_dt.strftime('%d/%m/%Y %H:%M') for exec_dt in next_executions
            ]
            
            # Contadores
            total_recipients = WACampaignRecipient.query.filter_by(campaign_id=campaign.id).count()
            total_runs = WACampaignRun.query.filter_by(campaign_id=campaign.id).count()
            success_runs = WACampaignRun.query.filter_by(campaign_id=campaign.id, status='ok').count()
            
            campaigns_data.append({
                **campaign.to_dict(),
                'total_recipients': total_recipients,
                'total_runs': total_runs,
                'success_runs': success_runs,
                'next_executions': next_executions_formatted
            })
        
        return jsonify({
            'success': True,
            'campaigns': campaigns_data,
            'pagination': {
                'page': campaigns.page,
                'pages': campaigns.pages,
                'per_page': campaigns.per_page,
                'total': campaigns.total,
                'has_next': campaigns.has_next,
                'has_prev': campaigns.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/campaigns', methods=['POST'])
@require_auth
def api_campaigns_create():
    """Criar nova campanha"""
    try:
        data = request.get_json()
        
        # Validações básicas
        required_fields = ['name', 'template_name', 'frequency', 'start_at', 'send_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Campo {field} é obrigatório'}), 400
        
        # Criar campanha
        campaign = WACampaign(
            name=data['name'],
            template_name=data['template_name'],
            lang_code=data.get('lang_code', 'pt_BR'),
            params_mode=data.get('params_mode', 'fixed'),
            fixed_params=data.get('fixed_params'),
            tz=data.get('tz', 'America/Sao_Paulo'),
            start_at=datetime.fromisoformat(data['start_at'].replace('Z', '+00:00')),
            end_at=datetime.fromisoformat(data['end_at'].replace('Z', '+00:00')) if data.get('end_at') else None,
            frequency=data['frequency'],
            days_of_week=data.get('days_of_week'),
            day_of_month=data.get('day_of_month'),
            send_time=datetime.strptime(data['send_time'], '%H:%M').time(),
            cron_expr=data.get('cron_expr'),
            status='active'
        )
        
        db.session.add(campaign)
        db.session.flush()  # Para obter o ID
        
        # Adicionar destinatários
        recipients = data.get('recipients', [])
        for recipient_data in recipients:
            if isinstance(recipient_data, str):
                # Formato simples: apenas telefone
                phone = recipient_data.strip()
                if phone.startswith('+'):
                    phone = phone[1:]
                
                recipient = WACampaignRecipient(
                    campaign_id=campaign.id,
                    phone_e164=phone
                )
            else:
                # Formato completo: telefone + parâmetros
                phone = recipient_data.get('phone', '').strip()
                if phone.startswith('+'):
                    phone = phone[1:]
                
                recipient = WACampaignRecipient(
                    campaign_id=campaign.id,
                    phone_e164=phone,
                    per_params=recipient_data.get('params')
                )
            
            db.session.add(recipient)
        
        db.session.commit()
        
        logger.info(f"Campaign created: {campaign.name} (ID: {campaign.id})")
        
        return jsonify({
            'success': True,
            'campaign': campaign.to_dict(),
            'message': 'Campanha criada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating campaign: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/campaigns/<campaign_id>/pause', methods=['POST'])
@require_auth
def api_campaign_pause(campaign_id):
    """Pausar campanha"""
    try:
        campaign = WACampaign.query.get_or_404(campaign_id)
        campaign.status = 'paused'
        db.session.commit()
        
        logger.info(f"Campaign paused: {campaign.name} (ID: {campaign.id})")
        
        return jsonify({
            'success': True,
            'message': 'Campanha pausada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error pausing campaign {campaign_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/campaigns/<campaign_id>/resume', methods=['POST'])
@require_auth
def api_campaign_resume(campaign_id):
    """Retomar campanha"""
    try:
        campaign = WACampaign.query.get_or_404(campaign_id)
        campaign.status = 'active'
        db.session.commit()
        
        logger.info(f"Campaign resumed: {campaign.name} (ID: {campaign.id})")
        
        return jsonify({
            'success': True,
            'message': 'Campanha retomada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resuming campaign {campaign_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/campaigns/<campaign_id>/test', methods=['POST'])
@require_auth
def api_campaign_test(campaign_id):
    """Testar campanha (enviar para admin)"""
    try:
        campaign = WACampaign.query.get_or_404(campaign_id)
        
        # Número do admin
        admin_phone = os.getenv('ADMIN_PHONE_NUMBER', '5514997799022').strip()
        if admin_phone.startswith('+'):
            admin_phone = admin_phone[1:]
        
        # Serviço WhatsApp
        whatsapp_service = AdminWhatsAppService()
        
        # Montar parâmetros
        params = {}
        if campaign.params_mode == 'fixed' and campaign.fixed_params:
            params = campaign.fixed_params.copy()
        
        # Parâmetros padrão para teste
        if not params:
            params = {
                '1': 'Admin Teste',
                '2': datetime.now().strftime('%d/%m/%Y')
            }
        
        # Enviar
        result = whatsapp_service.send_template(
            phone_e164=admin_phone,
            template_name=campaign.template_name,
            lang_code=campaign.lang_code,
            params=params
        )
        
        if result['success']:
            logger.info(f"Test campaign sent: {campaign.name} to admin")
            return jsonify({
                'success': True,
                'message': 'Teste da campanha enviado com sucesso',
                'message_id': result.get('message_id')
            })
        else:
            logger.error(f"Test campaign failed: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Erro desconhecido')
            }), 400
            
    except Exception as e:
        logger.error(f"Error testing campaign {campaign_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

