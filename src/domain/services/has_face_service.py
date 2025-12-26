"""
Serviço de domínio para detecção de faces.
"""

import logging
from typing import Dict, Any
import numpy as np
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class HasFaceService:
    """
    Serviço de domínio responsável por detectar se uma imagem
    contém uma face usando o modelo YOLO face.
    
    Pode usar:
    - Um modelo específico de uma câmera (recomendado para inferências)
    - Modelos em cache por backend (fallback para compatibilidade)
    
    Cada câmera carrega sua própria cópia do modelo face para inferências.
    """

    _model_cache: Dict[str, YOLO] = {}

    @staticmethod
    def detect_face(image: np.ndarray, face_config: Dict[str, Any], 
                   camera_model: YOLO = None) -> bool:
        """
        Detecta se há uma face na imagem usando o modelo YOLO configurado.
        
        :param image: Imagem como np.array (deve estar no formato BGR ou RGB).
        :param face_config: Configuração face_model do arquivo YAML contendo:
                           - backend: caminho do modelo (ex: "models/yolo/yolov12n-face.pt")
                           - params: dicionário com parâmetros YOLO (conf, device, classes, etc.)
        :param camera_model: (Opcional) Modelo YOLO já carregado da câmera específica.
                            Se fornecido, usa este modelo. Caso contrário, usa cache.
        :return: True se uma ou mais faces foram detectadas, False caso contrário.
        """
        if image is None or image.size == 0:
            return False

        try:
            # Extrair backend e parâmetros
            backend = face_config.get('backend')
            params = face_config.get('params', {}).copy()

            if not backend:
                return False

            # Validar que o modelo não é None
            if camera_model is not None:
                # Usar modelo específico da câmera
                model = camera_model
            else:
                # Fallback: usar modelo em cache por backend
                model = HasFaceService._get_or_load_model(backend)
            
            # Verificar se modelo foi carregado corretamente
            if model is None:
                logger.error("Modelo YOLO é None")
                return False

            # Filtrar parâmetros válidos para predict()
            # Remover parâmetros que são para treinamento ou configuração interna
            valid_predict_params = {
                'conf': params.get('conf', 0.25),
                'iou': params.get('iou', 0.45),
                'imgsz': params.get('imgsz', 640),
                'half': params.get('half', False),
                'device': params.get('device', None),
                'classes': params.get('classes', None),
                'verbose': params.get('verbose', False),
                'stream': params.get('stream', False),
            }

            # Executar inferência na imagem
            results = model.predict(image, **valid_predict_params)

            # Verificar se houve detecções
            if results and len(results) > 0:
                result = results[0]
                # Verificar se boxes foram detectadas
                if hasattr(result, 'boxes') and result.boxes is not None and len(result.boxes) > 0:
                    return True
                else:
                    pass
                    # logger.warning("Nenhuma bbox válida detectada na imagem")
            else:
                pass
                # logger.warning("Nenhuma detecção realizada para a imagem")

            return False

        except Exception as e:
            logger.error(f"Erro ao detectar face: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def _get_or_load_model(backend: str) -> YOLO:
        """
        Obtém modelo do cache ou carrega um novo.
        
        :param backend: Caminho do arquivo do modelo YOLO.
        :return: Instância do modelo YOLO.
        """
        if backend not in HasFaceService._model_cache:
            HasFaceService._model_cache[backend] = YOLO(backend)
        return HasFaceService._model_cache[backend]

    @staticmethod
    def clear_cache() -> None:
        """
        Limpa o cache de modelos carregados.
        Útil para testes ou liberação de memória.
        """
        HasFaceService._model_cache.clear()
