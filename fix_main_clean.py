# fix_main_clean.py — fallback estável com /health e uma home simples
from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify(status="ok", source="fix_main_clean"), 200

@app.get("/")
def home():
    return jsonify(
        service="whatsapp-medical-bot",
        mode="fallback",
        message="Fallback ativo (fix_main_clean). O main.py será carregado quando a correção entrar.",
        next_steps=[
            "Watcher deve abrir PR de correção de indentação no src/main.py",
            "Após o merge, o deploy volta a carregar o main.app automaticamente"
        ],
    ), 200
