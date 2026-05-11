import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

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
    @staticmethod
    def log_process_start(process_name: str, description: str):
        console.print(f"\n[step]🚀 STARTING PROCESS:[/step] [bold white]{process_name}[/bold white]")
        console.print(f"[info]{description}[/info]")
        console.print("═" * 80, style="blue")

    @staticmethod
    def log_process_end(process_name: str, duration: float):
        console.print("─" * 80, style="blue")
        console.print(f"[success]✅ PROCESS COMPLETED:[/success] [bold white]{process_name}[/bold white] in {duration:.2f}s\n")

    @staticmethod
    def log_ai_call(step_name: str, model_name: str, system_prompt: str, user_input: str, result: str = None):
        """Standard log for AI calls, showing full context."""
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
        console.print(f"\n[bold magenta]🤖 AI STREAMING START: {step_name}[/bold magenta] (Model: [cyan]{model_name}[/cyan])")
        console.print("[info]Streaming response...[/info]")

    @staticmethod
    def log_info(message: str):
        console.print(f"[info]ℹ️ {message}[/info]")

    @staticmethod
    def log_success(message: str):
        console.print(f"[success]✅ {message}[/success]")

    @staticmethod
    def log_error(message: str, error: Exception = None):
        console.print(f"[error]❌ ERROR: {message}[/error]")
        if error:
            console.print(f"[error]{str(error)}[/error]")

logger = AILogger()
