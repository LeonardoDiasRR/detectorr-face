"""
Serviço de domínio para encerrar um track.
"""

import logging
import threading
import queue
from typing import Optional

from src.domain.value_objects import IdVO
from src.domain.entities.track_entity import Track
from src.application.tracking.track_registry import TrackRegistry
from src.application.queues.best_event_queue import BestEventQueue


class FinishTrackService:
    """
    Serviço de domínio responsável por encerrar o ciclo de vida de um track.
    
    Quando um track é encerrado:
    1. Recupera o track do registro em memória
    2. Extrai o melhor evento do track
    3. Enfileira o melhor Event na BestEventQueue
    4. Remove o track do registro em memória
    
    Segue os princípios DDD:
    - Encapsula regras de negócio do domínio (ciclo de vida de track)
    - Não contém lógica de persistência (delega ao registry)
    - Não contém lógica de comunicação entre camadas (delega à fila)
    """

    def __init__(
        self,
        track_registry: TrackRegistry,
        best_event_queue: BestEventQueue
    ):
        """
        Inicializa o serviço de domínio.

        :param track_registry: Registro de tracks em memória.
        :param best_event_queue: Fila de melhores eventos.
        :raises TypeError: Se parâmetros forem do tipo inválido.
        """
        if not isinstance(track_registry, TrackRegistry):
            raise TypeError(f"track_registry deve ser TrackRegistry, recebido: {type(track_registry).__name__}")
        if not isinstance(best_event_queue, BestEventQueue):
            raise TypeError(f"best_event_queue deve ser BestEventQueue, recebido: {type(best_event_queue).__name__}")
        
        self._track_registry = track_registry
        self._best_event_queue = best_event_queue
        self._logger = logging.getLogger(self.__class__.__name__)
        self._lock = threading.Lock()

    def finish_track(self, camera_id: IdVO, track_id: int, reason: str) -> None:
        """
        Encerra o ciclo de vida de um track.
        
        Recupera o track, extrai seu melhor evento, enfileira-o,
        e remove o track do registro.

        :param camera_id: ID da câmera (IdVO).
        :param track_id: ID do track (int).
        :param reason: Motivo da finalização do track (str).
        :raises TypeError: Se camera_id não for IdVO, track_id não for int ou reason não for str.
        """
        if not isinstance(camera_id, IdVO):
            raise TypeError(f"camera_id deve ser IdVO, recebido: {type(camera_id).__name__}")
        if not isinstance(track_id, int):
            raise TypeError(f"track_id deve ser int, recebido: {type(track_id).__name__}")
        if not isinstance(reason, str) or not reason.strip():
            raise TypeError(f"reason deve ser string não-vazia, recebido: {reason}")
        
        # Proteger acesso ao registry contra race condition
        with self._lock:
            # Recuperar track do registro
            track: Optional[Track] = self._track_registry.get(camera_id.value(), track_id)
            
            if track is None:
                return
            
            # Verificar se o track possui melhor evento
            best_event = track.best_event
            if best_event is None:
                self._track_registry.remove(camera_id.value(), track_id)
                return
            
            # Remover track do registro (protegido por lock)
            self._track_registry.remove(camera_id.value(), track_id)
        
        # Marcar se o track teve movimento e enfileirar melhor evento (entidade de domínio) fora do lock
        # Usa put_nowait() para não bloquear caso a fila esteja cheia
        try:
            # Anexar flag de movimento para que o consumidor possa filtrar
            try:
                setattr(best_event, '_movement', track.has_movement)
            except Exception:
                pass
            self._best_event_queue.put_nowait(best_event)
        except queue.Full:
            # Fila cheia - descartar evento e liberar memória
            quality = best_event.face_quality_score.value() if best_event.face_quality_score else 0.0
            confidence = best_event.confidence.value()
            
            # # CRÍTICO: Liberar memória explicitamente para evitar vazamento
            # try:
            #     if best_event and best_event.frame and hasattr(best_event.frame, '_full_frame'):
            #         # Acessar atributo interno (_full_frame) já que full_frame é property read-only
            #         best_event.frame._full_frame = None
            # except Exception as cleanup_error:
            #     pass
            
            # # Liberar referência completa do evento
            # del best_event
        
        # Track removido do registry com sucesso
