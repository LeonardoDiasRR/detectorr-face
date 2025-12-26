"""
Adaptador FindFace.
Encapsula a comunicação com a API FindFace Multi.
Traduz entre entidades de domínio e a API externa, protegendo o domínio
de mudanças na infraestrutura externa.
"""

import logging
import re
from typing import Optional, Dict, Callable, Any, TYPE_CHECKING

from src.domain.entities import Event
from src.infrastructure.config import get_settings

if TYPE_CHECKING:
    from src.infrastructure.clients.findface_multi import FindfaceMulti


class FindfaceAdapter:
    """
    Adaptador que encapsula a comunicação com a API FindFace Multi.
    
    Responsabilidades:
    - Traduzir entidades de domínio (Event) para formato esperado pela API
    - Gerenciar encoding JPEG com qualidade configurável
    - Tratar erros e extrair mensagens significativas
    - Proteger o domínio de mudanças na infraestrutura FindFace
    - Fornecer acesso a propriedades e métodos do cliente FindfaceMulti
    
    Segue padrões:
    - Adapter Pattern: Traduz entre Event de domínio e API externa
    - DDD: Não expõe detalhes de infraestrutura ao domínio
    """
    
    def __init__(self, findface_client):
        """
        Inicializa o adaptador FindFace.
        
        :param findface_client: Cliente FindfaceMulti já autenticado.
        :raises TypeError: Se findface_client não for FindfaceMulti.
        """
        # Validar tipo do cliente (import local para evitar circular import)
        from src.infrastructure.clients.findface_multi import FindfaceMulti
        if not isinstance(findface_client, FindfaceMulti):
            raise TypeError(f"findface_client deve ser instância de FindfaceMulti, recebido: {type(findface_client).__name__}")
        
        self._findface = findface_client
        self._logger = logging.getLogger(self.__class__.__name__)
        
        # Carregar qualidade JPEG da configuração
        settings = get_settings()
        self._jpeg_quality = settings.findface.jpeg_quality
    
    @property
    def camera_groups(self) -> Callable:
        """
        Propriedade que retorna o método get_camera_groups do cliente.
        
        :return: Método get_camera_groups do cliente
        """
        return self._findface.get_camera_groups
    
    @property
    def cameras(self) -> Callable:
        """
        Propriedade que retorna o método get_cameras do cliente.
        
        :return: Método get_cameras do cliente
        """
        return self._findface.get_cameras
    
    def __getattr__(self, name: str) -> Any:
        """
        Delegar qualquer outro atributo para o cliente original.
        
        :param name: Nome do atributo
        :return: Atributo do cliente original
        """
        return getattr(self._findface, name)
    
    def __repr__(self) -> str:
        """Representação em string do adapter."""
        return f"FindfaceAdapter({self._findface})"

    def send_event(self, event: Event, track_id: Optional[int] = None) -> tuple:
        """
        Envia um evento de face para o FindFace.
        Converte a entidade Event para o formato esperado pela API.
        
        Correlação de atributos:
        - Event.frame.full_frame → fullframe (JPEG)
        - Event.bbox → roi (ROI sem expansão)
        - Event.frame.timestamp → timestamp (ISO 8601)
        - Event.frame.camera_token → token
        - Event.frame.camera_id → camera
        - Event.face_quality_score → logging/tracking
        - Event.confidence → logging/tracking
        
        :param event: Event a ser enviado.
        :param track_id: ID do track (opcional, para logs de erro).
        :return: Tuple (sucesso: bool, resposta_ou_motivo: Dict ou str).
                 Em caso de sucesso: (True, resposta_dict)
                 Em caso de erro: (False, motivo_str)
        :raises TypeError: Se event não for Event.
        """
        if not isinstance(event, Event):
            raise TypeError(f"event deve ser Event, recebido: {type(event).__name__}")

        try:
            # OTIMIZAÇÃO CRÍTICA: Encoding JPEG executado no worker thread (não bloqueia detecção)
            # A qualidade é configurável via jpeg_quality do config.yaml (padrão 95)
            # Quality 75 é 1.54x mais rápido que 95 (~12ms vs ~18ms)
            # Quality 60 é ~2x mais rápido que 95 (~9ms vs ~18ms)
            # Como está no worker thread, não afeta o throughput de detecção
            imagem_bytes = event.frame.full_frame.jpg(quality=self._jpeg_quality)
            
            # Expande bbox em 20% mantendo o centro
            x1, y1, x2, y2 = event.bbox.value()
            width = x2 - x1
            height = y2 - y1
            expand_w = width * 0.2 / 2
            expand_h = height * 0.2 / 2
            new_x1 = max(0, x1 - expand_w)
            new_y1 = max(0, y1 - expand_h)
            new_x2 = x2 + expand_w
            new_y2 = y2 + expand_h
            roi = [int(new_x1), int(new_y1), int(new_x2), int(new_y2)]
            
            # Converte timestamp para formato ISO 8601 com timezone local
            timestamp_iso = event.frame.timestamp.value().astimezone().isoformat()
            
            # Envia para FindFace
            resposta = self._findface.add_face_event(
                token=event.frame.camera_token.value(),
                fullframe=imagem_bytes,
                camera=event.frame.camera_id.value(),
                roi=roi,
                mf_selector="all",
                timestamp=timestamp_iso
            )
            
            return (True, resposta)

        except Exception as e:
            # Extrai a linha 'desc: ...' do texto da exceção usando regex.
            # Exemplo alvo no texto:
            # "\ndesc: Zero objects(type=\"face\") detected on the provided image, param: fullframe\n"
            desc = None
            try:
                # Obtém texto de resposta se disponível (requests.Response)
                text = ""
                resp = getattr(e, "response", None)
                if resp is not None:
                    try:
                        text = getattr(resp, 'text', '') or ''
                    except Exception:
                        text = ''

                # Se não houver .response text, usa representação da exceção
                if not text:
                    text = str(e)

                # Regex procura 'desc:' até ', param:' ou fim/newline
                m = re.search(r"desc:\s*(?P<desc>.+?)(?:,\s*param:|\\n|$)", text, flags=re.IGNORECASE)
                if m:
                    desc = m.group('desc').strip()
            except Exception:
                desc = None

            # Usa track_id fornecido ou event.track_id como fallback
            track_display = track_id if track_id is not None else event.track_id
            
            motivo = desc if desc else str(e)
            return (False, motivo)
