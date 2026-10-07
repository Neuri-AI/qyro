from pathlib import Path
from qyro import EngineContainer


def test_cli_project_settings_and_resources_are_loadable():
    project = Path(__file__).resolve().parents[1]
    container = EngineContainer(
        framework_name="Headless", custom_root=project, enable_sentry=False
    )
    assert container.load_settings_use_case.execute().app_name == "Qyro Kivy Demos"
    assert container.resolve_resource_use_case.execute("text/greeting.txt").exists()
