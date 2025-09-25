# src/models/mood_chart.py
# Stub de compatibilidade para imports legados.
# NÃO cria tabela, só evita ModuleNotFoundError.

from src.models.user import db

class MoodChart(db.Model):
    __abstract__ = True
