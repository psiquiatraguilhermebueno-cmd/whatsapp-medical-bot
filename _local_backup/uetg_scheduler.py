import os, requests, random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler

PHONE_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
TOKEN    = os.getenv('WHATSAPP_ACCESS_TOKEN')
ADMIN    = os.getenv('ADMIN_PHONE_NUMBER') or os.getenv('MY_NUMBER')
PATIENT  = os.getenv('UETG_PATIENT_MSISDN')
PATIENT_NAME = os.getenv('UETG_PATIENT_NAME', 'Paciente')
TZ = ZoneInfo(os.getenv('TIMEZONE', 'America/Sao_Paulo'))
TEMPLATE = 'uetg_paciente_agenda_ptbr'

planned_dates = set()  # YYYY-MM-DD das datas sorteadas

def send_template(to, name, date_str, slot):
    url = f"https://graph.facebook.com/v23.0/{PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": TEMPLATE,
            "language": {"code": "pt_BR"},
            "components": [{
                "type": "body",
                "parameters": [
                    {"type": "text", "text": name},
                    {"type": "text", "text": date_str},
                    {"type": "text", "text": slot}
                ]
            }]
        }
    }
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=20)
    print("send_template", to, r.status_code, r.text)
    return r

def send_text(to, text):
    url = f"https://graph.facebook.com/v23.0/{PHONE_ID}/messages"
    payload = {"messaging_product":"whatsapp","to":to,"type":"text","text":{"body":text}}
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=20)
    print("send_text", to, r.status_code, r.text)
    return r

def _next_monday(d):
    return d + timedelta(days=(7 - d.weekday()) % 7)

def plan_next_week():
    """Sorteia 2 dias úteis da semana que vem: seg/ter e qui/sex."""
    today = datetime.now(TZ).date()
    mon = _next_monday(today)
    days = [mon + timedelta(days=i) for i in range(5)]  # seg..sex
    early = [days[0], days[1]]  # seg/ter
    late  = [days[3], days[4]]  # qui/sex
    d1 = random.choice(early)
    d2 = random.choice(late)
    global planned_dates
    planned_dates = {d1.isoformat(), d2.isoformat()}
    send_text(ADMIN, f"✅ u-ETG sorteado: {d1.strftime('%d/%m')} e {d2.strftime('%d/%m')}.")

def send_today():
    """Se hoje é um dos sorteados (seg–sex), envia o template às 07:00."""
    if not (PATIENT and PHONE_ID and TOKEN):
        print("Missing envs, skipping send_today"); return
    today = datetime.now(TZ).date()
    if today.weekday() < 5 and today.isoformat() in planned_dates:
        date_str = today.strftime('%d/%m/%Y')
        slot = os.getenv('UETG_DEFAULT_SLOT', '07:30')
        send_template(PATIENT, PATIENT_NAME, date_str, slot)
        send_text(ADMIN, f"📤 u-ETG enviado para {PATIENT_NAME} em {date_str} às {slot}.")
    else:
        print("send_today: hoje não está sorteado ou é fim de semana.")

_scheduler = None
def init_scheduler():
    """Crons: sábado 12:00 sorteia; seg–sex 07:00 verifica e envia."""
    global _scheduler
    if _scheduler:
        return _scheduler
    _scheduler = BackgroundScheduler(timezone=TZ)
    _scheduler.add_job(plan_next_week, 'cron', day_of_week='sat', hour=12, minute=0)
    _scheduler.add_job(send_today,   'cron', day_of_week='mon-fri', hour=7,  minute=0)
    _scheduler.start()
    print("uETG Scheduler started.")
    return _scheduler
