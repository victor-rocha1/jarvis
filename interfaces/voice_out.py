"""
Módulo de Síntese de Voz (TTS) assíncrono para o J.A.R.V.I.S.
Implementa fila de reprodução assíncrona (Audio Queue) frase por frase,
com sintetização em paralelo via edge-tts e reprodução contínua via pygame.
"""

import asyncio
import logging
import os
import re
import tempfile
from typing import Optional

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import edge_tts
import pygame

from config.settings import settings

logger = logging.getLogger("JarvisVoice")


class JarvisVoice:
    """Controlador de saída de voz com streaming e fila frase-por-frase."""

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

        self._text_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        self._audio_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

        self._synth_task: Optional[asyncio.Task[None]] = None
        self._play_task: Optional[asyncio.Task[None]] = None
        self._stop_requested: bool = False
        self._playback_done_event: asyncio.Event = asyncio.Event()
        self._playback_done_event.set()

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
        """Remove marcações Markdown e caracteres especiais para pronúncia natural."""
        # Remove blocos de código
        cleaned = re.sub(r"```[\s\S]*?```", " [código omitido] ", text)
        # Remove links [texto](url) -> texto
        cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)
        # Remove códigos inline
        cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
        # Remove títulos (#, ##)
        cleaned = re.sub(r"#{1,6}\s*", "", cleaned)
        # Remove negrito, itálico e tachado
        cleaned = re.sub(r"[*_~]{1,3}", "", cleaned)
        # Remove marcadores de lista
        cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.MULTILINE)
        # Remove numeração de lista no início de linha ex: "1. "
        cleaned = re.sub(r"^\s*\d+\.\s+", "", cleaned, flags=re.MULTILINE)
        # Normaliza múltiplos espaços
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def start_session(self) -> None:
        """Inicia uma nova sessão de fala em streaming com workers de síntese e reprodução."""
        if not self.enabled:
            return

        self.stop()
        self._stop_requested = False
        self._playback_done_event.clear()
        self._text_queue = asyncio.Queue()
        self._audio_queue = asyncio.Queue()

        self._synth_task = asyncio.create_task(self._synthesis_worker())
        self._play_task = asyncio.create_task(self._playback_worker())

    async def enqueue_sentence(self, sentence: str) -> None:
        """Enfileira uma frase individual para sintetização e reprodução imediata."""
        if not self.enabled:
            return

        clean = self.clean_text_for_speech(sentence)
        if clean:
            await self._text_queue.put(clean)

    async def finish_stream(self) -> None:
        """Informa ao pipeline que todas as frases da resposta foram enfileiradas."""
        if not self.enabled:
            self._playback_done_event.set()
            return
        await self._text_queue.put(None)

    async def wait_until_done(self) -> None:
        """Aguarda a conclusão da reprodução de todas as frases enfileiradas."""
        if not self.enabled:
            return
        await self._playback_done_event.wait()

    def stop(self) -> None:
        """Interrompe imediatamente qualquer síntese ou áudio em reprodução."""
        self._stop_requested = True
        self._playback_done_event.set()

        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
        except Exception as exc:
            logger.warning("Erro ao parar mixer: %s", exc)

        # Cancela tarefas de background se ativas
        if self._synth_task and not self._synth_task.done():
            self._synth_task.cancel()
        if self._play_task and not self._play_task.done():
            self._play_task.cancel()

        # Drena filas e remove arquivos residuais
        while not self._audio_queue.empty():
            try:
                audio_file = self._audio_queue.get_nowait()
                if audio_file and os.path.exists(audio_file):
                    os.remove(audio_file)
            except Exception:
                pass

        while not self._text_queue.empty():
            try:
                self._text_queue.get_nowait()
            except Exception:
                pass

    async def speak(self, text: str) -> None:
        """Método de conveniência para sintetizar e reproduzir texto completo (one-shot)."""
        if not self.enabled or not text.strip():
            return
        self.start_session()
        await self.enqueue_sentence(text)
        await self.finish_stream()
        await self.wait_until_done()

    async def _synthesis_worker(self) -> None:
        """Consome frases da fila de texto, sintetiza em paralelo e enfileira os áudios gerados."""
        try:
            while not self._stop_requested:
                sentence = await self._text_queue.get()
                if sentence is None:
                    # Sinalizador de término da entrada de texto
                    await self._audio_queue.put(None)
                    self._text_queue.task_done()
                    break

                temp_path: Optional[str] = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                        temp_path = fp.name

                    communicate = edge_tts.Communicate(
                        text=sentence,
                        voice=self.voice,
                        rate=self.rate,
                        volume=self.volume,
                    )
                    await communicate.save(temp_path)

                    if self._stop_requested:
                        if temp_path and os.path.exists(temp_path):
                            os.remove(temp_path)
                        break

                    await self._audio_queue.put(temp_path)

                except Exception as exc:
                    logger.error("Erro na síntese da frase '%s': %s", sentence, exc)
                    if temp_path and os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except OSError:
                            pass
                finally:
                    self._text_queue.task_done()

        except asyncio.CancelledError:
            pass

    async def _playback_worker(self) -> None:
        """Consome áudios da fila e reproduz sequencialmente sem lacunas perceptíveis."""
        try:
            while not self._stop_requested:
                audio_path = await self._audio_queue.get()
                if audio_path is None:
                    # Fim do stream de áudios
                    self._audio_queue.task_done()
                    self._playback_done_event.set()
                    break

                try:
                    if pygame.mixer.get_init():
                        pygame.mixer.music.load(audio_path)
                        pygame.mixer.music.play()

                        while pygame.mixer.music.get_busy() and not self._stop_requested:
                            await asyncio.sleep(0.02)

                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()

                except Exception as exc:
                    logger.error("Erro ao reproduzir áudio '%s': %s", audio_path, exc)
                finally:
                    if os.path.exists(audio_path):
                        try:
                            os.remove(audio_path)
                        except OSError:
                            pass
                    self._audio_queue.task_done()

        except asyncio.CancelledError:
            pass
        finally:
            self._playback_done_event.set()

    @property
    def is_speaking(self) -> bool:
        """Indica se o assistente está reproduzindo voz atualmente."""
        try:
            return bool(pygame.mixer.get_init() and pygame.mixer.music.get_busy())
        except Exception:
            return False
