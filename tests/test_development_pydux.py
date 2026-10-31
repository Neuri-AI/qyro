"""Qyro ownership and rollback contract for Pydux hot refresh."""
from types import SimpleNamespace
import sys
import types

from qyro.client.development_pydux import prepare_pydux_refresh


class Store:
    def __init__(self, state, definitions):
        self._state = state
        self._pydux_slice_definitions = definitions
        self._reducer = lambda state, action: state
        self.notifications = 0

    def get_state(self):
        return self._state

    def replace_reducer(self, reducer, state):
        self._reducer = reducer
        self._state = state
        self.notifications += 1


def test_qyro_refresh_preserves_live_store_and_can_rollback(monkeypatch):
    live = Store({"user": {"name": "edited"}}, {"user": "previous"})
    transient = Store({"user": {"name": "initial", "email": "new"}}, {"user": "updated"})
    namespace = {"store": transient}

    def render_candidate():
        return store

    render_candidate = types.FunctionType(render_candidate.__code__, namespace)
    candidate = SimpleNamespace(render=render_candidate)
    context = SimpleNamespace(_pydux_store=lambda: live)

    module = types.ModuleType("pydux.toolkit.hot_reload")
    def reconfigure(store, definitions):
        assert store is live
        store.replace_reducer(lambda state, action: state, {
            "user": {"name": "edited", "email": "new"}
        })
        store._pydux_slice_definitions = definitions
    module.reconfigure_store = reconfigure
    monkeypatch.setitem(sys.modules, "pydux", types.ModuleType("pydux"))
    toolkit = types.ModuleType("pydux.toolkit")
    monkeypatch.setitem(sys.modules, "pydux.toolkit", toolkit)
    monkeypatch.setitem(sys.modules, "pydux.toolkit.hot_reload", module)

    rollback = prepare_pydux_refresh(context, candidate)
    assert rollback is not None
    assert namespace["store"] is live
    assert live.get_state()["user"]["email"] == "new"
    rollback()
    assert live.get_state() == {"user": {"name": "edited"}}
    assert live._pydux_slice_definitions == {"user": "previous"}
    assert live.notifications == 2


def test_qyro_refresh_is_noop_without_pydux():
    context = SimpleNamespace(_pydux_store=lambda: None)
    candidate = SimpleNamespace(render=lambda: None)
    assert prepare_pydux_refresh(context, candidate) is None
