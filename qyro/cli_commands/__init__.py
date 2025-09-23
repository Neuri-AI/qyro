import sys
import os
import pathlib
import subprocess
import importlib
from typing import NoReturn
from os import getcwd
from pathlib import Path
from string import Template
from shutil import rmtree
from getpass import getuser
from os import makedirs, getcwd
from os.path import join, exists, abspath
from questionary import select, text
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from qyro._store import QYRO_INTERNAL_STATE
from qyro.cli_engine import CLI
from qyro.utils import EngineMessage, EngineError, module_exists
from qyro.utils.fs import QYRO_METADATA, replicate_and_filter, write_safely_from_template, check_existing_project
from qyro.utils.parsers import to_camel_case
from qyro.utils.project_reader import get_project_settings, _find_and_store_settings, _validate_project_structure
from qyro.utils.helpers import valid_version
from qyro.pipelines import get_freezer
from qyro.cli_commands.templates.component import COMPONENT_TEMPLATE

console = Console()

custom_style = Style([
    ('qmark', 'fg:#ff00ff bold'),
    ('question', 'fg:#00ffff bold'),
    ('answer', 'fg:#00ffff bold'),
    ('pointer', 'fg:#ffff00 bold'),
    ('highlighted', 'fg:#2fe784 bold'),
    ('selected', 'fg:#2fe784 bold'),
])
bindings_template_map = {
    "PyQt5": "qt_boilerplate",
    "PyQt6": "qt_boilerplate",
    "PySide2": "qt_boilerplate",
    "PySide6": "qt_boilerplate",
    "kivy": "kivy_boilerplate",
    "tkinter": "tk_boilerplate",
}

modules = ['PySide6', 'PyQt6', 'PyQt5', 'PySide2', 'kivy', 'tkinter']



@CLI(help="Show the engine version.")
def version():
    """
        Displays the current version of the Qyro CLI.
    """
    EngineMessage.show(f"Qyro v{QYRO_METADATA['version']}", level="info")
    sys.exit(0)


@CLI(help="Initialize a new Qyro project.")
def init(name: str = "."):
    """
        Initializes a new Qyro project with a standard folder structure.

        Args:
            name (str, optional): The name of the project directory. Defaults to the current directory (".").
        Raises:
            EngineError: If the specified project directory already exists.
    """
    name = to_camel_case(name) if name != "." else "."
    project_path = abspath(name)

    if exists(project_path + "/src"):
        raise EngineError(
            f"Project folder already exists at: [bold]{project_path}[/bold]")

    console.print(
        f"✨ Welcome to [bold green]{QYRO_METADATA['name']} v{QYRO_METADATA['version']}[/bold green] ✨\n")
    console.print(
        "Let's create a new project! This will create a [bold]src/[/bold] directory "
        "with the necessary files and folders.\n"
    )

    # Hide app if user is using --name flag
    if name == ".":
        app = to_camel_case(Prompt.ask(
        "App name", default="MyApp" if name == "." else name))

    version = Prompt.ask("Version", default="1.0.0")

    try:
        default_author = getuser().title()
    except Exception:
        default_author = "Unknown"

    author = Prompt.ask("Author", default=default_author)

    # Select Qt binding
    python_binding = select(
        "Select your Qt binding [PyQt5/PyQt6/PySide2/PySide6] (default: PySide6):",
        choices=["PyQt5", "PyQt6", "PySide2",
                 "PySide6", "Kivy (Experimental)", "Tkinter"],
        style=custom_style
    ).ask()

    if python_binding not in ["PyQt5", "PyQt6", "PySide2", "PySide6"]:
        python_binding = python_binding.split()[0].lower()

    eg_bundle_id = f"com.{author.lower().split()[0]}.{''.join(app.lower().split())}"
    mac_bundle_identifier = Prompt.ask(
        f"Mac bundle identifier (e.g. {eg_bundle_id}, optional)",
        default=eg_bundle_id,
        show_default=False
    )
    if mac_bundle_identifier.strip() == "":
        mac_bundle_identifier = None

    # Display project configuration summary
    table = Table(title="Project Configuration", show_header=False, box=None)
    table.add_row("App name:", f"[cyan]{app}[/cyan]")
    table.add_row("Version:", f"[cyan]{version}[/cyan]")
    table.add_row("Author:", f"[cyan]{author}[/cyan]")
    table.add_row("Qt binding:", f"[cyan]{python_binding}[/cyan]")
    table.add_row("Mac bundle identifier:",f"[cyan]{mac_bundle_identifier or '(none)'}[/cyan]")

    console.print(Panel(
        table, title="[bold]Please confirm your settings[/bold]", border_style="blue"))

    if not Confirm.ask("Continue?"):
        console.print("[yellow]Operation aborted by user.[/yellow]")
        return

    console.print(
        f"\n🔎 Checking if [bold cyan]{python_binding}[/bold cyan] is installed...")

    if not module_exists(python_binding):
        EngineMessage.show(f"Installing {python_binding}...", level="info")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', python_binding], check=True)
        except subprocess.CalledProcessError as e:
            console.print(f"\n\n[red]❌ Failed to install [bold cyan]{python_binding}[/bold cyan]. Please check your internet connection and permissions, and try again.[/red]")
            return
        console.print(
        f"\n✅ [bold cyan]{python_binding}[/bold cyan] is installed!\n")

    if project_path != getcwd():
        makedirs(project_path, exist_ok=True)
    src_path = join(project_path, "src")

    makedirs(src_path, exist_ok=True)

    template_dir = bindings_template_map.get(python_binding, "qt_boilerplate")
    template_dir = (
        pathlib.Path(__file__).resolve().parent / f"templates/{template_dir}"
    )

    if not template_dir.exists():
        raise EngineError(
            f"Template directory not found at: [bold]{template_dir}[/bold]")

    # Copy boilerplate files and apply placeholder replacements
    replicate_and_filter(
        source_path=template_dir,
        destination_path=project_path,
        replacements={
            'app_name': app,
            'author': author,
            'mac_bundle_identifier': mac_bundle_identifier,
            'binding': python_binding,
            'version': version
        },
        files_to_filter=[
            'src/build/settings/base.json',
            'src/build/settings/mac.json',
            'src/main/python/main.py'
        ]
    )

    console.print(f"\n🎉 [bold green]Project created successfully, now you can navigate to it:\n\n    [bold cyan]cd {name}[/bold cyan]")
    console.print("\nThen, you can run:\n\n    [bold cyan]qyro start[/bold cyan]\n")


