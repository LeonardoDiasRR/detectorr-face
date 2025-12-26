"""
Entidade Frame do domínio.
"""

from typing import Optional, Tuple, List
import numpy as np
import cv2
from src.domain.value_objects import IdVO, NameVO, CameraTokenVO, TimestampVO, FullFrameVO, FrameIdVO, BboxVO, FaceLandmarksVO, ConfidenceVO


class Frame:
    """
    Entidade que representa um frame capturado de uma câmera.
    
    Contém tanto os dados básicos do frame quanto opcionalmente as detecções
    (bboxes, landmarks, track_ids, confidences) para processamento.
    """

    def __init__(
        self,
        full_frame: FullFrameVO,
        camera_id: IdVO,
        camera_name: NameVO,
        camera_token: CameraTokenVO,
        timestamp: TimestampVO,
        bboxes: Optional[List[BboxVO]] = None,
        landmarks: Optional[List[FaceLandmarksVO]] = None,
        track_ids: Optional[List[int]] = None,
        confidences: Optional[List[ConfidenceVO]] = None,
        classes: Optional[List[int]] = None
    ):
        """
        Inicializa a entidade Frame.

        :param full_frame: Frame completo como FullFrameVO.
        :param camera_id: ID da câmera que capturou o frame (IdVO).
        :param camera_name: Nome da câmera que capturou o frame (NameVO).
        :param camera_token: Token de autenticação da câmera (CameraTokenVO).
        :param timestamp: Timestamp de captura do frame (TimestampVO).
        :param bboxes: Lista opcional de bounding boxes das detecções.
        :param landmarks: Lista opcional de landmarks das detecções.
        :param track_ids: Lista opcional de IDs de track das detecções.
        :param confidences: Lista opcional de confiança das detecções.
        :param classes: Lista opcional de IDs de classe das detecções.
        :raises TypeError: Se algum parâmetro não for do tipo esperado.
        """
        if not isinstance(full_frame, FullFrameVO):
            raise TypeError(f"full_frame deve ser FullFrameVO, recebido: {type(full_frame).__name__}")
        
        if not isinstance(camera_id, IdVO):
            raise TypeError(f"camera_id deve ser IdVO, recebido: {type(camera_id).__name__}")
        
        if not isinstance(camera_name, NameVO):
            raise TypeError(f"camera_name deve ser NameVO, recebido: {type(camera_name).__name__}")
        
        if not isinstance(camera_token, CameraTokenVO):
            raise TypeError(f"camera_token deve ser CameraTokenVO, recebido: {type(camera_token).__name__}")
        
        if not isinstance(timestamp, TimestampVO):
            raise TypeError(f"timestamp deve ser TimestampVO, recebido: {type(timestamp).__name__}")
        
        if bboxes is not None and not isinstance(bboxes, list):
            raise TypeError(f"bboxes deve ser list ou None, recebido: {type(bboxes).__name__}")
        
        if bboxes is not None:
            for bbox in bboxes:
                if not isinstance(bbox, BboxVO):
                    raise TypeError(f"Cada bbox deve ser BboxVO, encontrado: {type(bbox).__name__}")
        
        if landmarks is not None and not isinstance(landmarks, list):
            raise TypeError(f"landmarks deve ser list ou None, recebido: {type(landmarks).__name__}")
        
        if landmarks is not None:
            for landmark in landmarks:
                if not isinstance(landmark, FaceLandmarksVO):
                    raise TypeError(f"Cada landmark deve ser FaceLandmarksVO, encontrado: {type(landmark).__name__}")
        
        if track_ids is not None and not isinstance(track_ids, list):
            raise TypeError(f"track_ids deve ser list ou None, recebido: {type(track_ids).__name__}")
        
        if track_ids is not None:
            for track_id in track_ids:
                if not isinstance(track_id, int):
                    raise TypeError(f"Cada track_id deve ser int, encontrado: {type(track_id).__name__}")
        
        if confidences is not None and not isinstance(confidences, list):
            raise TypeError(f"confidences deve ser list ou None, recebido: {type(confidences).__name__}")
        
        if confidences is not None:
            for confidence in confidences:
                if not isinstance(confidence, ConfidenceVO):
                    raise TypeError(f"Cada confidence deve ser ConfidenceVO, encontrado: {type(confidence).__name__}")
        
        if classes is not None and not isinstance(classes, list):
            raise TypeError(f"classes deve ser list ou None, recebido: {type(classes).__name__}")
        
        if classes is not None:
            for class_id in classes:
                if not isinstance(class_id, int):
                    raise TypeError(f"Cada class deve ser int, encontrado: {type(class_id).__name__}")
        
        self._full_frame = full_frame
        self._camera_id = camera_id
        self._camera_name = camera_name
        self._camera_token = camera_token
        self._timestamp = timestamp
        self._bboxes = bboxes or []
        self._landmarks = landmarks or []
        self._track_ids = track_ids or []
        self._confidences = confidences or []
        self._classes = classes or []

    @property
    def full_frame(self) -> FullFrameVO:
        """Retorna o FullFrameVO do frame."""
        return self._full_frame

    @property
    def ndarray(self) -> np.ndarray:
        """
        Retorna o array numpy do frame (cópia).
        Para operações read-only, use ndarray_readonly para evitar cópia.
        """
        return self._full_frame.value(copy=True)
    
    @property
    def ndarray_readonly(self) -> np.ndarray:
        """
        Retorna referência read-only ao array numpy do frame - ZERO cópias.
        OTIMIZAÇÃO: Use este método para operações de leitura.
        
        :return: Referência read-only ao ndarray.
        """
        return self._full_frame.ndarray_readonly

    @property
    def camera_id(self) -> IdVO:
        """Retorna o ID da câmera."""
        return self._camera_id

    @property
    def camera_name(self) -> NameVO:
        """Retorna o nome da câmera."""
        return self._camera_name

    @property
    def camera_token(self) -> CameraTokenVO:
        """Retorna o token da câmera."""
        return self._camera_token

    @property
    def timestamp(self) -> TimestampVO:
        """Retorna o timestamp de captura do frame."""
        return self._timestamp

    @property
    def bboxes(self) -> List[BboxVO]:
        """Retorna a lista de bounding boxes das detecções."""
        return self._bboxes

    @property
    def landmarks(self) -> List[FaceLandmarksVO]:
        """Retorna a lista de landmarks das detecções."""
        return self._landmarks

    @property
    def track_ids(self) -> List[int]:
        """Retorna a lista de IDs de track das detecções."""
        return self._track_ids

    @property
    def confidences(self) -> List[ConfidenceVO]:
        """Retorna a lista de confiança das detecções."""
        return self._confidences

    @property
    def classes(self) -> List[int]:
        """Retorna a lista de IDs de classe das detecções."""
        return self._classes

    def jpg(self, quality: int = 95) -> bytes:
        """
        Converte o frame para formato JPEG e retorna como bytes.
        OTIMIZAÇÃO: Usa ndarray_readonly para evitar cópia desnecessária.

        :param quality: Qualidade de compressão JPEG (0-100), padrão 95.
        :return: Frame codificado em JPEG como bytes.
        :raises ValueError: Se a qualidade for inválida.
        :raises RuntimeError: Se a codificação falhar.
        """
        if not 0 <= quality <= 100:
            raise ValueError(f"Qualidade deve estar entre 0 e 100, recebido: {quality}")
        
        # OTIMIZAÇÃO: Usa ndarray_readonly - cv2.imencode não modifica a imagem
        success, buffer = cv2.imencode('.jpg', self.ndarray_readonly, [cv2.IMWRITE_JPEG_QUALITY, quality])
        
        if not success:
            raise RuntimeError("Falha ao codificar o frame em JPEG")
        
        return buffer.tobytes()

    def png(self, compression: int = 0) -> bytes:
        """
        Converte o frame para formato PNG e retorna como bytes.
        PNG encoding é ~5-10x mais rápido que JPEG quality=95 (sem compressão).
        OTIMIZAÇÃO: Usa ndarray_readonly para evitar cópia desnecessária.

        :param compression: Nível de compressão PNG (0-9), padrão 0 (sem compressão = mais rápido).
        :return: Frame codificado em PNG como bytes.
        :raises ValueError: Se o nível de compressão for inválido.
        :raises RuntimeError: Se a codificação falhar.
        """
        if not 0 <= compression <= 9:
            raise ValueError(f"Compressão deve estar entre 0 e 9, recebido: {compression}")
        
        # OTIMIZAÇÃO: Usa ndarray_readonly - cv2.imencode não modifica a imagem
        # Compression 0 = sem compressão (máxima velocidade, ~5-10x mais rápido que JPEG)
        success, buffer = cv2.imencode('.png', self.ndarray_readonly, [cv2.IMWRITE_PNG_COMPRESSION, compression])
        
        if not success:
            raise RuntimeError("Falha ao codificar o frame em PNG")
        
        return buffer.tobytes()

    @property
    def shape(self) -> Tuple[int, ...]:
        """Retorna as dimensões do frame (altura, largura, canais)."""
        return self._full_frame.shape

    @property
    def height(self) -> int:
        """Retorna a altura do frame."""
        return self._full_frame.height

    @property
    def width(self) -> int:
        """Retorna a largura do frame."""
        return self._full_frame.width

    def copy(self) -> 'Frame':
        """
        Cria uma cópia do frame.

        :return: Nova instância de Frame com FullFrameVO copiado e detecções preservadas.
        """
        return Frame(
            full_frame=FullFrameVO(self.ndarray),
            camera_id=self._camera_id,
            camera_name=self._camera_name,
            camera_token=self._camera_token,
            timestamp=self._timestamp,
            bboxes=self._bboxes.copy(),
            landmarks=self._landmarks.copy(),
            track_ids=self._track_ids.copy(),
            confidences=self._confidences.copy(),
            classes=self._classes.copy()
        )

    def __eq__(self, other) -> bool:
        """Compara dois frames por igualdade (baseado na câmera e timestamp)."""
        if not isinstance(other, Frame):
            return False
        return (self._camera_id == other._camera_id and 
                self._timestamp == other._timestamp)

    def __hash__(self) -> int:
        """Retorna o hash do frame (baseado na câmera e timestamp)."""
        return hash((self._camera_id, self._timestamp))

    def __repr__(self) -> str:
        """Representação string do frame."""
        return (
            f"Frame("
            f"shape={self.shape}, "
            f"camera_id={self._camera_id.value()}, "
            f"camera_name='{self._camera_name.value()}')"
        )

    def __str__(self) -> str:
        """Conversão para string."""
        return f"Frame from Camera {self._camera_id.value()}: {self.width}x{self.height}"
