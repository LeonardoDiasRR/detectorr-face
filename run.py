"""
Módulo principal de execução da aplicação.
Gerencia a instância de FindfaceMulti e coordena a execução da aplicação.
"""

# IMPORTANTE: Configurar OpenMP ANTES de importar YOLO/NumPy
# Isso evita conflito com múltiplas bibliotecas OpenMP (libomp.dll vs libiomp5md.dll)
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import logging
import sys
import threading
import time
from pathlib import Path
from multiprocessing import cpu_count
from dotenv import load_dotenv
from src.infrastructure import FindfaceMulti, CameraRepositoryFindface, FindfaceAdapter, get_settings
from src.infrastructure.logging import setup_logging, get_logger
from src.infrastructure.tracking import InMemoryTrackRegistry
from src.application.use_cases import (
    MonitorCamerasUseCase,
    ProcessCameraStreamingUseCase,
    ProcessBestEventQueueUseCase,
    ExpireTracksUseCase
)
from src.application.queues import DomainEventQueue, BestEventQueue
from src.domain.services import FinishTrackService


def clear_log_file() -> None:
    """
    Limpa o arquivo de log a cada nova execução.
    Garante que os logs não se acumulem entre execuções.
    """
    log_file = Path("detectorr.log")
    if log_file.exists():
        try:
            log_file.unlink()
        except Exception:
            # Se houver erro ao deletar, ignora (arquivo pode estar em uso)
            pass


# Limpar log da execução anterior
clear_log_file()

# Logging será configurado dinamicamente após carregar as settings
logger = None


# Suprimir avisos de "Waiting for stream 0" do YOLO/OpenCV
class YOLOWarningFilter(logging.Filter):
    """Filtro para omitir warnings específicos do YOLO."""
    
    def filter(self, record):
        """Omite mensagens de 'Waiting for stream'."""
        return "Waiting for stream" not in record.getMessage()


# Aplicar filtro ao logger de ultralytics
yolo_logger = logging.getLogger("ultralytics")
yolo_logger.addFilter(YOLOWarningFilter())

# Também aplicar ao logger raiz para OpenCV
root_logger = logging.getLogger()
root_logger.addFilter(YOLOWarningFilter())


def _calculate_queue_workers(queue_name: str, configured_workers: int) -> int:
    """
    Calcular número de workers para uma fila.
    
    Se configured_workers == 0, calcula automaticamente conforme fórmulas:
    - FrameQueue: max(4, cpu_count() / 4)
    - EventQueue: max(4, cpu_count() / 2)
    - DomainEventQueue: max(2, cpu_count() / 5)
    - BestEventQueue: max(4, cpu_count())
    
    :param queue_name: Nome da fila.
    :param configured_workers: Número configurado (0 = automático).
    :return: Número de workers a usar.
    """
    if configured_workers > 0:
        return configured_workers
    
    cpu = cpu_count()
    formulas = {
        'FrameQueue': int(max(4, cpu / 2)),
        'EventQueue': int(max(4, cpu / 2)),
        'DomainEventQueue': int(max(2, cpu / 5)),
        'BestEventQueue': int(max(8, cpu * 2)),
    }
    
    return formulas.get(queue_name, 4)


