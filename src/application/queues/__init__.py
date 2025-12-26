"""
Filas de processamento da aplicação.
"""

from .best_event_queue import BestEventQueue
from .domain_event_queue import DomainEventQueue

__all__ = [
    'BestEventQueue',
    'DomainEventQueue',
]
