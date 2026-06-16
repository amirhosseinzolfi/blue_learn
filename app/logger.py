import sys
import time

# Force system stdout and stderr to UTF-8 to resolve Windows cp1252 character map codec crashes
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

# Define professional color theme for terminal diagnostics
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "model": "bold magenta",
    "step": "bold blue"
})

console = Console(theme=custom_theme)

class AILogger:
    """
    Highly descriptive custom logger that provides structured, visually pleasing,
    and premium console output for tracking AI interactions and background processing.
    """
    @staticmethod
    def log_process_start(process_name: str, description: str):
        """Prints a prominent visual indicator in the terminal when a major pipeline begins."""
        console.print(f"\n[step]🚀 STARTING PROCESS:[/step] [bold white]{process_name}[/bold white]")
        console.print(f"[info]{description}[/info]")
        console.print("═" * 80, style="blue")

    @staticmethod
    def log_process_end(process_name: str, duration: float):
        """Prints a completion signal with execution time measurements."""
        console.print("─" * 80, style="blue")
        console.print(f"[success]✅ PROCESS COMPLETED:[/success] [bold white]{process_name}[/bold white] in {duration:.2f}s\n")

    @staticmethod
    def log_ai_call(step_name: str, model_name: str, system_prompt: str, user_input: str, result: str = None):
        """
        Logs the full context of an AI/LLM invocation.
        Constructs elegant Panels to display System Prompts, User inputs, and generated responses.
        """
        console.print(f"\n[bold magenta]🤖 AI LLM CALL: {step_name}[/bold magenta]")
        console.print(f"[model]Model:[/model] [cyan]{model_name}[/cyan]")
        
        # System Prompt Panel
        if system_prompt:
            console.print(Panel(
                Text(system_prompt, style="white"),
                title="[bold yellow]📜 FULL SYSTEM PROMPT[/bold yellow]",
                subtitle="Instructions & Personality",
                border_style="yellow",
                padding=(1, 2)
            ))
            
        # User Input Panel
        if user_input:
            console.print(Panel(
                Text(user_input, style="cyan"),
                title="[bold cyan]📥 FULL USER INPUT / CONTEXT[/bold cyan]",
                subtitle="Data passed to Model",
                border_style="cyan",
                padding=(1, 2)
            ))
            
        # Result Panel (if available immediately)
        if result:
            console.print(Panel(
                Text(str(result), style="green"),
                title="[bold green]📤 FULL AI RESPONSE[/bold green]",
                subtitle="Raw Output",
                border_style="green",
                padding=(1, 2)
            ))

    @staticmethod
    def log_ai_stream_start(step_name: str, model_name: str):
        """Indicates that a streaming response has been initiated."""
        console.print(f"\n[bold magenta]🤖 AI STREAMING START: {step_name}[/bold magenta] (Model: [cyan]{model_name}[/cyan])")
        console.print("[info]Streaming response...[/info]")

    @staticmethod
    def log_info(message: str):
        """Basic informational log with customized coloring."""
        console.print(f"[info]ℹ️ {message}[/info]")

    @staticmethod
    def log_success(message: str):
        """Basic success status log."""
        console.print(f"[success]✅ {message}[/success]")

    @staticmethod
    def log_error(message: str, error: Exception = None):
        """Visual red highlighted error logging."""
        console.print(f"[error]❌ ERROR: {message}[/error]")
        if error:
            console.print(f"[error]{str(error)}[/error]")

logger = AILogger()
