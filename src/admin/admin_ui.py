#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin UI & routes (Fase 2)
- Tema claro alinhado ao consultório
- Login por token (ADMIN_UI_TOKEN)
- Painel u-ETG (/admin/uetg) com "Sortear semana agora (teste)"
- Cadastro rápido de paciente (nome + telefone E.164)
- Lista de pacientes (ativos)
- "Semana atual" por paciente (duas janelas: Seg/Ter e Qui/Sex) — cálculo determinístico por semana
- Runs recentes (se existirem em wa_campaign_runs)
OBS: Envio real ao paciente NÃO é alterado; botão de teste segue enviando APENAS ao ADMIN_PHONE.
"""

import os
import re
import json
import uuid
import random
import hashlib
from datetime import datetime, timedelta

import pytz
import requests
from flask import (
    Blueprint, request, jsonify, make_response,
    redirect, url_for, render_template_string
)
from sqlalchemy import text

from src.models.user import db

# Blueprint do Admin (registrado no main.py com url_prefix="/admin")
admin_bp = Blueprint("admin", __name__)

# ---------- Config & helpers ----------

TZ_NAME = os.getenv("TZ", "America/Sao_Paulo")
TZ = pytz.timezone(TZ_NAME)

ADMIN_TOKEN = os.getenv("ADMIN_UI_TOKEN", "")
ADMIN_PHONE = os.getenv("ADMIN_PHONE_NUMBER", "")

# WhatsApp (Meta)
WA_TOKEN = os.getenv("META_ACCESS_TOKEN", os.getenv("WHATSAPP_ACCESS_TOKEN", ""))
WA_PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

# u-ETG
UETG_TEMPLATE_NAME = os.getenv("UETG_TEMPLATE_NAME", "uetg_paciente_agenda_ptbr")
UETG_DEFAULT_SLOT = os.getenv("UETG_DEFAULT_SLOT", "07:30")
UETG_SLOTS_OFFER = ["12:15", "16:40", "19:00"]  # slots fixos exibidos na UI

# ------------ Auth ------------

def _is_authorized(req) -> bool:
    token_cookie = req.cookies.get("admin_token", "")
    if token_cookie and ADMIN_TOKEN and token_cookie == ADMIN_TOKEN:
        return True
    token_qs = (req.args.get("token") or "").strip()
    if token_qs and ADMIN_TOKEN and token_qs == ADMIN_TOKEN:
        return True
    return False

def _require_auth():
    if not _is_authorized(request):
        return redirect(url_for("admin.login", next=request.path))

# ------------ Time helpers ------------

def _week_bounds_today():
    now = datetime.now(TZ)
    base = now.date()
    monday = base - timedelta(days=base.weekday())  # 0=Mon
    sunday = monday + timedelta(days=6)
    return monday, sunday

# Sorteio "livre" (para o botão de teste)
def _sorted_week_draw(now=None):
    if now is None:
        now = datetime.now(TZ)
    base_date = now.date()
    monday = base_date - timedelta(days=base_date.weekday())

    first_candidates = [monday, monday + timedelta(days=1)]                 # seg/ter
    second_candidates = [monday + timedelta(days=3), monday + timedelta(days=4)]  # qui/sex

    first_pick = random.choice(first_candidates)
    second_pick = random.choice(second_candidates)

    pt_weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    def fmt(d):
        return f"{d.strftime('%d/%m')} ({pt_weekdays[d.weekday()]})"

    return {
        "first_date": first_pick,
        "second_date": second_pick,
        "first_label": fmt(first_pick),
        "second_label": fmt(second_pick),
        "tz": TZ_NAME,
        "slots": list(UETG_SLOTS_OFFER),
    }

# Sorteio determinístico por paciente/semana (sem persistir; evita mexer em schema)
def _deterministic_week_draw(key: str, now=None):
    if now is None:
        now = datetime.now(TZ)
    year, week, _ = now.isocalendar()
    base_date = now.date()
    monday = base_date - timedelta(days=base_date.weekday())
    c1 = [monday, monday + timedelta(days=1)]                 # seg/ter
    c2 = [monday + timedelta(days=3), monday + timedelta(days=4)]  # qui/sex

    seed_bytes = f"{key}:{year}:{week}".encode("utf-8")
    h = int(hashlib.sha256(seed_bytes).hexdigest(), 16)
    first_pick = c1[h & 1]
    second_pick = c2[(h >> 1) & 1]

    pt_weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    def fmt(d):
        return f"{d.strftime('%d/%m')} ({pt_weekdays[d.weekday()]})"

    return {
        "first_date": first_pick,
        "second_date": second_pick,
        "first_label": fmt(first_pick),
        "second_label": fmt(second_pick),
        "tz": TZ_NAME,
        "slots": list(UETG_SLOTS_OFFER),
        "seed_info": {"year": year, "week": week}
    }

# ------------ WhatsApp ------------

def _send_whatsapp_text(to_e164: str, body: str) -> dict:
    if not (WA_TOKEN and WA_PHONE_ID and to_e164):
        return {"ok": False, "reason": "missing_whatsapp_credentials_or_destination"}
    url = f"https://graph.facebook.com/v21.0/{WA_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to_e164,
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }
    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
        return {"ok": 200 <= r.status_code < 300, "status_code": r.status_code, "resp": r.text}
    except Exception as e:
        return {"ok": False, "exception": repr(e)}

# ------------ Pacientes (DB direto, sem depender de outros BPs) ------------

_PHONE_RE = re.compile(r"^\+?\d{10,15}$")

def _norm_phone_e164(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\D+", "", s)  # só dígitos
    # aceita sem '+', como "55DDDNNNNNNNN"
    return s

def _list_patients(limit=200):
    sql = text("""
        SELECT id, name, phone_e164, COALESCE(tags,'') AS tags, active, created_at
        FROM patients
        WHERE active = 1
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    try:
        rows = db.session.execute(sql, {"limit": limit}).mappings().all()
        return [dict(r) for r in rows]
    except Exception:
        return []

