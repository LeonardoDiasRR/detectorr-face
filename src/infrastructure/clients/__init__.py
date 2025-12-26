"""
Clientes para integração com sistemas externos.
"""

from src.infrastructure.clients.findface_multi import FindfaceMulti
from src.infrastructure.clients.findface_adapter import FindfaceAdapter

__all__ = ["FindfaceMulti", "FindfaceAdapter"]
