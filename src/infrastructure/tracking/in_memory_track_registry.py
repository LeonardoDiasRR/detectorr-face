"""
Implementação em memória do registro de tracks.
Utiliza dicionários aninhados para armazenar tracks por câmera e ID.

Esta implementação é thread-safe para operações básicas (leitura/escrita),
mas para operações complexas que envolvem múltiplas operações,
recomenda-se usar locks externos na camada de aplicação.

Estrutura interna:
    _tracks = {
        "camera_001": {
            1: track_object_1,
            2: track_object_2,
            ...
        },
        "camera_002": {
            1: track_object_1,
            ...
        }
    }
"""

from collections import defaultdict
from typing import Any, Iterable, Optional

from src.application.tracking.track_registry import TrackRegistry


class InMemoryTrackRegistry(TrackRegistry):
    """
    Registro de tracks em memória.
    
    Armazena tracks ativos de forma rápida e eficiente em memória.
    Ideal para aplicações em tempo real que precisam de acesso muito rápido.
    
    Características:
        - Acesso O(1) para get/register/remove
        - Armazenamento organizado por câmera
        - Limpeza automática por câmera
        - Thread-safe para operações individuais
    
    Limitações:
        - Dados perdidos ao reiniciar a aplicação
        - Memória cresce indefinidamente se tracks não forem removidos
        - Não persiste em disco
    
    Exemplo de uso:
        >>> registry = InMemoryTrackRegistry()
        >>> registry.register("cam_001", 1, {"center": (100, 100)})
        >>> track = registry.get("cam_001", 1)
        >>> print(track)
        {'center': (100, 100)}
        >>> registry.clear_camera("cam_001")
    """
    
    def __init__(self):
        """Inicializa o registro com dicionário vazio."""
        self._tracks = defaultdict(dict)
    
    def register(self, camera_id: str, track_id: int, track: Any) -> None:
        """
        Registra ou atualiza um track.
        
        Args:
            camera_id: ID da câmera
            track_id: ID do track (fornecido pelo YOLO)
            track: Objeto/dados do track
            
        Raises:
            ValueError: Se camera_id for vazio ou None
            TypeError: Se track_id não for inteiro
        """
        if not camera_id:
            raise ValueError("camera_id não pode ser vazio ou None")
        if not isinstance(track_id, int):
            raise TypeError(f"track_id deve ser inteiro, recebido {type(track_id)}")
        
        self._tracks[camera_id][track_id] = track
    
    def get(self, camera_id: str, track_id: int) -> Optional[Any]:
        """
        Recupera um track específico.
        
        Args:
            camera_id: ID da câmera
            track_id: ID do track
            
        Returns:
            O objeto do track se existir, None caso contrário
        """
        return self._tracks.get(camera_id, {}).get(track_id)
    
    def get_by_camera(self, camera_id: str) -> Iterable[Any]:
        """
        Recupera todos os tracks de uma câmera.
        
        Args:
            camera_id: ID da câmera
            
        Returns:
            Iterável com os valores dos tracks (não inclui IDs)
        """
        return self._tracks.get(camera_id, {}).values()
    
    def remove(self, camera_id: str, track_id: int) -> None:
        """
        Remove um track específico.
        Não lança erro se o track não existir.
        
        Args:
            camera_id: ID da câmera
            track_id: ID do track a remover
        """
        self._tracks.get(camera_id, {}).pop(track_id, None)
    
    def clear_camera(self, camera_id: str) -> None:
        """
        Remove todos os tracks de uma câmera.
        Limpa completamente a entrada da câmera do dicionário.
        
        Args:
            camera_id: ID da câmera
        """
        self._tracks.pop(camera_id, None)
    
    def get_camera_tracks_count(self, camera_id: str) -> int:
        """
        Retorna o número de tracks ativos de uma câmera.
        Método auxiliar não exigido pela interface, mas útil para monitoramento.
        
        Args:
            camera_id: ID da câmera
            
        Returns:
            Número de tracks ativos
        """
        return len(self._tracks.get(camera_id, {}))
    
    def get_all_cameras_stats(self) -> dict:
        """
        Retorna estatísticas sobre todos os tracks.
        Método auxiliar útil para monitoramento e debug.
        
        Returns:
            Dicionário com {camera_id: número_de_tracks}
        """
        return {camera_id: len(tracks) for camera_id, tracks in self._tracks.items()}