def _create_patient(name: str, phone_e164: str, tags: str = "") -> dict:
    pid = str(uuid.uuid4())
    phone = _norm_phone_e164(phone_e164)
    if not name or not phone or not _PHONE_RE.match("+" + phone):
        return {"ok": False, "error": "invalid_name_or_phone"}
    try:
        db.session.execute(
            text("""
                INSERT INTO patients (id, name, phone_e164, tags, active)
                VALUES (:id,:name,:phone,:tags,1)
            """),
            {"id": pid, "name": name.strip(), "phone": phone, "tags": (tags or "").strip()},
        )
        db.session.commit()
        return {"ok": True, "id": pid}
    except Exception as e:
        db.session.rollback()
        # violação de UNIQUE (phone)
        return {"ok": False, "error": "db_insert_failed", "detail": str(e)}

# Runs recentes (se existir tabela wa_campaign_runs)
def _fetch_runs(limit=50):
    sql = text("""
        SELECT 
            r.run_at AS run_at,
            r.phone_e164 AS phone,
            r.status AS status,
            COALESCE(r.error_message, '') AS error,
            COALESCE(c.name, '') AS campaign_name,
            COALESCE(c.template_name, '') AS template_name
        FROM wa_campaign_runs r
        LEFT JOIN wa_campaigns c ON r.campaign_id = c.id
        ORDER BY r.run_at DESC
        LIMIT :limit
    """)
    try:
        rows = db.session.execute(sql, {"limit": limit}).mappings().all()
        return [dict(row) for row in rows]
    except Exception:
        return []

# ---------- Views (rotas RELATIVAS ao prefixo "/admin") ----------

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        token = (request.form.get("token") or "").strip()
        nxt = request.args.get("next", url_for("admin.home"))
        if ADMIN_TOKEN and token == ADMIN_TOKEN:
            resp = make_response(redirect(nxt))
            resp.set_cookie("admin_token", token, httponly=True, samesite="Lax", max_age=7*24*3600)
            return resp
        return render_template_string(LOGIN_HTML, error="Token inválido")
    return render_template_string(LOGIN_HTML, error="")

@admin_bp.route("/logout", methods=["POST", "GET"])
def logout():
    resp = make_response(redirect(url_for("admin.login")))
    resp.delete_cookie("admin_token")
    return resp

