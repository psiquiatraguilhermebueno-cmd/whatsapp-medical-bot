"""
Sistema de agendamento automático para exames u-ETG
Sorteia 2 datas úteis por semana e envia lembretes automáticos
"""

import os
import json
import random
import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Configurações
TIMEZONE = pytz.timezone('America/Sao_Paulo')
DATA_DIR = '/tmp'  # Railway usa /tmp para arquivos temporários
PLAN_FILE = os.path.join(DATA_DIR, 'uetg_plan.json')
CONFIRMATIONS_FILE = os.path.join(DATA_DIR, 'uetg_confirmations.json')

# Variáveis de ambiente
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
ADMIN_PHONE_NUMBER = os.getenv('ADMIN_PHONE_NUMBER', '5514997799022')
UETG_PATIENT_PHONE = os.getenv('UETG_PATIENT_PHONE', '5514997799022')  # Por enquanto mesmo número
UETG_PATIENT_NAME = os.getenv('UETG_PATIENT_NAME', 'Paciente')
UETG_DEFAULT_SLOT = os.getenv('UETG_DEFAULT_SLOT', '07:30')

# URLs da API do WhatsApp
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

scheduler = None

def load_plan():
    """Carrega o plano de datas sorteadas"""
    try:
        if os.path.exists(PLAN_FILE):
            with open(PLAN_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar plano: {e}")
    return {}

def save_plan(plan):
    """Salva o plano de datas sorteadas"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(PLAN_FILE, 'w') as f:
            json.dump(plan, f, indent=2)
    except Exception as e:
        print(f"Erro ao salvar plano: {e}")

def load_confirmations():
    """Carrega as confirmações de horários"""
    try:
        if os.path.exists(CONFIRMATIONS_FILE):
            with open(CONFIRMATIONS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar confirmações: {e}")
    return {}

def save_confirmation(date, slot, patient_name):
    """Salva uma confirmação de horário"""
    try:
        confirmations = load_confirmations()
        confirmations[date] = {
            'slot': slot,
            'patient_name': patient_name,
            'confirmed_at': datetime.now(TIMEZONE).isoformat()
        }
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CONFIRMATIONS_FILE, 'w') as f:
            json.dump(confirmations, f, indent=2)
        return True
    except Exception as e:
        print(f"Erro ao salvar confirmação: {e}")
        return False

def send_whatsapp_message(phone_number, message):
    """Envia mensagem de texto via WhatsApp"""
    try:
        headers = {
            'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'messaging_product': 'whatsapp',
            'to': phone_number,
            'type': 'text',
            'text': {'body': message}
        }
        
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=data)
        
        if response.status_code == 200:
            print(f"Mensagem enviada para {phone_number}: {message[:50]}...")
            return True
        else:
            print(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Erro ao enviar mensagem WhatsApp: {e}")
        return False

def send_whatsapp_template(phone_number, template_name, parameters):
    """Envia template via WhatsApp"""
    try:
        headers = {
            'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'messaging_product': 'whatsapp',
            'to': phone_number,
            'type': 'template',
            'template': {
                'name': template_name,
                'language': {'code': 'pt_BR'},
                'components': [
                    {
                        'type': 'body',
                        'parameters': [{'type': 'text', 'text': param} for param in parameters]
                    }
                ]
            }
        }
        
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=data)
        
        if response.status_code == 200:
            print(f"Template {template_name} enviado para {phone_number}")
            return True
        else:
            print(f"Erro ao enviar template: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Erro ao enviar template WhatsApp: {e}")
        return False

def get_weekdays_next_week():
    """Retorna os dias úteis da próxima semana"""
    today = datetime.now(TIMEZONE).date()
    
    # Encontrar a próxima segunda-feira
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:  # Se hoje é segunda, pegar a próxima
        days_until_monday = 7
    
    next_monday = today + timedelta(days=days_until_monday)
    
    # Gerar dias úteis da semana (segunda a sexta)
    weekdays = []
    for i in range(5):  # 0=segunda, 4=sexta
        weekday = next_monday + timedelta(days=i)
        weekdays.append(weekday)
    
    return weekdays

def plan_next_week():
    """Sorteia 2 datas úteis para a próxima semana"""
    try:
        print("🎲 Iniciando sorteio semanal u-ETG...")
        
        weekdays = get_weekdays_next_week()
        
        # Separar início (seg/ter) e fim (qui/sex) da semana
        early_week = weekdays[:2]  # Segunda e terça
        late_week = weekdays[3:]   # Quinta e sexta
        
        # Sortear uma data de cada período
        selected_dates = [
            random.choice(early_week),
            random.choice(late_week)
        ]
        
        # Salvar o plano
        week_start = weekdays[0].isoformat()
        plan = {
            'week_start': week_start,
            'days': [date.isoformat() for date in selected_dates],
            'planned_at': datetime.now(TIMEZONE).isoformat()
        }
        
        save_plan(plan)
        
        # Notificar admin
        dates_text = '\n'.join([
            f"📅 {date.strftime('%d/%m/%Y (%A)')}" 
            for date in selected_dates
        ])
        
        admin_message = f"""🎲 *Sorteio u-ETG Realizado*

Datas sorteadas para {UETG_PATIENT_NAME}:

{dates_text}

Semana: {weekdays[0].strftime('%d/%m')} a {weekdays[-1].strftime('%d/%m/%Y')}
Sorteado em: {datetime.now(TIMEZONE).strftime('%d/%m/%Y às %H:%M')}"""

        send_whatsapp_message(ADMIN_PHONE_NUMBER, admin_message)
        
        print(f"✅ Sorteio concluído: {[d.strftime('%d/%m') for d in selected_dates]}")
        return True
        
    except Exception as e:
        print(f"❌ Erro no sorteio: {e}")
        error_message = f"❌ Erro no sorteio u-ETG: {str(e)}"
        send_whatsapp_message(ADMIN_PHONE_NUMBER, error_message)
        return False

def send_today():
    """Envia lembrete se hoje é um dia sorteado"""
    try:
        today = datetime.now(TIMEZONE).date().isoformat()
        plan = load_plan()
        
        if not plan or 'days' not in plan:
            print("📅 Nenhum plano encontrado para hoje")
            return False
        
        if today not in plan['days']:
            print(f"📅 Hoje ({today}) não está nos dias sorteados")
            return False
        
        print(f"🚨 Enviando lembrete u-ETG para hoje ({today})")
        
        # Formatar data para exibição
        today_date = datetime.now(TIMEZONE)
        formatted_date = today_date.strftime('%d/%m/%Y')
        
        # Enviar template para paciente
        template_sent = send_whatsapp_template(
            UETG_PATIENT_PHONE,
            'uetg_paciente_agenda_ptbr',
            [UETG_PATIENT_NAME, formatted_date, UETG_DEFAULT_SLOT]
        )
        
        # Notificar admin
        if template_sent:
            admin_message = f"""📨 *Lembrete u-ETG Enviado*

Paciente: {UETG_PATIENT_NAME}
Data: {formatted_date}
Horário sugerido: {UETG_DEFAULT_SLOT}

Template enviado às {today_date.strftime('%H:%M')}"""
        else:
            admin_message = f"""❌ *Erro no Envio u-ETG*

Falha ao enviar template para {UETG_PATIENT_NAME}
Data: {formatted_date}
Tentativa às {today_date.strftime('%H:%M')}"""
        
        send_whatsapp_message(ADMIN_PHONE_NUMBER, admin_message)
        
        return template_sent
        
    except Exception as e:
        print(f"❌ Erro ao enviar lembrete: {e}")
        error_message = f"❌ Erro ao enviar lembrete u-ETG: {str(e)}"
        send_whatsapp_message(ADMIN_PHONE_NUMBER, error_message)
        return False

def init_scheduler():
    """Inicializa o agendador automático"""
    global scheduler
    
    try:
        if scheduler is not None:
            print("⚠️ Scheduler já está rodando")
            return
        
        scheduler = BackgroundScheduler(timezone=TIMEZONE)
        
        # Sorteio semanal: todo sábado às 12:00
        scheduler.add_job(
            plan_next_week,
            CronTrigger(day_of_week='sat', hour=12, minute=0, timezone=TIMEZONE),
            id='uetg_weekly_planning',
            replace_existing=True
        )
        
        # Envio diário: segunda a sexta às 07:00
        scheduler.add_job(
            send_today,
            CronTrigger(day_of_week='mon-fri', hour=7, minute=0, timezone=TIMEZONE),
            id='uetg_daily_send',
            replace_existing=True
        )
        
        scheduler.start()
        print("✅ uETG Scheduler started.")
        print("📅 Sorteio: Sábados às 12:00")
        print("📨 Envio: Segunda a Sexta às 07:00")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar scheduler: {e}")

def stop_scheduler():
    """Para o agendador"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
        print("🛑 uETG Scheduler stopped.")

# Função para processar cliques nos botões (será chamada pelo webhook)
def process_button_click(button_id, patient_phone, patient_name):
    """Processa clique nos botões de horário"""
    try:
        today = datetime.now(TIMEZONE).date().isoformat()
        
        # Mapear IDs dos botões para horários
        slot_map = {
            'slot_0730': '07:30',
            'slot_1215': '12:15', 
            'slot_1900': '19:00'
        }
        
        selected_slot = slot_map.get(button_id, button_id)
        selected_slot = slot_map.get(button_id, button_id)
print(f"[uETG] button_id recebido: {button_id}")
print(f"[uETG] slot selecionado (mapeado): {selected_slot}")
        
        # Salvar confirmação
        if save_confirmation(today, selected_slot, patient_name):
            # Confirmar para o paciente
            patient_message = f"✅ Horário confirmado: {selected_slot} para hoje ({datetime.now(TIMEZONE).strftime('%d/%m/%Y')})\n\nObrigado! Aguardamos você no horário marcado."
            send_whatsapp_message(patient_phone, patient_message)
            
            # Notificar admin
            admin_message = f"✅ *Confirmação u-ETG*\n\n{patient_name} confirmou {selected_slot} para {datetime.now(TIMEZONE).strftime('%d/%m/%Y')}"
            send_whatsapp_message(ADMIN_PHONE_NUMBER, admin_message)
            
            print(f"✅ Confirmação processada: {patient_name} - {selected_slot}")
            return True
        else:
            print(f"❌ Erro ao salvar confirmação")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao processar clique: {e}")
        return False

