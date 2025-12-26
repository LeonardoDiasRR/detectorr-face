"""
Fila de processamento de eventos de domínio.
"""

import queue
from typing import Optional
from src.domain.events.domain_event import DomainEvent


class DomainEventQueue:
    """
    Fila thread-safe para enfileiramento de DomainEvent.
    
    Utiliza queue.Queue interna para thread-safety e permite
    múltiplos produtores e consumidores processar eventos de domínio
    de forma assíncrona.
    
    Exemplo de uso:
        queue = DomainEventQueue(maxsize=1000)
        queue.put(domain_event)
        event = queue.get(timeout=0.5)
    """

    def __init__(self, maxsize: int = 1000):
        """
        Inicializa a fila de eventos de domínio.

        :param maxsize: Tamanho máximo da fila. 0 = ilimitado.
        """
        self._queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self._maxsize = maxsize

    def put(self, domain_event: DomainEvent, block: bool = True, timeout: Optional[float] = None) -> None:
        """
        Enfileira um DomainEvent.

        :param domain_event: DomainEvent a ser enfileirado.
        :param block: Se True, bloqueia se a fila está cheia.
        :param timeout: Timeout em segundos para enfilar.
        :raises TypeError: Se domain_event não for DomainEvent.
        :raises queue.Full: Se timeout expirar e fila está cheia.
        """
        if not isinstance(domain_event, DomainEvent):
            raise TypeError(f"domain_event deve ser DomainEvent, recebido: {type(domain_event).__name__}")
        
        try:
            self._queue.put_nowait(domain_event)
        except queue.Full:
            import logging
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(f"DomainEventQueue está cheia! DomainEvent descartado. Tamanho da fila: {self._queue.qsize()}")
            raise

    def put_nowait(self, domain_event: DomainEvent) -> None:
        """
        Enfileira um DomainEvent sem bloqueio.

        :param domain_event: DomainEvent a ser enfileirado.
        :raises TypeError: Se domain_event não for DomainEvent.
        :raises queue.Full: Se a fila está cheia.
        """
        if not isinstance(domain_event, DomainEvent):
            raise TypeError(f"domain_event deve ser DomainEvent, recebido: {type(domain_event).__name__}")
        
        try:
            self._queue.put_nowait(domain_event)
        except queue.Full:
            import logging
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(f"DomainEventQueue está cheia! DomainEvent descartado. Tamanho da fila: {self._queue.qsize()}")
            raise

    def get(self, block: bool = True, timeout: Optional[float] = None) -> DomainEvent:
        """
        Desfileira um DomainEvent.

        :param block: Se True, bloqueia se a fila está vazia.
        :param timeout: Timeout em segundos para desfilar.
        :return: DomainEvent desfileirado.
        :raises queue.Empty: Se timeout expirar e fila está vazia.
        """
        return self._queue.get(block=block, timeout=timeout)

    def empty(self) -> bool:
        """
        Verifica se a fila está vazia.

        :return: True se fila vazia, False caso contrário.
        """
        return self._queue.empty()

    def full(self) -> bool:
        """
        Verifica se a fila está cheia.

        :return: True se fila cheia, False caso contrário.
        """
        return self._queue.full()

    def qsize(self) -> int:
        """
        Retorna o tamanho aproximado da fila.

        :return: Número aproximado de itens na fila.
        """
        return self._queue.qsize()

    def __repr__(self) -> str:
        """
        Representação da fila.

        :return: String representando a fila.
        """
        return f"DomainEventQueue(size={self.qsize()}/{self._maxsize if self._maxsize > 0 else 'unlimited'})"
