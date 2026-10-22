"""Authenticated change message processing without a GUI toolkit."""
import json
import socket
import threading
import time

from qyro.client.development_changes import DevelopmentChangeReceiver


def test_receives_valid_changes_and_ignores_replays_or_traversal():
    left, right = socket.socketpair()
    received = []
    receiver = DevelopmentChangeReceiver(received.append)
    receiver._connection = left
    left.settimeout(0.05)
    receiver._thread = threading.Thread(target=receiver._listen, daemon=True)
    receiver._thread.start()
    try:
        frames = [
            {"version": 1, "kind": "change", "request_id": "1",
             "paths": ["views/main.py"]},
            {"version": 1, "kind": "change", "request_id": "1",
             "paths": ["views/repeated.py"]},
            {"version": 1, "kind": "change", "request_id": "2",
             "paths": ["../outside.py"]},
            {"version": 2, "kind": "change", "request_id": "3",
             "paths": ["views/invalid.py"]},
            {"version": 1, "kind": "change", "request_id": "4",
             "paths": ["styles/main.css"]},
        ]
        for message in frames:
            right.sendall((json.dumps(message) + "\n").encode())
        deadline = time.monotonic() + 2
        while len(received) < 2 and time.monotonic() < deadline:
            time.sleep(0.02)
        assert received == [("views/main.py",), ("styles/main.css",)]
    finally:
        receiver.stop()
        right.close()


def test_missing_endpoint_never_starts_receiver(monkeypatch):
    monkeypatch.delenv("VELTO_RELOAD_ENDPOINT", raising=False)
    monkeypatch.delenv("VELTO_RELOAD_TOKEN", raising=False)
    receiver = DevelopmentChangeReceiver(lambda _: None)
    receiver.start()
    assert receiver._thread is None
    receiver.stop()


def test_frozen_context_never_allocates_notification_transport(monkeypatch):
    from qyro.client.velto_context import VeltoContext

    monkeypatch.setenv("VELTO_DEVELOPMENT", "1")
    monkeypatch.setenv("VELTO_RELOAD_ENDPOINT", "127.0.0.1:40000")
    monkeypatch.setenv("VELTO_RELOAD_TOKEN", "test")
    monkeypatch.setattr(VeltoContext, "_global_boot_info", {"is_frozen": True})
    context = object.__new__(VeltoContext)
    context._development_receiver = None
    context._start_development_receiver()
    assert context._development_receiver is None
