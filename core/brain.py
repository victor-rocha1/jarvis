"""
Motor de IA central do J.A.R.V.I.S.
Gerencia a comunicação assíncrona com o Gemini via google-genai,
com suporte a streaming de texto token-a-token e resiliência a falhas.
"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError, ServerError

from config.settings import settings
from core.memory import JarvisMemory
from plugins.base_plugin import BasePlugin

logger = logging.getLogger("JarvisBrain")


class JarvisBrain:
    """Núcleo cognitivo do J.A.R.V.I.S."""

    def __init__(
        self,
        memory: Optional[JarvisMemory] = None,
        model: Optional[str] = None,
    ) -> None:
        self.memory: JarvisMemory = memory or JarvisMemory()
        self.preferred_model: str = model or settings.GEMINI_MODEL
        # Lista de modelos alternativos em caso de indisponibilidade temporária (ex: 503)
        self.fallback_models: List[str] = [
            self.preferred_model,
            "gemini-3.5-flash",
            "gemini-3.7-flash",
            "gemini-3.8-flash",
            "gemini-2.5-flash-lite",
        ]
        self._current_model: str = self.preferred_model
        self._client: Optional[genai.Client] = None
        self._chat: Optional[Any] = None
        self._plugins: Dict[str, BasePlugin] = {}

        self._initialize_client()

    def _initialize_client(self) -> None:
        """Inicializa o cliente Google GenAI com a chave de API configurada."""
        if not settings.GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY não configurada no ambiente ou no arquivo .env!")
            raise ValueError("GEMINI_API_KEY ausente. Por favor, verifique o arquivo .env.")

        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._create_chat_session(self._current_model)
        logger.info("JarvisBrain inicializado com o modelo %s.", self._current_model)

    def _create_chat_session(self, model_name: str) -> None:
        """Cria ou reinicia uma sessão de chat assíncrona com as instruções do sistema."""
        if not self._client:
            return

        config = types.GenerateContentConfig(
            system_instruction=settings.SYSTEM_INSTRUCTION,
            temperature=0.7,
        )
        self._chat = self._client.aio.chats.create(
            model=model_name,
            config=config,
        )
        self._current_model = model_name

    def register_plugin(self, plugin: BasePlugin) -> None:
        """Registra um plugin no catálogo do assistente para Function Calling."""
        self._plugins[plugin.name] = plugin
        logger.info("Plugin '%s' registrado no JarvisBrain.", plugin.name)

    async def process_input_stream(self, user_input: str) -> AsyncIterator[str]:
        """Processa a mensagem do usuário via streaming em tempo real.
        
        Yields:
            str: Chunks de texto progressivos conforme são gerados pelo modelo.
        """
        if not user_input.strip():
            return

        # Registra a entrada do usuário na memória local
        self.memory.add_user_message(user_input)
        accumulated_chunks: List[str] = []
        last_error: Optional[Exception] = None

        for model_candidate in self.fallback_models:
            try:
                if self._current_model != model_candidate or self._chat is None:
                    self._create_chat_session(model_candidate)

                assert self._chat is not None
                response_stream = await self._chat.send_message_stream(user_input)

                async for chunk in response_stream:
                    if chunk.text:
                        accumulated_chunks.append(chunk.text)
                        yield chunk.text

                full_response = "".join(accumulated_chunks).strip()
                if not full_response:
                    full_response = "Comando processado com sucesso, senhor."
                    yield full_response

                # Salva a resposta completa gerada na memória
                self.memory.add_model_message(full_response)
                return

            except ServerError as srv_err:
                logger.warning(
                    "Modelo %s indisponível (%s). Tentando fallback de streaming...",
                    model_candidate,
                    srv_err,
                )
                last_error = srv_err
                accumulated_chunks.clear()
                continue

            except APIError as api_err:
                logger.error("Erro na API do Gemini [%s]: %s", model_candidate, api_err)
                last_error = api_err
                accumulated_chunks.clear()
                continue

            except Exception as exc:
                logger.error("Falha inesperada no streaming cognitivo: %s", exc)
                last_error = exc
                break

        # Fallback seguro caso todos os modelos falhem
        error_msg = (
            "Peço desculpas, senhor, mas estou enfrentando uma instabilidade na conexão "
            f"com os servidores centrais ({type(last_error).__name__ if last_error else 'Erro desconhecido'})."
        )
        self.memory.add_model_message(error_msg)
        yield error_msg

    async def think_and_respond(self, user_input: str) -> str:
        """Processa a mensagem do usuário e retorna a resposta completa agregada."""
        chunks: List[str] = []
        async for chunk in self.process_input_stream(user_input):
            chunks.append(chunk)
        return "".join(chunks).strip()
