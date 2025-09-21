# src/ops/boot_sentinel.py
import json, os, traceback, datetime, pathlib

STATE_PATH = "/tmp/boot_state.json"

def _now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

def read_state():
    p = pathlib.Path(STATE_PATH)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    # default
    return {
        "main_loaded": False,
        "error_type": None,
        "file": None,
        "line": None,
        "summary": None,
        "last_attempt": _now_iso(),
        "source": "default"
    }

def write_state(d):
    d = dict(d or {})
    d.setdefault("last_attempt", _now_iso())
    try:
        pathlib.Path(STATE_PATH).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

def from_exception(exc: Exception):
    tb = traceback.TracebackException.from_exception(exc)
    file = line = None
    for frame in tb.stack[::-1]:
        # prefer src/main.py se existir
        if frame.filename.endswith("src/main.py"):
            file = "src/main.py"
            line = frame.lineno
            break
        if file is None:
            file = frame.filename
            line = frame.lineno
    etype = type(exc).__name__
    return {
        "main_loaded": False,
        "error_type": etype,
        "file": file if file else None,
        "line": int(line) if line else None,
        "summary": "".join(tb.format_exception_only()).strip(),
        "last_attempt": _now_iso(),
        "source": "exception"
    }
