"""
Implementação do repositório de câmeras usando FindFace Multi API.
Infrastructure Layer - implementação concreta da interface do domínio.
"""

from typing import List, Union
import logging
from src.infrastructure.clients import FindfaceMulti, FindfaceAdapter
from src.domain.entities import Camera
from src.domain.repositories import CameraRepository
from src.domain.value_objects import IdVO, NameVO, CameraTokenVO, CameraSourceVO


class CameraRepositoryFindface(CameraRepository):
    """
    Implementação concreta do CameraRepository usando FindFace Multi API.
    """

    def __init__(
        self,
        findface_client: Union[FindfaceMulti, FindfaceAdapter],
        camera_prefix: str = 'TESTE'
    ):
        """
        Inicializa o repositório de câmeras do FindFace.

        :param findface_client: Instância do cliente FindfaceMulti ou seu adapter.
        :param camera_prefix: Prefixo para filtrar grupos de câmeras virtuais.
        """
        # Se recebeu FindfaceMulti direto, envolve em adapter
        if isinstance(findface_client, FindfaceMulti) and not isinstance(findface_client, FindfaceAdapter):
            findface_client = FindfaceAdapter(findface_client)
        
        # Validar que o cliente/adapter tem os métodos necessários
        if not hasattr(findface_client, 'camera_groups') or not hasattr(findface_client, 'cameras'):
            raise TypeError(
                "O parâmetro 'findface_client' deve ter as propriedades 'camera_groups' e 'cameras'."
            )
        
        self.findface = findface_client
        self.camera_prefix = camera_prefix
        self.logger = logging.getLogger(self.__class__.__name__)


    def get_cameras(self) -> List[Camera]:
        """
        Obtém todas as câmeras do FindFace (ativas e inativas).
        
        :return: Lista de entidades Camera.
        """
        cameras = []

        try:
            # Obtém grupos de câmeras
            grupos = self.findface.get_camera_groups()["results"]
            grupos_filtrados = [
                g for g in grupos 
                if g["name"].lower().startswith(self.camera_prefix.lower())
            ]

            # Para cada grupo, obtém câmeras
            for grupo in grupos_filtrados:
                cameras_response = self.findface.get_cameras(
                    camera_groups=[grupo["id"]],
                    external_detector=True,
                    ordering='id'
                )["results"]
                
                # Filtra câmeras com RTSP no comment
                cameras_filtradas = [
                    c for c in cameras_response 
                    if c.get("comment", "").startswith("rtsp://")
                ]
                
                # Converte para entidades Camera
                for camera_data in cameras_filtradas:
                    camera = Camera(
                        camera_id=IdVO(camera_data["id"]),
                        camera_name=NameVO(camera_data["name"]),
                        camera_token=CameraTokenVO(camera_data["external_detector_token"]),
                        source=CameraSourceVO(camera_data["comment"].strip()),
                        active=camera_data.get("active", True)
                    )
                    cameras.append(camera)

            return cameras

        except Exception as e:
            return []
