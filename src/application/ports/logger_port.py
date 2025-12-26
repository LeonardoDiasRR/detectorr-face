"""
Porta (Interface) para Logger.
Define o contrato que qualquer implementação de logger deve cumprir.
"""

from typing import Optional, Dict, Any, Protocol


class Logger(Protocol):
    """
    Porta que define a interface para logging.
    
    Qualquer implementação deve cumprir este contrato.
    """
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Registrar mensagem em nível DEBUG.
        
        Args:
            message: Mensagem a ser registrada
            extra: Dados adicionais a incluir no log
        """
        ...
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Registrar mensagem em nível INFO.
        
        Args:
            message: Mensagem a ser registrada
            extra: Dados adicionais a incluir no log
        """
        ...
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Registrar mensagem em nível WARNING.
        
        Args:
            message: Mensagem a ser registrada
            extra: Dados adicionais a incluir no log
        """
        ...
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Registrar mensagem em nível ERROR.
        
        Args:
            message: Mensagem a ser registrada
            extra: Dados adicionais a incluir no log
        """
        ...
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Registrar mensagem em nível CRITICAL.
        
        Args:
            message: Mensagem a ser registrada
            extra: Dados adicionais a incluir no log
        """
        ...
