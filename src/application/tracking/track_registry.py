"""
Interface para gerenciamento de tracks ativos.
Define o contrato que implementações concretas devem seguir.

Esta interface segue o padrão de Portas da Arquitetura Hexagonal,
permitindo que diferentes estratégias de armazenamento (em memória, banco de dados, etc)
sejam implementadas sem afetar a lógica de aplicação.
"""

from abc import ABC, abstractmethod
from typing import Any, Iterable, Optional


class TrackRegistry(ABC):
    """
    Registro central para rastreamento de tracks ativos por câmera.
    
    Um track representa um objeto sendo rastreado pelo modelo YOLO durante
    o streaming de vídeo. Este registro mantém os tracks ativos na memória
    e permite consultas por câmera e ID do track.
    
    Exemplo:
        >>> registry = InMemoryTrackRegistry()
        >>> registry.register("cam_001", 1, track_object)
        >>> track = registry.get("cam_001", 1)
        >>> all_tracks = list(registry.get_by_camera("cam_001"))
    """
    
    @abstractmethod
    def register(self, camera_id: str, track_id: int, track: Any) -> None:
        """
        Registra um novo track ou atualiza um existente.
        
        Args:
            camera_id: Identificador da câmera
            track_id: ID único do track (fornecido pelo YOLO)
            track: Objeto do track a ser armazenado
            
        Raises:
            ValueError: Se camera_id ou track_id forem inválidos
        """
        pass
    
    @abstractmethod
    def get(self, camera_id: str, track_id: int) -> Optional[Any]:
        """
        Recupera um track específico.
        
        Args:
            camera_id: Identificador da câmera
            track_id: ID do track a ser recuperado
            
        Returns:
            O objeto do track se existir, None caso contrário
        """
        pass
    
    @abstractmethod
    def get_by_camera(self, camera_id: str) -> Iterable[Any]:
        """
        Recupera todos os tracks ativos de uma câmera.
        
        Args:
            camera_id: Identificador da câmera
            
        Returns:
            Iterável com todos os tracks ativos da câmera
        """
        pass
    
    @abstractmethod
    def remove(self, camera_id: str, track_id: int) -> None:
        """
        Remove um track do registro.
        Utilizado quando um track é perdido ou finalizado.
        
        Args:
            camera_id: Identificador da câmera
            track_id: ID do track a ser removido
        """
        pass
    
    @abstractmethod
    def clear_camera(self, camera_id: str) -> None:
        """
        Remove todos os tracks de uma câmera.
        Utilizado quando uma câmera para de fazer streaming.
        
        Args:
            camera_id: Identificador da câmera
        """
        pass
