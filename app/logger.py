import sys
import time
import logging
import os
from logging.handlers import RotatingFileHandler

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

# ---------------------------------------------------------------------------
# File logging setup — structured, rotating, UTF-8
# ---------------------------------------------------------------------------
_LOG_FILE = os.getenv("LOG_FILE", "logs/blue_learn.log")
os.makedirs(os.path.dirname(_LOG_FILE), exist_ok=True)

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_file_handler = RotatingFileHandler(
    _LOG_FILE,
    maxBytes=10 * 1024 * 1024,   # 10 MB per file
    backupCount=5,                # keep last 5 rotated files
    encoding="utf-8",
)
_file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
_file_handler.setLevel(logging.DEBUG)

def get_file_logger(name: str) -> logging.Logger:
    """Return a stdlib logger that writes to the rotating log file."""
    lg = logging.getLogger(name)
    if not lg.handlers:
        lg.addHandler(_file_handler)
    lg.setLevel(logging.DEBUG)
    lg.propagate = False
    return lg

_flog = get_file_logger("blue_learn.app")

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
        _flog.info("PROCESS START | %s | %s", process_name, description)
        console.print(f"\n[step]🚀 STARTING PROCESS:[/step] [bold white]{process_name}[/bold white]")
        console.print(f"[info]{description}[/info]")
        console.print("═" * 80, style="blue")

    @staticmethod
    def log_process_end(process_name: str, duration: float):
        """Prints a completion signal with execution time measurements."""
        _flog.info("PROCESS END   | %s | %.2fs", process_name, duration)
        console.print("─" * 80, style="blue")
        console.print(f"[success]✅ PROCESS COMPLETED:[/success] [bold white]{process_name}[/bold white] in {duration:.2f}s\n")

    @staticmethod
    def log_ai_call(step_name: str, model_name: str, system_prompt: str, user_input: str, result: str = None):
        """Logs full AI/LLM invocation content to file and renders it in terminal."""
        sep = "=" * 80
        _flog.debug(
            "AI CALL | step=%s | model=%s | prompt_len=%d | input_len=%d | result_len=%d\n"
            "%s\n"
            "[SYSTEM PROMPT]\n%s\n"
            "%s\n"
            "[USER INPUT]\n%s\n"
            "%s\n"
            "[AI RESPONSE]\n%s\n"
            "%s",
            step_name, model_name,
            len(system_prompt or ""), len(user_input or ""), len(str(result or "")),
            sep,
            system_prompt or "(none)",
            sep,
            user_input or "(none)",
            sep,
            str(result) if result else "(none)",
            sep,
        )
        console.print(f"\n[bold magenta]🤖 AI LLM CALL: {step_name}[/bold magenta]")
        console.print(f"[model]Model:[/model] [cyan]{model_name}[/cyan]")

        if system_prompt:
            console.print(Panel(
                Text(system_prompt, style="white"),
                title="[bold yellow]📜 FULL SYSTEM PROMPT[/bold yellow]",
                subtitle="Instructions & Personality",
                border_style="yellow",
                padding=(1, 2)
            ))

        if user_input:
            console.print(Panel(
                Text(user_input, style="cyan"),
                title="[bold cyan]📥 FULL USER INPUT / CONTEXT[/bold cyan]",
                subtitle="Data passed to Model",
                border_style="cyan",
                padding=(1, 2)
            ))

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
        _flog.debug("AI STREAM START | step=%s | model=%s", step_name, model_name)
        console.print(f"\n[bold magenta]🤖 AI STREAMING START: {step_name}[/bold magenta] (Model: [cyan]{model_name}[/cyan])")
        console.print("[info]Streaming response...[/info]")

    @staticmethod
    def log_info(message: str):
        """Basic informational log with customized coloring."""
        _flog.info(message)
        console.print(f"[info]ℹ️ {message}[/info]")

    @staticmethod
    def log_success(message: str):
        """Basic success status log."""
        _flog.info("SUCCESS | %s", message)
        console.print(f"[success]✅ {message}[/success]")

    @staticmethod
    def log_error(message: str, error: Exception = None):
        """Visual red highlighted error logging."""
        _flog.error("%s | %s", message, str(error) if error else "")
        console.print(f"[error]❌ ERROR: {message}[/error]")
        if error:
            console.print(f"[error]{str(error)}[/error]")

logger = AILogger()
