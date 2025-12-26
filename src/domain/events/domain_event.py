"""
Classe base para eventos de domínio.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict


class DomainEvent(ABC):
    """
    Classe base para eventos de domínio.
    
    Eventos de domínio representam fatos importantes que ocorreram no domínio
    e devem ser processados por interessados (handlers).
    
    Implementa padrão Observer para desacoplar entidades de seus consumidores.
    """

    def __init__(self):
        """Inicializa o evento com timestamp."""
        self._occurred_at: datetime = datetime.now()

    @property
    def occurred_at(self) -> datetime:
        """Retorna o momento em que o evento ocorreu."""
        return self._occurred_at

    @abstractmethod
    def event_name(self) -> str:
        """
        Retorna o nome do evento.
        
        Deve ser implementado por subclasses.
        :return: Nome único do evento (ex: "TrackMaxEventsReached").
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o evento para dicionário.
        
        Deve ser implementado por subclasses para serialização.
        :return: Dicionário com dados do evento.
        """
        pass

    def __repr__(self) -> str:
        """Representação do evento."""
        return f"{self.event_name()}(occurred_at={self._occurred_at})"
