"""
Publicador de eventos de domínio (singleton thread-safe).
"""

import logging
from typing import List, Callable, Dict
from threading import Lock
from src.domain.events.domain_event import DomainEvent


class DomainEventPublisher:
    """
    Publicador centralizado de eventos de domínio.
    
    Implementa padrão Observer para desacoplar entidades de seus handlers.
    Thread-safe com lock para operações de registro e publicação.
    
    Singleton: Uma única instância por aplicação.
    
    Exemplo de uso:
        publisher = DomainEventPublisher()
        publisher.subscribe("TrackMaxEventsReached", meu_handler)
        publisher.publish(evento)
    """

    _instance = None
    _lock = Lock()
    _initialized = False

    def __new__(cls):
        """Implementa singleton thread-safe."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Inicializa o publicador apenas uma vez."""
        # Evita reinicialização em múltiplas chamadas
        if DomainEventPublisher._initialized:
            return
        
        self._handlers: Dict[str, List[Callable]] = {}
        self._logger = logging.getLogger(self.__class__.__name__)
        DomainEventPublisher._initialized = True

    def subscribe(self, event_name: str, handler: Callable[[DomainEvent], None]) -> None:
        """
        Registra um handler para um tipo de evento.

        :param event_name: Nome do evento (ex: "TrackMaxEventsReached").
        :param handler: Função callable que processa o evento.
        :raises TypeError: Se handler não for callable.
        """
        if not callable(handler):
            raise TypeError(f"handler deve ser callable, recebido: {type(handler).__name__}")
        
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        
        self._handlers[event_name].append(handler)
        self._logger.debug(f"Handler registrado para evento: {event_name}")

    def unsubscribe(self, event_name: str, handler: Callable[[DomainEvent], None]) -> None:
        """
        Remove um handler de um tipo de evento.

        :param event_name: Nome do evento.
        :param handler: Função a ser removida.
        """
        if event_name in self._handlers:
            try:
                self._handlers[event_name].remove(handler)
                self._logger.debug(f"Handler removido de evento: {event_name}")
            except ValueError:
                pass

    def publish(self, event: DomainEvent) -> None:
        """
        Publica um evento para todos os handlers registrados.

        :param event: Evento a ser publicado.
        :raises TypeError: Se event não for DomainEvent.
        """
        if not isinstance(event, DomainEvent):
            raise TypeError(f"event deve ser DomainEvent, recebido: {type(event).__name__}")
        
        event_name = event.event_name()
        handlers = self._handlers.get(event_name, [])
        
        self._logger.debug(f"Publicando evento: {event_name}, handlers: {len(handlers)}")
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                pass

    def clear(self) -> None:
        """
        Limpa todos os handlers registrados.
        
        Útil para testes onde é necessário limpar estado anterior.
        """
        self._handlers.clear()
        self._logger.debug("Todos os handlers foram removidos")

    def __repr__(self) -> str:
        """Representação do publicador."""
        total_handlers = sum(len(h) for h in self._handlers.values())
        return f"DomainEventPublisher(events={len(self._handlers)}, handlers={total_handlers})"
