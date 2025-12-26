"""
Fixtures compartilhadas para testes de domínio.
"""

import pytest
import numpy as np
from datetime import datetime
from src.domain.entities.frame_entity import Frame
from src.domain.value_objects import IdVO, NameVO, CameraTokenVO, FullFrameVO, TimestampVO, FrameIdVO


@pytest.fixture
def sample_frame():
    """Fixture para criar um Frame de exemplo com FrameIdVO."""
    frame_array = np.zeros((480, 640, 3), dtype=np.uint8)
    full_frame = FullFrameVO(frame_array)
    return Frame(
        FrameIdVO(camera_id=1, timestamp=datetime.now()),
        full_frame,
        IdVO(1),
        NameVO("Câmera 1"),
        CameraTokenVO("token123"),
        TimestampVO(datetime.now())
    )


@pytest.fixture
def sample_frame_with_id(sample_frame):
    """Fixture que retorna o frame com seu ID."""
    return sample_frame
