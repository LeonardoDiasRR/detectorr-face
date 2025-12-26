"""
Carregador de configurações.
Responsável por ler arquivos YAML e variáveis de ambiente, 
convertendo-os em objetos de configuração type-safe.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

import yaml
from dotenv import load_dotenv

from .settings import ApplicationSettings, TrackModelConfig, FaceModelConfig, FaceModelParams, PerformanceConfig, FindfaceConfig, LoggingConfig, TrackConfig, QueuesConfig, FilterConfig


class ConfigLoader:
    """
    Carregador de configurações centralizado.
    
    Lê e valida configurações de:
    - Arquivo YAML (config.yaml)
    - Variáveis de ambiente (.env)
    
    Fornece configurações type-safe através de dataclasses.
    """
    
    DEFAULT_CONFIG_PATH = Path('config.yaml')
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Inicializar carregador de configurações.
        
        :param config_path: Caminho para arquivo de configuração YAML.
                           Se não fornecido, usa 'config.yaml' no diretório atual.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config_cache: Optional[ApplicationSettings] = None
    
    def load(self, force_reload: bool = False) -> ApplicationSettings:
        """
        Carregar e validar configurações.
        
        :param force_reload: Se True, recarrega as configurações mesmo se em cache.
        :return: Objeto ApplicationSettings com as configurações type-safe.
        :raises FileNotFoundError: Se arquivo de configuração não for encontrado.
        :raises yaml.YAMLError: Se arquivo YAML for inválido.
        :raises ValueError: Se configurações obrigatórias estiverem faltando.
        """
        # Retornar do cache se disponível
        if self._config_cache is not None and not force_reload:
            return self._config_cache
        
        # Carregar variáveis de ambiente
        load_dotenv()
        
        # Ler arquivo YAML
        config_dict = self._read_yaml()
        
        # Extrair configurações do modelo de rastreamento
        track_model_dict = config_dict.get('track_model', {})
        if not track_model_dict:
            raise ValueError('Chave "track_model" não encontrada em config.yaml')
        
        track_model = TrackModelConfig.from_dict(track_model_dict)
        
        # Extrair configurações do modelo de detecção facial (opcional)
        face_model_dict = config_dict.get('face_model', {})
        face_model = FaceModelConfig.from_dict(face_model_dict) if face_model_dict else FaceModelConfig(
            backend='models/yolo/yolov12n-face.pt',
            params=FaceModelParams()
        )
        
        # Extrair configurações do FindFace a partir de variáveis de ambiente + config.yaml
        findface_dict = config_dict.get('findface', {})
        try:
            findface = FindfaceConfig.from_dict(findface_dict)
        except ValueError as e:
            raise ValueError(f'Erro ao carregar configurações FindFace: {e}')
        
        # Extrair configurações de logging
        logging_dict = config_dict.get('logging', {})
        logging_config = LoggingConfig.from_dict(logging_dict) if logging_dict else LoggingConfig()
        
        # Extrair configurações de track
        track_dict = config_dict.get('track', {})
        track_config = TrackConfig.from_dict(track_dict) if track_dict else TrackConfig()

        # Extrair configurações de filtro
        filter_dict = config_dict.get('filter', {})
        filter_config = FilterConfig.from_dict(filter_dict) if filter_dict else FilterConfig()
        
        # Extrair configurações de filas
        queues_dict = config_dict.get('queues', {})
        queues_config = QueuesConfig.from_dict(queues_dict) if queues_dict else QueuesConfig()
        
        # Extrair configurações de performance
        performance_dict = config_dict.get('performance', {})
        performance_config = PerformanceConfig.from_dict(performance_dict) if performance_dict else PerformanceConfig()
        
        # Criar objeto de configurações
        settings = ApplicationSettings(
            track_model=track_model,
            findface=findface,
            logging=logging_config,
            track=track_config,
            queues=queues_config,
            filter=filter_config,
            face_model=face_model,
            performance=performance_config,
        )
        
        # Cachear configurações
        self._config_cache = settings
        
        return settings
    
    def _read_yaml(self) -> Dict[str, Any]:
        """
        Ler arquivo YAML de configuração.
        
        :return: Dicionário com conteúdo do YAML.
        :raises FileNotFoundError: Se arquivo não existir.
        :raises yaml.YAMLError: Se YAML for inválido.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f'Arquivo de configuração não encontrado: {self.config_path.absolute()}'
            )
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if config is None:
                raise ValueError('Arquivo YAML está vazio')
            
            return config
        except yaml.YAMLError as e:
            raise yaml.YAMLError(
                f'Erro ao ler arquivo YAML {self.config_path}: {e}'
            )
    
    def reload(self) -> ApplicationSettings:
        """
        Recarregar configurações do disco.
        
        :return: Objeto ApplicationSettings atualizado.
        """
        return self.load(force_reload=True)


# Singleton global
_global_loader: Optional[ConfigLoader] = None
_global_settings: Optional[ApplicationSettings] = None


def get_settings(config_path: Optional[Path] = None) -> ApplicationSettings:
    """
    Obter configurações da aplicação (singleton).
    
    Carrega as configurações uma única vez e retorna do cache em chamadas subsequentes.
    
    :param config_path: Caminho para arquivo de configuração (usado na primeira chamada).
    :return: Objeto ApplicationSettings com configurações type-safe.
    """
    global _global_loader, _global_settings
    
    if _global_settings is None:
        _global_loader = ConfigLoader(config_path)
        _global_settings = _global_loader.load()
    
    return _global_settings


def reload_settings(config_path: Optional[Path] = None) -> ApplicationSettings:
    """
    Recarregar configurações (útil para testes).
    
    :param config_path: Caminho para arquivo de configuração.
    :return: Objeto ApplicationSettings recarregado.
    """
    global _global_loader, _global_settings
    
    _global_loader = ConfigLoader(config_path)
    _global_settings = _global_loader.load()
    
    return _global_settings
