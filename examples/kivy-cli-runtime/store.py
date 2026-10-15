"""Pydux state shared by the Kivy demo components."""

from pydux import configure_store, create_selector, create_slice
from qyro import is_frozen, load_build_settings


RUNNING_FROZEN = is_frozen()

counter_slice = create_slice(
    name="counter",
    initial_state={"value": 0},
    reducers={
        "increment": lambda state, action: state.update(value=state["value"] + 1),
        "decrement": lambda state, action: state.update(value=state["value"] - 1),
    },
)
profile_slice = create_slice(
    name="profile",
    initial_state={"name": "Sin seleccionar", "role": "—"},
    reducers={"set_profile": lambda state, action: state.update(**action.payload)},
)
runtime_slice = create_slice(
    name="runtime",
    initial_state={"app_name": "Cargando…", "theme": "—", "is_frozen": False},
    reducers={"set_info": lambda state, action: state.update(**action.payload)},
)
store = configure_store(
    {
        "counter": counter_slice,
        "profile": profile_slice,
        "runtime": runtime_slice,
    },
    devtools=not RUNNING_FROZEN,
    inspector_auto_start=not RUNNING_FROZEN,
)

select_counter = create_selector(
    lambda state: state["counter"]["value"],
    lambda value: f"Contador compartido: {value}",
)
select_profile = lambda state: state["profile"]
select_runtime_info = lambda state: state["runtime"]


def refresh_runtime_info():
    """Move Qyro helper data into Pydux so a component can react to it."""
    settings = load_build_settings()
    return runtime_slice.actions.set_info({
        "app_name": settings.get("app_name", "Qyro Application"),
        "theme": settings.get("theme", "sin tema"),
        "is_frozen": RUNNING_FROZEN,
    })
