"""
Caso de uso para processamento de streaming de câmera com YOLO tracking.
Application Layer - especializado em leitura e processamento de vídeo.

Responsabilidades integradas (Refatorado):
- Carregar modelos YOLO (track e face) por câmera
- Executar YOLO tracking na stream RTSP
- Processar frames e gerar detecções
- Detectar faces em crop de detecção usando modelo específico
- Criar eventos a partir das detecções com face
- Criar tracks e adicionar eventos aos tracks
- Atualizar InMemoryTrackRegistry com novos tracks/eventos
"""

import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
import numpy as np
from ultralytics import YOLO
from src.domain.entities import Frame, Camera, Event, Track
from src.domain.value_objects import IdVO, NameVO, CameraTokenVO, TimestampVO, FullFrameVO, BboxVO, FaceLandmarksVO, ConfidenceVO
from src.domain.services import FrontalFaceScoreService
from src.infrastructure.tracking.in_memory_track_registry import InMemoryTrackRegistry
from src.infrastructure.config.config_loader import ConfigLoader


class ProcessCameraStreamingUseCase:
    """
    Caso de uso para processar streaming de vídeo de uma câmera.
    
    Responsabilidades integradas:
    - Carregar CÓPIA dos modelos YOLO (track e face) para esta câmera
    - Executar YOLO tracking na stream RTSP
    - Processar frames extraindo detecções
    - Detectar faces nos crops usando modelo específico
    - Criar eventos para detecções com face
    - Gerenciar tracks (criar/atualizar) via InMemoryTrackRegistry
    
    Executado em thread independente pelo MonitorCamerasUseCase.
    Cada câmera tem sua própria cópia dos modelos carregados.
    Pipeline completo sem filas: Frame → Event → Track (síncrono).
    """

    def __init__(self, skip_frames: int = 0) -> None:
        """
        Inicializa o caso de uso de processamento de streaming.
        
        :param skip_frames: Número de frames a pular entre processamentos (0 = processa todos).
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.track_model: YOLO = None  # Modelo TRACK específico desta câmera
        self.face_model: YOLO = None   # Modelo FACE específico desta câmera
        self.camera_id: Optional[int] = None  # ID da câmera que este caso de uso processa
        self._skip_frames = skip_frames
        self._frame_counter = 0
        
        # Referências para processamento de pipeline
        self._track_registry: Optional[InMemoryTrackRegistry] = None
        self._face_config: Optional[Dict[str, Any]] = None
        self._config = ConfigLoader().load()

        # Controle de execução para parada graciosa
        self._running = True

    def stop(self):
        """
        Sinaliza para o loop de streaming encerrar de forma graciosa.
        """
        self._running = False
        
        # Compatibilidade com versão anterior (deprecada)
        self.frame_queue = None

    def set_track_registry(self, track_registry: InMemoryTrackRegistry) -> None:
        """
        Define o registro de tracks para este caso de uso.
        Necessário para integração com InMemoryTrackRegistry.
        
        :param track_registry: Instância do InMemoryTrackRegistry.
        """
        self._track_registry = track_registry

    def execute(self, camera: Camera, yolo_config: Dict[str, Any], face_config: Dict[str, Any] = None) -> None:
        """
        Executa o processamento de streaming para uma câmera com pipeline integrado.
        
        Pipeline: Frame → Event → Track (Síncrono)
        
        Cada câmera que ativa terá suas próprias cópias dos modelos carregados
        na memória do device configurado. Toda detecção passa por:
        1. Extração de frame via YOLO track
        2. Criação de detecções (bboxes, landmarks)
        3. Detecção de faces usando modelo específico da câmera
        4. Criação de eventos para detecções com face
        5. Gerenciamento de tracks no InMemoryTrackRegistry
        
        :param camera: Entidade Camera com dados da câmera.
        :param yolo_config: Configuração do modelo YOLO (track_model).
        :param face_config: Configuração do modelo de face (face_model).
        """
        camera_id = camera.camera_id.value()
        camera_name = camera.camera_name.value()
        rtsp_url = camera.source.value()
        camera_token = camera.camera_token.value()
        
        self.camera_id = camera_id
        self._face_config = face_config

        try:
            # Carregar modelo TRACK - cópia dedicada para esta câmera
            if self.track_model is None:
                self.logger.info(f"[Camera {camera_id}] Carregando cópia do modelo TRACK...")
                try:
                    self.track_model = YOLO(yolo_config['backend'])
                    self.logger.info(f"[Camera {camera_id}] Modelo TRACK carregado com sucesso")
                except Exception as e:
                    self.logger.error(f"[Camera {camera_id}] Erro ao carregar modelo TRACK: {e}", exc_info=True)
                    return
            
            # Carregar modelo FACE - cópia dedicada para esta câmera
            if face_config and self.face_model is None:
                self.logger.info(f"[Camera {camera_id}] Carregando cópia do modelo FACE...")
                try:
                    self.face_model = YOLO(face_config['backend'])
                    self.logger.info(f"[Camera {camera_id}] Modelo FACE carregado com sucesso")
                except Exception as e:
                    self.logger.error(f"[Camera {camera_id}] Erro ao carregar modelo FACE: {e}", exc_info=True)
                    self.face_model = None  # Resetar se erro

            # Extrair e normalizar parâmetros para model.track()
            track_args = yolo_config.get('params', {}).copy()
            track_args['source'] = rtsp_url

            # Executar YOLO tracking no fluxo RTSP com o modelo dedicado desta câmera
            capture_started = False
            for frame_results in self.track_model.track(**track_args):
                if not self._running:
                    self.logger.info(f"[Camera {camera_id}] Parada graciosa do streaming solicitada.")
                    break
                # Log de confirmação na primeira iteração
                if not capture_started:
                    capture_started = True
                    self.logger.info(f"[Camera {camera_id}] Streaming iniciado com sucesso")
                # Processar pipeline completo: Frame → Event → Track
                self._process_frame_pipeline(camera_id, camera_name, camera_token, frame_results)

        except Exception as e:
            self.logger.error(f"[Camera {camera_id}] Erro ao processar streaming: {e}", exc_info=True)
        finally:
            # Limpar modelos ao finalizar
            self._cleanup_models(camera_id)

    def _to_numpy(self, tensor_or_array):
        """
        Converte um tensor PyTorch (possivelmente em CUDA) para numpy array.
        
        Lida com:
        - Tensores em CUDA: move para CPU antes de converter
        - Tensores em CPU: converte diretamente
        - Arrays numpy: retorna como está
        
        :param tensor_or_array: Tensor PyTorch ou array numpy.
        :return: Array numpy.
        """
        # Se for tensor CUDA/CPU, converter para numpy
        if hasattr(tensor_or_array, 'cpu'):
            # É um tensor PyTorch
            tensor = tensor_or_array.cpu() if tensor_or_array.is_cuda else tensor_or_array
            return tensor.numpy() if hasattr(tensor, 'numpy') else tensor
        elif hasattr(tensor_or_array, 'numpy'):
            # É um tensor que tem método numpy (PyTorch CPU)
            return tensor_or_array.numpy()
        else:
            # Já é numpy array ou escalar
            return tensor_or_array

    def _cleanup_models(self, camera_id: int) -> None:
        """
        Libera os modelos carregados para esta câmera.
        Cada câmera tem suas próprias cópias e devem ser liberadas
        quando a câmera desativa.
        
        :param camera_id: ID da câmera.
        """
        try:
            if self.track_model is not None:
                self.logger.info(f"[Camera {camera_id}] Liberando modelo TRACK da memória")
                del self.track_model
                self.track_model = None
            
            if self.face_model is not None:
                self.logger.info(f"[Camera {camera_id}] Liberando modelo FACE da memória")
                del self.face_model
                self.face_model = None
        except Exception as e:
            self.logger.warning(f"[Camera {camera_id}] Erro ao liberar modelos: {e}")

    def _normalize_landmarks(self, landmarks_data):
        """
        Normaliza dados de landmarks para o formato esperado (x, y, confidence).
        Se landmarks tiver apenas 2 elementos (x, y), adiciona confidence padrão de 1.0.
        
        :param landmarks_data: Array ou lista com landmarks.
        :return: Lista de landmarks no formato [(x, y, confidence), ...] ou None.
        """
        if landmarks_data is None:
            return None
        
        try:
            # Converter para lista se for ndarray
            if hasattr(landmarks_data, 'tolist'):
                landmarks_list = landmarks_data.tolist()
            else:
                landmarks_list = list(landmarks_data)
            
            # Normalizar cada landmark
            normalized = []
            for landmark in landmarks_list:
                if len(landmark) == 2:
                    # Adicionar confidence padrão de 1.0
                    normalized.append((float(landmark[0]), float(landmark[1]), 1.0))
                elif len(landmark) == 3:
                    # Já tem confidence
                    normalized.append((float(landmark[0]), float(landmark[1]), float(landmark[2])))
                else:
                    # Formato inválido, retornar None
                    return None
            
            return normalized
        except Exception:
            return None

    def _to_numpy(self, tensor_or_array):
        """
        Converte um tensor PyTorch (possivelmente em CUDA) para numpy array.
        
        Lida com:
        - Tensores em CUDA: move para CPU antes de converter
        - Tensores em CPU: converte diretamente
        - Arrays numpy: retorna como está
        
        :param tensor_or_array: Tensor PyTorch ou array numpy.
        :return: Array numpy.
        """
        # Se for tensor CUDA/CPU, converter para numpy
        if hasattr(tensor_or_array, 'cpu'):
            # É um tensor PyTorch
            tensor = tensor_or_array.cpu() if tensor_or_array.is_cuda else tensor_or_array
            return tensor.numpy() if hasattr(tensor, 'numpy') else tensor
        elif hasattr(tensor_or_array, 'numpy'):
            # É um tensor que tem método numpy (PyTorch CPU)
            return tensor_or_array.numpy()
        else:
            # Já é numpy array ou escalar
            return tensor_or_array

    def _extract_detection_data(self, detection, detection_idx: int, frame_results_keypoints, frame_height: int, frame_width: int) -> Optional[Tuple]:
        """
        Extrai dados de uma detecção YOLO.
        
        Trata tensores em CUDA movendo-os para CPU antes da conversão para numpy.
        
        :param detection: Objeto de detecção YOLO (box resultado de model.track()).
        :param detection_idx: Índice da detecção no frame.
        :param frame_results_keypoints: Objeto de keypoints do Results (contém landmarks de todas as detecções).
        :param frame_height: Altura do frame.
        :param frame_width: Largura do frame.
        :return: Tupla (bbox, confidence, landmarks_data, track_id) ou None em caso de erro.
        """
        try:
            # Extrair bounding box (x1, y1, x2, y2) com suporte a CUDA
            if hasattr(detection, 'xyxy') and detection.xyxy is not None:
                bbox_tensor = detection.xyxy[0] if len(detection.xyxy.shape) > 1 else detection.xyxy
                bbox_array = self._to_numpy(bbox_tensor)
                x1, y1, x2, y2 = bbox_array[:4].astype(np.float32)
            else:
                return None
            
            # Extrair confiança com suporte a CUDA
            if hasattr(detection, 'conf') and detection.conf is not None:
                conf_tensor = detection.conf[0] if len(detection.conf.shape) > 0 else detection.conf
                confidence_value = float(self._to_numpy(conf_tensor))
            else:
                confidence_value = 0.0
            
            # Extrair landmarks do objeto frame_results.keypoints pelo índice
            landmarks_data = None
            if frame_results_keypoints is not None and hasattr(frame_results_keypoints, 'xy') and frame_results_keypoints.xy is not None:
                try:
                    kpts_tensor = frame_results_keypoints.xy[detection_idx] if detection_idx < len(frame_results_keypoints.xy) else None
                    if kpts_tensor is not None:
                        landmarks_data = self._to_numpy(kpts_tensor).astype(np.float32)
                except Exception as e:
                    pass
            else:
                pass
            
            # Extrair track_id se disponível (com suporte a CUDA)
            track_id = None
            if hasattr(detection, 'id') and detection.id is not None:
                track_id_tensor = detection.id[0] if len(detection.id.shape) > 0 else detection.id
                track_id = int(self._to_numpy(track_id_tensor))
            
            # Validar coordenadas
            if not (0 <= x1 < x2 <= frame_width and 0 <= y1 < y2 <= frame_height):
                return None
            
            return (x1, y1, x2, y2), confidence_value, landmarks_data, track_id
        
        except Exception as e:
            return None

    def _process_frame_pipeline(self, camera_id: int, camera_name: str, camera_token: str, 
                                 frame_results) -> None:
        """
        Processa pipeline completo: Frame → Event → Track (Síncrono)
        
        Responsabilidades:
        1. Extrair informações do frame
        2. Criar Frame com resultados
        3. Para cada detecção: Criar Event + Detectar Face
        4. Para cada Event com face: Criar/atualizar Track no registry
        
        :param camera_id: ID da câmera.
        :param camera_name: Nome da câmera.
        :param camera_token: Token da câmera.
        :param frame_results: Resultados do YOLO track para o frame.
        """
        # Incrementar contador e verificar se deve pular frame
        self._frame_counter += 1
        if self._skip_frames > 0 and self._frame_counter % (self._skip_frames + 1) != 0:
            return
        
        try:
            # ETAPA 1: Criar Frame a partir dos resultados do YOLO track
            frame = self._create_frame_from_results(camera_id, camera_name, camera_token, frame_results)
            
            if frame is None or not frame.bboxes:
                return
            
            # ETAPA 2: Para cada detecção, criar Event e detectar face
            # ETAPA 3: Para cada Event com face, gerenciar track
            self._process_detections_and_tracks(camera_id, frame)
            
        except Exception as e:
            self.logger.error(f"[Camera {camera_id}] Erro ao processar frame pipeline: {e}", exc_info=True)

    def _create_frame_from_results(self, camera_id: int, camera_name: str, camera_token: str,
                                   frame_results) -> Optional[Frame]:
        """
        Cria objeto Frame a partir dos resultados do YOLO track.
        
        Extrai bboxes, landmarks, track_ids, confidences e classes.
        
        :param camera_id: ID da câmera.
        :param camera_name: Nome da câmera.
        :param camera_token: Token da câmera.
        :param frame_results: Resultados do YOLO track.
        :return: Objeto Frame ou None se houver erro.
        """
        try:
            # Extrair full_frame da imagem original
            frame_image = frame_results.orig_img if hasattr(frame_results, 'orig_img') and frame_results.orig_img is not None else np.zeros((1, 1, 3), dtype=np.uint8)
            full_frame_vo = FullFrameVO(frame_image, copy=False)
            
            # Obter dimensões do frame
            frame_height, frame_width = frame_image.shape[:2]
            
            # Extrair keypoints do Results se disponíveis
            frame_keypoints = frame_results.keypoints if hasattr(frame_results, 'keypoints') else None
            
            # Extrair bboxes, landmarks, track_ids e confidences dos resultados
            bboxes = []
            landmarks_list = []
            track_ids = []
            confidences = []
            
            if frame_results.boxes and hasattr(frame_results.boxes, '__len__'):
                for detection_idx, box in enumerate(frame_results.boxes):
                    detection_data = self._extract_detection_data(box, detection_idx, frame_keypoints, frame_height, frame_width)
                    
                    if detection_data is None:
                        continue
                    
                    (x1, y1, x2, y2), confidence_value, landmarks_data, track_id = detection_data
                    
                    # Criar BboxVO
                    bbox = BboxVO((int(x1), int(y1), int(x2), int(y2)))
                    bboxes.append(bbox)
                    
                    # Criar FaceLandmarksVO - normalizar landmarks (adicionar confidence se necessário)
                    normalized_landmarks = self._normalize_landmarks(landmarks_data)
                    landmarks = FaceLandmarksVO(normalized_landmarks)
                    landmarks_list.append(landmarks)
                    
                    # Usar track_id extraído ou fallback para índice
                    if track_id is None:
                        track_id = detection_idx
                    track_ids.append(track_id)
                    
                    # Criar ConfidenceVO
                    confidence = ConfidenceVO(confidence_value)
                    confidences.append(confidence)
            
            # Extrair class IDs de frame_results.boxes.cls
            classes = []
            if frame_results.boxes and hasattr(frame_results.boxes, 'cls') and frame_results.boxes.cls is not None:
                cls_data = self._to_numpy(frame_results.boxes.cls)
                classes = [int(cls) for cls in cls_data]
            
            # Criar Frame com informações do frame e detecções decompostas
            frame = Frame(
                full_frame=full_frame_vo,
                camera_id=IdVO(camera_id),
                camera_name=NameVO(camera_name),
                camera_token=CameraTokenVO(camera_token),
                timestamp=TimestampVO(datetime.now()),
                bboxes=bboxes,
                landmarks=landmarks_list,
                track_ids=track_ids,
                confidences=confidences,
                classes=classes
            )
            
            return frame
            
        except Exception as e:
            self.logger.error(f"[Camera {camera_id}] Erro ao criar Frame: {e}", exc_info=True)
            return None

    def _process_detections_and_tracks(self, camera_id: int, frame: Frame) -> None:
        """
        Processa cada detecção do frame:
        1. Cria Event para cada detecção
        2. Detecta face usando modelo específico da câmera
        3. Para detecções com face, cria/atualiza track no registry
        
        :param camera_id: ID da câmera.
        :param frame: Frame contendo detecções.
        """
        try:
            for detection_idx, bbox in enumerate(frame.bboxes):
                try:
                    # Obter dados da detecção
                    track_id = frame.track_ids[detection_idx] if detection_idx < len(frame.track_ids) else detection_idx
                    
                    # Validar track_id (não pode ser 0)
                    if track_id == 0:
                        continue
                    
                    confidence = frame.confidences[detection_idx] if detection_idx < len(frame.confidences) else ConfidenceVO(0.0)
                    landmarks = frame.landmarks[detection_idx] if detection_idx < len(frame.landmarks) else FaceLandmarksVO(None)
                    
                    # Calcular score de frontalidade da face
                    frontal_score = 0.0
                    if landmarks is not None and landmarks.value() is not None:
                        frontal_score = FrontalFaceScoreService.calculate(landmarks)
                    
                    face_quality_score_vo = ConfidenceVO(frontal_score)
                    
                    # Extrair class_id
                    class_id = None
                    if detection_idx < len(frame.classes):
                        class_id = frame.classes[detection_idx]
                    
                    # Aplicar filtros de tamanho e confiança do bbox
                    x1, y1, x2, y2 = bbox.value()
                    bbox_area = (x2 - x1) * (y2 - y1)
                    confidence_value = confidence.value()
                    
                    min_box_area = self._config.filter.min_box_area
                    min_box_conf = self._config.filter.min_box_conf
                    
                    if bbox_area < min_box_area or confidence_value < min_box_conf:
                        continue
                    
                    # Criar Event
                    event = Event(
                        frame=frame,
                        bbox=bbox,
                        confidence=confidence,
                        landmarks=landmarks,
                        track_id=track_id,
                        face_quality_score=face_quality_score_vo,
                        class_id=class_id
                    )
                    
                    # Processar track
                    if self._track_registry is not None:
                        self._process_event_to_track(camera_id, event)
                    
                except Exception as detection_error:
                    self.logger.debug(f"[Camera {camera_id}] Erro ao processar detecção {detection_idx}: {detection_error}")
                    continue
        
        except Exception as e:
            self.logger.error(f"[Camera {camera_id}] Erro ao processar detecções: {e}", exc_info=True)

    def _process_event_to_track(self, camera_id: int, event: Event) -> None:
        """
        Processa um evento criando ou atualizando track no registry.
        
        Se track não existe:
        - Cria novo Track com o track_id do evento
        - Adiciona evento ao novo track
        - Registra no InMemoryTrackRegistry
        
        Se track existe:
        - Adiciona evento ao track existente
        
        :param camera_id: ID da câmera.
        :param event: Event a processar.
        """
        try:
            track_id = event.track_id
            
            # Validar track_id
            if track_id == 0 or track_id is None:
                return
            
            if self._track_registry is None:
                self.logger.warning(f"[Camera {camera_id}] Track registry não configurado")
                return
            
            # Verificar/criar/atualizar track
            track = self._track_registry.get(camera_id, track_id)
            
            if track is None:
                # Track não existe - criar novo
                track = Track(
                    id=IdVO(track_id),
                    min_movement_pixels=self._config.track.min_movement_pixels
                )
                
                # Adicionar primeiro evento ao track
                track.add_event(event)
                
                # Registrar novo track
                self._track_registry.register(camera_id, track_id, track)
                self.logger.debug(f"[Camera {camera_id}] Novo track criado: {track_id}")
            else:
                # Track existe - adicionar evento
                track.add_event(event)
                self.logger.debug(f"[Camera {camera_id}] Evento adicionado ao track: {track_id}")
        
        except Exception as e:
            self.logger.error(f"[Camera {camera_id}] Erro ao processar track: {e}", exc_info=True)

    def _process_frame(self, camera_id: int, camera_name: str, camera_token: str, 
                       frame_results) -> None:
        """
        Processa resultados de um frame do tracking.
        
        Responsabilidades:
        - Extrair informações do frame
        - Criar Frame com resultados
        - Enfileirar para processamento assíncrono em workers
        
        :param camera_id: ID da câmera.
        :param camera_name: Nome da câmera.
        :param camera_token: Token da câmera.
        :param frame_results: Resultados do YOLO track para o frame.
        """
        # Incrementar contador e verificar se deve pular frame
        self._frame_counter += 1
        if self._skip_frames > 0 and self._frame_counter % (self._skip_frames + 1) != 0:
            return
       
        # Se houver fila configurada, enfileirar frame para processamento
        if self.frame_queue is not None:
            try:
                # Extrair full_frame da imagem original
                frame_image = frame_results.orig_img if hasattr(frame_results, 'orig_img') and frame_results.orig_img is not None else np.zeros((1, 1, 3), dtype=np.uint8)
                full_frame_vo = FullFrameVO(frame_image, copy=False)
                
                # Obter dimensões do frame
                frame_height, frame_width = frame_image.shape[:2]
                
                # Extrair keypoints do Results se disponíveis
                frame_keypoints = frame_results.keypoints if hasattr(frame_results, 'keypoints') else None
                
                # Extrair bboxes, landmarks, track_ids e confidences dos resultados
                bboxes = []
                landmarks_list = []
                track_ids = []
                confidences = []
                
                if frame_results.boxes and hasattr(frame_results.boxes, '__len__'):
                    for detection_idx, box in enumerate(frame_results.boxes):
                        # Usar método helper que trata tensores CUDA
                        # Passar frame_keypoints e detection_idx para extrair landmarks corretamente
                        detection_data = self._extract_detection_data(box, detection_idx, frame_keypoints, frame_height, frame_width)
                        
                        if detection_data is None:
                            continue
                        
                        (x1, y1, x2, y2), confidence_value, landmarks_data, track_id = detection_data
                        
                        # Criar BboxVO
                        bbox = BboxVO((int(x1), int(y1), int(x2), int(y2)))
                        bboxes.append(bbox)
                        
                        # Criar FaceLandmarksVO - normalizar landmarks (adicionar confidence se necessário)
                        normalized_landmarks = self._normalize_landmarks(landmarks_data)
                        landmarks = FaceLandmarksVO(normalized_landmarks)
                        landmarks_list.append(landmarks)
                        
                        # Usar track_id extraído ou fallback para índice
                        if track_id is None:
                            track_id = detection_idx
                        track_ids.append(track_id)
                        
                        # Criar ConfidenceVO
                        confidence = ConfidenceVO(confidence_value)
                        confidences.append(confidence)
                
                # Extrair class IDs de frame_results.boxes.cls
                classes = []
                if frame_results.boxes and hasattr(frame_results.boxes, 'cls') and frame_results.boxes.cls is not None:
                    cls_data = self._to_numpy(frame_results.boxes.cls)
                    classes = [int(cls) for cls in cls_data]
                
                # Criar Frame com informações do frame e detecções decompostas
                frame = Frame(
                    full_frame=full_frame_vo,
                    camera_id=IdVO(camera_id),
                    camera_name=NameVO(camera_name),
                    camera_token=CameraTokenVO(camera_token),
                    timestamp=TimestampVO(datetime.now()),
                    bboxes=bboxes,
                    landmarks=landmarks_list,
                    track_ids=track_ids,
                    confidences=confidences,
                    classes=classes
                )
                
                # Enfileirar de forma não-bloqueante
                self.frame_queue.put_nowait(frame)
                self.logger.debug(
                )
                
            except Exception as e:
                pass
