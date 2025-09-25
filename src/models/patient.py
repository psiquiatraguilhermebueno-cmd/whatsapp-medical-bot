# src/models/patient.py
# Alias/shim para manter compatibilidade com imports antigos.
# Não cria tabela; apenas reexporta o modelo canônico.
from .patients import Patient  # noqa: F401
