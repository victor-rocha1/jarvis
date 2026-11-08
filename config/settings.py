"""
Configurações globais e variáveis de ambiente do J.A.R.V.I.S.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings:
    """Configurações centrais do sistema carregadas de variáveis de ambiente."""

    def __init__(self) -> None:
        load_dotenv(dotenv_path=ENV_FILE)

        self.GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        self.GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        
        # Text-To-Speech (edge-tts)
        self.TTS_VOICE: str = os.getenv("TTS_VOICE", "pt-BR-AntonioNeural")
        self.TTS_RATE: str = os.getenv("TTS_RATE", "+0%")
        self.TTS_VOLUME: str = os.getenv("TTS_VOLUME", "+0%")
        self.ENABLE_VOICE: bool = os.getenv("ENABLE_VOICE", "true").lower() in ("true", "1", "yes")

        # Bluetooth / Hardware (Fase 2)
        self.GEONAV_MAC_ADDRESS: str = os.getenv("GEONAV_MAC_ADDRESS", "")

        # Personalidade e Instruções do Sistema
        self.SYSTEM_INSTRUCTION: str = (
            "Você é o J.A.R.V.I.S. (Just A Rather Very Intelligent System), um assistente virtual pessoal "
            "altamente sofisticado, eficiente, cortês e objetivo. "
            "Responda sempre em português brasileiro de forma natural, elegante e concisa, "
            "priorizando clareza e utilidade prática. Mantenha um tom profissional e prestativo, "
            "adequado para um assistente de voz e terminal."
        )


settings = Settings()
