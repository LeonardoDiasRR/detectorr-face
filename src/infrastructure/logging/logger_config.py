"""
Configuração centralizada de logging assíncrono.
Fornece logs em arquivo com rotação automática usando fila thread-safe.

Arquitetura:
- LoggerConfig: Gerenciador centralizado
- AsyncLogHandler: Handler customizado que enfileira mensagens
- LogConsumerThread: Thread que processa a fila e escreve no arquivo
"""

import logging
import logging.handlers
import queue
import threading
from pathlib import Path
from typing import Optional


class AsyncLogHandler(logging.Handler):
    """
    Handler assíncrono que coloca mensagens em uma fila.
    
    A fila é processada por uma thread consumidora separada
    que grava as mensagens no arquivo de log.
    """
    
    def __init__(self, log_queue: queue.Queue):
        """
        Inicializar handler assíncrono.
        
        :param log_queue: Fila thread-safe para mensagens de log
        """
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Enfileirar mensagem de log.
        
        :param record: Registro de log a enfileirar
        """
        try:
            # Formatar a mensagem
            msg = self.format(record)
            # Enfileirar sem bloquear
            self.log_queue.put_nowait(msg)
        except queue.Full:
            # Se a fila estiver cheia, descartar mensagem
            pass
        except Exception:
            # Erros no handler não devem quebrar a aplicação
            self.handleError(record)


class LogConsumerThread(threading.Thread):
    """
    Thread consumidora que processa a fila de logs.
    
    Lê mensagens da fila e escreve no arquivo de log com rotação.
    """
    
    def __init__(
        self,
        log_queue: queue.Queue,
        log_file: Path,
        max_bytes: int = 2 * 1024 * 1024,
        backup_count: int = 2
    ):
        """
        Inicializar thread consumidora de logs.
        
        :param log_queue: Fila de mensagens de log
        :param log_file: Caminho do arquivo de log
        :param max_bytes: Tamanho máximo antes de rotacionar
        :param backup_count: Número de backups a manter
        """
        super().__init__(daemon=True, name='LogConsumer')
        self.log_queue = log_queue
        self.log_file = log_file
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.stop_event = threading.Event()
        self.rotating_handler: Optional[logging.handlers.RotatingFileHandler] = None
        self._setup_file_handler()
    
    def _setup_file_handler(self) -> None:
        """Configurar handler de arquivo com rotação."""
        self.rotating_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
    
    def run(self) -> None:
        """Processar fila de logs continuamente."""
        while not self.stop_event.is_set():
            try:
                # Tentar pegar mensagem da fila (timeout para poder checar stop_event)
                msg = self.log_queue.get(timeout=0.5)
                
                # Escrever no arquivo
                if self.rotating_handler:
                    self.rotating_handler.stream.write(msg + '\n')
                    self.rotating_handler.stream.flush()
                    
                    # Verificar se precisa rotacionar
                    if (self.rotating_handler.stream.tell() >= self.max_bytes and
                            self.rotating_handler.stream):
                        self.rotating_handler.doRollover()
                
            except queue.Empty:
                # Timeout normal, continuar processando
                continue
            except Exception as e:
                # Log de erro (não pode enfileirar, usar stderr)
                import sys
                print(f"Erro ao processar log: {e}", file=sys.stderr)
    
    def stop(self) -> None:
        """Parar thread consumidora."""
        self.stop_event.set()
        
        # Processar mensagens restantes na fila
        while True:
            try:
                msg = self.log_queue.get_nowait()
                if self.rotating_handler:
                    self.rotating_handler.stream.write(msg + '\n')
                    self.rotating_handler.stream.flush()
            except queue.Empty:
                break
        
        # Fechar handler
        if self.rotating_handler:
            self.rotating_handler.close()


class LoggerConfig:
    """
    Gerenciador centralizado de logging assíncrono.
    
    Configura logs em arquivo com rotação automática usando fila:
    - Handler assíncrono enfileira mensagens
    - Thread consumidora processa a fila
    - Arquivo de log: detectorr.log (raiz do projeto)
    - Rotação: A cada 2MB
    - Backup: Até 2 arquivos anteriores
    """
    
    # Constantes de configuração padrão
    LOG_FILE = Path("detectorr.log")
    MAX_BYTES = 2 * 1024 * 1024  # 2MB
    BACKUP_COUNT = 2
    QUEUE_MAX_SIZE = 10000  # Máximo de mensagens na fila
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_LEVEL = logging.INFO
    
    _initialized = False
    _log_queue: Optional[queue.Queue] = None
    _consumer_thread: Optional[LogConsumerThread] = None
    
    @classmethod
    def configure(
        cls,
        log_level: int = logging.INFO,
        log_file: Optional[str] = None,
        log_format: Optional[str] = None,
        max_bytes: Optional[int] = None,
        backup_count: Optional[int] = None,
        queue_size: Optional[int] = None
    ) -> None:
        """
        Configurar logging centralizado assíncrono.
        
        :param log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        :param log_file: Caminho do arquivo de log (padrão: "detectorr.log")
        :param log_format: Formato das mensagens (padrão: '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        :param max_bytes: Tamanho máximo do arquivo antes de rotacionar em bytes (padrão: 2MB)
        :param backup_count: Número de arquivos antigos a manter (padrão: 2)
        :param queue_size: Tamanho máximo da fila de mensagens (padrão: 10000)
        """
        if cls._initialized:
            return
        
        # Usar valores passados ou padrões
        log_file_path = Path(log_file or cls.LOG_FILE)
        log_format_str = log_format or cls.LOG_FORMAT
        max_bytes_val = max_bytes if max_bytes is not None else cls.MAX_BYTES
        backup_count_val = backup_count if backup_count is not None else cls.BACKUP_COUNT
        queue_size_val = queue_size if queue_size is not None else cls.QUEUE_MAX_SIZE
        
        # Criar fila de logs com tamanho configurável
        cls._log_queue = queue.Queue(maxsize=queue_size_val)
        
        # Criar e iniciar thread consumidora
        cls._consumer_thread = LogConsumerThread(
            log_queue=cls._log_queue,
            log_file=log_file_path,
            max_bytes=max_bytes_val,
            backup_count=backup_count_val
        )
        cls._consumer_thread.start()
        
        # Criar formatador com formato configurável
        formatter = logging.Formatter(log_format_str)
        
        # Criar handler assíncrono
        async_handler = AsyncLogHandler(cls._log_queue)
        async_handler.setLevel(log_level)
        async_handler.setFormatter(formatter)
        
        # Configurar logger raiz
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(async_handler)
        
        # Também adicionar console handler para visualização em tempo real
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Obter logger para um módulo específico.
        
        :param name: Nome do logger (normalmente __name__)
        :return: Logger configurado
        """
        if not cls._initialized:
            cls.configure()
        
        return logging.getLogger(name)
    
    @classmethod
    def get_log_file_path(cls) -> Path:
        """
        Obter caminho completo do arquivo de log.
        
        :return: Path para o arquivo de log
        """
        return cls.LOG_FILE.resolve()
    
    @classmethod
    def get_queue_size(cls) -> int:
        """
        Obter número de mensagens na fila.
        
        :return: Tamanho atual da fila
        """
        if cls._log_queue:
            return cls._log_queue.qsize()
        return 0
    
    @classmethod
    def shutdown(cls) -> None:
        """
        Desligar gerenciador de logs.
        Deve ser chamado ao final da aplicação para descarregar fila.
        """
        if cls._consumer_thread:
            cls._consumer_thread.stop()
            # Aguardar thread terminar
            cls._consumer_thread.join(timeout=5.0)
            cls._consumer_thread = None
        
        cls._log_queue = None
        cls._initialized = False
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Verificar se logging está inicializado."""
        return cls._initialized


# Funções globais para conveniência
def get_logger(name: str) -> logging.Logger:
    """
    Obter logger configurado para um módulo.
    
    Exemplo:
        logger = get_logger(__name__)
        logger.info("Mensagem de teste")
    
    :param name: Nome do logger (normalmente __name__)
    :return: Logger configurado
    """
    return LoggerConfig.get_logger(name)


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    max_bytes: Optional[int] = None,
    backup_count: Optional[int] = None,
    queue_size: Optional[int] = None
) -> None:
    """
    Configurar logging centralizado assíncrono.
    
    Deve ser chamado uma vez no início da aplicação.
    
    :param log_level: Nível de log desejado (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    :param log_file: Caminho do arquivo de log (padrão: "detectorr.log")
    :param log_format: Formato das mensagens de log (padrão: '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    :param max_bytes: Tamanho máximo do arquivo em bytes antes de rotacionar (padrão: 2MB)
    :param backup_count: Número de arquivos de backup a manter (padrão: 2)
    :param queue_size: Tamanho máximo da fila de mensagens (padrão: 10000)
    """
    LoggerConfig.configure(
        log_level=log_level,
        log_file=log_file,
        log_format=log_format,
        max_bytes=max_bytes,
        backup_count=backup_count,
        queue_size=queue_size
    )


def shutdown_logging() -> None:
    """
    Desligar sistema de logging.
    
    Deve ser chamado ao final da aplicação.
    """
    LoggerConfig.shutdown()

