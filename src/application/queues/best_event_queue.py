"""
Fila de processamento dos melhores eventos de tracks encerrados.
"""

import queue
from typing import Optional
from src.domain.entities import Event


class BestEventQueue:
    """
    Fila thread-safe para enfileiramento de Event (melhor evento de tracks).
    
    Utiliza queue.Queue interna para thread-safety e permite
    múltiplos produtores e consumidores.
    """

    def __init__(self, maxsize: int = 1000):
        """
        Inicializa a fila de melhores eventos.

        :param maxsize: Tamanho máximo da fila. 0 = ilimitado.
        """
        self._queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self._maxsize = maxsize

    def put(self, event: Event, block: bool = True, timeout: Optional[float] = None) -> None:
        """
        Enfileira um Event (melhor evento).

        :param event: Event a ser enfileirado.
        :param block: Se True, bloqueia se a fila está cheia.
        :param timeout: Timeout em segundos para enfilar.
        :raises TypeError: Se event não for Event.
        :raises queue.Full: Se timeout expirar e fila está cheia.
        """
        if not isinstance(event, Event):
            raise TypeError(f"event deve ser Event, recebido: {type(event).__name__}")
        
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            import logging
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning(f"BestEventQueue está cheia! Event descartado. Tamanho da fila: {self._queue.qsize()}")
            raise

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Event:
        """
        Desfileira um Event.

        :param block: Se True, bloqueia se a fila está vazia.
        :param timeout: Timeout em segundos para desfilar.
        :return: Event desfileirado.
        :raises queue.Empty: Se timeout expirar e fila está vazia.
        """
        return self._queue.get(block=block, timeout=timeout)

    def empty(self) -> bool:
        """
        Verifica se a fila está vazia.

        :return: True se fila vazia, False caso contrário.
        """
        return self._queue.empty()

    def qsize(self) -> int:
        """
        Retorna o tamanho aproximado da fila.

        :return: Número aproximado de itens na fila.
        """
        return self._queue.qsize()

    def full(self) -> bool:
        """
        Verifica se a fila está cheia.

        :return: True se fila cheia, False caso contrário.
        """
        return self._queue.full()

    def get_nowait(self) -> Event:
        """
        Tenta desfilear sem bloquear.

        :return: Event desfileirado.
        :raises queue.Empty: Se a fila está vazia.
        """
        return self._queue.get_nowait()

    def put_nowait(self, event: Event) -> None:
        """
        Tenta enfileirar um Event sem bloquear.

        :param event: Event a ser enfileirado.
        :raises TypeError: Se event não for Event.
        :raises queue.Full: Se a fila está cheia.
        """
        if not isinstance(event, Event):
            raise TypeError(f"event deve ser Event, recebido: {type(event).__name__}")
        
        self._queue.put_nowait(event)

    def __repr__(self) -> str:
        """
        Representação da fila.

        :return: String representando a fila.
        """
        return f"BestEventQueue(size={self.qsize()}/{self._maxsize})"
