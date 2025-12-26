"""
Value Object para os 17 landmarks corporais (formato COCO Keypoints).
"""

from typing import Any, Tuple


Keypoint = Tuple[float, float, float]  # (x, y, confidence)


class BodyLandmarksVO:
    """
    Value Object que representa os 17 landmarks corporais (formato COCO).

    Keypoints 0-4: Face/Cabeça
    0 → Nose (ponta do nariz)
    1 → Left Eye (centro do olho esquerdo)
    2 → Right Eye (centro do olho direito)
    3 → Left Ear (região da orelha esquerda)
    4 → Right Ear (região da orelha direita)

    Keypoints 5-10: Braços
    5 → Left Shoulder (ombro esquerdo)
    6 → Right Shoulder (ombro direito)
    7 → Left Elbow (cotovelo esquerdo)
    8 → Right Elbow (cotovelo direito)
    9 → Left Wrist (pulso esquerdo)
    10 → Right Wrist (pulso direito)

    Keypoints 11-12: Tronco
    11 → Left Hip (quadril esquerdo)
    12 → Right Hip (quadril direito)

    Keypoints 13-16: Pernas
    13 → Left Knee (joelho esquerdo)
    14 → Right Knee (joelho direito)
    15 → Left Ankle (tornozelo esquerdo)
    16 → Right Ankle (tornozelo direito)
    """

    # Índices para Face/Cabeça
    NOSE = 0
    LEFT_EYE = 1
    RIGHT_EYE = 2
    LEFT_EAR = 3
    RIGHT_EAR = 4

    # Índices para Braços
    LEFT_SHOULDER = 5
    RIGHT_SHOULDER = 6
    LEFT_ELBOW = 7
    RIGHT_ELBOW = 8
    LEFT_WRIST = 9
    RIGHT_WRIST = 10

    # Índices para Tronco
    LEFT_HIP = 11
    RIGHT_HIP = 12

    # Índices para Pernas
    LEFT_KNEE = 13
    RIGHT_KNEE = 14
    LEFT_ANKLE = 15
    RIGHT_ANKLE = 16

    # Total de landmarks esperados
    EXPECTED_COUNT = 17

    # Nomes legíveis dos landmarks
    KEYPOINT_NAMES = {
        0: "Nose",
        1: "Left Eye",
        2: "Right Eye",
        3: "Left Ear",
        4: "Right Ear",
        5: "Left Shoulder",
        6: "Right Shoulder",
        7: "Left Elbow",
        8: "Right Elbow",
        9: "Left Wrist",
        10: "Right Wrist",
        11: "Left Hip",
        12: "Right Hip",
        13: "Left Knee",
        14: "Right Knee",
        15: "Left Ankle",
        16: "Right Ankle",
    }

    def __init__(self, landmarks: Any):
        """
        Inicializa o BodyLandmarksVO.

        :param landmarks: Sequência com 17 keypoints corporais no formato:
                         [(x, y, conf), ...] para cada um dos 17 pontos
        :raises TypeError: Se landmarks não for uma sequência.
        :raises ValueError: Se não contiver exatamente 17 landmarks.
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

        :return: Tuple com os 17 keypoints corporais.
        """
        return self._landmarks

    # ========================
    # Métodos de acesso - Face
    # ========================

    def nose(self) -> Keypoint:
        """Retorna o keypoint do nariz."""
        return self._landmarks[self.NOSE]

    def left_eye(self) -> Keypoint:
        """Retorna o keypoint do olho esquerdo."""
        return self._landmarks[self.LEFT_EYE]

    def right_eye(self) -> Keypoint:
        """Retorna o keypoint do olho direito."""
        return self._landmarks[self.RIGHT_EYE]

    def left_ear(self) -> Keypoint:
        """Retorna o keypoint da orelha esquerda."""
        return self._landmarks[self.LEFT_EAR]

    def right_ear(self) -> Keypoint:
        """Retorna o keypoint da orelha direita."""
        return self._landmarks[self.RIGHT_EAR]

    # ==========================
    # Métodos de acesso - Braços
    # ==========================

    def left_shoulder(self) -> Keypoint:
        """Retorna o keypoint do ombro esquerdo."""
        return self._landmarks[self.LEFT_SHOULDER]

    def right_shoulder(self) -> Keypoint:
        """Retorna o keypoint do ombro direito."""
        return self._landmarks[self.RIGHT_SHOULDER]

    def left_elbow(self) -> Keypoint:
        """Retorna o keypoint do cotovelo esquerdo."""
        return self._landmarks[self.LEFT_ELBOW]

    def right_elbow(self) -> Keypoint:
        """Retorna o keypoint do cotovelo direito."""
        return self._landmarks[self.RIGHT_ELBOW]

    def left_wrist(self) -> Keypoint:
        """Retorna o keypoint do pulso esquerdo."""
        return self._landmarks[self.LEFT_WRIST]

    def right_wrist(self) -> Keypoint:
        """Retorna o keypoint do pulso direito."""
        return self._landmarks[self.RIGHT_WRIST]

    # ==========================
    # Métodos de acesso - Tronco
    # ==========================

    def left_hip(self) -> Keypoint:
        """Retorna o keypoint do quadril esquerdo."""
        return self._landmarks[self.LEFT_HIP]

    def right_hip(self) -> Keypoint:
        """Retorna o keypoint do quadril direito."""
        return self._landmarks[self.RIGHT_HIP]

    # ==========================
    # Métodos de acesso - Pernas
    # ==========================

    def left_knee(self) -> Keypoint:
        """Retorna o keypoint do joelho esquerdo."""
        return self._landmarks[self.LEFT_KNEE]

    def right_knee(self) -> Keypoint:
        """Retorna o keypoint do joelho direito."""
        return self._landmarks[self.RIGHT_KNEE]

    def left_ankle(self) -> Keypoint:
        """Retorna o keypoint do tornozelo esquerdo."""
        return self._landmarks[self.LEFT_ANKLE]

    def right_ankle(self) -> Keypoint:
        """Retorna o keypoint do tornozelo direito."""
        return self._landmarks[self.RIGHT_ANKLE]

    # ==========================
    # Métodos de acesso genérico
    # ==========================

    def get_landmark(self, index: int) -> Keypoint:
        """
        Retorna um landmark específico pelo índice.

        :param index: Índice do landmark (0-16).
        :return: Keypoint (x, y, confidence).
        :raises IndexError: Se índice fora do intervalo 0-16.
        """
        if not 0 <= index < self.EXPECTED_COUNT:
            raise IndexError(
                f"Índice {index} fora do intervalo [0, {self.EXPECTED_COUNT - 1}]"
            )
        return self._landmarks[index]

    def get_landmark_name(self, index: int) -> str:
        """
        Retorna o nome legível de um landmark.

        :param index: Índice do landmark (0-16).
        :return: Nome do landmark (ex: "Left Shoulder").
        :raises IndexError: Se índice fora do intervalo.
        """
        if not 0 <= index < self.EXPECTED_COUNT:
            raise IndexError(f"Índice {index} fora do intervalo")
        return self.KEYPOINT_NAMES[index]

    def as_list(self) -> list:
        """
        Converte landmarks para lista.

        :return: Lista com os 17 keypoints.
        """
        return list(self._landmarks)

    def to_dict(self) -> dict:
        """
        Converte landmarks para dicionário nomeado.

        :return: Dicionário com nomes dos landmarks como chaves.
        """
        return {
            self.KEYPOINT_NAMES[i]: landmark
            for i, landmark in enumerate(self._landmarks)
        }

    def get_face_landmarks(self) -> Tuple[Keypoint, ...]:
        """
        Retorna apenas os 5 landmarks faciais (0-4).

        :return: Tuple com os keypoints da face.
        """
        return self._landmarks[0:5]

    def get_arm_landmarks(self) -> Tuple[Keypoint, ...]:
        """
        Retorna apenas os 6 landmarks de braços (5-10).

        :return: Tuple com os keypoints dos braços.
        """
        return self._landmarks[5:11]

    def get_torso_landmarks(self) -> Tuple[Keypoint, ...]:
        """
        Retorna apenas os 2 landmarks de tronco (11-12).

        :return: Tuple com os keypoints do tronco.
        """
        return self._landmarks[11:13]

    def get_leg_landmarks(self) -> Tuple[Keypoint, ...]:
        """
        Retorna apenas os 4 landmarks de pernas (13-16).

        :return: Tuple com os keypoints das pernas.
        """
        return self._landmarks[13:17]

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

    def count_valid_landmarks(self, min_confidence: float = 0.0) -> int:
        """
        Conta quantos landmarks têm confiança acima do mínimo.

        :param min_confidence: Confiança mínima.
        :return: Número de landmarks válidos.
        """
        return sum(1 for _, _, conf in self._landmarks if conf >= min_confidence)

    def __eq__(self, other) -> bool:
        """Compara dois BodyLandmarksVO por igualdade."""
        if not isinstance(other, BodyLandmarksVO):
            return False
        return self._landmarks == other._landmarks

    def __hash__(self) -> int:
        """Retorna o hash do valor."""
        return hash(self._landmarks)

    def __repr__(self) -> str:
        """Representação string do objeto."""
        return f"BodyLandmarksVO({self.EXPECTED_COUNT} landmarks)"

    def __str__(self) -> str:
        """Conversão para string amigável."""
        return (
            f"BodyLandmarks({self.EXPECTED_COUNT} pontos: "
            f"face={len(self.get_face_landmarks())}, "
            f"arms={len(self.get_arm_landmarks())}, "
            f"torso={len(self.get_torso_landmarks())}, "
            f"legs={len(self.get_leg_landmarks())})"
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
