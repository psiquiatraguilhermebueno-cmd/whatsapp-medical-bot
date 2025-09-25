# src/admin/routes/admin.py
import logging
from datetime import datetime
from typing import List, Dict, Any

from flask import Blueprint, render_template, jsonify
from sqlalchemy import text, inspect

from src.models.user import db

logger = logging.getLogger(__name__)

# O template_folder aponta para ../templates relativo a este arquivo
admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="../templates",
    static_folder="../static",
)

# ----------------------------
# Helpers seguros (não quebram se a tabela não existir)
# ----------------------------
def _tables() -> List[str]:
    """Lista nomes de tabelas existentes no DB."""
    try:
        return inspect(db.engine).get_table_names()
    except Exception as e:
        logger.warning(f"Inspector failed: {e}")
        return []

def _first_existing(candidates: List[str]) -> str | None:
    """Retorna o primeiro nome de tabela que existir dentre os candidatos."""
    existing = set(_tables())
    for name in candidates:
        if name in existing:
            return name
    return None

def _safe_count(table_candidates: List[str]) -> int:
    """COUNT(*) robusto: retorna 0 se a(s) tabela(s) não existir(em)."""
    table = _first_existing(table_candidates)
    if not table:
        return 0
    try:
        sql = text(f"SELECT COUNT(*) AS c FROM {table}")
        row = db.session.execute(sql).first()
        return int(row[0]) if row else 0
    except Exception as e:
        logger.warning(f"count({table}) failed: {e}")
        return 0

def _safe_recent_campaign_runs(limit: int = 5) -> List[Dict[str, Any]]:
    """Últimas execuções de campanhas, se a tabela existir."""
    table = _first_existing(["wa_campaign_runs"])
    if not table:
        return []
    try:
        sql = text(
            f"""
            SELECT id, campaign_id, run_at, phone_e164, status, error_message
            FROM {table}
            ORDER BY run_at DESC
            LIMIT :lim
            """
        )
        rows = db.session.execute(sql, {"lim": limit}).mappings().all()
        out = []
        for r in rows:
            out.append(
                {
                    "id": r.get("id"),
                    "campaign_id": str(r.get("campaign_id")) if r.get("campaign_id") else None,
                    "run_at": r.get("run_at").isoformat() if r.get("run_at") else None,
                    "phone_e164": r.get("phone_e164"),
                    "status": r.get("status"),
                    "error_message": r.get("error_message"),
                }
            )
        return out
    except Exception as e:
        logger.warning(f"recent campaign runs failed: {e}")
        return []

def _safe_recent_patients(limit: int = 5) -> List[Dict[str, Any]]:
    """Alguns pacientes recentes, tentando ambos esquemas ('patients' e 'patient')."""
    table = _first_existing(["patients", "patient"])
    if not table:
        return []
    cols_candidates = [
        # esquema mais novo
        ("id", "name", "phone_e164", "active", "created_at"),
        # esquema alternativo antigo
        ("id", "name", "whatsapp_phone", "is_active", "created_at"),
    ]
    try:
        # Descobrir colunas disponíveis nesta tabela
        insp = inspect(db.engine)
        colnames = {c["name"] for c in insp.get_columns(table)}
        cols = None
        mapping = None
        for cand in cols_candidates:
            if set(cand).issubset(colnames):
                cols = cand
                # mapeia nomes para saída comum
                if cand == ("id", "name", "phone_e164", "active", "created_at"):
                    mapping = {"id": "id", "name": "name", "phone": "phone_e164", "active": "active", "created_at": "created_at"}
                else:
                    mapping = {"id": "id", "name": "name", "phone": "whatsapp_phone", "active": "is_active", "created_at": "created_at"}
                break
        if not cols:
            return []

        sql = text(
            f"""
            SELECT {", ".join(cols)}
            FROM {table}
            ORDER BY created_at DESC
            LIMIT :lim
            """
        )
        rows = db.session.execute(sql, {"lim": limit}).mappings().all()
        out = []
        for r in rows:
            out.append(
                {
                    "id": r.get(mapping["id"]),
                    "name": r.get(mapping["name"]),
                    "phone": r.get(mapping["phone"]),
                    "active": r.get(mapping["active"]),
                    "created_at": r.get(mapping["created_at"]).isoformat() if r.get(mapping["created_at"]) else None,
                }
            )
        return out
    except Exception as e:
        logger.warning(f"recent patients failed: {e}")
        return []