def main(findface_client: FindfaceMulti) -> None:
    # Dicionário para mapear camera_id -> (thread, streaming_instance)
    camera_id_to_thread: dict = {}
    """
    Função principal da aplicação.
    Executa o monitoramento contínuo de câmeras e processamento de streaming YOLO.
    
    :param findface_client: Instância do cliente FindfaceMulti já autenticado.
    """
    # Variáveis para guardar referências para cleanup
    domain_events_use_case = None
    best_event_queue_use_case = None
    expire_tracks_use_case = None
    
    try:
        # Carregar configurações type-safe
        settings = get_settings()
        
        # Configurar logging com todos os parâmetros do config.yaml
        log_level_str = settings.logging.level.upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        # Converter max_size de MB para bytes
        max_bytes = settings.logging.max_size * 1024 * 1024
        
        # Configurar logging com todos os parâmetros
        setup_logging(
            log_level=log_level,
            log_file=settings.logging.file,
            log_format=settings.logging.format,
            max_bytes=max_bytes,
            backup_count=settings.logging.backup_count,
            queue_size=settings.logging.queue_size
        )
        global logger
        logger = get_logger(__name__)
        
        logger.info(f"Configurações carregadas: {settings}")
        logger.info(f"Nível de logging: {log_level_str}")
        logger.info(f"Arquivo de log: {settings.logging.file}")
        logger.info(f"Tamanho máximo: {settings.logging.max_size}MB")
        logger.info(f"Arquivos de backup: {settings.logging.backup_count}")
        
        # Extrair configuração YOLO
        yolo_config = {
            'backend': settings.track_model.backend,
            'params': settings.track_model.params.to_dict()
        }
        logger.info("Configuração YOLO extraída com sucesso")
        
        # Extrair configuração face_model
        face_config = {
            'backend': settings.face_model.backend,
            'params': settings.face_model.params.to_dict()
        }
        logger.info("Configuração face_model extraída com sucesso")
        
        # NÃO pré-carregar modelo facial globalmente
        # Cada câmera carregará sua própria cópia quando ativar
        logger.info("Modelos serão carregados individualmente por câmera quando ativadas")
        
        # Criar repositório de câmeras
        camera_repository = CameraRepositoryFindface(findface_client)
        logger.info("Repositório de câmeras criado com sucesso")
        
        # Criar registro de tracks em memória (global e compartilhado)
        track_registry = InMemoryTrackRegistry()
        logger.info("InMemoryTrackRegistry criada com sucesso (registro global de tracks)")
        
        # Fila de melhor evento (para tracks finalizados)
        best_event_queue_config = settings.queues.BestEventQueue
        best_workers = _calculate_queue_workers('BestEventQueue', best_event_queue_config.workers)
        best_event_queue = BestEventQueue(maxsize=best_event_queue_config.maxsize)
        logger.info(f"BestEventQueue criada com sucesso (maxsize={best_event_queue_config.maxsize}, workers={best_workers} automáticos)")
                
        # Criar adaptador FindFace
        findface_adapter = FindfaceAdapter(findface_client)
        logger.info("FindfaceAdapter criado com sucesso")
        
        # Criar e iniciar processador de melhores eventos com adapter
        best_event_queue_use_case = ProcessBestEventQueueUseCase(
            best_event_queue=best_event_queue,
            findface_adapter=findface_adapter,
            num_workers=best_workers,
            timeout=best_event_queue_config.timeout
        )
        best_event_queue_use_case.start()
        logger.info(f"ProcessBestEventQueueUseCase iniciado com {best_event_queue_use_case._num_workers} workers")
        
        # Criar serviço de finalização de tracks
        finish_track_service = FinishTrackService(
            track_registry=track_registry,
            best_event_queue=best_event_queue
        )
        
        # Criar e iniciar caso de uso de expiração de TTL
        expire_tracks_use_case = ExpireTracksUseCase(
            track_registry=track_registry,
            finish_track_service=finish_track_service,
            num_workers=None,  # Usa CPUs/4 por padrão
            sleep_interval=1.0
        )
        expire_tracks_use_case.start()
        logger.info(f"ExpireTracksUseCase iniciado com {expire_tracks_use_case.get_num_workers()} workers")
        
        # Definir callbacks para o monitor de câmeras
        def on_camera_active(camera, yolo_config, face_config):
            """
            Callback chamado quando uma câmera fica ativa.
            Cria uma nova instância de ProcessCameraStreamingUseCase para esta câmera.
            Pipeline integrado: Frame → Event → Track (síncrono, sem filas)
            """
            camera_id = camera.camera_id.value()
            logger.info(f"Iniciando processamento de streaming para câmera {camera_id}")
            
            try:
                # Criar nova instância dedicada para esta câmera
                # Sem fila, pipeline síncrono integrado
                camera_streaming_use_case = ProcessCameraStreamingUseCase(
                    skip_frames=settings.performance.skip_frames
                )
                camera_streaming_use_case.set_track_registry(track_registry)
                logger.info(f"[Camera {camera_id}] Nova instância ProcessCameraStreamingUseCase criada (pipeline integrado)")

                def run_camera_streaming():
                    try:
                        camera_streaming_use_case.execute(camera, yolo_config, face_config)
                    except Exception as e:
                        logger.error(f"[Camera {camera_id}] Erro durante execução de streaming: {e}", exc_info=True)

                thread = threading.Thread(
                    target=run_camera_streaming,
                    daemon=True,
                    name=f"Streaming-Camera-{camera_id}"
                )
                thread.start()

                # Registrar thread e instância para controle de parada
                camera_id_to_thread[camera_id] = (thread, camera_streaming_use_case)

            except Exception as e:
                logger.error(f"[Camera {camera_id}] Erro ao iniciar streaming: {e}", exc_info=True)
        
        def on_camera_inactive(camera, yolo_config, face_config):
            """Callback chamado quando uma câmera fica inativa."""
            camera_id = camera.camera_id.value()
            logger.info(f"Parando processamento de streaming para câmera {camera_id}")
            # Parar thread e instância associada
            if camera_id in camera_id_to_thread:
                thread, streaming_instance = camera_id_to_thread.pop(camera_id)
                try:
                    streaming_instance.stop()
                    if thread.is_alive():
                        thread.join(timeout=5)
                    logger.info(f"[Camera {camera_id}] Streaming parado com sucesso")
                except Exception as e:
                    logger.error(f"[Camera {camera_id}] Erro ao parar streaming: {e}", exc_info=True)
        
        # Criar e executar o monitor de câmeras com face_config
        monitor = MonitorCamerasUseCase(
            camera_repository=camera_repository,
            yolo_config=yolo_config,
            face_config=face_config,
            on_camera_active=on_camera_active,
            on_camera_inactive=on_camera_inactive
        )
        
        logger.info("MonitorCamerasUseCase instanciado com sucesso")
        
        # Iniciar o monitor (executa em thread separada)
        monitor.start()
        logger.info("Monitor de câmeras iniciado")
        
        # Manter a aplicação em execução
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interrupção do teclado detectada, encerrando...")
            monitor.stop()
            logger.info("Monitor de câmeras parado com sucesso")
            
            # Parar processadores de filas
            if frame_queue_use_case and frame_queue_use_case.is_running():
                frame_queue_use_case.stop()
                logger.info("ProcessFrameQueueUseCase parado com sucesso")
            
            if event_queue_use_case and event_queue_use_case.is_running():
                event_queue_use_case.stop()
                logger.info("ProcessEventQueueUseCase parado com sucesso")
            
            if best_event_queue_use_case and best_event_queue_use_case.is_running():
                best_event_queue_use_case.stop()
                logger.info("ProcessBestEventQueueUseCase parado com sucesso")
            
            if expire_tracks_use_case and expire_tracks_use_case.is_running():
                expire_tracks_use_case.stop()
                logger.info("ExpireTracksUseCase parado com sucesso")
    
    except FileNotFoundError as e:
        if logger:
            logger.error(f"Erro: Arquivo não encontrado: {e}")
        raise
    except ValueError as e:
        if logger:
            logger.error(f"Erro de configuração: {e}")
        raise
    except Exception as e:
        if logger:
            logger.error(f"Erro na execução principal: {e}", exc_info=True)
        # Garantir que os processadores sejam parados em caso de erro
        if best_event_queue_use_case and best_event_queue_use_case.is_running():
            try:
                best_event_queue_use_case.stop()
            except Exception as stop_error:
                if logger:
                    logger.error(f"Erro ao parar ProcessBestEventQueueUseCase: {stop_error}")
        if expire_tracks_use_case and expire_tracks_use_case.is_running():
            try:
                expire_tracks_use_case.stop()
            except Exception as stop_error:
                if logger:
                    logger.error(f"Erro ao parar ExpireTracksUseCase: {stop_error}")
        
        raise


