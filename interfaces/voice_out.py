"""
Módulo de Síntese de Voz (TTS) assíncrono para o J.A.R.V.I.S.
Utiliza edge-tts para geração e pygame para reprodução assíncrona.
"""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import edge_tts
import pygame

from config.settings import settings

logger = logging.getLogger("JarvisVoice")


class JarvisVoice:
    """Controlador de saída de voz do assistente."""

    def __init__(
        self,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        volume: Optional[str] = None,
    ) -> None:
        self.voice: str = voice or settings.TTS_VOICE
        self.rate: str = rate or settings.TTS_RATE
        self.volume: str = volume or settings.TTS_VOLUME
        self.enabled: bool = settings.ENABLE_VOICE
        self._is_speaking: bool = False
        self._init_mixer()

    def _init_mixer(self) -> None:
        """Inicializa o subsistema de áudio do pygame de forma segura."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
                logger.info("Subsistema de áudio inicializado com sucesso.")
        except Exception as exc:
            logger.warning("Falha ao inicializar pygame.mixer: %s. Voz desativada.", exc)
            self.enabled = False

    @staticmethod
    def clean_text_for_speech(text: str) -> str:
        """Remove marcações Markdown e formatações para pronúncia natural."""
        import re

        # Remove blocos de código cercados por ```
        cleaned = re.sub(r"```[\s\S]*?```", " [código omitido] ", text)
        # Remove links no formato [texto](url) -> texto
        cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)
        # Remove formatação inline como `código`
        cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
        # Remove cabeçalhos (#, ##, etc.)
        cleaned = re.sub(r"#{1,6}\s*", "", cleaned)
        # Remove asteriscos e sublinhados de negrito/itálico
        cleaned = re.sub(r"[*_~]{1,3}", "", cleaned)
        # Remove marcadores de lista (*, -, +)
        cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.MULTILINE)
        # Normaliza espaços em branco
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    async def speak(self, text: str) -> None:
        """Sintetiza e reproduz o texto de forma assíncrona sem bloquear o loop principal."""
        clean_text = self.clean_text_for_speech(text)
        if not self.enabled or not clean_text:
            return

        self._is_speaking = True
        temp_audio: Optional[str] = None

        try:
            # Cria arquivo temporário para o áudio MP3
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_audio = fp.name

            # Síntese via edge-tts
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume,
            )
            await communicate.save(temp_audio)

            # Reprodução assíncrona via pygame.mixer
            if pygame.mixer.get_init():
                pygame.mixer.music.load(temp_audio)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy() and self._is_speaking:
                    await asyncio.sleep(0.05)

                pygame.mixer.music.stop()
                pygame.mixer.music.unload()

        except Exception as exc:
            logger.error("Erro durante a síntese ou reprodução de voz: %s", exc)
        finally:
            self._is_speaking = False
            if temp_audio and os.path.exists(temp_audio):
                try:
                    os.remove(temp_audio)
                except OSError:
                    pass

    def stop(self) -> None:
        """Interrompe imediatamente qualquer reprodução de áudio em andamento."""
        self._is_speaking = False
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
        except Exception as exc:
            logger.warning("Erro ao interromper áudio: %s", exc)

    @property
    def is_speaking(self) -> bool:
        """Retorna se o assistente está falando no momento."""
        return self._is_speaking