@admin_bp.route("/")
def home():
    if not _is_authorized(request):
        return _require_auth()

    monday, sunday = _week_bounds_today()
    patients = _list_patients(limit=200)
    # monta painel "Semana atual" determinístico por paciente
    weekly = []
    for p in patients:
        key = p["phone_e164"] or p["id"]
        draw = _deterministic_week_draw(key)
        weekly.append({
            "name": p["name"],
            "phone": p["phone_e164"],
            "first": draw["first_label"],
            "second": draw["second_label"],
        })

    runs = _fetch_runs(limit=50)

    return render_template_string(
        HOME_HTML,
        tz=TZ_NAME,
        monday=monday.strftime("%d/%m"),
        sunday=sunday.strftime("%d/%m"),
        patients=patients,
        weekly=weekly,
        runs=runs,
        slots=UETG_SLOTS_OFFER,
        template_name=UETG_TEMPLATE_NAME,
        default_slot=UETG_DEFAULT_SLOT
    )

@admin_bp.route("/uetg")
def uetg_page():
    if not _is_authorized(request):
        return _require_auth()

    monday, sunday = _week_bounds_today()
    draw = _sorted_week_draw()
    runs = _fetch_runs(limit=50)

    return render_template_string(
        UETG_HTML,
        tz=TZ_NAME,
        monday=monday.strftime("%d/%m"),
        sunday=sunday.strftime("%d/%m"),
        draw=draw,
        runs=runs,
        slots=UETG_SLOTS_OFFER,
        template_name=UETG_TEMPLATE_NAME,
        default_slot=UETG_DEFAULT_SLOT
    )

# ---------- APIs Admin (seguras por token) ----------

