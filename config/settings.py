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

        # Personalidade e Instruções do Sistema (Foco em Baixa Latência e Concisão)
        self.SYSTEM_INSTRUCTION: str = (
            "Você é o J.A.R.V.I.S., um assistente virtual pessoal tático, altamente inteligente e de prontidão operacional.\n"
            "Diretrizes obrigatórias de resposta:\n"
            "1. Seja extremamente conciso, direto e objetivo (estilo assistente tático de voz).\n"
            "2. Limite sua resposta estritamente a 1 ou no máximo 3 frases curtas, exceto se explicações aprofundadas ou código forem explicitamente requisitados.\n"
            "3. Mantenha tom sofisticado, profissional e cortês (utilize vocativos como 'Senhor', termos como 'Sistemas operacionais em prontidão', 'Às suas ordens').\n"
            "4. Responda sempre em português do Brasil sem delongas, preâmbulos vazios ou repetições desnecessárias."
        )


settings = Settings()
