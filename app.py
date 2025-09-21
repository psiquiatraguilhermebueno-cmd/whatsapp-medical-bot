#!/usr/bin/env python3
"""
Entry point com sentinela de boot.
- Inicializa DB
- Tenta carregar main.app
- Em falha, registra arquivo/linha e carrega fallback (fix_main_clean ou simple_app)
- Exponde /ops/boot-state em QUALQUER app carregado
"""
import os, sys, sqlite3, importlib, traceback
from datetime import datetime

# Adiciona src ao path
BASE_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Sentinela
from ops.boot_sentinel import read_state, write_state, from_exception

def init_database():
    db_path = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "app.db"))
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' LIMIT 1")
            cur.fetchone()
            conn.close()
            print("✅ Database already initialized")
            return
        except Exception:
            pass

    print("🚀 Initializing database...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("""CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone_e164 TEXT NOT NULL UNIQUE,
            tags TEXT,
            active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS wa_campaigns (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            template_name TEXT NOT NULL,
            lang_code TEXT NOT NULL DEFAULT 'pt_BR',
            params_mode TEXT NOT NULL DEFAULT 'fixed',
            fixed_params TEXT,
            tz TEXT NOT NULL DEFAULT 'America/Sao_Paulo',
            start_at DATETIME NOT NULL,
            end_at DATETIME,
            frequency TEXT NOT NULL DEFAULT 'once',
            days_of_week TEXT,
            day_of_month INTEGER,
            send_time TEXT NOT NULL,
            cron_expr TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS wa_campaign_recipients (
            campaign_id TEXT NOT NULL,
            phone_e164 TEXT NOT NULL,
            per_params TEXT,
            PRIMARY KEY (campaign_id, phone_e164)
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS wa_campaign_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id TEXT NOT NULL,
            run_at DATETIME NOT NULL,
            phone_e164 TEXT NOT NULL,
            payload TEXT,
            wa_response TEXT,
            status TEXT NOT NULL DEFAULT 'ok',
            error_message TEXT
        )""")
        conn.commit()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        conn.rollback()
    finally:
        conn.close()

def _attach_boot_state_route(flask_app):
    @flask_app.get("/ops/boot-state")
    def boot_state():
        st = read_state()
        # PATCH: se não houver state e app atual for "main", considerar loaded
        try:
            name = flask_app.import_name or ""
        except Exception:
            name = ""
        if st.get("source") == "default" and ("main" in (name or "")):
            st["main_loaded"] = True
            st["source"] = "inferred"
        return (st, 200)

def _load_module_app(mod_name, attr="app"):
    mod = importlib.import_module(mod_name)
    app = getattr(mod, attr, None)
    if app is None:
        raise RuntimeError(f"Module '{mod_name}' does not expose '{attr}'")
    return app

def create_app():
    # 1) tenta main
    try:
        app = _load_module_app("main", "app")
        write_state({"main_loaded": True, "source": "main_boot"})
        _attach_boot_state_route(app)
        print("[BOOT] Loaded main.app")
        return app
    except Exception as e:
        # 2) registra falha com arquivo/linha
        st = from_exception(e)
        write_state(st)
        print(f"[BOOT][WARN] Failed to load main.app: {st.get('error_type')} ({st.get('file')}, line {st.get('line')})")
        # 3) fallback 1: fix_main_clean
        try:
            app = _load_module_app("fix_main_clean", "app")
            _attach_boot_state_route(app)
            print("[BOOT] Loaded fix_main_clean.app")
            return app
        except Exception as e2:
            print(f"[BOOT][WARN] Failed to load fix_main_clean.app: {e2}")
        # 4) fallback 2: simple_app
        from simple_app import app as simple
        _attach_boot_state_route(simple)
        print("[BOOT] Loaded simple_app.app")
        return simple

# --- main ---
init_database()
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
