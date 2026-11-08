"""
Módulo de Memória e Gerenciamento de Histórico de Conversação.
"""

from typing import Any, List, Optional
from dataclasses import dataclass, field
import json


@dataclass
class ChatTurn:
    """Representa um turno de diálogo entre o usuário e o J.A.R.V.I.S."""
    role: str  # 'user' ou 'model'
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class JarvisMemory:
    """Gerenciador de memória de curto prazo e histórico da sessão."""

    def __init__(self, max_turns: int = 30) -> None:
        self.max_turns: int = max_turns
        self._history: List[ChatTurn] = []

    def add_user_message(self, message: str) -> None:
        """Adiciona uma mensagem do usuário ao histórico."""
        self._history.append(ChatTurn(role="user", content=message))
        self._auto_trim()

    def add_model_message(self, message: str) -> None:
        """Adiciona uma resposta do assistente ao histórico."""
        self._history.append(ChatTurn(role="model", content=message))
        self._auto_trim()

    def get_history(self) -> List[ChatTurn]:
        """Retorna uma cópia da lista de turnos de diálogo."""
        return list(self._history)

    def to_gemini_contents(self) -> List[dict[str, Any]]:
        """Converte o histórico para o formato compatível com a API do Gemini."""
        return [
            {
                "role": turn.role,
                "parts": [{"text": turn.content}]
            }
            for turn in self._history
        ]

    def clear(self) -> None:
        """Limpa todo o histórico de conversação."""
        self._history.clear()

    @property
    def turn_count(self) -> int:
        """Retorna o número total de turnos armazenados."""
        return len(self._history)

    def _auto_trim(self) -> None:
        """Remove mensagens antigas se o limite de turnos for excedido."""
        if len(self._history) > self.max_turns:
            # Preserva os últimos max_turns
            self._history = self._history[-self.max_turns:]
