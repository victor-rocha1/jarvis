"""
Orquestrador Principal do J.A.R.V.I.S.
Gerencia o ciclo de vida da aplicação, loop assíncrono de eventos,
e coordenação de streaming em tempo real entre CLI, Cérebro (Gemini) e Voz (TTS).
"""

import asyncio
import logging
import re
import sys
from typing import List, Optional, Tuple

from config.settings import settings
from core.brain import JarvisBrain
from core.memory import JarvisMemory
from interfaces.cli import JarvisCLI
from interfaces.voice_out import JarvisVoice

# Configuração de logging estruturado (arquivo para manter terminal limpo)
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

# Abreviações comuns que não devem encerrar frases prematuramente
ABBREVIATIONS = {"sr.", "sra.", "dr.", "dra.", "etc.", "ex.", "vs."}


def extract_complete_sentences(buffer: str) -> Tuple[List[str], str]:
    """Extrai frases completas do buffer baseado em pontuação terminal (. ! ? \\n).
    
    Preserva abreviações comuns e números decimais sem fragmentá-los.
    
    Returns:
        Tuple[List[str], str]: Lista de frases completas encontradas e o restante do buffer.
    """
    sentences: List[str] = []
    start = 0

    for m in re.finditer(r"([.!?]+|\n+)(?:\s+|$)", buffer):
        end_pos = m.end(1)
        candidate = buffer[start:end_pos].strip()
        last_word = candidate.split()[-1].lower() if candidate.split() else ""

        # Evita divisão em abreviações ou dígitos seguidos de ponto
        if last_word in ABBREVIATIONS or re.search(r"\d+\.$", candidate):
            continue

        if candidate:
            sentences.append(candidate)
        start = m.end()

    remaining = buffer[start:]
    return sentences, remaining


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

    # Saudação inicial de prontidão do sistema
    greeting = "Sistemas operacionais em prontidão. À sua disposição, senhor."
    cli.display_response(greeting)
    if voice.enabled:
        await voice.speak(greeting)

    try:
        while True:
            # Captura assíncrona da entrada do usuário
            user_input = await cli.get_user_input()

            # Ignora comandos vazios
            if not user_input:
                continue

            # Se houver áudio em reprodução anterior, interrompe imediatamente
            voice.stop()

            # Checagem de intenção de saída
            if user_input.lower().strip() in EXIT_COMMANDS:
                farewell = "Encerrando sistemas. Tenha um excelente dia, senhor."
                cli.display_response(farewell)
                if voice.enabled:
                    await voice.speak(farewell)
                break

            # Inicia nova sessão de pipeline de áudio
            voice.start_session()

            accumulated_text = ""
            sentence_buffer = ""

            # Exibe status de processamento até o primeiro chunk ser recebido
            with cli.show_thinking():
                stream_generator = brain.process_input_stream(user_input)
                try:
                    first_chunk = await stream_generator.__anext__()
                    accumulated_text += first_chunk
                    sentence_buffer += first_chunk
                except StopAsyncIteration:
                    first_chunk = ""

            # Avalia se o primeiro chunk já fecha uma frase completa
            if sentence_buffer:
                sentences, sentence_buffer = extract_complete_sentences(sentence_buffer)
                for sentence in sentences:
                    await voice.enqueue_sentence(sentence)

            # Inicia o painel Live para exibição em tempo real token a token
            live = cli.create_live_response()
            with live:
                cli.update_live_response(live, accumulated_text)

                async for chunk in stream_generator:
                    accumulated_text += chunk
                    sentence_buffer += chunk
                    cli.update_live_response(live, accumulated_text)

                    # Extrai frases completas e encaminha para sintetização em fila
                    sentences, sentence_buffer = extract_complete_sentences(sentence_buffer)
                    for sentence in sentences:
                        await voice.enqueue_sentence(sentence)

            # Envia qualquer texto remanescente como frase final
            if sentence_buffer.strip():
                await voice.enqueue_sentence(sentence_buffer.strip())

            # Sinaliza conclusão do stream de texto e aguarda reprodução final do áudio
            await voice.finish_stream()
            if voice.enabled:
                await voice.wait_until_done()

            cli.console.print()

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
