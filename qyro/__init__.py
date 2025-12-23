from os.path import abspath
from qyro._store import QYRO_INTERNAL_STATE
from qyro._exceptions import EngineError
from qyro_engine._qyro import get_config_path, generate_core_profiles
from qyro_engine._source import _get_settings_paths
from qyro_engine._settings import load_json_configs, resolve_placeholders
from qyro_engine._source import path as _source_path

def init(project_dir: str):
    """
    Initializes Qyro for a given project directory. Loads core settings and
    activates default profiles.
    """
    PROJECT_DIR = abspath(project_dir)
    core_config = get_config_path(PROJECT_DIR)["project_dir"]

    QYRO_INTERNAL_STATE.set_config('settings', {'project_dir': core_config})

    for profile in generate_core_profiles():
        enable_profile(profile)


def enable_profile(profile: str):
    """
    Loads a specific profile's settings and merges them into the global state.
    """
    PROJECT_DIR = QYRO_INTERNAL_STATE.get_config('settings')['project_dir']
    QYRO_INTERNAL_STATE.mount_profile(profile)

    json_paths = _get_settings_paths(PROJECT_DIR, QYRO_INTERNAL_STATE._loaded_profiles)
    core_config = get_config_path(PROJECT_DIR)

    merged_settings = load_json_configs(json_paths, core_config)
    QYRO_INTERNAL_STATE.set_config('settings', merged_settings)



def path(path: str) -> str:
    """
    Returns the absolute path of a file in the project directory.
    Supports placeholders like `${freeze_dir}`.
    """
    settings = QYRO_INTERNAL_STATE.get_config('settings')
    path = resolve_placeholders(path, settings)

    try:
        PROJECT_DIR = QYRO_INTERNAL_STATE.get_config('settings')['project_dir']
    except KeyError:
        raise EngineError("Cannot call path(...) until init(...) has been called.") from None

    return _source_path(PROJECT_DIR, path)
