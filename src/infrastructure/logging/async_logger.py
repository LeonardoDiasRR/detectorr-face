"""
AsyncFileLogger - Implementação assíncrona da porta Logger.
Coloca mensagens em fila sem bloquear a aplicação.
"""

import queue
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from src.application.ports.logger_port import Logger
from src.infrastructure.logging.file_log_writer import LogFileWriter
from src.infrastructure.messaging.log_queue_consumer import LogQueueConsumer


class AsyncFileLogger:
    """
    Implementação assíncrona de Logger que usa fila e thread.
    
    Não bloqueia a aplicação - coloca mensagens em fila para processamento.
    """
    
    def __init__(
        self,
        log_file: Path,
        log_level: int = logging.INFO,
        queue_size: int = 10000,
        max_bytes: int = 2 * 1024 * 1024,
        backup_count: int = 2
    ):
        """
        Inicializar logger assíncrono.
        
        Args:
            log_file: Caminho do arquivo de log
            log_level: Nível de logging
            queue_size: Capacidade máxima da fila
            max_bytes: Tamanho máximo de arquivo antes de rotacionar
            backup_count: Número de backups a manter
        """
        self.log_file = log_file
        self.log_level = log_level
        self.queue_size = queue_size
        
        # Criar fila thread-safe
        self.log_queue: queue.Queue = queue.Queue(maxsize=queue_size)
        
        # Criar escritor de arquivo
        self.writer = LogFileWriter(
            filepath=log_file,
            max_bytes=max_bytes,
            backup_count=backup_count
        )
        
        # Criar e iniciar consumer thread
        self.consumer = LogQueueConsumer(self.log_queue, self.writer)
        self.consumer.start()
        
        # Configurar logger padrão Python
        self._setup_python_logger()
    
    def _setup_python_logger(self) -> None:
        """Configurar logger padrão Python como fallback."""
        self.python_logger = logging.getLogger('app')
        self.python_logger.setLevel(self.log_level)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # Adicionar só se não tiver handlers
        if not self.python_logger.handlers:
            self.python_logger.addHandler(console_handler)
    
    def _enqueue_message(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Enfileirar mensagem para processamento assíncrono.
        
        Args:
            level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Mensagem a registrar
            extra: Dados adicionais
        """
        # Formatar mensagem
        formatted = f"{level} - {message}"
        if extra:
            formatted += f" - {extra}"
        
        # Tentar enfileirar (não bloqueia)
        try:
            self.log_queue.put_nowait(formatted)
        except queue.Full:
            # Se fila cheia, não bloqueia - apenas descarta
            # (pode ser configurado para enviar para console)
            pass
        
        # Também logar no Python logger (para console)
        log_method = getattr(self.python_logger, level.lower())
        log_method(message, extra={'extra_data': extra} if extra else {})
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Registrar DEBUG."""
        self._enqueue_message("DEBUG", message, extra)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Registrar INFO."""
        self._enqueue_message("INFO", message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Registrar WARNING."""
        self._enqueue_message("WARNING", message, extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Registrar ERROR."""
        self._enqueue_message("ERROR", message, extra)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Registrar CRITICAL."""
        self._enqueue_message("CRITICAL", message, extra)
    
    def get_queue_size(self) -> int:
        """Obter tamanho atual da fila."""
        return self.log_queue.qsize()
    
    def is_running(self) -> bool:
        """Verificar se consumer está rodando."""
        return self.consumer.is_running()
    
    def shutdown(self) -> None:
        """
        Desligar logger graciosamente.
        Drena fila antes de fechar.
        """
        if self.consumer.is_alive():
            self.consumer.stop()
            self.consumer.join(timeout=5)
