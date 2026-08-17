"""`MainWindow`/`_MeshGenerationWorker` integrációs tesztjei: a
"Generálás" gomb (`ParameterPanel.generate_mesh_requested`) háttérszálas
feldolgozása (ADR-0017, prompt 2.2 szakasz)."""

from __future__ import annotations

import os
import threading
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from pytestqt.qtbot import QtBot  # noqa: E402

from slicedesigner.engines.mesh_import import BoundingBox, Mesh  # noqa: E402
from slicedesigner.gui.main_window import MainWindow  # noqa: E402


@pytest.fixture
def main_window(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[MainWindow]:
    """L. `tests/gui/test_main_window.py::main_window` docstringje — azonos
    indok (`QtInteractor` auto-update-timer, elkülönített `SETTINGS_PATH`)."""
    monkeypatch.setattr(
        "slicedesigner.gui.app_settings.SETTINGS_PATH", tmp_path / "settings.json"
    )
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    yield window
    window.preview_panel.plotter.close()


def _make_stub_mesh() -> Mesh:
    return Mesh(
        vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        triangles=((0, 1, 2),),
        source_path=None,
        bounding_box=BoundingBox(min=(0.0, 0.0, 0.0), max=(1.0, 1.0, 0.0)),
        is_valid=True,
        warnings=(),
    )


def _make_stub_descriptor(display_name: str = "Stub Generator") -> SimpleNamespace:
    """`_on_generate_mesh_requested()` kizárólag a `display_name` mezőt
    olvassa a `descriptor`-ból (a tényleges `build()`-et a mockolt
    `build_mesh()` helyettesíti) — egy `SimpleNamespace` elegendő."""
    return SimpleNamespace(display_name=display_name)


def test_generate_mesh_requested_success_updates_generated_mesh_and_preview(
    main_window: MainWindow, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    mesh = _make_stub_mesh()
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.build_mesh",
        lambda descriptor, values: mesh,
    )
    show_mesh_calls: list[object] = []
    monkeypatch.setattr(main_window.preview_panel, "show_mesh", show_mesh_calls.append)
    descriptor = _make_stub_descriptor()

    main_window.parameter_panel.generate_mesh_requested.emit(descriptor, {"width": 2.0})
    qtbot.waitUntil(lambda: main_window._mesh_generation_worker is None, timeout=2000)

    assert main_window.parameter_panel.generated_mesh is mesh
    assert show_mesh_calls == [mesh]
    assert "sikeres" in main_window.run_panel.status_log.toPlainText()
    assert main_window.run_panel.run_button.isEnabled()
    assert main_window._save_action.isEnabled()
    assert main_window._open_action.isEnabled()


def test_generate_mesh_requested_failure_clears_generated_mesh(
    main_window: MainWindow, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    main_window.parameter_panel.generated_mesh = _make_stub_mesh()

    def _raise(descriptor: object, values: object) -> None:
        raise RuntimeError("teszt-hiba")

    monkeypatch.setattr("slicedesigner.gui.main_window.build_mesh", _raise)
    descriptor = _make_stub_descriptor()

    main_window.parameter_panel.generate_mesh_requested.emit(descriptor, {})
    qtbot.waitUntil(lambda: main_window._mesh_generation_worker is None, timeout=2000)

    assert main_window.parameter_panel.generated_mesh is None
    assert "Hiba a generálás során" in main_window.run_panel.status_log.toPlainText()
    assert main_window.run_panel.run_button.isEnabled()
    assert main_window._save_action.isEnabled()
    assert main_window._open_action.isEnabled()


def test_generate_and_run_buttons_disabled_while_generating(
    main_window: MainWindow, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    release_event = threading.Event()
    mesh = _make_stub_mesh()

    def _blocking_build_mesh(descriptor: object, values: object) -> Mesh:
        assert release_event.wait(timeout=2.0)
        return mesh

    monkeypatch.setattr(
        "slicedesigner.gui.main_window.build_mesh", _blocking_build_mesh
    )
    monkeypatch.setattr(main_window.preview_panel, "show_mesh", lambda mesh: None)
    descriptor = _make_stub_descriptor()

    main_window.parameter_panel.generate_mesh_requested.emit(descriptor, {})

    assert main_window._mesh_generation_worker is not None
    assert not main_window.run_panel.run_button.isEnabled()
    assert not main_window._save_action.isEnabled()
    assert not main_window._open_action.isEnabled()
    generate_button = main_window.parameter_panel.generate_mesh_button
    assert generate_button is not None
    assert not generate_button.isEnabled()

    release_event.set()
    qtbot.waitUntil(lambda: main_window._mesh_generation_worker is None, timeout=2000)

    assert main_window.run_panel.run_button.isEnabled()
    assert main_window._save_action.isEnabled()
    assert main_window._open_action.isEnabled()
    assert generate_button.isEnabled()


def test_close_event_rejects_close_while_mesh_generation_running(
    main_window: MainWindow, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A `closeEvent()` a MeshSource generálás háttérszála alatt is védi
    az ablakbezárást (ADR-0017) — ugyanaz a minta, mint
    `test_main_window.py::test_close_event_rejects_close_while_pipeline_running`."""
    release_event = threading.Event()
    mesh = _make_stub_mesh()

    def _blocking_build_mesh(descriptor: object, values: object) -> Mesh:
        assert release_event.wait(timeout=2.0)
        return mesh

    monkeypatch.setattr(
        "slicedesigner.gui.main_window.build_mesh", _blocking_build_mesh
    )
    monkeypatch.setattr(main_window.preview_panel, "show_mesh", lambda mesh: None)
    save_calls: list[bool] = []
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.app_settings.save_current_config",
        lambda parameter_panel, run_panel: save_calls.append(True),
    )
    descriptor = _make_stub_descriptor()

    main_window.parameter_panel.generate_mesh_requested.emit(descriptor, {})
    assert main_window._mesh_generation_worker is not None

    main_window.close()

    assert main_window.isVisible()
    assert save_calls == []
    assert "Futtatás folyamatban" in main_window.run_panel.status_log.toPlainText()

    release_event.set()
    qtbot.waitUntil(lambda: main_window._mesh_generation_worker is None, timeout=2000)
