import sys
import textwrap
import logging
import qyro
from os import getcwd
from qyro.utils import EngineError, EngineMessage
from qyro.cli_engine import _create_arg_parser, _execute_command
from qyro import cli_commands

class WrappingStreamHandler(logging.StreamHandler):
    """
    Stream handler that wraps long lines in the output.
    This handler is used only for INFO level messages.
    """
    def __init__(self, *args, **kwargs):
        self.wrap = kwargs.pop('wrap', True)
        self.width = kwargs.pop('width', 70)
        super().__init__(*args, **kwargs)

    def emit(self, record):
        if self.wrap and getattr(record, 'wrap', True):
            record.msg = '\n'.join(textwrap.wrap(str(record.msg), width=self.width, subsequent_indent='    '))
        super().emit(record)

def _setup_logging():
    """
    Sets up the logging system to handle INFO-level messages with wrapping.
    Error and warning messages are handled directly by EngineMessage.
    """
    if logging.getLogger().hasHandlers():
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # Set base level to INFO

    # Handler for stdout (INFO level and below messages) with wrapping
    stdout_handler = WrappingStreamHandler(sys.stdout, wrap=True, width=70)
    stdout_handler.setLevel(logging.INFO)
    stdout_formatter = logging.Formatter('%(message)s')
    stdout_handler.setFormatter(stdout_formatter)
    root_logger.addHandler(stdout_handler)

def main():
    """
    Main function of the CLI. It initializes logging,
    parses commands, and handles major exceptions.
    """
    _setup_logging()

    project_dir = getcwd()
    qyro.init(project_dir)

    parser = _create_arg_parser()

    try:
        _execute_command(parser)
    except EngineError:
        sys.exit(1)
    except KeyboardInterrupt:
        EngineMessage.show("Execution canceled by the user.", level="warning")
        sys.exit(1)

if __name__ == '__main__':
    main()