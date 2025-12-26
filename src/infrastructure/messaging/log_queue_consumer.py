"""
LogQueueConsumer - Thread daemon que consome mensagens da fila e escreve em arquivo.
"""

import queue
import threading
from typing import Optional
from src.infrastructure.logging.file_log_writer import LogFileWriter


class LogQueueConsumer(threading.Thread):
    """
    Daemon thread que consome mensagens de log da fila e escreve em arquivo.
    """
    
    def __init__(
        self,
        log_queue: queue.Queue,
        writer: LogFileWriter,
        timeout: float = 0.5
    ):
        """
        Inicializar consumidor de fila de logs.
        
        Args:
            log_queue: Fila de mensagens de log
            writer: Escritor de arquivo
            timeout: Timeout para get na fila (segundos)
        """
        super().__init__(daemon=True, name='LogQueueConsumer')
        self.log_queue = log_queue
        self.writer = writer
        self.timeout = timeout
        self.stop_event = threading.Event()
    
    def run(self) -> None:
        """
        Executar consumer - processar fila continuamente.
        """
        while not self.stop_event.is_set():
            try:
                # Tentar obter mensagem da fila com timeout
                message = self.log_queue.get(timeout=self.timeout)
                
                # Escrever no arquivo
                self.writer.write(message)
                
            except queue.Empty:
                # Timeout normal, continuar loop
                continue
            except Exception as e:
                # Log de erro (sem usar logger para evitar recursão)
                print(f"Erro ao processar mensagem de log: {e}")
    
    def stop(self) -> None:
        """
        Parar consumer graciosamente.
        Drena fila antes de fechar.
        """
        # Sinalizar parada
        self.stop_event.set()
        
        # Drenar fila restante
        while not self.log_queue.empty():
            try:
                message = self.log_queue.get_nowait()
                self.writer.write(message)
            except queue.Empty:
                break
        
        # Fechar escritor
        self.writer.close()
    
    def is_running(self) -> bool:
        """Verificar se thread está rodando."""
        return self.is_alive() and not self.stop_event.is_set()
