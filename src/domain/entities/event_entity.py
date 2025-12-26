"""
Entidade Event representando uma detecção de face em um frame.
"""

from typing import Optional
from src.domain.entities.frame_entity import Frame
from src.domain.value_objects import IdVO, BboxVO, ConfidenceVO, FaceLandmarksVO


class Event:
    """
    Entidade que representa uma detecção de face (evento) em um frame específico.
    """

    def __init__(
        self,
        frame: Frame,
        bbox: BboxVO,
        confidence: ConfidenceVO,
        landmarks: FaceLandmarksVO,
        track_id: int,
        face_quality_score: Optional[ConfidenceVO] = None,
        class_id: Optional[int] = None
    ):
        """
        Inicializa a entidade Event.

        :param frame: Frame onde a face foi detectada.
        :param bbox: Bounding box da face.
        :param confidence: Confiança da detecção YOLO.
        :param landmarks: Landmarks faciais.
        :param track_id: ID do rastreamento (vem do YOLO tracking).
        :param face_quality_score: Score de qualidade da face (opcional, pode ser None).
        :param class_id: ID da classe da detecção YOLO (opcional).
        """
        if not isinstance(frame, Frame):
            raise TypeError(f"frame deve ser Frame, recebido: {type(frame).__name__}")
        if not isinstance(bbox, BboxVO):
            raise TypeError(f"bbox deve ser BboxVO, recebido: {type(bbox).__name__}")
        if not isinstance(confidence, ConfidenceVO):
            raise TypeError(f"confidence deve ser ConfidenceVO, recebido: {type(confidence).__name__}")
        if not isinstance(landmarks, FaceLandmarksVO):
            raise TypeError(f"landmarks deve ser FaceLandmarksVO, recebido: {type(landmarks).__name__}")
        if not isinstance(track_id, int):
            raise TypeError(f"track_id deve ser int, recebido: {type(track_id).__name__}")
        if face_quality_score is not None and not isinstance(face_quality_score, ConfidenceVO):
            raise TypeError(f"face_quality_score deve ser ConfidenceVO, recebido: {type(face_quality_score).__name__}")
        if class_id is not None and not isinstance(class_id, int):
            raise TypeError(f"class_id deve ser int ou None, recebido: {type(class_id).__name__}")

        self._frame = frame
        self._bbox = bbox
        self._confidence = confidence
        self._landmarks = landmarks
        self._track_id = track_id
        # face_quality_score permanece None se não for fornecido
        # A entidade não é responsável por calcular a qualidade (responsabilidade do serviço de aplicação)
        self._face_quality_score = face_quality_score
        self._class_id = class_id

    @property
    def frame(self) -> Frame:
        """Retorna o frame do evento."""
        return self._frame

    @property
    def bbox(self) -> BboxVO:
        """Retorna o bounding box."""
        return self._bbox

    @property
    def confidence(self) -> ConfidenceVO:
        """Retorna a confiança da detecção."""
        return self._confidence

    @property
    def landmarks(self) -> FaceLandmarksVO:
        """Retorna os landmarks."""
        return self._landmarks

    @property
    def track_id(self) -> int:
        """Retorna o ID do rastreamento."""
        return self._track_id

    @property
    def face_quality_score(self) -> Optional[ConfidenceVO]:
        """Retorna o score de qualidade da face (pode ser None)."""
        return self._face_quality_score

    @property
    def class_id(self) -> Optional[int]:
        """Retorna o ID da classe YOLO (pode ser None)."""
        return self._class_id

    @property
    def camera_id(self) -> IdVO:
        """Retorna o ID da câmera (delegado ao frame)."""
        return self._frame.camera_id

    @property
    def camera_name(self):
        """Retorna o nome da câmera (delegado ao frame)."""
        return self._frame.camera_name

    @property
    def camera_token(self):
        """Retorna o token da câmera (delegado ao frame)."""
        return self._frame.camera_token

    def remove_frame(self) -> None:
        """
        Remove o frame do evento para economizar memória.
        O frame é descartado após ser processado.
        """
        self._frame = None

    def to_dict(self) -> dict:
        """
        Converte o evento para dicionário.

        :return: Dicionário com os dados do evento.
        """
        return {
            "track_id": self._track_id,
            "bbox": self._bbox.value(),
            "confidence": self._confidence.value(),
            "landmarks": self._landmarks.to_list() if not self._landmarks.is_empty() else None,
            "face_quality_score": self._face_quality_score.value() if self._face_quality_score is not None else None,
            "camera_id": self.camera_id.value(),
            "camera_name": self.camera_name.value(),
            "camera_token": self.camera_token.value()
        }

    def __eq__(self, other) -> bool:
        """Verifica igualdade baseada no frame, bbox e track_id."""
        if not isinstance(other, Event):
            return False
        return self._frame == other._frame and self._bbox == other._bbox and self._track_id == other._track_id

    def __hash__(self) -> int:
        """Retorna hash baseado no frame, bbox e track_id."""
        return hash((self._frame, self._bbox, self._track_id))

    def __repr__(self) -> str:
        """Representação técnica do evento."""
        quality_str = f"{self._face_quality_score.value():.4f}" if self._face_quality_score is not None else "None"
        return (
            f"Event("
            f"track_id={self._track_id}, "
            f"bbox={self._bbox}, "
            f"confidence={self._confidence.value():.4f}, "
            f"quality={quality_str})"
        )

    def __str__(self) -> str:
        """Representação legível do evento."""
        quality = self._face_quality_score.value() if self._face_quality_score is not None else 0.0
        return f"Event (Quality: {quality:.4f})"
