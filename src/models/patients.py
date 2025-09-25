# src/models/patients.py
# Compatibilidade: NÃO declare outra tabela aqui.
# Apenas reexporta o modelo oficial para manter imports antigos funcionando.
from src.models.patient import Patient  # noqa: F401

__all__ = ["Patient"]
