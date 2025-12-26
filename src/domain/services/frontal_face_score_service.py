"""
Serviço de domínio para cálculo de índice de frontalidade facial.
"""

import math
from typing import Tuple
from src.domain.value_objects import FaceLandmarksVO


class FrontalFaceScoreService:
    """
    Serviço de domínio responsável por calcular o score
    de frontalidade facial (0.0 – 1.0) usando 5 keypoints faciais.

    Os 5 keypoints esperados são:
    0 → olho esquerdo (x, y, confidence)
    1 → olho direito (x, y, confidence)
    2 → nariz (x, y, confidence)
    3 → canto esquerdo da boca (x, y, confidence)
    4 → canto direito da boca (x, y, confidence)
    """

    # Parâmetros para cálculo de proporção vertical
    VERTICAL_RATIO_MIN = 0.35
    VERTICAL_RATIO_MAX = 0.75

    # Pesos para cálculo do score final
    SYMMETRY_WEIGHT = 0.35
    ROLL_WEIGHT = 0.25
    VERTICAL_WEIGHT = 0.20
    MOUTH_SYMMETRY_WEIGHT = 0.20

    @staticmethod
    def calculate(landmarks: FaceLandmarksVO) -> float:
        """
        Calcula o score de frontalidade da face.

        :param landmarks: FaceLandmarksVO com os 5 keypoints faciais
        :return: Score de frontalidade entre 0.0 e 1.0
        :raises TypeError: Se landmarks não for FaceLandmarksVO
        """
        if not isinstance(landmarks, FaceLandmarksVO):
            raise TypeError(
                f"landmarks deve ser FaceLandmarksVO, "
                f"recebido: {type(landmarks).__name__}"
            )

        # Extrai coordenadas
        le = landmarks.left_eye()
        re = landmarks.right_eye()
        nose = landmarks.nose()
        lm = landmarks.left_mouth()
        rm = landmarks.right_mouth()

        x_le, y_le, _ = le
        x_re, y_re, _ = re
        x_n, y_n, _ = nose
        x_lm, y_lm, _ = lm
        x_rm, y_rm, _ = rm

        # Distância interpupilar (escala base)
        eye_dist = FrontalFaceScoreService._calculate_distance(
            (x_le, y_le), (x_re, y_re)
        )
        if eye_dist < 1e-6:
            return 0.0

        # 1. Simetria horizontal (nariz centralizado)
        symmetry_score = FrontalFaceScoreService._calculate_symmetry(
            x_le, x_re, x_n, eye_dist
        )

        # 2. Alinhamento dos olhos (roll)
        roll_score = FrontalFaceScoreService._calculate_roll(
            y_le, y_re, eye_dist
        )

        # 3. Proporção vertical nariz → boca
        vertical_score = FrontalFaceScoreService._calculate_vertical(
            y_n, y_lm, y_rm, eye_dist
        )

        # 4. Simetria da boca
        mouth_symmetry_score = FrontalFaceScoreService._calculate_mouth_symmetry(
            x_lm, x_rm, x_n, eye_dist
        )

        # Score final com pesos
        score = (
            FrontalFaceScoreService.SYMMETRY_WEIGHT * symmetry_score +
            FrontalFaceScoreService.ROLL_WEIGHT * roll_score +
            FrontalFaceScoreService.VERTICAL_WEIGHT * vertical_score +
            FrontalFaceScoreService.MOUTH_SYMMETRY_WEIGHT * mouth_symmetry_score
        )

        # Garante resultado entre 0.0 e 1.0
        final_score = max(0.0, min(1.0, score))
        return round(final_score, 3)

    @staticmethod
    def _calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calcula distância euclidiana entre dois pontos."""
        return math.dist(p1, p2)

    @staticmethod
    def _calculate_symmetry(x_le: float, x_re: float, x_n: float, eye_dist: float) -> float:
        """
        Calcula simetria horizontal (nariz centralizado).

        :return: Score entre 0.0 e 1.0
        """
        eye_center_x = (x_le + x_re) / 2
        nose_offset = abs(x_n - eye_center_x) / eye_dist
        return max(0.0, 1.0 - nose_offset)

    @staticmethod
    def _calculate_roll(y_le: float, y_re: float, eye_dist: float) -> float:
        """
        Calcula alinhamento dos olhos (roll).

        :return: Score entre 0.0 e 1.0
        """
        eye_vertical_diff = abs(y_le - y_re) / eye_dist
        return max(0.0, 1.0 - eye_vertical_diff)

    @staticmethod
    def _calculate_vertical(y_n: float, y_lm: float, y_rm: float, eye_dist: float) -> float:
        """
        Calcula proporção vertical nariz → boca.

        :return: Score entre 0.0 e 1.0
        """
        mouth_center_y = (y_lm + y_rm) / 2
        vertical_ratio = (mouth_center_y - y_n) / eye_dist

        if vertical_ratio < FrontalFaceScoreService.VERTICAL_RATIO_MIN:
            return vertical_ratio / FrontalFaceScoreService.VERTICAL_RATIO_MIN
        elif vertical_ratio > FrontalFaceScoreService.VERTICAL_RATIO_MAX:
            return max(
                0.0,
                1.0 - (vertical_ratio - FrontalFaceScoreService.VERTICAL_RATIO_MAX)
            )
        else:
            return 1.0

    @staticmethod
    def _calculate_mouth_symmetry(x_lm: float, x_rm: float, x_n: float, eye_dist: float) -> float:
        """
        Calcula simetria da boca.

        :return: Score entre 0.0 e 1.0
        """
        mouth_center_x = (x_lm + x_rm) / 2
        mouth_offset = abs(mouth_center_x - x_n) / eye_dist
        return max(0.0, 1.0 - mouth_offset)
