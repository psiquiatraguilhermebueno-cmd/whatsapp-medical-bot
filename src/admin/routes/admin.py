# src/admin/routes/admin.py
import logging
from flask import Blueprint, render_template, jsonify, redirect
from src.models.user import db

logger = logging.getLogger(__name__)

# Blueprint do Admin. O prefixo /admin é aplicado no main.py
admin_bp = Blueprint("admin", __name__)

# ------------------------
# Helpers tolerantes a erro
# ------------------------
def _model_class(module_name: str, class_name: str):
    """
    Importa dinamicamente um modelo. Retorna None se falhar.
    """
    try:
        mod = __import__(f"src.models.{module_name}", fromlist=[class_name])
        return getattr(mod, class_name, None)
    except Exception as e:
        logger.warning("Falha ao importar %s.%s: %s", module_name, class_name, e)
        return None


def _safe_count(module_name: str, class_name: str) -> int:
    """
    Faz COUNT(*) com segurança; se falhar, retorna 0.
    """
    Model = _model_class(module_name, class_name)
    if Model is None:
        return 0
    try:
        return db.session.query(Model).count()
    except Exception as e:
        logger.warning("COUNT falhou para %s.%s: %s", module_name, class_name, e)
        return 0


def _safe_recent(module_name: str, class_name: str, order_field: str = "created_at", limit: int = 5):
    """
    Busca registros recentes com segurança; se falhar, retorna lista vazia.
    """
    Model = _model_class(module_name, class_name)
    if Model is None:
        return []

    try:
        col = getattr(Model, order_field, None)
        q = db.session.query(Model)
        if col is not None:
            q = q.order_by(col.desc())
        rows = q.limit(limit).all()
        out = []
        for r in rows:
            if hasattr(r, "to_dict"):
                out.append(r.to_dict())
            else:
                # fallback mínimo
                out.append({"id": getattr(r, "id", None)})
        return out
    except Exception as e:
        logger.warning("Recent falhou para %s.%s: %s", module_name, class_name, e)
        return []


# ------------------------
# Rotas da UI do Admin
# ------------------------
@admin_bp.route("/", methods=["GET"])
def admin_home():
    """
    Página raiz do Admin. Renderiza o template SPA.
    """
    try:
        # Mantemos o caminho 'admin/index.html' para compatibilidade
        return render_template("admin/index.html"), 200
    except Exception:
        # Fallback em JSON para diagnóstico, caso o template não esteja acessível
        return (
            jsonify(
                {
                    "ok": True,
                    "ui": "admin",
                    "message": "Template admin/index.html não encontrado. Verifique a pasta src/templates/admin/",
                }
            ),
            200,
        )


# ------------------------
# APIs usadas pelo dashboard do Admin
# ------------------------
@admin_bp.route("/api/stats", methods=["GET"])
def stats():
    """
    Retorna contadores básicos do sistema.
    Tolerante à ausência de modelos/tabelas.
    """
    data = {
        # Pacientes: prioriza Patient em src/models/patient.py (tabela 'patients')
        "patients": _safe_count("patient", "Patient"),
        "reminders": _safe_count("reminder", "Reminder"),
        "responses": _safe_count("response", "Response"),
        "medications": _safe_count("medication", "Medication"),
        "breathing_exercises": _safe_count("breathing_exercise", "BreathingExercise"),
        # Campanhas são opcionais; se não existirem, retornam 0
        "wa_campaigns": _safe_count("campaign", "WACampaign"),
    }
    return jsonify(data), 200


@admin_bp.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    """
    Alias simples para /admin/api/stats (mantém compatibilidade com o frontend).
    """
    return stats()


@admin_bp.route("/api/dashboard/recent", methods=["GET"])
def dashboard_recent():
    """
    Retorna itens recentes por tipo para preencher cards do dashboard.
    """
    data = {
        "patients": _safe_recent("patient", "Patient"),
        "reminders": _safe_recent("reminder", "Reminder"),
        "responses": _safe_recent("response", "Response"),
        "medications": _safe_recent("medication", "Medication"),
        "breathing": _safe_recent("breathing_exercise", "BreathingExercise"),
        # Campanhas são opcionais
        "campaigns": _safe_recent("campaign", "WACampaign"),
    }
    return jsonify(data), 200


# ------------------------------------------------------
# SPA catch-all: qualquer /admin/* (exceto /admin/api/*)
# renderiza a mesma SPA para suportar deep links do frontend
# ------------------------------------------------------
@admin_bp.route("/<path:subpath>", methods=["GET"])
def admin_spa_catch_all(subpath: str):
    if subpath.startswith("api/"):
        # Deixa as rotas de API responderem 404 normalmente se não existirem
        return jsonify({"error": "Not Found"}), 404
    try:
        return render_template("admin/index.html"), 200
    except Exception:
        # Se o template não estiver acessível, redireciona para a raiz do Admin
        return redirect("/admin")
