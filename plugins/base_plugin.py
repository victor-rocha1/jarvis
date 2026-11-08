"""
Contrato e interface base para todos os plugins do J.A.R.V.I.S.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BasePlugin(ABC):
    """Classe base abstrata para plugins do J.A.R.V.I.S.
    
    Cada plugin exporta a especificação de Function Calling para o Gemini
    e um método execute assíncrono para processamento da ação.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome único da ferramenta/função."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Descrição clara do que a ferramenta realiza para o modelo."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """Esquema JSON Schema compatível com a declaração de parâmetros do Gemini."""
        pass

    def get_declaration(self) -> Dict[str, Any]:
        """Gera a declaração de ferramenta formatada para a API do Gemini."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Executa a lógica da ferramenta de forma assíncrona.
        
        Args:
            **kwargs: Parâmetros informados pelo modelo Gemini.
            
        Returns:
            Dict[str, Any]: Resultado da execução a ser retornado para o modelo.
        """
        pass
