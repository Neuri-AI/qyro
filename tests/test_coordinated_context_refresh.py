"""Exercise coordinated development refresh through the actual VeltoContext mount."""
from __future__ import annotations

from pathlib import Path

from qyro.client.velto_context import VeltoContext
from qyro.domain.entities import AppMetadata


class Demo(VeltoContext):
    def render(self):
        from psx import Text, use_state\nfrom psx.core.vnode import Box
        count, _ = use_state(23)
        return Box(Text(f"before:{count}"))


def test_context_applies_authored_source_change_without_recreating_native_host(
    tmp_path, monkeypatch,
):
    from psx.renderers.headless import HeadlessRenderer

    source = tmp_path / "main.py"
    source.write_text(
        "from psx import Text, use_state\nfrom psx.core.vnode import Box\n"
        "class Demo:\n"
        "    def render(self):\n"
        "        count, _ = use_state(23)\n"
        "        return Box(Text(f'after:{count}'))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PSX_SOURCE_ENTRY", str(source))
    monkeypatch.setenv("VELTO_PROJECT_ROOT", str(tmp_path))
    previous_container = VeltoContext._global_container
    previous_boot = VeltoContext._global_boot_info
    VeltoContext._global_container = object()
    VeltoContext._global_boot_info = {
        "metadata": AppMetadata(app_name="Refresh test", raw_settings={"framework": "pyside6"}),
        "is_frozen": False,
    }
    # Box is the stable host used by Qyro. Unlike Flex, it does not demand
    # a Cinnamon viewport or a numerical layout engine in headless tests.
    renderer = HeadlessRenderer()
    monkeypatch.setattr(Demo, "_create_renderer", lambda *_: renderer)
    monkeypatch.setattr(Demo, "_present", lambda *_: None)
    context = None
    try:
        context = Demo()
        context.mount()
        native_host = context.app.reconciler.root.native_handle()
        assert native_host.children[0].props["value"] == "before:23"
        context._apply_development_change(("main.py",))
        assert context.app.reconciler.root.native_handle() is native_host
        assert native_host.children[0].props["value"] == "after:23"
    finally:
        if context is not None:
            context.unmount()
        VeltoContext._global_container = previous_container
        VeltoContext._global_boot_info = previous_boot


def test_context_remounts_hook_incompatible_root_and_keeps_native_host(
    tmp_path, monkeypatch,
):
    from psx.renderers.headless import HeadlessRenderer

    source = tmp_path / "main.py"
    source.write_text(
        "from psx import Text, use_state, use_ref\nfrom psx.core.vnode import Box\n"
        "class Demo:\n"
        "    def render(self):\n"
        "        count, _ = use_state(23)\n"
        "        use_ref()\n"
        "        return Box(Text(f'remounted:{count}'))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PSX_SOURCE_ENTRY", str(source))
    monkeypatch.setenv("VELTO_PROJECT_ROOT", str(tmp_path))
    previous_container = VeltoContext._global_container
    previous_boot = VeltoContext._global_boot_info
    VeltoContext._global_container = object()
    VeltoContext._global_boot_info = {
        "metadata": AppMetadata(app_name="Remount test", raw_settings={"framework": "pyside6"}),
        "is_frozen": False,
    }
    # Box is the stable host used by Qyro. Unlike Flex, it does not demand
    # a Cinnamon viewport or a numerical layout engine in headless tests.
    renderer = HeadlessRenderer()
    monkeypatch.setattr(Demo, "_create_renderer", lambda *_: renderer)
    monkeypatch.setattr(Demo, "_present", lambda *_: None)
    context = None
    try:
        context = Demo()
        context.mount()
        previous_root = context.app.reconciler.root
        host = previous_root.native_handle()
        context._apply_development_change(("main.py",))
        assert previous_root.disposed
        assert context.app.reconciler.root is not previous_root
        assert context.app.reconciler.root.native_handle() is host
        assert host.children[0].props["value"] == "remounted:23"
    finally:
        if context is not None:
            context.unmount()
        VeltoContext._global_container = previous_container
        VeltoContext._global_boot_info = previous_boot
