"""
Value Objects para o domínio da aplicação.
"""

from .id_vo import IdVO
from .name_vo import NameVO
from .camera_token_vo import CameraTokenVO
from .camera_source_vo import CameraSourceVO
from .bbox_vo import BboxVO
from .confidence_vo import ConfidenceVO
from .face_landmarks_vo import FaceLandmarksVO
from .body_landmarks_vo import BodyLandmarksVO
from .timestamp_vo import TimestampVO
from .full_frame_vo import FullFrameVO
from .frame_id_vo import FrameIdVO

__all__ = [
    'IdVO',
    'NameVO',
    'CameraTokenVO',
    'CameraSourceVO',
    'BboxVO',
    'ConfidenceVO',
    'FaceLandmarksVO',
    'BodyLandmarksVO',
    'TimestampVO',
    'FullFrameVO',
    'FrameIdVO',
]
