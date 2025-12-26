"""
Domain Events - Eventos de domínio.

Implementa o padrão Observer para desacoplar entidades de seus consumidores.
Permite que eventos de domínio sejam publicados sem acoplamento direto.

Exportações públicas da camada de domínio.
"""

from .domain_event import DomainEvent
from .domain_event_publisher import DomainEventPublisher

__all__ = [
    'DomainEvent',
    'DomainEventPublisher',
]
