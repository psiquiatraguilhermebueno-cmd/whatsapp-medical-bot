#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin UI & routes (inclui /admin e /admin/uetg)
- Login por token (ADMIN_UI_TOKEN)
- Painel u-ETG com sorteio da semana e botão "Sortear semana agora (teste)"
- Lista de execuções (runs) recentes, quando existirem
"""

import os
import json
import random
from datetime import datetime, timedelta

import pytz
import requests
from flask import (
    Blueprint, request, jsonify, make_response,
    redirect, url_for, render_template_string
)
from sqlalchemy import text

# Reutiliza a instância de db do projeto
from src.models.user import db

# Blueprint do Admin (será registrado com url_prefix="/admin" no main.py)
admin_bp = Blueprint("admin", __name__)

# ---------- Config & helpers ----------

TZ_NAME = os.getenv("TZ", "America/Sao_Paulo")
TZ = pytz.timezone(TZ_NAME)

ADMIN_TOKEN = os.getenv("ADMIN_UI_TOKEN", "")
ADMIN_PHONE = os.getenv("ADMIN_PHONE_NUMBER", "")
WA_TOKEN = os.getenv("META_ACCESS_TOKEN", os.getenv("WHATSAPP_ACCESS_TOKEN", ""))
WA_PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

UETG_TEMPLATE_NAME = os.getenv("UETG_TEMPLATE_NAME", "uetg_paciente_agenda_ptbr")
UETG_DEFAULT_SLOT = os.getenv("UETG_DEFAULT_SLOT", "07:30")

# Slots fixos de oferta ao paciente
UETG_SLOTS_OFFER = ["12:15", "16:40", "19:00"]


def _is_authorized(req) -> bool:
    token_cookie = req.cookies.get("admin_token", "")
    if token_cookie and ADMIN_TOKEN and token_cookie == ADMIN_TOKEN:
        return True
    token_qs = req.args.get("token", "").strip()
    if token_qs and ADMIN_TOKEN and token_qs == ADMIN_TOKEN:
        return True
    return False


def _require_auth():
    if not _is_authorized(request):
        return redirect(url_for("admin.login", next=request.path))


def _week_bounds_today():
    now = datetime.now(TZ)
    today = now.date()
    monday = today - timedelta(days=today.weekday())  # 0 = Monday
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _sorted_week_draw(now=None):
    if now is None:
        now = datetime.now(TZ)
    base_date = now.date()
    monday = base_date - timedelta(days=base_date.weekday())

    first_candidates = [monday, monday + timedelta(days=1)]       # seg/ter
    second_candidates = [monday + timedelta(days=3), monday + timedelta(days=4)]  # qui/sex

    first_pick = random.choice(first_candidates)
    second_pick = random.choice(second_candidates)

    def fmt(d):
        # exemplo "23/09 (Ter)"
        return d.strftime("%d/%m (%a)")

    return {
        "first_date": first_pick,
        "second_date": second_pick,
        "first_label": fmt(first_pick),
        "second_label": fmt(second_pick),
        "tz": TZ_NAME,
        "slots": list(UETG_SLOTS_OFFER),
    }


def _send_whatsapp_text(to_e164: str, body: str) -> dict:
    """
    Envia texto simples via Graph API. NÃO grava em base, NÃO dispara para paciente.
    Apenas para smoke/admin.
    """
    if not (WA_TOKEN and WA_PHONE_ID and to_e164):
        return {"ok": False, "reason": "missing_whatsapp_credentials_or_destination"}

    url = f"https://graph.facebook.com/v21.0/{WA_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_e164,
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }
    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
        ok = 200 <= r.status_code < 300
        return {"ok": ok, "status_code": r.status_code, "resp": r.text}
    except Exception as e:
        return {"ok": False, "exception": repr(e)}


def _fetch_runs(limit=50):
    """
    Busca execuções recentes (se as tabelas existirem).
    Retorna lista de dicts ou lista vazia.
    """
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
    return render_template_string(HOME_HTML, tz=TZ_NAME)


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


@admin_bp.route("/api/uetg/test-draw", methods=["POST"])
def uetg_test_draw():
    """
    Sorteio “FAKE” só para o admin: NÃO toca em paciente, NÃO grava banco.
    Envia WhatsApp para ADMIN_PHONE com as duas datas sorteadas + slots.
    """
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


# ---------- Templates (inline) ----------

LOGIN_HTML = u"""
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8"/>
  <title>WhatsApp Admin — Login</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Helvetica,Arial,sans-serif;background:#0b1020;color:#e7eaf6;margin:0}
    .wrap{max-width:420px;margin:8vh auto;padding:24px 20px;background:#0f1730;border:1px solid #1c2748;border-radius:16px;box-shadow:0 10px 30px rgba(0,0,0,.25)}
    h1{font-size:20px;margin:0 0 8px}
    p{opacity:.85}
    input[type=password]{width:100%;padding:12px 14px;background:#0b1020;color:#e7eaf6;border:1px solid #29365e;border-radius:10px}
    button{margin-top:12px;width:100%;padding:12px 14px;background:#2aa772;color:#fff;border:none;border-radius:12px;font-weight:600;cursor:pointer}
    .err{margin:8px 0 0;color:#ff6b6b;font-size:14px;min-height:1em}
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
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Helvetica,Arial,sans-serif;background:#0b1020;color:#e7eaf6;margin:0}
    header{padding:16px 20px;border-bottom:1px solid #1c2748}
    .tag{padding:4px 10px;border-radius:999px;font-size:12px;background:#132040;border:1px solid #273a6a}
    main{max-width:980px;margin:20px auto;padding:0 16px}
    a.btn{display:inline-block;margin-top:16px;padding:10px 14px;border-radius:10px;background:#2aa772;color:#fff;text-decoration:none;font-weight:600}
  </style>
</head>
<body>
  <header>
    <div class="tag">Sistema Online · TZ {{ tz }}</div>
  </header>
  <main>
    <h1>Admin</h1>
    <p>Bem-vindo! Use os atalhos abaixo.</p>
    <a class="btn" href="/admin/uetg">Abrir painel u-ETG</a>
  </main>
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
    :root{--bg:#0b1020;--card:#0f1730;--ink:#e7eaf6;--mut:#a8b2d9;--br:#1c2748;--acc:#2aa772;--warn:#e79a3a;--err:#ff6b6b}
    *{box-sizing:border-box}
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);margin:0}
    header{padding:16px 20px;border-bottom:1px solid var(--br)}
    .tag{padding:4px 10px;border-radius:999px;font-size:12px;background:#132040;border:1px solid #273a6a}
    main{max-width:1100px;margin:20px auto;padding:0 16px}
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
    .card{background:var(--card);border:1px solid var(--br);border-radius:14px;padding:16px;box-shadow:0 10px 30px rgba(0,0,0,.25)}
    h2{margin:0 0 10px;font-size:18px}
    p{margin:8px 0;color:var(--mut)}
    table{width:100%;border-collapse:collapse;margin-top:8px}
    th,td{padding:10px;border-bottom:1px solid var(--br);text-align:left;font-size:14px}
    th{color:#b8c3ee}
    .btn{display:inline-flex;align-items:center;gap:8px;padding:10px 12px;background:var(--acc);color:#fff;border:none;border-radius:10px;font-weight:700;cursor:pointer}
    .btn:disabled{opacity:.6;cursor:not-allowed}
    .mono{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace}
    .ok{color:#9be99b}
    .err{color:var(--err)}
    .caps{font-variant:all-small-caps;opacity:.9}
    .slots{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}
    .chip{border:1px solid var(--br);background:#0b132a;color:#dce2ff;padding:6px 10px;border-radius:999px;font-size:13px}
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
        <p class="caps">Gerados localmente (visualização administrativa)</p>
        <ul>
          <li>Primeira janela: <strong>{{ draw.first_label }}</strong></li>
          <li>Segunda janela: <strong>{{ draw.second_label }}</strong></li>
        </ul>
        <p>Horários oferecidos ao paciente:</p>
        <div class="slots">
          {% for s in slots %}
          <div class="chip">{{ s }}</div>
          {% endfor %}
        </div>
        <p style="margin-top:10px" class="mono">TEMPLATE: {{ template_name }} · DISPARO: {{ default_slot }}</p>
        <button id="btnTest" class="btn">🎲 Sortear semana agora (teste só p/ admin)</button>
        <div id="testOut" class="mono" style="margin-top:8px;color:#b8c3ee"></div>
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
        if (data.ok) {
          out.textContent = '✅ Enviado ao WhatsApp do admin.';
        } else {
          out.textContent = '⚠️ Falha: ' + (data.error || data.meta?.resp || 'erro desconhecido');
        }
      } catch (e) {
        out.textContent = '⚠️ Erro de rede.';
      } finally {
        btn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""
