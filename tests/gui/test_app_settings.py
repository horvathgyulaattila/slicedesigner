"""`load_startup_config()`/`save_current_config()` tesztjei: az
alkalmazás-szintű alapértelmezések be-/kitöltése (ROADMAP Phase 5, ötödik
tétel). Minden teszt a `SETTINGS_PATH`-t egy `tmp_path`-alapú fájlra
monkeypatch-eli — egyetlen teszt sem érhet a valódi felhasználói
home-mappához."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from pytestqt.qtbot import QtBot  # noqa: E402

from slicedesigner.gui import app_settings  # noqa: E402
from slicedesigner.gui.parameter_panel import ParameterPanel  # noqa: E402
from slicedesigner.gui.run_panel import RunPanel  # noqa: E402


def _make_panels(qtbot: QtBot) -> tuple[ParameterPanel, RunPanel]:
    parameter_panel = ParameterPanel()
    run_panel = RunPanel()
    qtbot.addWidget(parameter_panel)
    qtbot.addWidget(run_panel)
    return parameter_panel, run_panel


def _use_settings_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    settings_path = tmp_path / ".slicedesigner" / "settings.json"
    monkeypatch.setattr(app_settings, "SETTINGS_PATH", settings_path)
    return settings_path


def test_load_startup_config_missing_file_does_nothing(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _use_settings_path(monkeypatch, tmp_path)
    parameter_panel, run_panel = _make_panels(qtbot)
    original_mesh_text = parameter_panel.mesh_file_path_label.text()
    original_output_text = run_panel.output_directory_label.text()

    app_settings.load_startup_config(parameter_panel, run_panel)

    assert parameter_panel.mesh_file_path_label.text() == original_mesh_text
    assert run_panel.output_directory_label.text() == original_output_text


def test_save_current_config_creates_parent_directory(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    settings_path = _use_settings_path(monkeypatch, tmp_path)
    parameter_panel, run_panel = _make_panels(qtbot)
    assert not settings_path.parent.exists()

    app_settings.save_current_config(parameter_panel, run_panel)

    assert settings_path.is_file()


def test_round_trip_save_then_load_restores_widget_state(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _use_settings_path(monkeypatch, tmp_path)
    source_panel, source_run_panel = _make_panels(qtbot)
    source_panel.use_dowels_checkbox.setChecked(True)
    source_panel.dowel_diameter_spin.setValue(6.5)
    source_run_panel.output_directory_label.setText("C:/settings-out")
    source_run_panel.dxf_version_combo.setCurrentText("R2013")

    app_settings.save_current_config(source_panel, source_run_panel)

    target_panel, target_run_panel = _make_panels(qtbot)
    app_settings.load_startup_config(target_panel, target_run_panel)

    assert target_panel.use_dowels_checkbox.isChecked() is True
    assert target_panel.dowel_diameter_spin.value() == pytest.approx(6.5)
    assert target_run_panel.output_directory_label.text() == "C:/settings-out"
    assert target_run_panel.dxf_version_combo.currentText() == "R2013"


def test_load_startup_config_corrupt_file_logs_and_does_not_raise(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    settings_path = _use_settings_path(monkeypatch, tmp_path)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text("nem ervenyes json {{{", encoding="utf-8")
    parameter_panel, run_panel = _make_panels(qtbot)
    original_mesh_text = parameter_panel.mesh_file_path_label.text()

    app_settings.load_startup_config(parameter_panel, run_panel)

    assert parameter_panel.mesh_file_path_label.text() == original_mesh_text


def test_save_current_config_write_failure_does_not_raise(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _use_settings_path(monkeypatch, tmp_path)
    parameter_panel, run_panel = _make_panels(qtbot)

    def _raise(*args: object, **kwargs: object) -> None:
        raise OSError("teszt: írásvédett célútvonal")

    monkeypatch.setattr(app_settings.persistence, "save_project_config", _raise)

    app_settings.save_current_config(parameter_panel, run_panel)
