"""Qyro-owned coordination between source refresh and the Pydux state adapter.

This module does not watch files or import native widgets. It is invoked by
VeltoContext on the renderer's UI thread after a candidate has been loaded
and before PSX reconciles its view.
"""
from __future__ import annotations

import copy
from typing import Any, Callable


def prepare_pydux_refresh(context: Any, candidate: type) -> Callable[[], None] | None:
    """Reconcile freshly evaluated Pydux slices into the live store.

    Returns a rollback callback used when PSX rejects a candidate. The candidate
    module may contain a disposable temporary store, but subscribers and the
    inspector remain attached exclusively to the original live store.
    """
    live_store = context._pydux_store()
    if live_store is None:
        return None

    globals_dict = getattr(candidate.render, "__globals__", {})
    candidates = {
        id(value): value
        for value in globals_dict.values()
        if value is not live_store
        and isinstance(getattr(value, "_pydux_slice_definitions", None), dict)
        and callable(getattr(value, "get_state", None))
    }
    if not candidates:
        return None
    if len(candidates) != 1:
        raise RuntimeError("Cannot hot-reload multiple candidate Pydux stores")

    new_store = next(iter(candidates.values()))
    definitions = new_store._pydux_slice_definitions

    try:
        from pydux.toolkit.hot_reload import reconfigure_store
    except ImportError as exc:
        raise RuntimeError("Pydux installed without hot-reload state reconciliation support") from exc

    original_reducer = live_store._reducer
    original_state = copy.deepcopy(live_store.get_state())
    original_definitions = dict(getattr(live_store, "_pydux_slice_definitions", {}))
    reconfigure_store(live_store, definitions)

    # The candidate's lexical store must reference the preserved live store,
    # not its temporary configure_store() result.
    for name, value in tuple(globals_dict.items()):
        if value is new_store:
            globals_dict[name] = live_store

    def rollback() -> None:
        live_store.replace_reducer(original_reducer, original_state)
        live_store._pydux_slice_definitions = original_definitions
        inspector = getattr(live_store, "inspector", None)
        publish = getattr(inspector, "_broadcast_snapshot", None)
        if callable(publish):
            publish()

    return rollback
