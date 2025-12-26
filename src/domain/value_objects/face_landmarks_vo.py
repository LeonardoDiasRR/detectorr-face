"""
Value Object para os 5 landmarks faciais principais.
"""

from typing import Any, Sequence, Tuple


Keypoint = Tuple[float, float, float]  # (x, y, confidence)


class FaceLandmarksVO:
    """
    Value Object que representa os 5 landmarks faciais principais.

    Os 5 landmarks esperados são:
    0 → olho esquerdo (x, y, confidence)
    1 → olho direito (x, y, confidence)
    2 → nariz (x, y, confidence)
    3 → canto esquerdo da boca (x, y, confidence)
    4 → canto direito da boca (x, y, confidence)
    """

    # Índices dos landmarks
    LEFT_EYE = 0
    RIGHT_EYE = 1
    NOSE = 2
    LEFT_MOUTH = 3
    RIGHT_MOUTH = 4

    EXPECTED_COUNT = 5

    def __init__(self, landmarks: Any):
        """
        Inicializa o FaceLandmarksVO.

        :param landmarks: Sequência com 5 keypoints faciais no formato:
                         [(x_le, y_le, conf), (x_re, y_re, conf), ...]
        :raises TypeError: Se landmarks não for uma sequência.
        :raises ValueError: Se não contiver exatamente 5 landmarks.
        :raises ValueError: Se algum landmark não tiver 3 elementos.
        """
        if not isinstance(landmarks, (list, tuple)):
            raise TypeError(
                f"landmarks deve ser uma sequência (list ou tuple), "
                f"recebido: {type(landmarks).__name__}"
            )

        if len(landmarks) != self.EXPECTED_COUNT:
            raise ValueError(
                f"Esperados {self.EXPECTED_COUNT} landmarks, "
                f"recebidos: {len(landmarks)}"
            )

        # Valida estrutura de cada landmark
        for i, landmark in enumerate(landmarks):
            if not isinstance(landmark, (tuple, list)):
                raise TypeError(
                    f"Landmark {i} deve ser uma sequência, "
                    f"recebido: {type(landmark).__name__}"
                )
            if len(landmark) != 3:
                raise ValueError(
                    f"Landmark {i} deve ter 3 elementos (x, y, confidence), "
                    f"recebidos: {len(landmark)}"
                )

            # Tenta converter para float para validação
            try:
                x, y, conf = landmark
                float(x)
                float(y)
                float(conf)
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Landmark {i} contém valores não numéricos: {landmark}"
                ) from e

        # Armazena como tuple imutável
        self._landmarks = tuple(
            (float(x), float(y), float(conf))
            for x, y, conf in landmarks
        )

    def value(self) -> Tuple[Keypoint, ...]:
        """
        Retorna o valor dos landmarks.

        :return: Tuple com os 5 keypoints faciais.
        """
        return self._landmarks

    def left_eye(self) -> Keypoint:
        """Retorna o keypoint do olho esquerdo."""
        return self._landmarks[self.LEFT_EYE]

    def right_eye(self) -> Keypoint:
        """Retorna o keypoint do olho direito."""
        return self._landmarks[self.RIGHT_EYE]

    def nose(self) -> Keypoint:
        """Retorna o keypoint do nariz."""
        return self._landmarks[self.NOSE]

    def left_mouth(self) -> Keypoint:
        """Retorna o keypoint do canto esquerdo da boca."""
        return self._landmarks[self.LEFT_MOUTH]

    def right_mouth(self) -> Keypoint:
        """Retorna o keypoint do canto direito da boca."""
        return self._landmarks[self.RIGHT_MOUTH]

    def get_landmark(self, index: int) -> Keypoint:
        """
        Retorna um landmark específico pelo índice.

        :param index: Índice do landmark (0-4).
        :return: Keypoint (x, y, confidence).
        :raises IndexError: Se índice fora do intervalo 0-4.
        """
        if not 0 <= index < self.EXPECTED_COUNT:
            raise IndexError(f"Índice {index} fora do intervalo [0, {self.EXPECTED_COUNT - 1}]")
        return self._landmarks[index]

    def as_list(self) -> list:
        """
        Converte landmarks para lista.

        :return: Lista com os 5 keypoints.
        """
        return list(self._landmarks)

    def to_dict(self) -> dict:
        """
        Converte landmarks para dicionário nomeado.

        :return: Dicionário com nomes dos landmarks.
        """
        return {
            'left_eye': self._landmarks[self.LEFT_EYE],
            'right_eye': self._landmarks[self.RIGHT_EYE],
            'nose': self._landmarks[self.NOSE],
            'left_mouth': self._landmarks[self.LEFT_MOUTH],
            'right_mouth': self._landmarks[self.RIGHT_MOUTH],
        }

    def has_valid_confidence(self, min_confidence: float = 0.0) -> bool:
        """
        Verifica se todos os landmarks têm confiança acima do mínimo.

        :param min_confidence: Confiança mínima esperada (padrão 0.0).
        :return: True se todos os landmarks têm confiança >= min_confidence.
        """
        return all(conf >= min_confidence for _, _, conf in self._landmarks)

    def get_min_confidence(self) -> float:
        """
        Retorna a menor confiança entre os landmarks.

        :return: Menor valor de confiança.
        """
        return min(conf for _, _, conf in self._landmarks)

    def get_max_confidence(self) -> float:
        """
        Retorna a maior confiança entre os landmarks.

        :return: Maior valor de confiança.
        """
        return max(conf for _, _, conf in self._landmarks)

    def get_mean_confidence(self) -> float:
        """
        Retorna a confiança média entre os landmarks.

        :return: Valor médio de confiança.
        """
        return sum(conf for _, _, conf in self._landmarks) / self.EXPECTED_COUNT

    def __eq__(self, other) -> bool:
        """Compara dois FaceLandmarksVO por igualdade."""
        if not isinstance(other, FaceLandmarksVO):
            return False
        return self._landmarks == other._landmarks

    def __hash__(self) -> int:
        """Retorna o hash do valor."""
        return hash(self._landmarks)

    def __repr__(self) -> str:
        """Representação string do objeto."""
        return f"FaceLandmarksVO({self._landmarks})"

    def __str__(self) -> str:
        """Conversão para string amigável."""
        return (
            f"FaceLandmarks(left_eye={self._landmarks[0]}, "
            f"right_eye={self._landmarks[1]}, "
            f"nose={self._landmarks[2]}, "
            f"left_mouth={self._landmarks[3]}, "
            f"right_mouth={self._landmarks[4]})"
        )

    def __iter__(self):
        """Permite iteração sobre os landmarks."""
        return iter(self._landmarks)

    def __len__(self) -> int:
        """Retorna o número de landmarks."""
        return len(self._landmarks)

    def __getitem__(self, index: int) -> Keypoint:
        """Permite acesso por índice."""
        return self._landmarks[index]