# ----------------------------
# Rotas de UI
# ----------------------------
@admin_bp.route("/", strict_slashes=False)
def admin_index():
    """
    Tenta renderizar o template principal do Admin.
    Se o template não existir, retorna um JSON com dica.
    """
    try:
        # Tente estes nomes (ajuste aqui se o seu template tiver outro nome)
        for tpl in ("index.html", "admin.html", "dashboard.html"):
            try:
                return render_template(tpl)
            except Exception:
                continue
        # Se nenhum template rendeu, informe com JSON (sem derrubar o Admin)
        return jsonify(
            {
                "ok": False,
                "error": "Admin UI not loaded",
                "hint": "verifique templates em src/admin/templates (ex.: index.html)",
            }
        ), 503
    except Exception as e:
        logger.error(f"Admin index failed: {e}")
        return jsonify({"ok": False, "error": "Admin UI fatal error"}), 500

# ----------------------------
# APIs usadas pelo painel
# ----------------------------
@admin_bp.route("/api/health", methods=["GET"])
def admin_health():
    """Saúde básica do Admin + DB ping."""
    try:
        db.session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.warning(f"DB ping failed: {e}")
        db_ok = False

    return jsonify(
        {
            "ok": True,
            "service": "admin-ui",
            "db": "up" if db_ok else "down",
            "time": datetime.utcnow().isoformat() + "Z",
        }
    )

@admin_bp.route("/api/stats", methods=["GET"])
def admin_stats():
    """
    Estatísticas compactas (alguns frontends antigos chamam este endpoint).
    """
    try:
        total_patients = _safe_count(["patients", "patient"])
        total_campaigns = _safe_count(["wa_campaigns"])
        total_runs = _safe_count(["wa_campaign_runs"])
        return jsonify(
            {
                "ok": True,
                "stats": {
                    "patients": total_patients,
                    "campaigns": total_campaigns,
                    "campaign_runs": total_runs,
                },
            }
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"ok": False, "error": "stats failed"}), 500

@admin_bp.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    """
    Versão “dashboard” das estatísticas (alguns UIs usam este caminho).
    """
    try:
        total_patients = _safe_count(["patients", "patient"])
        active_patients = 0
        # tenta contar ativos se existir a coluna correspondente
        table = _first_existing(["patients", "patient"])
        if table:
            try:
                # tenta variantes de coluna de ativo
                for col in ("active", "is_active"):
                    try:
                        sql = text(f"SELECT COUNT(*) FROM {table} WHERE {col}=1")
                        active_patients = db.session.execute(sql).scalar() or 0
                        break
                    except Exception:
                        continue
            except Exception:
                pass

        total_campaigns = _safe_count(["wa_campaigns"])
        total_runs = _safe_count(["wa_campaign_runs"])

        return jsonify(
            {
                "ok": True,
                "stats": {
                    "patients_total": total_patients,
                    "patients_active": active_patients,
                    "wa_campaigns": total_campaigns,
                    "wa_campaign_runs": total_runs,
                },
            }
        )
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({"ok": False, "error": "dashboard stats failed"}), 500

@admin_bp.route("/api/dashboard/recent", methods=["GET"])
def dashboard_recent():
    """
    Itens recentes para cards do painel.
    """
    try:
        return jsonify(
            {
                "ok": True,
                "recent": {
                    "patients": _safe_recent_patients(limit=5),
                    "campaign_runs": _safe_recent_campaign_runs(limit=5),
                },
            }
        )
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return jsonify({"ok": False, "error": "recent failed"}), 500