@CLI(help="Create a new component or view")
def create(type: str = None, name: str = None, inherit: str = None):
    """Creates a new component or view in the project.

    Args:
        type (str, optional): The type of the item to create. Defaults to 'component'.
        name (str, optional): The name of the item to create. Defaults to None.
        inherit (str, optional): The name of the component to inherit from. Defaults to None.
    """

    # validate obligatory args (type, name)
    if not name:
        raise EngineError("The 'name' argument is required.")

    if type is None:
        raise EngineError(
            "The 'type' argument is required and must be either 'component' or 'view'.")

    if type.lower() not in ['component', 'view']:
        raise EngineError(
            "The 'type' argument must be either 'component' or 'view'.")

    name = to_camel_case(name)
    binding = get_project_settings('binding')

    if not inherit:
        inherit = text("Inherit from: ", default="QtWidget").ask()

    template = Template(COMPONENT_TEMPLATE)
    code = template.substitute(Binding=binding, Name=name, Widget=inherit)

    project_path = pathlib.Path.cwd()
    type_lower = type.lower()
    path = project_path / "src" / "main" / "python" / f"{type_lower}s"
    file_path = path / f"{name}.py"

    write_safely_from_template(
        file_path=file_path,
        code=code,
        item_name=name,
        item_type=type
    )


@CLI(help="Starts the application")
def start():
    """
    Starts the Qyro application.
    """
    check_existing_project()
    _find_and_store_settings()
    project_dir = _validate_project_structure()

    if not any(module_exists(name) for name in modules):
        raise EngineError(
        "At least one of the following modules must be installed:"
        " [bold cyan]PySide6[/bold cyan], [bold cyan]PyQt6[/bold cyan], [bold cyan]PyQt5[/bold cyan], [bold cyan]PySide2[/bold cyan], [bold cyan]kivy[/bold cyan], [bold cyan]tkinter[/bold cyan]"
        "\n\nYou can install them using pip:"
        "\n\n[bold green]pip install PySide6[/bold green]"
        "\n[bold green]pip install PySide2[/bold green]"
        "\n[bold green]pip install PyQt6[/bold green]"
        "\n[bold green]pip install PyQt5[/bold green]"
        "\n\nIf you have already installed one of these modules, make sure it is in your PYTHONPATH."
    )
    env = os.environ.copy()
    src_path = str(pathlib.Path(project_dir) / "src" / "main" / "python")
    old_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{old_pythonpath}" if old_pythonpath else src_path

    main_module = QYRO_INTERNAL_STATE.get_config("main_module")

    if not main_module:
        raise EngineError(
            "The 'main_module' setting is missing. Check your project settings.")
    try:
        subprocess.run([sys.executable, main_module], env=env, check=True)
    except subprocess.CalledProcessError as e:
        raise EngineError(
            f"Application failed with exit code {e.returncode}") from e
    except FileNotFoundError:
        raise EngineError(
            "Python interpreter not found. Make sure Python is correctly installed.")


