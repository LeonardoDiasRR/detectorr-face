"""
Exemplo de uso do TrackRegistry na aplicação.

Este módulo demonstra como integrar o gerenciamento de tracks
na lógica de processamento de streaming.
"""

from src.application.tracking.track_registry import TrackRegistry
from src.infrastructure.tracking.in_memory_track_registry import InMemoryTrackRegistry


def exemplo_uso_basico():
    """
    Exemplo básico de uso do TrackRegistry.
    """
    # 1. Criar uma instância do registry
    registry: TrackRegistry = InMemoryTrackRegistry()
    
    # 2. Registrar tracks quando o YOLO os detecta
    camera_id = "camera_001"
    
    # Simular detecção de 3 tracks
    registry.register(camera_id, 1, {"center": (100, 100), "conf": 0.95})
    registry.register(camera_id, 2, {"center": (200, 200), "conf": 0.92})
    registry.register(camera_id, 3, {"center": (300, 300), "conf": 0.88})
    
    print(f"✓ Registrados 3 tracks para {camera_id}")
    
    # 3. Recuperar um track específico
    track_1 = registry.get(camera_id, 1)
    print(f"✓ Track 1 recuperado: {track_1}")
    
    # 4. Listar todos os tracks de uma câmera
    all_tracks = list(registry.get_by_camera(camera_id))
    print(f"✓ Total de tracks na câmera: {len(all_tracks)}")
    
    # 5. Remover um track (quando é perdido/finalizado)
    registry.remove(camera_id, 2)
    print(f"✓ Track 2 removido")
    
    # 6. Verificar tracks restantes
    remaining = list(registry.get_by_camera(camera_id))
    print(f"✓ Tracks restantes: {len(remaining)}")


def exemplo_multiplas_cameras():
    """
    Exemplo com múltiplas câmeras.
    """
    registry: TrackRegistry = InMemoryTrackRegistry()
    
    # Registrar tracks de múltiplas câmeras
    cameras = ["camera_001", "camera_002", "camera_003"]
    
    for cam_id in cameras:
        for track_id in range(1, 4):
            registry.register(cam_id, track_id, {
                "camera": cam_id,
                "track_id": track_id,
                "center": (track_id * 100, 100)
            })
    
    print(f"✓ Registrados tracks para {len(cameras)} câmeras")
    
    # Verificar tracks por câmera
    for cam_id in cameras:
        count = len(list(registry.get_by_camera(cam_id)))
        print(f"  {cam_id}: {count} tracks")
    
    # Limpar uma câmera quando ela desconecta
    registry.clear_camera("camera_002")
    print(f"✓ Câmera 'camera_002' desconectada, tracks removidos")


def exemplo_integracao_use_case():
    """
    Exemplo de como integrar o registry em um Use Case.
    """
    from abc import ABC, abstractmethod
    
    class ProcessCameraStreamingWithTracking:
        """
        Use Case que processa streaming de câmera com gerenciamento de tracks.
        """
        
        def __init__(self, track_registry: TrackRegistry):
            self.track_registry = track_registry
        
        def process_frame(self, camera_id: str, yolo_results):
            """
            Processa um frame e atualiza tracks no registry.
            
            Args:
                camera_id: ID da câmera
                yolo_results: Resultados do YOLO (contém track IDs)
            """
            # Exemplo simplificado
            for detection in yolo_results.boxes:
                track_id = int(detection.id)
                track_data = {
                    "bbox": detection.xyxy,
                    "confidence": detection.conf,
                    "center": self._get_center(detection.xyxy),
                }
                
                # Registrar ou atualizar track no registry
                self.track_registry.register(camera_id, track_id, track_data)
        
        def on_camera_disconnect(self, camera_id: str):
            """
            Chamado quando uma câmera desconecta.
            Limpa todos os tracks dessa câmera.
            """
            self.track_registry.clear_camera(camera_id)
            print(f"✓ Tracks da câmera {camera_id} foram removidos")
        
        @staticmethod
        def _get_center(bbox):
            """Calcula centro da bounding box."""
            x1, y1, x2, y2 = bbox
            return ((x1 + x2) / 2, (y1 + y2) / 2)


if __name__ == "__main__":
    print("=" * 60)
    print("EXEMPLO 1: Uso Básico")
    print("=" * 60)
    exemplo_uso_basico()
    
    print("\n" + "=" * 60)
    print("EXEMPLO 2: Múltiplas Câmeras")
    print("=" * 60)
    exemplo_multiplas_cameras()
    
    print("\n" + "=" * 60)
    print("EXEMPLO 3: Integração com Use Case")
    print("=" * 60)
    print("✓ Classe ProcessCameraStreamingWithTracking mostrada acima")
    print("  Demonstra como integrar o registry na lógica de negócio")
