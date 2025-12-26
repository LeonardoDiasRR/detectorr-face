"""
Pacote de configuração da infraestrutura.
Fornece gerenciamento centralizado de configurações type-safe.
"""

from .settings import (
    ApplicationSettings,
    TrackModelConfig,
    YOLOParams,
    FindfaceConfig,
)
from .config_loader import ConfigLoader, get_settings, reload_settings

__all__ = [
    'ApplicationSettings',
    'TrackModelConfig',
    'YOLOParams',
    'FindfaceConfig',
    'ConfigLoader',
    'get_settings',
    'reload_settings',
]
