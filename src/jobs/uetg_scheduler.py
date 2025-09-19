"""
Sistema de agendamento automático para exames u-ETG
Sorteia 2 datas úteis por semana e envia lembretes automáticos
"""

import os
import json
import random
import requests
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Configurações
TIMEZONE = pytz.timezone("America/Sao_Paulo")
DATA_DIR = "/tmp"  # Railway usa /tmp para arquivos temporários
PLAN_FILE = os.path.join(DATA_DIR, "uetg_plan.json")
CONFIRMATIONS_FILE = os.path.join(DATA_DIR, "uetg_confirmations.json")

# Variáveis de ambiente com validação robusta
WHATSAPP_ACCESS_TOKEN = (os.getenv("WHATSAPP_ACCESS_TOKEN") or "").strip()
WHATSAPP_PHONE_NUMBER_ID = (os.getenv("WHATSAPP_PHONE_NUMBER_ID") or "").strip()
ADMIN_PHONE_NUMBER = (os.getenv("ADMIN_PHONE_NUMBER") or "5514997799022").strip()
UETG_PATIENT_PHONE = (os.getenv("UETG_PATIENT_PHONE") or "5514997799022").strip()
UETG_PATIENT_NAME = (os.getenv("UETG_PATIENT_NAME") or "Paciente").strip()
UETG_DEFAULT_SLOT = (os.getenv("UETG_DEFAULT_SLOT") or "07:30").strip()

# URLs da API do WhatsApp
WHATSAPP_API_URL = (
    f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
)

# Logger
logger = logging.getLogger(__name__)
scheduler = None


def validate_config():
    """Valida configurações necessárias"""
    missing_vars = []

    if not WHATSAPP_ACCESS_TOKEN:
        missing_vars.append("WHATSAPP_ACCESS_TOKEN")
    if not WHATSAPP_PHONE_NUMBER_ID:
        missing_vars.append("WHATSAPP_PHONE_NUMBER_ID")

    if missing_vars:
        logger.warning(
            f"Variáveis de ambiente faltando para u-ETG: {', '.join(missing_vars)}"
        )
        return False

    logger.info(
        f"u-ETG Config OK - Admin: {ADMIN_PHONE_NUMBER}, Patient: {UETG_PATIENT_NAME}"
    )
    return True


