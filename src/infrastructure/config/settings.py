"""
Objeto de configuração centralizado.
Fornece acesso type-safe às configurações da aplicação.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class YOLOParams:
    """Parâmetros de configuração do modelo YOLO."""
    
    conf: float = 0.05
    iou: float = 0.5
    imgsz: int = 1280
    device: str = "cpu"
    half: bool = True
    classes: List[int] = field(default_factory=lambda: [0])
    tracker: str = "custom_track.yaml"
    stream: bool = True
    show: bool = True
    persist: bool = False
    verbose: bool = False
    save: bool = True
    project: str = "yolo_results"
    name: str = "yolo_run"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter parâmetros para dicionário."""
        return {
            'conf': self.conf,
            'iou': self.iou,
            'imgsz': self.imgsz,
            'device': self.device,
            'half': self.half,
            'classes': self.classes,
            'tracker': self.tracker,
            'stream': self.stream,
            'show': self.show,
            'persist': self.persist,
            'verbose': self.verbose,
            'save': self.save,
            'project': self.project,
            'name': self.name,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'YOLOParams':
        """Criar parâmetros a partir de dicionário."""
        return cls(
            conf=data.get('conf', 0.05),
            iou=data.get('iou', 0.5),
            imgsz=data.get('imgsz', 1280),
            device=data.get('device', 'cpu'),
            half=data.get('half', True),
            classes=data.get('classes', [0]),
            tracker=data.get('tracker', 'custom_track.yaml'),
            stream=data.get('stream', True),
            show=data.get('show', True),
            persist=data.get('persist', False),
            verbose=data.get('verbose', False),
            save=data.get('save', True),
            project=data.get('project', 'yolo_results'),
            name=data.get('name', 'yolo_run'),
        )


@dataclass
class TrackModelConfig:
    """Configuração do modelo de rastreamento YOLO."""
    
    backend: str
    params: YOLOParams
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter configuração para dicionário."""
        return {
            'backend': self.backend,
            'params': self.params.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrackModelConfig':
        """Criar configuração a partir de dicionário."""
        params_data = data.get('params', {})
        return cls(
            backend=data.get('backend', ''),
            params=YOLOParams.from_dict(params_data) if params_data else YOLOParams(),
        )


@dataclass
class FaceModelParams:
    """Parâmetros de configuração do modelo de detecção facial."""
    
    conf: float = 0.5
    device: str = "cpu"
    half: bool = False
    classes: List[int] = field(default_factory=lambda: [0])
    stream: bool = False
    verbose: bool = False
    save: bool = False
    project: str = "yolo_results"
    name: str = "yolo_run_faces"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter parâmetros para dicionário."""
        return {
            'conf': self.conf,
            'device': self.device,
            'half': self.half,
            'classes': self.classes,
            'stream': self.stream,
            'verbose': self.verbose,
            'save': self.save,
            'project': self.project,
            'name': self.name,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FaceModelParams':
        """Criar parâmetros a partir de dicionário."""
        return cls(
            conf=data.get('conf', 0.5),
            device=data.get('device', 'cpu'),
            half=data.get('half', False),
            classes=data.get('classes', [0]),
            stream=data.get('stream', False),
            verbose=data.get('verbose', False),
            save=data.get('save', False),
            project=data.get('project', 'yolo_results'),
            name=data.get('name', 'yolo_run_faces'),
        )


@dataclass
class FaceModelConfig:
    """Configuração do modelo de detecção facial."""
    
    backend: str
    params: FaceModelParams
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter configuração para dicionário."""
        return {
            'backend': self.backend,
            'params': self.params.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FaceModelConfig':
        """Criar configuração a partir de dicionário."""
        params_data = data.get('params', {})
        return cls(
            backend=data.get('backend', ''),
            params=FaceModelParams.from_dict(params_data) if params_data else FaceModelParams(),
        )


@dataclass
class TrackConfig:
    """Configuração dos parâmetros de rastreamento (Track)."""
    
    min_movement_pixels: float = 2.0
    lost_ttl: int = 3
    active_ttl: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter configuração para dicionário."""
        return {
            'min_movement_pixels': self.min_movement_pixels,
            'lost_ttl': self.lost_ttl,
            'active_ttl': self.active_ttl,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrackConfig':
        """Criar configuração a partir de dicionário."""
        return cls(
            min_movement_pixels=data.get('min_movement_pixels', 2.0),
            lost_ttl=data.get('lost_ttl', 3),
            active_ttl=data.get('active_ttl', 30),
        )


@dataclass
class FilterConfig:
    """Configuração de filtros de detecção."""
    
    min_box_area: int = 1000  # Área mínima da caixa delimitadora
    min_box_conf: float = 0.5  # Confiança mínima da caixa delimitadora
    min_movement_pixels: float = 2.0  # Limiar mínimo de variação em pixels para considerar movimento
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter configuração para dicionário."""
        return {
            'min_box_area': self.min_box_area,
            'min_box_conf': self.min_box_conf,
            'min_movement_pixels': self.min_movement_pixels,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterConfig':
        """Criar configuração a partir de dicionário."""
        return cls(
            min_box_area=data.get('min_box_area', 1000),
            min_box_conf=data.get('min_box_conf', 0.5),
            min_movement_pixels=data.get('min_movement_pixels', 2.0),
        )


@dataclass
class LoggingConfig:
    """Configuração do sistema de logging assíncrono."""
    
    file: str = "detectorr.log"
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_size: int = 2  # MB
    backup_count: int = 2
    queue_size: int = 10000
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter configuração para dicionário."""
        return {
            'file': self.file,
            'level': self.level,
            'format': self.format,
            'max_size': self.max_size,
            'backup_count': self.backup_count,
            'queue_size': self.queue_size,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoggingConfig':
        """Criar configuração a partir de dicionário."""
        return cls(
            file=data.get('file', 'detectorr.log'),
            level=data.get('level', 'INFO'),
            format=data.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            max_size=data.get('max_size', 2),
            backup_count=data.get('backup_count', 2),
            queue_size=data.get('queue_size', 10000),
        )


@dataclass
class QueueConfig:
    """Configuração de uma fila de processamento."""
    
    maxsize: int = 100
    workers: int = 0    # 0 = automático conforme fórmula
    timeout: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter configuração para dicionário."""
        return {
            'maxsize': self.maxsize,
            'workers': self.workers,
            'timeout': self.timeout,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueueConfig':
        """Criar configuração a partir de dicionário."""
        return cls(
            maxsize=data.get('maxsize', 100),
            workers=data.get('workers', 0),
            timeout=data.get('timeout', 0.5),
        )


@dataclass
class QueuesConfig:
    """Configuração de todas as filas de processamento."""
    
    FrameQueue: QueueConfig = field(default_factory=lambda: QueueConfig(maxsize=5, workers=0, timeout=0.5))
    EventQueue: QueueConfig = field(default_factory=lambda: QueueConfig(maxsize=35, workers=0, timeout=0.5))
    BestEventQueue: QueueConfig = field(default_factory=lambda: QueueConfig(maxsize=120, workers=0, timeout=0.5))
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter configuração para dicionário."""
        return {
            'FrameQueue': self.FrameQueue.to_dict(),
            'EventQueue': self.EventQueue.to_dict(),
            'BestEventQueue': self.BestEventQueue.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueuesConfig':
        """Criar configuração a partir de dicionário."""
        return cls(
            FrameQueue=QueueConfig.from_dict(data.get('FrameQueue', {})),
            EventQueue=QueueConfig.from_dict(data.get('EventQueue', {})),
            BestEventQueue=QueueConfig.from_dict(data.get('BestEventQueue', {})),
        )


@dataclass
class FindfaceConfig:
    """Configuração do cliente FindFace."""
    
    url: str
    user: str
    password: str
    uuid: str
    camera_group_prefix: str = 'TESTE'
    jpeg_quality: int = 95
    
    @classmethod
    def from_env(cls, url: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None, uuid: Optional[str] = None, jpeg_quality: int = 95) -> 'FindfaceConfig':
        """Criar configuração a partir de variáveis de ambiente."""
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        findface_url = url or os.getenv('FINDFACE_URL', 'http://localhost:3185')
        findface_user = user or os.getenv('FINDFACE_USER', '')
        findface_password = password or os.getenv('FINDFACE_PASSWORD', '')
        findface_uuid = uuid or os.getenv('FINDFACE_UUID', '')
        
        if not findface_user or not findface_password or not findface_uuid:
            raise ValueError(
                'FINDFACE_USER, FINDFACE_PASSWORD e FINDFACE_UUID devem ser definidos. '
                'Configure as variáveis de ambiente ou passe como parâmetros.'
            )
        
        return cls(url=findface_url, user=findface_user, password=findface_password, uuid=findface_uuid, camera_group_prefix='TESTE', jpeg_quality=jpeg_quality)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], jpeg_quality: int = 95) -> 'FindfaceConfig':
        """Criar configuração a partir de dicionário (misturando YAML e variáveis de ambiente)."""
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        findface_url = os.getenv('FINDFACE_URL', 'http://localhost:3185')
        findface_user = os.getenv('FINDFACE_USER', '')
        findface_password = os.getenv('FINDFACE_PASSWORD', '')
        findface_uuid = os.getenv('FINDFACE_UUID', '')
        
        if not findface_user or not findface_password or not findface_uuid:
            raise ValueError(
                'FINDFACE_USER, FINDFACE_PASSWORD e FINDFACE_UUID devem ser definidos. '
                'Configure as variáveis de ambiente.'
            )
        
        # Carrega configurações opcionais do config.yaml
        camera_group_prefix = data.get('camera_group_prefix', 'TESTE') if data else 'TESTE'
        yaml_jpeg_quality = data.get('jpeg_quality', 95) if data else 95
        
        return cls(
            url=findface_url,
            user=findface_user,
            password=findface_password,
            uuid=findface_uuid,
            camera_group_prefix=camera_group_prefix,
            jpeg_quality=yaml_jpeg_quality
        )
    
    @classmethod
    def from_env(cls, url: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None, uuid: Optional[str] = None) -> 'FindfaceConfig':
        """Criar configuração a partir de variáveis de ambiente."""
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        findface_url = url or os.getenv('FINDFACE_URL', 'http://localhost:3185')
        findface_user = user or os.getenv('FINDFACE_USER', '')
        findface_password = password or os.getenv('FINDFACE_PASSWORD', '')
        findface_uuid = uuid or os.getenv('FINDFACE_UUID', '')
        
        if not findface_user or not findface_password or not findface_uuid:
            raise ValueError(
                'FINDFACE_USER, FINDFACE_PASSWORD e FINDFACE_UUID devem ser definidos. '
                'Configure as variáveis de ambiente ou passe como parâmetros.'
            )
        
        return cls(url=findface_url, user=findface_user, password=findface_password, uuid=findface_uuid, camera_group_prefix='TESTE')


@dataclass
class PerformanceConfig:
    """Configuração de performance e otimizações."""
    
    skip_frames: int = 0  # Número de frames a pular entre processamentos (0 = processa todos)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter configuração para dicionário."""
        return {
            'skip_frames': self.skip_frames,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceConfig':
        """Criar configuração a partir de dicionário."""
        return cls(
            skip_frames=data.get('skip_frames', 0),
        )


@dataclass
class FilterConfig:
    """Configuração de filtros de detecção."""
    
    min_box_area: int = 1000  # Área mínima da caixa delimitadora
    min_box_conf: float = 0.5  # Confiança mínima da caixa delimitadora
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter configuração para dicionário."""
        return {
            'min_box_area': self.min_box_area,
            'min_box_conf': self.min_box_conf,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterConfig':
        """Criar configuração a partir de dicionário."""
        return cls(
            min_box_area=data.get('min_box_area', 1000),
            min_box_conf=data.get('min_box_conf', 0.5),
        )


@dataclass
class ApplicationSettings:
    """Configurações centralizadas da aplicação."""
    
    track_model: TrackModelConfig
    findface: FindfaceConfig
    logging: LoggingConfig
    track: TrackConfig
    queues: QueuesConfig
    filter: FilterConfig = field(default_factory=lambda: FilterConfig())
    face_model: FaceModelConfig = field(default_factory=lambda: FaceModelConfig(
        backend='models/yolo/yolov12n-face.pt',
        params=FaceModelParams()
    ))
    performance: PerformanceConfig = field(default_factory=lambda: PerformanceConfig())

    def __repr__(self) -> str:
        """Representação da configuração."""
        return (
            f"ApplicationSettings("
            f"track_model={self.track_model.backend}, "
            f"face_model={self.face_model.backend}, "
            f"findface={self.findface.url}, "
            f"logging={self.logging.file}, "
            f"track={{'min_movement_pixels': {self.track.min_movement_pixels}, 'lost_ttl': {self.track.lost_ttl}, 'active_ttl': {self.track.active_ttl}}}, "
            f"filter={{'min_movement_pixels': {self.filter.min_movement_pixels}}})"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter configurações para dicionário."""
        return {
            'track_model': self.track_model.to_dict(),
            'face_model': self.face_model.to_dict(),
            'findface': {
                'url': self.findface.url,
                'user': self.findface.user,
                'password': self.findface.password,
                'uuid': self.findface.uuid,
                'camera_group_prefix': self.findface.camera_group_prefix,
                'jpeg_quality': self.findface.jpeg_quality,
            },
            'logging': self.logging.to_dict(),
            'track': self.track.to_dict(),
            'filter': self.filter.to_dict(),
        }