@CLI(help="Build the project")
def build(profile: str | bool = None, bundle: bool = False):
    """
    Builds the project using the appropriate pipeline for the current platform.

    Args:
        profile (str | bool, optional): Determines the build type.
            - If None, the default 'release' setting from the project configuration is used.
            - If a string, 'prod' or 'production' will be treated as a production build (True),
              any other string will be treated as a development build (False).
            - If a boolean, True indicates a production build and False a development build.

    Raises:
        EngineError: If PyInstaller is not installed.
        EngineError: If the project version does not follow the MAJOR.MINOR.PATCH format.
        EngineError: If the function cannot detect the appropriate build pipeline for the current OS.

    Behavior:
        1. Checks that the current directory is a valid project.
        2. Determines the build profile (production or development).
        3. Loads the project configuration.
        4. Validates that PyInstaller is installed.
        5. Validates that the project version string is correctly formatted.
        6. Detects the current platform and selects the correct build pipeline function.
        7. Prints an informative message about the platform and pipeline being used.
        8. Dynamically imports the module containing the pipeline function and executes it
           with the 'debug' argument set according to the build profile.
    """
    check_existing_project()
    console.print(
        "⏳ Freezing your app... \n\nThis may take a while, please be patient.")

    if profile is None:
        profile = QYRO_INTERNAL_STATE.get_config("settings")['release']

    if isinstance(profile, str):
        profile = profile.lower() in ('prod', 'production')

    profile = bool(profile)

    _app = QYRO_INTERNAL_STATE.get_config("settings")

    if not module_exists('PyInstaller'):
        raise EngineError(
            "The 'PyInstaller' module is required for building the project."
        )

    if not valid_version(_app['version']):
        raise EngineError(
            f"Invalid application version '{_app['version']}'. "
            "Expected format is MAJOR.MINOR.PATCH (e.g., 1.0.0 or 2.3.5). "
            "Please update the version string in your configuration file."
        )
    os_key, module_name, func_name = get_freezer()

    EngineMessage.show(
        f"Platform detected: [bold green]{to_camel_case(os_key)}[/bold green].\nRunning pipeline '{func_name}' from module '{module_name}'.",
        level="info"
    )

    module = importlib.import_module(module_name)
    pipeline = getattr(module, func_name)
    pipeline(debug=not profile, bundle=bundle)

    binary = join('target', _app["app_name"], _app["app_name"])

    console.print(
        f"\n🎉 [bold green]Your app was frozen successfully! 🎉[/bold green]\n\nYou can find the executable at: [cyan]{binary}[/cyan].\n\nIf that doesn't work, see https://github.com/runesc/qyro-engine/issues to report the issue.")


@CLI(help="Build the project")
def freeze(profile: str | bool = None, bundle: bool = False) -> NoReturn:
    """
    Alias for the build command.
    """
    build(profile=profile, bundle=bundle)


@CLI(help="Cleans the 'target' directory.")
def clean():
    """
    Deletes the 'target' directory and 'build.log' file safely.

    - Ignores missing files/directories.
    - If 'target' cannot be removed, cleans its contents individually.
    """
    target = Path('target')
    log_file = Path('build.log')

    try:
        if target.exists():
            rmtree(target)
            print(f"Deleted directory: {target}")
    except OSError:
        for item in target.glob('*'):
            try:
                if item.is_dir():
                    rmtree(item)
                else:
                    item.unlink()
            except Exception as e:
                print(f"Failed to delete {item}: {e}")
    try:
        if log_file.exists():
            log_file.unlink()
            print(f"Deleted file: {log_file}")
    except Exception as e:
        print(f"Failed to delete {log_file}: {e}")
