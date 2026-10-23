"""Registered development state survives a compatible process replacement."""
from types import SimpleNamespace

from pydux import Action, Store

from qyro.client.development_state import capture_restart_state, restore_restart_state


def reducer(state, action):
    if action.type == "increment":
        return {"count": state["count"] + 1}
    return state


def make_context(store, *, frozen=False, enabled=True):
    return SimpleNamespace(
        is_frozen=frozen,
        app_settings={"hot_reload": {
            "preserve_state": enabled,
            "state": {
                "snapshot_on_restart": enabled,
                "restore_on_restart": enabled,
            },
        }},
        _pydux_store=lambda: store,
    )


def test_process_replacement_restores_json_state_into_new_store(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setenv("VELTO_DEVELOPMENT", "1")
    monkeypatch.setenv("VELTO_RESTART_STATE_PATH", str(state_path))
    old = Store(reducer, {"count": 3})
    old.dispatch(Action("increment"))
    assert capture_restart_state(make_context(old))
    fresh = Store(reducer, {"count": 0})
    observed = []
    fresh.select(lambda state: state["count"], observed.append)
    assert restore_restart_state(make_context(fresh), fresh)
    assert fresh.get_state() == {"count": 4}
    assert observed == [4]
    assert not state_path.exists()
    assert not restore_restart_state(make_context(fresh), fresh)


def test_invalid_snapshot_is_consumed_without_modifying_store(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    state_path.write_text('{"version":2,"store":{}}', encoding="utf-8")
    monkeypatch.setenv("VELTO_DEVELOPMENT", "1")
    monkeypatch.setenv("VELTO_RESTART_STATE_PATH", str(state_path))
    fresh = Store(reducer, {"count": 7})
    assert not restore_restart_state(make_context(fresh), fresh)
    assert fresh.get_state() == {"count": 7}
    assert not state_path.exists()


def test_frozen_and_disabled_contexts_never_export_state(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setenv("VELTO_DEVELOPMENT", "1")
    monkeypatch.setenv("VELTO_RESTART_STATE_PATH", str(state_path))
    store = Store(reducer, {"count": 1})
    assert not capture_restart_state(make_context(store, frozen=True))
    assert not capture_restart_state(make_context(store, enabled=False))
    assert not state_path.exists()


def test_rejects_oversized_or_nonserializable_state(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setenv("VELTO_DEVELOPMENT", "1")
    monkeypatch.setenv("VELTO_RESTART_STATE_PATH", str(state_path))
    store = Store(reducer, {"payload": "x" * 1_048_577})
    assert not capture_restart_state(make_context(store))
    assert not state_path.exists()
    store = Store(reducer, {"object": object()})
    assert not capture_restart_state(make_context(store))
    assert not state_path.exists()
