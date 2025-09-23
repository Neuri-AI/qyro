import inspect
from rich.console import Console
console = Console(stderr=True)

class EngineMessage:
    LEVEL_STYLES = {
        "error": ("❌", "bold red"),
        "warning": ("⚠️ ", "bold yellow"),
        "info": ("ℹ️", "bold cyan"),
        "debug": ("🛠️", "bold magenta"),
        "critical": ("🚨", "bold red on white"),
        "hot": ("🔥", "bold red"),
        "success": ("✅", "bold green"),
    }

    @classmethod
    def show(cls, message: str, level: str = "error", caller_info: str = ""):
        emoji, style = cls.LEVEL_STYLES.get(level, ("❌", "bold red"))
        caller_text = f" (called from {caller_info})" if caller_info else ""
        console.print(f"{emoji} [{style}]{level.upper()}:[/{style}] {message}{caller_text}", highlight=False)


class EngineError(Exception):
    def __init__(self, message: str, verbose=True):
        # Obtener información del archivo y línea que llamó a EngineError
        stack = inspect.stack()
        # stack[1] es la función que llamó a EngineError
        caller_frame = stack[1]
        caller_info = f"{caller_frame.filename}:{caller_frame.lineno} in {caller_frame.function}"
        super().__init__(message)
        EngineMessage.show(message, level="error", caller_info=caller_info if verbose else "")