@admin_bp.route("/api/uetg/test-draw", methods=["POST"])
def uetg_test_draw():
    if not _is_authorized(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    if not ADMIN_PHONE:
        return jsonify({"ok": False, "error": "ADMIN_PHONE_NUMBER not configured"}), 400

    draw = _sorted_week_draw()
    msg = (
        f"u-ETG — SORTEIO (TESTE, APENAS ADMIN)\n\n"
        f"Semana: TZ {draw['tz']}\n"
        f"1ª data: {draw['first_label']}\n"
        f"2ª data: {draw['second_label']}\n\n"
        f"Horários oferecidos ao paciente:\n"
        f"• {draw['slots'][0]}\n• {draw['slots'][1]}\n• {draw['slots'][2]}"
    )
    res = _send_whatsapp_text(ADMIN_PHONE, msg)
    return jsonify({"ok": bool(res.get("ok")), "meta": res}), (200 if res.get("ok") else 500)

@admin_bp.route("/api/patients/add", methods=["POST"])
def api_patients_add():
    if not _is_authorized(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    tags = (data.get("tags") or "").strip()
    res = _create_patient(name, phone, tags)
    status = 200 if res.get("ok") else 400
    return jsonify(res), status

@admin_bp.route("/api/patients/list", methods=["GET"])
def api_patients_list():
    if not _is_authorized(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    return jsonify({"ok": True, "patients": _list_patients(limit=500)})

# ---------- Templates (inline) ----------

LOGIN_HTML = u"""
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8"/>
  <title>WhatsApp Admin — Login</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>
    :root{--bg:#f7fafb;--card:#ffffff;--ink:#1b2a36;--mut:#4b5b68;--br:#e5edf2;--acc:#1ba4a9;--acc2:#f4a340;--err:#d13b3b}
    *{box-sizing:border-box}
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);margin:0}
    .wrap{max-width:420px;margin:8vh auto;padding:24px 20px;background:var(--card);border:1px solid var(--br);border-radius:16px;box-shadow:0 10px 30px rgba(14,30,37,.06)}
    h1{font-size:20px;margin:0 0 8px}
    p{color:var(--mut)}
    input[type=password]{width:100%;padding:12px 14px;background:#f2f7fa;color:var(--ink);border:1px solid var(--br);border-radius:10px}
    button{margin-top:12px;width:100%;padding:12px 14px;background:var(--acc);color:#fff;border:none;border-radius:12px;font-weight:600;cursor:pointer}
    .err{margin:8px 0 0;color:var(--err);font-size:14px;min-height:1em}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>WhatsApp Admin — Faça login</h1>
    <p>Sistema Online</p>
    <form method="post">
      <label for="token">Token de acesso</label>
      <input id="token" name="token" type="password" placeholder="Digite seu token" autofocus />
      <div class="err">{{ error }}</div>
      <button type="submit">Entrar</button>
    </form>
  </div>
</body>
</html>
"""

HOME_HTML = u"""
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8"/>
  <title>Admin — Painel</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>
    :root{--bg:#f7fafb;--card:#ffffff;--ink:#1b2a36;--mut:#4b5b68;--br:#e5edf2;--acc:#1ba4a9;--acc2:#f4a340;--err:#d13b3b}
    *{box-sizing:border-box}
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);margin:0}
    header{padding:16px 20px;border-bottom:1px solid var(--br);background:#ffffffa8;backdrop-filter:saturate(180%) blur(8px)}
    .tag{padding:4px 10px;border-radius:999px;font-size:12px;background:#e8f6f7;border:1px solid #c7e8ea;color:#0f6f72}
    main{max-width:1120px;margin:20px auto;padding:0 16px}
    .grid{display:grid;grid-template-columns:2fr 1fr;gap:16px}
    .card{background:var(--card);border:1px solid var(--br);border-radius:14px;padding:16px;box-shadow:0 10px 30px rgba(14,30,37,.06)}
    h1{margin:10px 0 18px}
    h2{margin:0 0 10px;font-size:18px}
    p{margin:8px 0;color:var(--mut)}
    table{width:100%;border-collapse:collapse;margin-top:8px}
    th,td{padding:10px;border-bottom:1px solid var(--br);text-align:left;font-size:14px}
    th{color:#30576a}
    .btn{display:inline-flex;align-items:center;gap:8px;padding:10px 12px;background:var(--acc);color:#fff;border:none;border-radius:10px;font-weight:700;cursor:pointer}
    .btn-alt{background:var(--acc2);color:#1b2a36}
    .mono{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace}
    .row{display:flex;gap:10px;flex-wrap:wrap}
    input,textarea{width:100%;padding:10px;border:1px solid var(--br);border-radius:10px;background:#f2f7fa}
    label{font-size:12px;color:#30576a}
    .slots{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}
    .chip{border:1px solid var(--br);background:#f0fbfb;color:#185e61;padding:6px 10px;border-radius:999px;font-size:13px}
    .ok{color:#2c8f2c}.err{color:#d13b3b}
  </style>
</head>
<body>
  <header>
    <div class="tag">Admin · TZ {{ tz }}</div>
  </header>
  <main>
    <h1>Painel do Admin</h1>
    <div class="grid">
      <!-- Coluna principal -->
      <section class="card">
        <h2>Semana atual ({{ monday }} → {{ sunday }})</h2>
        {% if weekly and weekly|length>0 %}
        <table>
          <thead><tr><th>Paciente</th><th>Telefone</th><th>1ª janela</th><th>2ª janela</th></tr></thead>
          <tbody>
            {% for w in weekly %}
            <tr>
              <td>{{ w.name }}</td>
              <td class="mono">{{ w.phone }}</td>
              <td class="mono">{{ w.first }}</td>
              <td class="mono">{{ w.second }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        {% else %}
          <p>Nenhum paciente ativo cadastrado ainda.</p>
        {% endif %}
      </section>

      <!-- Coluna lateral: ações rápidas -->
      <aside class="card">
        <h2>Ações rápidas</h2>
        <p class="mono">TEMPLATE: {{ template_name }} · DISPARO: {{ default_slot }}</p>
        <div class="slots">
          {% for s in slots %}<div class="chip">{{ s }}</div>{% endfor %}
        </div>
        <button id="btnTest" class="btn" style="margin-top:10px">🎲 Sortear semana agora (teste p/ admin)</button>
        <a class="btn btn-alt" style="margin-top:10px;text-decoration:none;display:inline-flex" href="/admin/uetg">Abrir painel u-ETG</a>
        <div id="testOut" class="mono" style="margin-top:8px;color:#30576a"></div>
      </aside>
    </div>

    <div class="grid" style="grid-template-columns:1fr 2fr; margin-top:16px">
      <!-- Cadastro rápido -->
      <section class="card">
        <h2>Cadastrar paciente</h2>
        <form id="formAdd">
          <div class="row">
            <div style="flex:1 1 100%">
              <label>Nome</label>
              <input name="name" placeholder="Nome completo"/>
            </div>
            <div style="flex:1 1 100%">
              <label>Telefone (E.164 — ex.: 55DDDNNNNNNNN)</label>
              <input name="phone" placeholder="5511999999999"/>
            </div>
            <div style="flex:1 1 100%">
              <label>Tags (opcional)</label>
              <input name="tags" placeholder="u-etg, semanal"/>
            </div>
          </div>
          <button class="btn" type="submit" style="margin-top:10px">➕ Adicionar</button>
          <div id="addOut" class="mono" style="margin-top:8px;color:#30576a"></div>
        </form>
      </section>

      <!-- Lista de pacientes -->
      <section class="card">
        <h2>Pacientes</h2>
        {% if patients and patients|length>0 %}
        <table>
          <thead><tr><th>Nome</th><th>Telefone</th><th>Tags</th><th>Desde</th></tr></thead>
          <tbody>
            {% for p in patients %}
            <tr>
              <td>{{ p.name }}</td>
              <td class="mono">{{ p.phone_e164 }}</td>
              <td class="mono">{{ p.tags }}</td>
              <td class="mono">{{ p.created_at }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        {% else %}
          <p>Nenhum paciente cadastrado ainda.</p>
        {% endif %}
      </section>
    </div>

    <section class="card" style="margin-top:16px">
      <h2>Execuções recentes (runs)</h2>
      {% if runs and runs|length>0 %}
      <table>
        <thead><tr><th>Quando</th><th>Para</th><th>Status</th><th>Campanha</th><th>Template</th><th>Erro</th></tr></thead>
        <tbody>
          {% for r in runs %}
          <tr>
            <td class="mono">{{ r.run_at }}</td>
            <td class="mono">{{ r.phone }}</td>
            <td class="{{ 'ok' if (r.status or '').lower()=='ok' else 'err' }}">{{ r.status }}</td>
            <td class="mono">{{ r.campaign_name }}</td>
            <td class="mono">{{ r.template_name }}</td>
            <td class="mono">{{ r.error }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
      {% else %}
        <p>Nenhum envio registrado ainda.</p>
      {% endif %}
    </section>
  </main>

  <script>
    // Ensaio
    const btn = document.getElementById('btnTest');
    const out = document.getElementById('testOut');
    btn?.addEventListener('click', async () => {
      btn.disabled = true; out.textContent = 'Enviando sorteio de teste para o admin...';
      try {
        const res = await fetch('/admin/api/uetg/test-draw', {method:'POST', headers:{'Content-Type':'application/json'}});
        const data = await res.json();
        if (data.ok) out.textContent = '✅ Enviado ao WhatsApp do admin.';
        else out.textContent = '⚠️ Falha: ' + (data.error || data.meta?.resp || 'erro desconhecido');
      } catch { out.textContent = '⚠️ Erro de rede.'; }
      finally { btn.disabled = false; }
    });

    // Cadastro rápido
    const form = document.getElementById('formAdd');
    const addOut = document.getElementById('addOut');
    form?.addEventListener('submit', async (e) => {
      e.preventDefault();
      addOut.textContent = 'Adicionando...';
      const fd = new FormData(form);
      const payload = {name: fd.get('name'), phone: fd.get('phone'), tags: fd.get('tags')};
      try {
        const res = await fetch('/admin/api/patients/add', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.ok) { addOut.textContent = '✅ Paciente cadastrado'; setTimeout(()=>location.reload(), 700); }
        else { addOut.textContent = '⚠️ ' + (data.error || data.detail || 'Erro ao cadastrar'); }
      } catch { addOut.textContent = '⚠️ Erro de rede.'; }
    });
  </script>
</body>
</html>
"""

UETG_HTML = u"""
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8"/>
  <title>Admin — u-ETG</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>
    :root{--bg:#f7fafb;--card:#ffffff;--ink:#1b2a36;--mut:#4b5b68;--br:#e5edf2;--acc:#1ba4a9;--acc2:#f4a340;--err:#d13b3b}
    *{box-sizing:border-box}
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);margin:0}
    header{padding:16px 20px;border-bottom:1px solid var(--br);background:#ffffffa8;backdrop-filter:saturate(180%) blur(8px)}
    .tag{padding:4px 10px;border-radius:999px;font-size:12px;background:#e8f6f7;border:1px solid #c7e8ea;color:#0f6f72}
    main{max-width:1100px;margin:20px auto;padding:0 16px}
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
    .card{background:var(--card);border:1px solid var(--br);border-radius:14px;padding:16px;box-shadow:0 10px 30px rgba(14,30,37,.06)}
    h2{margin:0 0 10px;font-size:18px}
    p{margin:8px 0;color:var(--mut)}
    table{width:100%;border-collapse:collapse;margin-top:8px}
    th,td{padding:10px;border-bottom:1px solid var(--br);text-align:left;font-size:14px}
    th{color:#30576a}
    .btn{display:inline-flex;align-items:center;gap:8px;padding:10px 12px;background:var(--acc);color:#fff;border:none;border-radius:10px;font-weight:700;cursor:pointer}
    .mono{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace}
    .slots{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}
    .chip{border:1px solid var(--br);background:#f0fbfb;color:#185e61;padding:6px 10px;border-radius:999px;font-size:13px}
    .ok{color:#2c8f2c}.err{color:#d13b3b}
  </style>
</head>
<body>
  <header>
    <div class="tag">u-ETG · TZ {{ tz }}</div>
  </header>
  <main>
    <div class="grid">
      <section class="card">
        <h2>Próximos sorteios (semana {{ monday }} → {{ sunday }})</h2>
        <p class="mono">TEMPLATE: {{ template_name }} · DISPARO: {{ default_slot }}</p>
        <ul>
          <li>Primeira janela: <strong>{{ draw.first_label }}</strong></li>
          <li>Segunda janela: <strong>{{ draw.second_label }}</strong></li>
        </ul>
        <p>Horários oferecidos ao paciente:</p>
        <div class="slots">
          {% for s in slots %}<div class="chip">{{ s }}</div>{% endfor %}
        </div>
        <button id="btnTest" class="btn" style="margin-top:10px">🎲 Sortear semana agora (teste só p/ admin)</button>
        <div id="testOut" class="mono" style="margin-top:8px;color:#30576a"></div>
      </section>

      <section class="card">
        <h2>Execuções recentes (runs)</h2>
        {% if runs and runs|length>0 %}
          <table>
            <thead><tr><th>Quando</th><th>Para</th><th>Status</th><th>Campanha</th><th>Template</th><th>Erro</th></tr></thead>
            <tbody>
              {% for r in runs %}
              <tr>
                <td class="mono">{{ r.run_at }}</td>
                <td class="mono">{{ r.phone }}</td>
                <td class="{{ 'ok' if (r.status or '').lower()=='ok' else 'err' }}">{{ r.status }}</td>
                <td class="mono">{{ r.campaign_name }}</td>
                <td class="mono">{{ r.template_name }}</td>
                <td class="mono">{{ r.error }}</td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        {% else %}
          <p>Nenhuma execução registrada ainda.</p>
        {% endif %}
      </section>
    </div>
  </main>

  <script>
    const btn = document.getElementById('btnTest');
    const out = document.getElementById('testOut');
    btn?.addEventListener('click', async () => {
      btn.disabled = true; out.textContent = 'Enviando sorteio de teste para o admin...';
      try {
        const res = await fetch('/admin/api/uetg/test-draw', {method:'POST', headers:{'Content-Type':'application/json'}});
        const data = await res.json();
        if (data.ok) out.textContent = '✅ Enviado ao WhatsApp do admin.';
        else out.textContent = '⚠️ Falha: ' + (data.error || data.meta?.resp || 'erro desconhecido');
      } catch { out.textContent = '⚠️ Erro de rede.'; }
      finally { btn.disabled = false; }
    });
  </script>
</body>
</html>
"""
