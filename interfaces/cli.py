"""
Interface de Linha de Comando (CLI) para o J.A.R.V.I.S.
Oferece formatação rica no terminal com baixa latência e status visual.
"""

import asyncio
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.status import Status


class JarvisCLI:
    """Controlador de interface no terminal utilizando Rich."""

    def __init__(self) -> None:
        self.console: Console = Console()

    def show_banner(self, model: str, voice: str, voice_enabled: bool) -> None:
        """Exibe o cabeçalho estilizado do assistente J.A.R.V.I.S."""
        banner_text = Text()
        banner_text.append("   __      _     ___   __      __  ___   ___  \n", style="bold cyan")
        banner_text.append("  / /     /_\\   | _ \\  \\ \\    / / |_ _| / __| \n", style="bold cyan")
        banner_text.append(" / _ \\   / _ \\  |   /   \\ \\/\\/ /   | |  \\__ \\ \n", style="bold cyan")
        banner_text.append(" \\___/  /_/ \\_\\ |_|_\\    \\_/\\_/   |___| |___/ \n", style="bold cyan")
        banner_text.append("\n  Just A Rather Very Intelligent System (Local Edition)\n", style="italic blue")

        info_text = (
            f"[bold green]Status:[/bold green] Online  |  "
            f"[bold green]Modelo:[/bold green] [cyan]{model}[/cyan]  |  "
            f"[bold green]Voz:[/bold green] [cyan]{voice if voice_enabled else 'Desativada'}[/cyan]\n"
            f"[dim]Digite seu comando ou 'sair' para encerrar a sessão.[/dim]"
        )

        self.console.print(Panel(banner_text, subtitle="v1.0 - Fase 1 (MVP)", border_style="cyan"))
        self.console.print(info_text)
        self.console.print()

    async def get_user_input(self, prompt: str = "[bold cyan]Você > [/bold cyan]") -> str:
        """Lê a entrada do usuário de forma assíncrona sem travar o loop de eventos."""
        # asyncio.to_thread para não bloquear tarefas em background
        raw_text = await asyncio.to_thread(self.console.input, prompt)
        return raw_text.strip()

    def show_thinking(self) -> Status:
        """Retorna um spinner de status indicando processamento cognitivo."""
        return self.console.status("[bold blue]J.A.R.V.I.S. está processando...", spinner="dots")

    def display_response(self, text: str) -> None:
        """Exibe a resposta formatada do assistente no terminal."""
        md = Markdown(text)
        self.console.print(
            Panel(
                md,
                title="[bold cyan]J.A.R.V.I.S.[/bold cyan]",
                border_style="cyan",
                padding=(0, 2),
            )
        )
        self.console.print()

    def display_system_message(self, message: str, style: str = "bold yellow") -> None:
        """Exibe mensagens informativas ou de diagnóstico do sistema."""
        self.console.print(f"[{style}][SISTEMA][/{style}] {message}")

    def display_error(self, message: str) -> None:
        """Exibe mensagens de erro destacadas no terminal."""
        self.console.print(f"[bold red][ERRO][/bold red] {message}")
