"""
LogFileWriter - Responsável por escrita em arquivo com rotação.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class LogFileWriter:
    """
    Gerencia escrita de logs em arquivo com rotação automática.
    """
    
    def __init__(
        self,
        filepath: Path,
        max_bytes: int = 2 * 1024 * 1024,  # 2MB
        backup_count: int = 2
    ):
        """
        Inicializar escritor de arquivo de log.
        
        Args:
            filepath: Caminho do arquivo de log
            max_bytes: Tamanho máximo em bytes antes de rotacionar
            backup_count: Número de arquivos de backup a manter
        """
        self.filepath = filepath
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.handler: Optional[RotatingFileHandler] = None
        self._setup_handler()
    
    def _setup_handler(self) -> None:
        """Configurar handler com rotação."""
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        
        self.handler = RotatingFileHandler(
            filename=str(self.filepath),
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.handler.setFormatter(formatter)
    
    def write(self, message: str) -> None:
        """
        Escrever mensagem em arquivo.
        
        Args:
            message: Mensagem a escrever (já formatada)
        """
        if self.handler and self.handler.stream:
            try:
                self.handler.stream.write(message + '\n')
                self.handler.stream.flush()
                
                # Checar tamanho do arquivo para rotação
                if self.handler.stream.tell() >= self.max_bytes:
                    self.handler.doRollover()
            except Exception as e:
                print(f"Erro ao escrever log: {e}")
    
    def close(self) -> None:
        """Fechar arquivo de log."""
        if self.handler:
            self.handler.flush()
            self.handler.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