if __name__ == '__main__':
    try:
        # Carregar variáveis de ambiente do arquivo .env
        load_dotenv()
        
        # Obter credenciais do FindFace das variáveis de ambiente
        findface_url = os.getenv('FINDFACE_URL')
        findface_user = os.getenv('FINDFACE_USER')
        findface_password = os.getenv('FINDFACE_PASSWORD')
        findface_uuid = os.getenv('FINDFACE_UUID')
        
        # Validar se todas as variáveis estão configuradas
        if not all([findface_url, findface_user, findface_password, findface_uuid]):
            raise ValueError(
                "Erro: Uma ou mais variáveis de ambiente do FindFace não foram configuradas. "
                "Verifique o arquivo .env e certifique-se de que as seguintes variáveis estão preenchidas: "
                "FINDFACE_URL, FINDFACE_USER, FINDFACE_PASSWORD, FINDFACE_UUID"
            )
        
        # Instanciar o cliente FindfaceMulti
        findface = FindfaceMulti(
            url_base=findface_url,
            user=findface_user,
            password=findface_password,
            uuid=findface_uuid
        )
        
        # Executar a aplicação principal
        main(findface)
        
    except Exception as e:
        print(f"Erro durante execução: {e}")
        raise
    
    finally:
        # Realizar logout da instância FindfaceMulti
        findface.logout()
