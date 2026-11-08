"""
Orquestrador Principal do J.A.R.V.I.S.
Gerencia o ciclo de vida da aplicação, loop assíncrono de eventos,
e coordenação entre CLI, Cérebro (Gemini) e Voz (TTS).
"""

import asyncio
import logging
import sys
from typing import Optional

from config.settings import settings
from core.brain import JarvisBrain
from core.memory import JarvisMemory
from interfaces.cli import JarvisCLI
from interfaces.voice_out import JarvisVoice

# Configuração de logging estruturado (arquivo e console para warnings/erros)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    handlers=[
        logging.FileHandler("jarvis.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("JarvisMain")

# Palavras-chave para encerramento da sessão
EXIT_COMMANDS = {"sair", "exit", "quit", "desligar", "encerrar", "tchau", "bye"}


async def main() -> None:
    """Ponto de entrada assíncrono do J.A.R.V.I.S."""
    cli = JarvisCLI()
    voice = JarvisVoice()
    memory = JarvisMemory(max_turns=30)
    
    # Exibe banner inicial da interface
    cli.show_banner(
        model=settings.GEMINI_MODEL,
        voice=settings.TTS_VOICE,
        voice_enabled=voice.enabled,
    )

    # Inicialização do JarvisBrain
    try:
        brain = JarvisBrain(memory=memory)
    except Exception as exc:
        cli.display_error(f"Falha crítica na inicialização do cérebro: {exc}")
        logger.exception("Erro ao inicializar JarvisBrain")
        return

    # Saudação de prontidão do sistema
    greeting = "Sistemas operacionais em prontidão. À sua disposição, senhor."
    cli.display_response(greeting)
    if voice.enabled:
        await voice.speak(greeting)

    speech_task: Optional[asyncio.Task[None]] = None

    try:
        while True:
            # Captura assíncrona da entrada do usuário
            user_input = await cli.get_user_input()

            # Ignora comandos vazios
            if not user_input:
                continue

            # Se houver áudio sendo reproduzido no momento, interrompe
            if speech_task and not speech_task.done():
                voice.stop()
                speech_task.cancel()

            # Checagem de intenção de saída
            if user_input.lower().strip() in EXIT_COMMANDS:
                farewell = "Encerrando subsistemas. Tenha um excelente dia, senhor."
                cli.display_response(farewell)
                if voice.enabled:
                    await voice.speak(farewell)
                break

            # Processamento cognitivo com indicador visual
            with cli.show_thinking():
                response_text = await brain.think_and_respond(user_input)

            # Exibição da resposta no terminal
            cli.display_response(response_text)

            # Reprodução de voz sem bloquear a próxima iteração
            if voice.enabled:
                speech_task = asyncio.create_task(voice.speak(response_text))

    except (KeyboardInterrupt, asyncio.CancelledError):
        cli.display_system_message("Interrupção manual detectada. Finalizando processos...")
    finally:
        voice.stop()
        logger.info("J.A.R.V.I.S. finalizado.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"\n[FATAL] Falha no sistema: {exc}", file=sys.stderr)
