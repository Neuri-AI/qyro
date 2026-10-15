"""Shared Pydux state for the Tkinter Qyro demos."""

from pydux import configure_store, create_selector, create_slice
from qyro import is_frozen, load_build_settings

RUNNING_FROZEN = is_frozen()
counter_slice = create_slice(
    "counter", {"value": 0},
    {"increment": lambda state, action: state.update(value=state["value"] + 1),
     "decrement": lambda state, action: state.update(value=state["value"] - 1)},
)
profile_slice = create_slice(
    "profile", {"name": "Sin seleccionar", "role": "—"},
    {"set_profile": lambda state, action: state.update(**action.payload)},
)
runtime_slice = create_slice(
    "runtime", {"app_name": "Cargando…", "theme": "—", "is_frozen": False},
    {"set_info": lambda state, action: state.update(**action.payload)},
)
store = configure_store(
    {"counter": counter_slice, "profile": profile_slice, "runtime": runtime_slice},
    devtools=not RUNNING_FROZEN, inspector_auto_start=not RUNNING_FROZEN,
)
select_counter = create_selector(
    lambda state: state["counter"]["value"],
    lambda value: f"Contador compartido: {value}",
)
select_profile = lambda state: state["profile"]
select_runtime_info = lambda state: state["runtime"]


def refresh_runtime_info():
    settings = load_build_settings()
    return runtime_slice.actions.set_info({
        "app_name": settings.get("app_name", "Qyro Application"),
        "theme": settings.get("theme", "sin tema"),
        "is_frozen": RUNNING_FROZEN,
    })
