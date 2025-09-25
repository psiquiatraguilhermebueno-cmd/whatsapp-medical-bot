# Compatibility shim to avoid double table mapping.
# This file exposes Patient from the canonical 'patients' module.
from src.models.patients import Patient  # noqa: F401
__all__ = ["Patient"]
