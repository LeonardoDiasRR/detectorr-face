"""
Caso de uso para monitoramento contínuo de câmeras.
Application Layer - orquestra domínio e infraestrutura.
"""

import threading
import time
import logging
from typing import Dict, Optional, Callable, List, Any

from src.domain.entities import Camera
from src.domain.repositories import CameraRepository


class MonitorCamerasUseCase:
    """
    Caso de uso para monitorar câmeras ativas e inativas.
    
    Responsabilidades:
    - Ler câmeras a cada 10 segundos
    - Filtrar apenas câmeras ativas (active=True)
    - Iniciar/parar processamento de streaming via callback
    - Gerenciar ciclo de vida com graceful shutdown
    
    Cada câmera ativa recebe suas próprias cópias dos modelos TRACK e FACE
    carregados na memória do device configurado.
    
    NÃO é responsável por:
    - Inicializar YOLO
    - Executar tracking
    - Processar frames
    """

    def __init__(
        self,
        camera_repository: CameraRepository,
        yolo_config: Dict[str, Any],
        face_config: Dict[str, Any],
        on_camera_active: Callable[[Camera, Dict[str, Any], Dict[str, Any]], None],
        on_camera_inactive: Callable[[Camera, Dict[str, Any], Dict[str, Any]], None]
    ) -> None:
        """
        Inicializa o caso de uso de monitoramento de câmeras.

        :param camera_repository: Repositório para leitura de câmeras.
        :param yolo_config: Configuração do modelo YOLO (track_model).
        :param face_config: Configuração do modelo de faces (face_model).
        :param on_camera_active: Callback quando câmera fica ativa (recebe Camera, yolo_config, face_config).
        :param on_camera_inactive: Callback quando câmera fica inativa (recebe Camera, yolo_config, face_config).
        """
        # Duck typing: validar que tem o método necessário
        if not hasattr(camera_repository, 'get_cameras') or not callable(getattr(camera_repository, 'get_cameras')):
            raise TypeError("camera_repository deve ter um método 'get_cameras' callable")
        
        if not isinstance(yolo_config, dict):
            raise TypeError("yolo_config deve ser um dicionário")
        
        if 'backend' not in yolo_config:
            raise ValueError("yolo_config deve conter a chave 'backend'")
        
        if not isinstance(face_config, dict):
            raise TypeError("face_config deve ser um dicionário")
        
        if 'backend' not in face_config:
            raise ValueError("face_config deve conter a chave 'backend'")
        
        if not callable(on_camera_active):
            raise TypeError("on_camera_active deve ser callable")
        
        if not callable(on_camera_inactive):
            raise TypeError("on_camera_inactive deve ser callable")

        self.camera_repository = camera_repository
        self.yolo_config = yolo_config
        self.face_config = face_config
        self.on_camera_active = on_camera_active
        self.on_camera_inactive = on_camera_inactive
        self.logger = logging.getLogger(self.__class__.__name__)

        # Estado do monitor
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None

        # Câmeras em monitoramento: {camera_id: camera}
        self.monitored_cameras: Dict[int, Camera] = {}

        # Lock para sincronização thread-safe
        self.lock = threading.Lock()

    def get_active_cameras(self) -> List[Camera]:
        """
        Obtém lista de câmeras ativas do repositório.

        :return: Lista de entidades Camera com active=True.
        """
        all_cameras = self.camera_repository.get_cameras()
        active_cameras = [c for c in all_cameras if c.active]
        return active_cameras

    def sync_cameras(self) -> None:
        """
        Sincroniza estado das câmeras monitoradas com câmeras ativas.
        - Inicia monitoramento de câmeras que ficaram ativas
        - Para monitoramento de câmeras que ficaram inativas
        """
        active_cameras = self.get_active_cameras()
        active_ids = {c.camera_id.value() for c in active_cameras}

        with self.lock:
            # Câmeras que ficaram ativas (adicionar ao monitoramento)
            for camera in active_cameras:
                camera_id = camera.camera_id.value()
                if camera_id not in self.monitored_cameras:
                    self.monitored_cameras[camera_id] = camera
                    # Chamar callback para iniciar streaming com ambas as configurações
                    self.on_camera_active(camera, self.yolo_config, self.face_config)

            # Câmeras que ficaram inativas (remover do monitoramento)
            inactive_ids = set(self.monitored_cameras.keys()) - active_ids
            for camera_id in inactive_ids:
                camera = self.monitored_cameras.pop(camera_id)
                # Chamar callback para parar streaming com ambas as configurações
                self.on_camera_inactive(camera, self.yolo_config, self.face_config)

    def monitor(self, interval: float = 10.0) -> None:
        """
        Loop de monitoramento contínuo de câmeras.
        Sincroniza câmeras a cada intervalo de tempo.

        :param interval: Intervalo em segundos para sincronizar câmeras (padrão: 10s).
        """
        while self.running:
            try:
                self.sync_cameras()
                time.sleep(interval)
            except Exception as e:
                time.sleep(interval)

    def start(self) -> None:
        """
        Inicia o monitor em uma thread separada.
        Pode ser chamado múltiplas vezes com segurança (idempotente).
        """
        if self.running:
            return

        self.running = True
        self.monitor_thread = threading.Thread(
            target=self.monitor,
            daemon=False,
            name="CameraMonitor"
        )
        self.monitor_thread.start()

    def stop(self) -> None:
        """
        Para o monitor com graceful shutdown.
        Sinaliza parada, aguarda thread finalizar.
        """
        if not self.running:
            return

        self.running = False

        # Parar streaming de todas as câmeras monitoradas
        with self.lock:
            cameras_to_stop = list(self.monitored_cameras.values())
            self.monitored_cameras.clear()

        for camera in cameras_to_stop:
            self.on_camera_inactive(camera, self.yolo_config, self.face_config)

        # Aguardar thread do monitor finalizar
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
