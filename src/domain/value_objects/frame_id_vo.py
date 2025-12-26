"""
Value Object para ID de frame.
"""

from typing import Union
from datetime import datetime


class FrameIdVO:
    """
    Value Object que representa o ID único de um frame.
    
    Formato: {camera_id}-{unix_epoch_time_microsegundos}
    Exemplo: 282-1735009389123
    
    Segue o padrão DDD de Value Object imutável.
    """

    def __init__(self, camera_id: Union[int, str], timestamp: Union[datetime, float, int]):
        """
        Inicializa o FrameIdVO.

        :param camera_id: ID da câmera (inteiro ou string numérica).
        :param timestamp: Timestamp (datetime, float Unix ou int Unix).
        :raises TypeError: Se camera_id não for int/str ou timestamp inválido.
        :raises ValueError: Se camera_id for inválido ou timestamp negativo.
        """
        # Validar e converter camera_id
        if isinstance(camera_id, int):
            if camera_id < 0:
                raise ValueError(f"camera_id deve ser não-negativo, recebido: {camera_id}")
            camera_id_str = str(camera_id)
        elif isinstance(camera_id, str):
            try:
                camera_id_int = int(camera_id)
                if camera_id_int < 0:
                    raise ValueError(f"camera_id deve ser não-negativo, recebido: {camera_id_int}")
                camera_id_str = camera_id
            except ValueError as e:
                raise ValueError(f"camera_id deve ser um inteiro válido, recebido: {camera_id}") from e
        else:
            raise TypeError(f"camera_id deve ser int ou str, recebido: {type(camera_id).__name__}")

        # Converter timestamp para Unix timestamp com microsegundos
        if isinstance(timestamp, datetime):
            unix_timestamp_ms = int(timestamp.timestamp() * 1000)
        elif isinstance(timestamp, (float, int)):
            # Se o timestamp tiver mais de 13 dígitos, provavelmente é em milissegundos/microsegundos
            # Caso contrário, é em segundos
            # Threshold: 100000000000 = ~3169-08-26 em milissegundos
            if abs(timestamp) > 100000000000:
                # Já está em milissegundos ou superior
                unix_timestamp_ms = int(timestamp)
            else:
                # Está em segundos, converter para milissegundos
                unix_timestamp_ms = int(timestamp * 1000)
        else:
            raise TypeError(
                f"timestamp deve ser datetime, float ou int, recebido: {type(timestamp).__name__}"
            )

        if unix_timestamp_ms < 0:
            raise ValueError(f"timestamp não pode ser negativo, recebido: {unix_timestamp_ms}")

        # Formatar como "camera_id-timestamp_ms"
        self._value = f"{camera_id_str}-{unix_timestamp_ms}"
        self._camera_id = int(camera_id_str)
        self._timestamp_ms = unix_timestamp_ms

    def value(self) -> str:
        """
        Retorna o valor do ID do frame.

        :return: ID do frame no formato "camera_id-timestamp_ms".
        """
        return self._value

    def camera_id(self) -> int:
        """
        Retorna o ID da câmera extraído do frame ID.

        :return: ID da câmera como inteiro.
        """
        return self._camera_id

    def timestamp_ms(self) -> int:
        """
        Retorna o timestamp em milissegundos (Unix epoch).

        :return: Timestamp em milissegundos.
        """
        return self._timestamp_ms

    def timestamp_s(self) -> float:
        """
        Retorna o timestamp em segundos (Unix epoch).

        :return: Timestamp em segundos como float.
        """
        return self._timestamp_ms / 1000.0

    def __eq__(self, other) -> bool:
        """Compara dois FrameIdVO por igualdade."""
        if not isinstance(other, FrameIdVO):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        """Retorna o hash do valor para uso em conjuntos e dicionários."""
        return hash(self._value)

    def __repr__(self) -> str:
        """Representação string do objeto."""
        return f"FrameIdVO('{self._value}')"

    def __str__(self) -> str:
        """Conversão para string."""
        return self._value

    def __lt__(self, other) -> bool:
        """Compara se este FrameIdVO é anterior a outro (por timestamp)."""
        if not isinstance(other, FrameIdVO):
            return NotImplemented
        return self._timestamp_ms < other._timestamp_ms

    def __le__(self, other) -> bool:
        """Compara se este FrameIdVO é anterior ou igual a outro."""
        if not isinstance(other, FrameIdVO):
            return NotImplemented
        return self._timestamp_ms <= other._timestamp_ms

    def __gt__(self, other) -> bool:
        """Compara se este FrameIdVO é posterior a outro (por timestamp)."""
        if not isinstance(other, FrameIdVO):
            return NotImplemented
        return self._timestamp_ms > other._timestamp_ms

    def __ge__(self, other) -> bool:
        """Compara se este FrameIdVO é posterior ou igual a outro."""
        if not isinstance(other, FrameIdVO):
            return NotImplemented
        return self._timestamp_ms >= other._timestamp_ms
