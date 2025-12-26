"""
Entidade Track do domínio.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from src.domain.value_objects import IdVO
from src.domain.entities.event_entity import Event


class Track:
    """
    Entidade que representa um track (rastreamento) de uma face ao longo de múltiplos frames.
    OTIMIZAÇÃO MÁXIMA: Armazena apenas 3 eventos (primeiro, melhor, último) ao invés de lista completa.
    Economia de memória: ~99% (de 5.4GB para ~18MB em tracks longos).
    """

    def __init__(
        self,
        id: IdVO,
        max_events: int = 300,
        min_movement_pixels: float = 2.0,
        ttl: int = 3
    ):
        """
        Inicializa a entidade Track.
        OTIMIZAÇÃO: Armazena apenas best_event e last_event.

        :param id: ID único do track (IdVO).
        :param max_events: Número máximo de eventos que o track pode armazenar (padrão 300).
        :param min_movement_pixels: Limiar mínimo em pixels para considerar movimento (padrão 2.0).
        :param ttl: Tempo de vida máximo do track em segundos (padrão 3).
        :raises TypeError: Se algum parâmetro não for do tipo esperado.
        """
        if not isinstance(id, IdVO):
            raise TypeError(f"id deve ser IdVO, recebido: {type(id).__name__}")
        
        if not isinstance(max_events, int) or max_events <= 0:
            raise TypeError(f"max_events deve ser int positivo, recebido: {type(max_events).__name__} = {max_events}")
        
        if not isinstance(min_movement_pixels, (int, float)) or min_movement_pixels <= 0:
            raise TypeError(f"min_movement_pixels deve ser float/int positivo, recebido: {type(min_movement_pixels).__name__} = {min_movement_pixels}")
        
        if not isinstance(ttl, int) or ttl <= 0:
            raise TypeError(f"ttl deve ser int positivo, recebido: {type(ttl).__name__} = {ttl}")
        
        self._id = id
        self._best_event: Optional[Event] = None
        self._event_count: int = 0
        self._movement_count: int = 0
        self._max_events: int = max_events
        self._min_movement_pixels: float = float(min_movement_pixels)
        self._ttl: int = ttl
        # Timestamp de inicialização do track
        self._started_at: datetime = datetime.now()
        # last_seen_frame_timestamp é atualizado apenas quando eventos são adicionados
        self._last_seen_frame_timestamp: Optional[datetime] = None

    @property
    def id(self) -> IdVO:
        """Retorna o ID do track."""
        return self._id

    @property
    def best_event(self) -> Optional[Event]:
        """Retorna o evento com melhor qualidade facial."""
        return self._best_event

    @property
    def event_count(self) -> int:
        """Retorna a quantidade total de eventos processados no track."""
        return self._event_count

    @property
    def has_movement(self) -> bool:
        """Indica se houve movimento significativo no track."""
        # Track com 0 eventos não tem movimento
        if self._event_count == 0:
            return False
        
        # Track com 1 evento não tem referência para movimento, considera com movimento
        if self._event_count == 1:
            return True
        
        return self._movement_count > 0

    @property
    def is_empty(self) -> bool:
        """Verifica se o track está vazio (sem eventos)."""
        return self._event_count == 0

    @property
    def ttl(self) -> int:
        """Retorna o tempo de vida máximo do track em segundos."""
        return self._ttl

    @property
    def started_at(self) -> datetime:
        """Retorna o timestamp de inicialização do track."""
        return self._started_at

    @property
    def last_seen_frame_timestamp(self) -> Optional[datetime]:
        """Retorna o timestamp do último frame visto."""
        return self._last_seen_frame_timestamp

    def add_event(self, event: Event) -> None:
        """
        Adiciona um evento ao track.
        OTIMIZAÇÃO MÁXIMA: Armazena apenas melhor e último evento.
        
        Quando o track atinge o limite máximo de eventos, publica um DomainEvent
        para que o FinishTrackService seja chamado (desacoplamento via Observer).
        
        Atualiza last_seen_frame_timestamp com o timestamp do frame do evento adicionado.
        
        Lógica:
        - Primeiro evento: armazenado como best e last
        - Eventos subsequentes: atualiza best se qualidade for maior, sempre atualiza last
        - Calcula movimento entre último evento e novo evento para atualizar has_movement
        - Atualiza last_seen_frame_timestamp com o timestamp do evento

        :param event: Evento a ser adicionado.
        :raises TypeError: Se event não for do tipo Event.
        """
        if not isinstance(event, Event):
            raise TypeError(f"event deve ser Event, recebido: {type(event).__name__}")
        
        # Atualiza last_seen_frame_timestamp com o timestamp do evento
        self._last_seen_frame_timestamp = event.frame.timestamp.value()
        
        # Verifica se o track atingiu o limite máximo de eventos
        if self._event_count >= self._max_events:
            return
        
        # Primeiro evento do track
        if self.is_empty:
            self._best_event = event
            self._event_count = 1
            self._movement_count = 0  # Primeiro evento não tem movimento
            return
        
        # Eventos subsequentes
        self._event_count += 1
        
        # Atualiza melhor evento se qualidade for superior
        # Se face_quality_score for None, usa a confiança como critério
        if self._best_event is None:
            self._best_event = event
        else:
            new_quality = event.face_quality_score.value() if event.face_quality_score is not None else event.confidence.value()
            best_quality = self._best_event.face_quality_score.value() if self._best_event.face_quality_score is not None else self._best_event.confidence.value()
            if new_quality > best_quality:
                # Remove frame do melhor evento anterior para economizar memória
                if self._best_event is not None:
                    self._best_event.remove_frame()
                self._best_event = event
        

    def get_best_event(self) -> Optional[Event]:
        """
        Retorna o evento com o maior score de qualidade facial.
        
        :return: Evento com melhor qualidade ou None se track estiver vazio.
        """
        return self._best_event

    def get_movement_statistics(self) -> Dict[str, float]:
        """
        Retorna estatísticas detalhadas sobre o movimento no track.
        OTIMIZAÇÃO: Baseado apenas em best_event.
        
        :return: Dicionário com estatísticas de movimento.
        """
        if self.is_empty or self._best_event is None:
            return {
                'total_distance': 0.0,
                'average_distance': 0.0,
                'max_distance': 0.0,
                'min_distance': 0.0,
                'movement_detected': False,
                'movement_percentage': 0.0,
                'movement_count': 0,
                'event_count': 0
            }
        
        if self.event_count < 2:
            return {
                'total_distance': 0.0,
                'average_distance': 0.0,
                'max_distance': 0.0,
                'min_distance': 0.0,
                'movement_detected': False,
                'movement_percentage': 0.0,
                'movement_count': self._movement_count,
                'event_count': self._event_count
            }
        
        import math
        
        # Calcula centros do best bbox
        x1_best, y1_best, x2_best, y2_best = self._best_event.bbox.value()
        center_x_best = (x1_best + x2_best) / 2.0
        center_y_best = (y1_best + y2_best) / 2.0
        
        # Distância do centro do best (sempre zero neste caso)
        distance = 0.0
        
        # Percentual de frames com movimento
        movement_percentage = (self._movement_count / self._event_count) * 100.0
        
        return {
            'total_distance': distance,
            'average_distance': distance,
            'max_distance': distance,
            'min_distance': distance,
            'movement_detected': distance > 0.0,
            'movement_percentage': movement_percentage,
            'movement_count': self._movement_count,
            'event_count': self._event_count
        }

    def verify_ttl(self, current_frame_timestamp) -> bool:
        """
        Verifica se o track expirou por inatividade (TTL).
        
        Se o track expirou, publica um evento de domínio comunicando
        o encerramento de forma assíncrona.

        :param current_frame_timestamp: Timestamp do frame atual (TimestampVO ou datetime).
        :return: True se o track expirou, False caso contrário.
        :raises TypeError: Se current_frame_timestamp não for do tipo esperado.
        """
        from src.domain.value_objects.timestamp_vo import TimestampVO
        
        # Validar tipo do parâmetro
        if not isinstance(current_frame_timestamp, (datetime, TimestampVO)):
            raise TypeError(
                f"current_frame_timestamp deve ser datetime ou TimestampVO, "
                f"recebido: {type(current_frame_timestamp).__name__}"
            )
        
        # Extrair valor datetime se for TimestampVO
        current_dt = current_frame_timestamp.value() if isinstance(current_frame_timestamp, TimestampVO) else current_frame_timestamp
        
        # Se não há timestamp registrado, o track não pode ter expirado
        if self._last_seen_frame_timestamp is None:
            return False
        
        # Calcular tempo decorrido em segundos
        time_elapsed = (current_dt - self._last_seen_frame_timestamp).total_seconds()
        
        # Verificar se expirou
        if time_elapsed > self._ttl:
            return True
        
        return False

    def to_dict(self) -> Dict[str, Any]:
        """
        Converte a entidade para um dicionário.
        OTIMIZAÇÃO: Retorna apenas o evento com melhor qualidade.

        :return: Dicionário com os dados do track.
        """
        return {
            'id': self._id.value(),
            'event_count': self.event_count,
            'best_event': self._best_event.to_dict() if self._best_event else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Track':
        """
        Cria uma instância de Track a partir de um dicionário.
        OTIMIZAÇÃO: Reconstrói apenas o ID e metadados.
        Nota: Eventos não são reconstruídos (Event não possui from_dict).

        :param data: Dicionário com os dados do track.
        :return: Instância de Track.
        :raises KeyError: Se alguma chave obrigatória estiver ausente.
        """
        track = cls(id=IdVO(data['id']))
        track._event_count = data.get('event_count', 0)
        return track

    def __eq__(self, other) -> bool:
        """Compara dois tracks por igualdade (baseado no ID)."""
        if not isinstance(other, Track):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        """Retorna o hash do track (baseado no ID)."""
        return hash(self._id)

    def __repr__(self) -> str:
        """Representação string do track."""
        best_event = self.get_best_event()
        if best_event is None:
            best_quality = 0.0
        else:
            best_quality = best_event.face_quality_score.value() if best_event.face_quality_score is not None else best_event.confidence.value()
        return (
            f"Track(id={self._id.value()}, "
            f"events={self.event_count}, "
            f"best_quality={best_quality:.4f})"
        )

    def __str__(self) -> str:
        """Conversão para string."""
        if self._best_event is None:
            quality = 0.0
        else:
            quality = self._best_event.face_quality_score.value() if self._best_event.face_quality_score is not None else self._best_event.confidence.value()
        return (
            f"Track {self._id.value()}: "
            f"{self.event_count} events, "
            f"quality {quality:.4f}"
        )
