"""
Configurações pytest para testes da camada de aplicação.
"""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_camera_repository():
    """Mock do repositório de câmeras com configuração padrão."""
    repo = Mock()
    repo.get_cameras = Mock(return_value=[])
    return repo
