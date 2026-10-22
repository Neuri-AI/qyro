"""Receive authenticated development source-change messages from the CLI."""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import threading


class DevelopmentChangeReceiver:
    """Passive, source-only child-side coordination endpoint."""

    def __init__(self, on_change):
        self.on_change = on_change
        self._stop = threading.Event()
        self._connection = None
        self._thread = None
        self._last_revision = 0
        self._send_lock = threading.Lock()

    def start(self):
        if self._thread is not None:
            return
        endpoint = os.environ.get("VELTO_RELOAD_ENDPOINT")
        token = os.environ.get("VELTO_RELOAD_TOKEN")
        if not endpoint or not token:
            return
        host, separator, port = endpoint.rpartition(":")
        if host != "127.0.0.1" or not separator or not port.isdecimal():
            return
        try:
            connection = socket.create_connection((host, int(port)), timeout=2)
            connection.sendall((token + "\n").encode())
            connection.settimeout(0.2)
        except OSError:
            return
        self._connection = connection
        self._thread = threading.Thread(target=self._listen, daemon=True,
                                        name="velto-development-messages")
        self._thread.start()

    def _listen(self):
        connection = self._connection
        if connection is None:
            return
        data = bytearray()
        while not self._stop.is_set():
            try:
                chunk = connection.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                return
            if not chunk:
                return
            data.extend(chunk)
            if len(data) > 65536:
                return
            while b"\n" in data:
                raw, _, remainder = data.partition(b"\n")
                data = bytearray(remainder)
                try:
                    message = json.loads(raw)
                    if message.get("version") != 1 or message.get("kind") != "change":
                        continue
                    request_id = message.get("request_id")
                    paths = message.get("paths")
                    if not isinstance(request_id, str) or not request_id.isdecimal():
                        continue
                    revision = int(request_id)
                    if revision <= self._last_revision:
                        continue
                    if not isinstance(paths, list) or not paths or not all(
                        isinstance(path, str) and path and not Path(path).is_absolute()
                        and ".." not in Path(path).parts for path in paths
                    ):
                        continue
                    self._last_revision = revision
                    self.on_change(tuple(paths))
                except (ValueError, TypeError, AttributeError):
                    continue

    def request_restart(self, reason):
        """Ask the authenticated parent to replace this process generation."""
        if reason not in {
            "loaded_native_extension_changed",
            "runtime_bootstrap_changed",
            "backend_changed",
        }:
            raise ValueError("Unsupported process restart reason.")
        message = json.dumps({
            "version": 1, "kind": "restart_request", "reason": reason,
        }, separators=(",", ":")) + "\n"
        with self._send_lock:
            if self._stop.is_set() or self._connection is None:
                return False
            try:
                self._connection.sendall(message.encode("utf-8"))
                return True
            except OSError:
                return False

    def stop(self):
        self._stop.set()
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        self._last_revision = 0
