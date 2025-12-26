"""
Caso de uso para processamento da fila de melhores eventos.
"""

import logging
import threading
import queue
from multiprocessing import cpu_count
from typing import List, Optional, TYPE_CHECKING

from src.application.queues.best_event_queue import BestEventQueue
from src.domain.entities import Event

if TYPE_CHECKING:
    from src.infrastructure.clients import FindfaceAdapter


class ProcessBestEventQueueUseCase:
    """
    Caso de uso para consumir melhores eventos da fila e processar.
    
    Instancia N consumidores (onde N = CPUs*2) que consomem eventos
    da fila com timeout configurável. Monitora o estado das filas
    e registra warnings quando alguma fila estiver cheia.
    
    Segue os princípios:
    - DDD: Interage com a aplicação através de casos de uso
    - SOLID (SRP): Responsável apenas por consumir e processar fila
    - TDD: Totalmente testável com mocks
    """

    def __init__(
        self,
        best_event_queue: BestEventQueue,
        findface_adapter: Optional['FindfaceAdapter'] = None,
        num_workers: Optional[int] = None,
        timeout: float = 0.5,
    ):
        """
        Inicializa o caso de uso.

        :param best_event_queue: Fila de Event a ser consumida.
        :param findface_adapter: Adaptador FindFace para enviar eventos (opcional).
        :param num_workers: Número de consumidores. Se None, usa 2xCPUs (mínimo CPUs).
        :param timeout: Timeout em segundos para desfilear da fila.
        :raises TypeError: Se best_event_queue não for BestEventQueue.
        """
        if not isinstance(best_event_queue, BestEventQueue):
            raise TypeError(f"best_event_queue deve ser BestEventQueue, recebido: {type(best_event_queue).__name__}")
        
        self._queue = best_event_queue
        self._findface_adapter = findface_adapter
        self._num_workers = num_workers or max(cpu_count() * 2, cpu_count())
        self._timeout = timeout
        self._workers: List[threading.Thread] = []
        self._stop_event = threading.Event()
        self._logger = logging.getLogger(self.__class__.__name__)



    def start(self) -> None:
        """
        Inicia os consumidores de fila.
        
        Cria N threads consumidoras (daemon) que aguardam eventos
        na fila com timeout configurável e processam continuamente.
        """
        self._stop_event.clear()
        
        for worker_id in range(self._num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(worker_id,),
                daemon=True,
                name=f"BestEventQueueWorker-{worker_id}"
            )
            worker.start()
            self._workers.append(worker)

    def stop(self, timeout: Optional[float] = None) -> None:
        """
        Para os consumidores de fila.

        :param timeout: Tempo em segundos para aguardar término das threads.
        """
        self._stop_event.set()
        
        for worker in self._workers:
            worker.join(timeout=timeout)

    def get_num_workers(self) -> int:
        """
        Retorna o número de workers.

        :return: Número de threads consumidoras.
        """
        return self._num_workers

    def is_running(self) -> bool:
        """
        Verifica se os consumidores de fila estão em execução.

        :return: True se pelo menos um worker está ativo, False caso contrário.
        """
        return not self._stop_event.is_set()

    def _worker_loop(self, worker_id: int) -> None:
        """
        Loop principal de um consumidor.

        :param worker_id: ID único do consumidor.
        """
        while not self._stop_event.is_set():
            try:
                event: Event = self._queue.get(
                    block=True,
                    timeout=self._timeout
                )
                self._process_best_event(event, worker_id)
            
            except queue.Empty:
                # Timeout normal, volta ao loop
                continue
            
            except Exception as e:
                self._logger.error(
                    f"Erro ao processar melhor evento. worker_id={worker_id}, erro={str(e)}",
                    exc_info=True
                )

    def _process_best_event(self, event: Event, worker_id: int) -> None:
        """
        Processa um melhor evento consumido da fila.
        
        Se um adaptador FindFace estiver configurado, envia o evento de forma
        síncrona (bloqueante) e registra o resultado.
        Caso contrário, apenas registra um log DEBUG.

        :param event: Event consumido.
        :param worker_id: ID do consumidor.
        """
        # Log de consumo da fila
        self._logger.debug(
            f"Consumido da BestEventQueue. Itens restantes na fila: {self._queue.qsize()}"
        )

        # Aplicar filtros de tamanho, confiança e movimento antes de enviar
        try:
            from src.infrastructure.config.config_loader import get_settings
            settings = get_settings()
            min_box_area = settings.filter.min_box_area
            min_box_conf = settings.filter.min_box_conf
        except Exception:
            min_box_area = 1000
            min_box_conf = 0.5

        try:
            x1, y1, x2, y2 = event.bbox.value()
            bbox_area = (x2 - x1) * (y2 - y1)
        except Exception:
            bbox_area = 0.0

        try:
            confidence_value = event.confidence.value()
        except Exception:
            confidence_value = 0.0

        movement_flag = getattr(event, '_movement', False)        

        if bbox_area < min_box_area or confidence_value < min_box_conf or not movement_flag:
            self._logger.debug(
                f"Event filtrado (não enviado a FindFace). area={bbox_area}, conf={confidence_value}, movement={movement_flag}"
            )
            return

        if self._findface_adapter:
            # Envio síncrono - bloqueia até conclusão
            try:
                # Enviar cópia do evento para liberar referência original
                sucesso, resultado_ou_motivo = self._findface_adapter.send_event(
                    event,
                    track_id=event.track_id
                )
                
                if sucesso:
                    self._logger.info(
                        f"Event enviado para FindFace. "
                        f"track_id={event.track_id}, "
                        f"camera_id={event.frame.camera_id.value()}, "
                        f"class_id={event.class_id}, "
                        f"confidence={event.confidence.value():.4f}, "
                        f"quality={event.face_quality_score.value():.4f}, "
                        f"worker_id={worker_id}"
                    )
                else:
                    self._logger.error(
                        f"Falha ao enviar Event para FindFace. "
                        f"track_id={event.track_id}, "
                        f"camera_id={event.frame.camera_id.value()}, "
                        f"motivo={resultado_ou_motivo}, "
                        f"worker_id={worker_id}"
                    )
                
            except Exception as e:
                self._logger.error(
                    f"Exceção ao enviar Event para FindFace. "
                    f"track_id={event.track_id}, "
                    f"camera_id={event.frame.camera_id.value()}, "
                    f"worker_id={worker_id}, "
                    f"erro={str(e)}",
                    exc_info=True
                )

    def _log_memory_snapshot(self) -> None:
        """
        Método removido: monitoramento de memória foi desabilitado.
        """
        pass

    def _check_queue_status(self) -> None:
        """
        Método removido: monitoramento de memória foi desabilitado.
        """
        pass
       