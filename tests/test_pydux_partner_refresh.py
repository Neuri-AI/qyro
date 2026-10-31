"""Integration with actual PSX source reload and Pydux slice definitions."""
from pathlib import Path
from types import SimpleNamespace

from pydux import configure_store, create_slice
from psx.devtools.qyro_reload import _load_updated_class
from qyro.client.development_pydux import prepare_pydux_refresh


class Demo:
    def render(self):
        return None


def test_new_pydux_slice_schema_reconciles_through_qyro(tmp_path: Path):
    original = create_slice(
        name="user",
        initial_state={"name": "fredo"},
        reducers={"rename": lambda state, action: {**state, "name": action.payload}},
    )
    live = configure_store({"user": original}, devtools=False)
    live.dispatch(original.actions.rename("edited"))

    source = tmp_path / "main.py"
    source.write_text(
        "from pydux import configure_store, create_slice\n"
        "user_slice = create_slice(name='user', initial_state={'name': 'default', 'email': 'new'}, "
        "reducers={'rename': lambda state, action: {**state, 'name': action.payload.upper()}})\n"
        "settings_slice = create_slice(name='settings', initial_state={'theme': 'dark'}, reducers={})\n"
        "store = configure_store({'user': user_slice, 'settings': settings_slice}, devtools=False)\n"
        "class Demo:\n"
        "    def render(self):\n"
        "        return None\n",
        encoding="utf-8",
    )
    candidate = _load_updated_class(source, Demo, frozenset())
    rollback = prepare_pydux_refresh(
        SimpleNamespace(_pydux_store=lambda: live), candidate
    )
    assert rollback is not None
    assert live.get_state() == {
        "user": {"name": "edited", "email": "new"},
        "settings": {"theme": "dark"},
    }
    assert candidate.render.__globals__["store"] is live
    candidate.render.__globals__["user_slice"].actions.rename("next")
    live.dispatch(candidate.render.__globals__["user_slice"].actions.rename("next"))
    assert live.get_state()["user"]["name"] == "NEXT"
    rollback()
    assert live.get_state() == {"user": {"name": "edited"}}
