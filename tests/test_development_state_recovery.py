"""Recover compatible Pydux state without losing the mounted root on rejected edits."""
from types import SimpleNamespace

from pydux import Action, Store
from qyro.client.velto_context import VeltoContext


def reducer(state, action):
    if action.type == "advance":
        return {"count": state["count"] + 1}
    return state


def context_with_store(store, *, preserve=True):
    ctx = object.__new__(VeltoContext)
    ctx._mounted = True
    ctx._app = SimpleNamespace(
        reconciler=SimpleNamespace(_coordinated_remount_applied=False)
    )
    ctx._pydux_store = lambda: store
    ctx._test_settings = {"hot_reload": {"preserve_state": preserve}}
    return ctx


def test_failed_refresh_restores_store_and_updates_subscribers(tmp_path, monkeypatch):
    import psx.devtools.coordinated_refresh as refresh
    store = Store(reducer, {"count": 1})
    events = []
    store.select(lambda s: s["count"], events.append)
    ctx = context_with_store(store)
    monkeypatch.setattr(VeltoContext, "app_settings", property(lambda self: self._test_settings))
    entry = tmp_path / "main.py"
    entry.write_text("x = 1", encoding="utf-8")
    monkeypatch.setenv("PSX_SOURCE_ENTRY", str(entry))
    def fail(*_):
        store.dispatch(Action("advance"))
        raise SyntaxError("invalid source")
    monkeypatch.setattr(refresh, "refresh_context_source", fail)
    ctx._apply_development_change(("main.py",))
    assert store.get_state() == {"count": 1}
    assert events == [2, 1]


def test_committed_remount_is_not_rolled_back_after_cleanup_failure(tmp_path, monkeypatch):
    import psx.devtools.coordinated_refresh as refresh
    store = Store(reducer, {"count": 1})
    ctx = context_with_store(store)
    monkeypatch.setattr(VeltoContext, "app_settings", property(lambda self: self._test_settings))
    entry = tmp_path / "main.py"
    entry.write_text("x = 1", encoding="utf-8")
    monkeypatch.setenv("PSX_SOURCE_ENTRY", str(entry))
    def fail(*_):
        store.dispatch(Action("advance"))
        ctx._app.reconciler._coordinated_remount_applied = True
        raise RuntimeError("effect cleanup failed")
    monkeypatch.setattr(refresh, "refresh_context_source", fail)
    ctx._apply_development_change(("main.py",))
    assert store.get_state() == {"count": 2}


def test_disabled_state_preservation_never_reverts_dispatch(tmp_path, monkeypatch):
    import psx.devtools.coordinated_refresh as refresh
    store = Store(reducer, {"count": 1})
    ctx = context_with_store(store, preserve=False)
    monkeypatch.setattr(VeltoContext, "app_settings", property(lambda self: self._test_settings))
    entry = tmp_path / "main.py"
    entry.write_text("x = 1", encoding="utf-8")
    monkeypatch.setenv("PSX_SOURCE_ENTRY", str(entry))
    def fail(*_):
        store.dispatch(Action("advance"))
        raise RuntimeError("failed")
    monkeypatch.setattr(refresh, "refresh_context_source", fail)
    ctx._apply_development_change(("main.py",))
    assert store.get_state() == {"count": 2}