def load_plan():
    """Carrega o plano de datas sorteadas"""
    try:
        if os.path.exists(PLAN_FILE):
            with open(PLAN_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar plano: {e}")
    return {}


def save_plan(plan):
    """Salva o plano de datas sorteadas"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(PLAN_FILE, "w") as f:
            json.dump(plan, f, indent=2)
        logger.info("Plano salvo com sucesso")
    except Exception as e:
        logger.error(f"Erro ao salvar plano: {e}")


def load_confirmations():
    """Carrega as confirmações de horários"""
    try:
        if os.path.exists(CONFIRMATIONS_FILE):
            with open(CONFIRMATIONS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar confirmações: {e}")
    return {}


def save_confirmation(date, slot, patient_name):
    """Salva uma confirmação de horário"""
    try:
        confirmations = load_confirmations()
        confirmations[date] = {
            "slot": slot,
            "patient_name": patient_name,
            "confirmed_at": datetime.now(TIMEZONE).isoformat(),
        }
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CONFIRMATIONS_FILE, "w") as f:
            json.dump(confirmations, f, indent=2)
        logger.info(f"Confirmação salva: {patient_name} - {slot} em {date}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar confirmação: {e}")
        return False


def send_whatsapp_message(phone_number, message):
    """Envia mensagem de texto via WhatsApp"""
    if not phone_number or not phone_number.strip():
        logger.error("Número de telefone inválido")
        return False

    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.error("Credenciais WhatsApp não configuradas")
        return False

    try:
        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

        data = {
            "messaging_product": "whatsapp",
            "to": phone_number.strip(),
            "type": "text",
            "text": {"body": message},
        }

        response = requests.post(WHATSAPP_API_URL, headers=headers, json=data)

        if response.status_code == 200:
            logger.info(f"Mensagem enviada para {phone_number[:8]}***")
            return True
        else:
            logger.error(
                f"Erro ao enviar mensagem: {response.status_code} - {response.text}"
            )
            return False

    except Exception as e:
        logger.error(f"Erro ao enviar mensagem WhatsApp: {e}")
        return False


def send_whatsapp_template(phone_number, template_name, parameters):
    """Envia template via WhatsApp"""
    if not phone_number or not phone_number.strip():
        logger.error("Número de telefone inválido para template")
        return False

    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.error("Credenciais WhatsApp não configuradas para template")
        return False

    try:
        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

        data = {
            "messaging_product": "whatsapp",
            "to": phone_number.strip(),
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "pt_BR"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": str(param)} for param in parameters
                        ],
                    }
                ],
            },
        }

        response = requests.post(WHATSAPP_API_URL, headers=headers, json=data)

        if response.status_code == 200:
            logger.info(f"Template {template_name} enviado para {phone_number[:8]}***")
            return True
        else:
            logger.error(
                f"Erro ao enviar template: {response.status_code} - {response.text}"
            )
            return False

    except Exception as e:
        logger.error(f"Erro ao enviar template WhatsApp: {e}")
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
        logger.info("🎲 Iniciando sorteio semanal u-ETG...")

        if not validate_config():
            logger.error("Configuração inválida - sorteio cancelado")
            return False

        weekdays = get_weekdays_next_week()

        # Separar início (seg/ter) e fim (qui/sex) da semana
        early_week = weekdays[:2]  # Segunda e terça
        late_week = weekdays[3:]  # Quinta e sexta

        # Sortear uma data de cada período
        selected_dates = [random.choice(early_week), random.choice(late_week)]

        # Salvar o plano
        week_start = weekdays[0].isoformat()
        plan = {
            "week_start": week_start,
            "days": [date.isoformat() for date in selected_dates],
            "planned_at": datetime.now(TIMEZONE).isoformat(),
        }

        save_plan(plan)

        # Notificar admin
        dates_text = "\n".join(
            [f"📅 {date.strftime('%d/%m/%Y (%A)')}" for date in selected_dates]
        )

        admin_message = f"""🎲 *Sorteio u-ETG Realizado*

Datas sorteadas para {UETG_PATIENT_NAME}:

{dates_text}

Semana: {weekdays[0].strftime('%d/%m')} a {weekdays[-1].strftime('%d/%m/%Y')}
Sorteado em: {datetime.now(TIMEZONE).strftime('%d/%m/%Y às %H:%M')}"""

        if send_whatsapp_message(ADMIN_PHONE_NUMBER, admin_message):
            logger.info(
                f"Sorteio concluído: {[d.strftime('%d/%m') for d in selected_dates]}"
            )
            return True
        else:
            logger.error("Falha ao notificar admin sobre sorteio")
            return False

    except Exception as e:
        logger.error(f"Erro no sorteio: {e}")
        error_message = f"❌ Erro no sorteio u-ETG: {str(e)}"
        send_whatsapp_message(ADMIN_PHONE_NUMBER, error_message)
        return False


def send_today():
    """Envia lembrete se hoje é um dia sorteado"""
    try:
        today = datetime.now(TIMEZONE).date().isoformat()
        plan = load_plan()

        if not plan or "days" not in plan:
            logger.info("Nenhum plano encontrado para hoje")
            return False

        if today not in plan["days"]:
            logger.info(f"Hoje ({today}) não está nos dias sorteados")
            return False

        logger.info(f"🚨 Enviando lembrete u-ETG para hoje ({today})")

        if not validate_config():
            logger.error("Configuração inválida - envio cancelado")
            return False

        # Formatar data para exibição
        today_date = datetime.now(TIMEZONE)
        formatted_date = today_date.strftime("%d/%m/%Y")

        # Enviar template para paciente
        template_sent = send_whatsapp_template(
            UETG_PATIENT_PHONE,
            "uetg_paciente_agenda_ptbr",
            [UETG_PATIENT_NAME, formatted_date, UETG_DEFAULT_SLOT],
        )

        # Notificar admin
        if template_sent:
            admin_message = f"""📨 *Lembrete u-ETG Enviado*

Paciente: {UETG_PATIENT_NAME}
Data: {formatted_date}
Horário sugerido: {UETG_DEFAULT_SLOT}

Template enviado às {today_date.strftime('%H:%M')}"""
            send_whatsapp_message(ADMIN_PHONE_NUMBER, admin_message)
        else:
            admin_message = f"""❌ *Erro no Envio u-ETG*

Falha ao enviar template para {UETG_PATIENT_NAME}
Data: {formatted_date}
Tentativa às {today_date.strftime('%H:%M')}"""
            send_whatsapp_message(ADMIN_PHONE_NUMBER, admin_message)

        return template_sent

    except Exception as e:
        logger.error(f"Erro ao enviar lembrete: {e}")
        error_message = f"❌ Erro ao enviar lembrete u-ETG: {str(e)}"
        send_whatsapp_message(ADMIN_PHONE_NUMBER, error_message)
        return False


def init_scheduler():
    """Inicializa o agendador automático"""
    global scheduler

    try:
        if scheduler is not None:
            logger.warning("Scheduler já está rodando")
            return

        if not validate_config():
            logger.error("Configuração inválida - scheduler não iniciado")
            return

        scheduler = BackgroundScheduler(timezone=TIMEZONE)

        # Sorteio semanal: todo sábado às 12:00
        scheduler.add_job(
            plan_next_week,
            CronTrigger(day_of_week="sat", hour=12, minute=0, timezone=TIMEZONE),
            id="uetg_weekly_planning",
            replace_existing=True,
        )

        # Envio diário: segunda a sexta às 07:00
        scheduler.add_job(
            send_today,
            CronTrigger(day_of_week="mon-fri", hour=7, minute=0, timezone=TIMEZONE),
            id="uetg_daily_send",
            replace_existing=True,
        )

        scheduler.start()
        logger.info("✅ uETG Scheduler started.")
        logger.info("📅 Sorteio: Sábados às 12:00")
        logger.info("📨 Envio: Segunda a Sexta às 07:00")

    except Exception as e:
        logger.error(f"Erro ao inicializar scheduler: {e}")


def stop_scheduler():
    """Para o agendador"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
        logger.info("🛑 uETG Scheduler stopped.")


# Mapeamento de botões para horários
SLOT_MAPPING = {
    "slot_0730": "07:30",
    "slot_1200": "12:00",
    "slot_1215": "12:15",
    "slot_1640": "16:40",
    "slot_1900": "19:00",
    # Mapeamento reverso para compatibilidade
    "07:30": "slot_0730",
    "12:00": "slot_1200",
    "12:15": "slot_1215",
    "16:40": "slot_1640",
    "19:00": "slot_1900",
}


def process_button_click(button_id, patient_phone, patient_name):
    """Processa clique nos botões de horário"""
    try:
        if not button_id or not button_id.strip():
            logger.error("Button ID inválido")
            return False

        if not patient_phone or not patient_phone.strip():
            logger.error("Número do paciente inválido")
            return False

        if not patient_name or not patient_name.strip():
            logger.error("Nome do paciente inválido")
            return False

        today = datetime.now(TIMEZONE).date().isoformat()
        button_id = button_id.strip()

        # Mapear ID do botão para horário
        selected_slot = SLOT_MAPPING.get(button_id, button_id)

        logger.info(f"Processando clique: {button_id} -> {selected_slot}")

        # Salvar confirmação
        if save_confirmation(today, selected_slot, patient_name.strip()):
            # Confirmar para o paciente
            patient_message = f"""✅ Horário confirmado: {selected_slot} para hoje ({datetime.now(TIMEZONE).strftime('%d/%m/%Y')})

Obrigado! Aguardamos você no horário marcado."""

            send_whatsapp_message(patient_phone.strip(), patient_message)

            # Notificar admin
            admin_message = f"""✅ *Confirmação u-ETG*

{patient_name.strip()} confirmou {selected_slot} para {datetime.now(TIMEZONE).strftime('%d/%m/%Y')}"""

            send_whatsapp_message(ADMIN_PHONE_NUMBER, admin_message)

            logger.info(f"Confirmação processada: {patient_name} - {selected_slot}")
            return True
        else:
            logger.error("Erro ao salvar confirmação")
            return False

    except Exception as e:
        logger.error(f"Erro ao processar clique: {e}")
        return False
