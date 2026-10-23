"""Opt-in bounded Pydux data transfer between development child generations.

The supervisor owns the private directory; Qyro only writes or consumes the
state data when its application explicitly enables restart preservation.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import tempfile

_LOG = logging.getLogger("qyro.development")
_MAX_BYTES = 1_048_576


def _state_path(context, option: str):
    if context.is_frozen or os.environ.get("VELTO_DEVELOPMENT") != "1":
        return None
    settings = context.app_settings.get("hot_reload", {})
    if not isinstance(settings, dict) or settings.get("preserve_state") is not True:
        return None
    policy = settings.get("state", {})
    if not isinstance(policy, dict) or policy.get(option) is not True:
        return None
    configured = os.environ.get("VELTO_RESTART_STATE_PATH")
    if not configured:
        return None
    candidate = Path(configured)
    if not candidate.is_absolute() or not candidate.parent.is_dir():
        return None
    return candidate


def capture_restart_state(context):
    """Snapshot only compatible JSON store data; never persist live objects."""
    target = _state_path(context, "snapshot_on_restart")
    if target is None:
        return False
    try:
        from pydux.devtools.state_snapshot import capture_store_state

        store = context._pydux_store()
        if store is None:
            return False
        payload = json.dumps(
            {"version": 1, "store": capture_store_state(store)},
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
        if len(payload) > _MAX_BYTES:
            raise ValueError("Development restart state exceeds the size limit.")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=target.parent, prefix=".snapshot-", delete=False
            ) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
            temporary.replace(target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return True
    except (OSError, ValueError, TypeError, ImportError) as exc:
        _LOG.warning("Development restart snapshot rejected: %s", exc)
        return False


def restore_restart_state(context, store):
    """Consume the snapshot once, before the new root mounts or subscribes."""
    target = _state_path(context, "restore_on_restart")
    if target is None or store is None:
        return False
    try:
        try:
            with target.open("rb") as stream:
                payload = stream.read(_MAX_BYTES + 1)
        except FileNotFoundError:
            return False
        if len(payload) > _MAX_BYTES:
            raise ValueError("Development restart snapshot is too large.")
        data = json.loads(payload)
        if (type(data) is not dict or set(data) != {"version", "store"}
                or type(data["version"]) is not int or data["version"] != 1):
            raise ValueError("Invalid development restart state.")
        from pydux.devtools.state_snapshot import restore_store_state

        restore_store_state(store, data["store"])
        return True
    except (ValueError, TypeError, KeyError, OSError, ImportError) as exc:
        _LOG.warning("Development restart restoration rejected: %s", exc)
        return False
    finally:
        # Even invalid or incompatible data cannot be retried indefinitely.
        target.unlink(missing_ok=True)
