"""
Caso de uso para expiração de tracks por TTL (Time-To-Live).
"""

import logging
import threading
import time
from multiprocessing import cpu_count
from datetime import datetime
from typing import List, Optional

from src.infrastructure.tracking.in_memory_track_registry import InMemoryTrackRegistry
from src.domain.services.finish_track_service import FinishTrackService
from src.domain.value_objects import IdVO
from src.infrastructure.config import get_settings


class ExpireTracksUseCase:
    """
    Caso de uso para monitorar e expirar tracks inativos por TTL.
    
    Instancia N workers (CPUs/4) que executam em threads daemon.
    Cada worker:
    - Aguarda 1 segundo
    - Acessa todos os tracks de todas as câmeras
    - Verifica o _last_seen_frame_timestamp de cada track
    - Se (agora - last_seen) > TTL: chama FinishTrackService
    
    Segue os princípios:
    - DDD: Processa regra de negócio (expiração por TTL)
    - SOLID (SRP): Responsável apenas por expiração de TTL
    - Concorrência: N workers independentes em daemon threads
    
    Exemplo de uso:
        use_case = ExpireTracksUseCase(track_registry, finish_service)
        use_case.start()
        # ... aplicação roda ...
        use_case.stop(timeout=5.0)
    """

    def __init__(
        self,
        track_registry: InMemoryTrackRegistry,
        finish_track_service: FinishTrackService,
        num_workers: Optional[int] = None,
        sleep_interval: float = 1.0,
        config_path: Optional[str] = None
    ):
        """
        Inicializa o caso de uso.

        :param track_registry: Registro de tracks em memória.
        :param finish_track_service: Serviço para encerrar tracks.
        :param num_workers: Número de workers. Se None, usa CPUs/4.
        :param sleep_interval: Intervalo de sleep em segundos (padrão 1.0).
        :param config_path: Caminho para arquivo de configuração (opcional).
        :raises TypeError: Se parâmetros forem do tipo inválido.
        """
        if not isinstance(track_registry, InMemoryTrackRegistry):
            raise TypeError(
                f"track_registry deve ser InMemoryTrackRegistry, "
                f"recebido: {type(track_registry).__name__}"
            )
        
        if not isinstance(finish_track_service, FinishTrackService):
            raise TypeError(
                f"finish_track_service deve ser FinishTrackService, "
                f"recebido: {type(finish_track_service).__name__}"
            )
        
        self._track_registry = track_registry
        self._finish_track_service = finish_track_service
        self._num_workers = num_workers or max(cpu_count() // 4, 1)
        self._sleep_interval = sleep_interval
        self._workers: List[threading.Thread] = []
        self._stop_event = threading.Event()
        self._lock = threading.Lock()  # Lock para acesso thread-safe ao registry
        self._logger = logging.getLogger(self.__class__.__name__)
        
        # Carregar TTL da configuração centralizada
        settings = get_settings()
        self._lost_ttl = settings.track.lost_ttl if hasattr(settings.track, 'lost_ttl') else 3
        self._active_ttl = settings.track.active_ttl if hasattr(settings.track, 'active_ttl') else 30

    def start(self) -> None:
        """
        Inicia os workers de expiração de TTL.
        
        Cria N threads daemon que checam expiração a cada 1 segundo.
        """
        self._stop_event.clear()
        
        for worker_id in range(self._num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(worker_id,),
                daemon=True,
                name=f"ExpireTracksWorker-{worker_id}"
            )
            worker.start()
            self._workers.append(worker)

    def stop(self, timeout: Optional[float] = None) -> None:
        """
        Para os workers de expiração.

        :param timeout: Tempo em segundos para aguardar término das threads.
        """
        self._stop_event.set()
        
        for worker in self._workers:
            worker.join(timeout=timeout)
        
        self._workers.clear()

    def _worker_loop(self, worker_id: int) -> None:
        """
        Loop principal de um worker de expiração.
        
        A cada intervalo configurado:
        1. Obtém timestamp atual
        2. Itera sobre todos os tracks de todas as câmeras
        3. Verifica TTL de cada track
        4. Encerra tracks expirados
        
        :param worker_id: ID único do worker.
        """
        
        while not self._stop_event.is_set():
            try:
                # Aguardar intervalo configurado
                if self._stop_event.wait(timeout=self._sleep_interval):
                    # Stop event foi sinalizado
                    break
                
                # Obter timestamp atual
                current_time = datetime.now()
                
                # Verificar expiração de tracks
                self._check_expired_tracks(current_time, worker_id)
            
            except Exception as e:
                pass

    def _check_expired_tracks(self, current_time: datetime, worker_id: int) -> None:
        """
        Verifica expiração de todos os tracks de todas as câmeras.
        
        Acessa InMemoryTrackRegistry com lock para evitar race conditions
        entre múltiplos workers e outras threads que acessam o registry.
        
        Itera sobre:
        - Todas as câmeras
        - Todos os tracks de cada câmera
        - Compara (agora - last_seen) com TTL
        
        :param current_time: Timestamp atual.
        :param worker_id: ID do worker para logging.
        """
        try:
            # Usar lock para acesso thread-safe ao registry
            with self._lock:
                # Acessar dicionário interno do registry
                registry_dict = self._track_registry._tracks
                
                # Iterar sobre todas as câmeras (criar cópia da lista de keys)
                for camera_id in list(registry_dict.keys()):
                    tracks_dict = registry_dict.get(camera_id)
                    
                    if tracks_dict is None:
                        continue
                    
                    # Iterar sobre todos os tracks da câmera (criar cópia da lista de keys)
                    for track_id in list(tracks_dict.keys()):
                        track = tracks_dict.get(track_id)
                        
                        if track is None:
                            continue
                        
                        # Verificar se track expirou por TTL
                        last_seen = track._last_seen_frame_timestamp
                        
                        if last_seen is None:
                            # Track sem eventos ainda, não expira
                            continue
                        
                        # Calcular tempo inativo
                        time_inactive = (current_time - last_seen).total_seconds()
                        
                        # Calcular tempo de vida ativo
                        started_at = track._started_at
                        time_active = (current_time - started_at).total_seconds()
                        
                        # Se tempo inativo > lost_ttl ou tempo de vida > active_ttl, encerrar track
                        if time_inactive > self._lost_ttl or time_active > self._active_ttl:
                            try:
                                # Chamar serviço para encerrar track
                                if time_inactive > self._lost_ttl:
                                    reason = f"Track encerrado por inatividade (lost_ttl={self._lost_ttl}s)."
                                else:
                                    reason = f"Track encerrado por idade máxima (active_ttl={self._active_ttl}s)."
                                self._finish_track_service.finish_track(
                                    camera_id=IdVO(camera_id),
                                    track_id=track_id,
                                    reason=reason
                                )
                                
                                # self._logger.info(
                                #     f"Worker {worker_id}: Track encerrado por TTL. "
                                #     f"camera_id={camera_id}, track_id={track_id}, "
                                #     f"time_inactive={time_inactive:.2f}s"
                                # )
                            
                            except Exception as e:
                                pass
        
        except Exception as e:
            pass

    def is_running(self) -> bool:
        """
        Verifica se os workers estão em execução.

        :return: True se há workers ativos, False caso contrário.
        """
        return not self._stop_event.is_set()

    def get_num_workers(self) -> int:
        """
        Retorna o número de workers.

        :return: Número de workers.
        """
        return self._num_workers

    def __repr__(self) -> str:
        """Representação do caso de uso."""
        return (
            f"ExpireTracksUseCase("
            f"workers={self._num_workers}, "
            f"sleep_interval={self._sleep_interval}s, "
            f"lost_ttl={self._lost_ttl}s, "
            f"active_ttl={self._active_ttl}s)"
        )
