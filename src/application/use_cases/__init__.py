"""
Package de casos de uso da aplicação.
"""

from .monitor_cameras_use_case import MonitorCamerasUseCase
from .process_best_event_queue_use_case import ProcessBestEventQueueUseCase
from .expire_tracks_use_case import ExpireTracksUseCase

# Lazy import - importado apenas quando necessário
def __getattr__(name):
    if name == 'ProcessCameraStreamingUseCase':
        from .process_camera_streaming_use_case import ProcessCameraStreamingUseCase
        return ProcessCameraStreamingUseCase
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    'MonitorCamerasUseCase',
    'ProcessCameraStreamingUseCase',
    'ProcessBestEventQueueUseCase',
    'ExpireTracksUseCase',
]
