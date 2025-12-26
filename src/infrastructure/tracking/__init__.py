"""
Módulo de infraestrutura para gerenciamento de tracks.
Implementações concretas de armazenamento de tracks.
"""

from .in_memory_track_registry import InMemoryTrackRegistry

__all__ = ['InMemoryTrackRegistry']
