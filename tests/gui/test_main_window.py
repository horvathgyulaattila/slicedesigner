"""Smoke teszt: a `MainWindow` szerkezeti váza hibamentesen felépül, a
három összeépítési kapcsoló show/hide viselkedése működik, és a
"Futtatás" gomb ténylegesen bekötve fut le (prompt 8. szakasz)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PySide6.QtGui import QAction  # noqa: E402
from PySide6.QtWidgets import QMenu  # noqa: E402
from pytestqt.qtbot import QtBot  # noqa: E402

from slicedesigner.gui.main_window import MainWindow  # noqa: E402
from slicedesigner.project.exceptions import PipelineConfigurationError  # noqa: E402


def _get_file_menu(main_window: MainWindow) -> QMenu:
    """A 'Fájl' `QMenu` megkeresése `findChildren()`-nel.

    `main_window.menuBar().actions()[0].menu()` — a szokásos
    `QAction.menu()` út — ezen a PySide6-build-en (6.11.1) egy, a
    VTK/offscreen tesztstabilitástól független, önmagában is
    reprodukálható shiboken-hibát vált ki (`RuntimeError: Internal C++
    object (PySide6.QtWidgets.QMenu) already deleted.`, egy minimális,
    `QMainWindow.menuBar().addMenu()` + `.actions()[0].menu()` szkripttel
    is előidézhető, natív "windows" platform alatt is). A
    `findChildren(QMenu)` ugyanazt a widgetet megbízhatóan, ép állapotban
    adja vissza.
    """
    for menu in main_window.findChildren(QMenu):
        if menu.title() == "Fájl":
            return menu
    raise AssertionError("'Fájl' menü nem található.")


def _get_file_menu_action(main_window: MainWindow, text: str) -> QAction:
    file_menu = _get_file_menu(main_window)
    for action in file_menu.actions():
        if action.text() == text:
            return action
    raise AssertionError(f"'Fájl' menü akció nem található: {text!r}")


@pytest.fixture
def main_window(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[MainWindow]:
    """`MainWindow` a teszthez — a `QtInteractor` explicit `close()`-a
    nélkül a beépített auto-update időzítője egy már törölt render-
    kontextusra próbál renderelni egy későbbi teszt event-loop
    feldolgozásakor, ami natív összeomlást (access violation) okoz.

    A `SETTINGS_PATH` minden teszthez egy `tmp_path`-alapú, nem létező
    fájlra van állítva, hogy a `MainWindow.__init__` végén futó
    `app_settings.load_startup_config()` (és a bezáráskor futó
    `save_current_config()`) sose érjen a valódi felhasználói
    home-mappához."""
    monkeypatch.setattr(
        "slicedesigner.gui.app_settings.SETTINGS_PATH", tmp_path / "settings.json"
    )
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    yield window
    window.preview_panel.plotter.close()


def test_main_window_builds_three_areas(main_window: MainWindow) -> None:
    assert main_window.parameter_panel is not None
    assert main_window.preview_panel is not None
    assert main_window.run_panel is not None

    assert hasattr(main_window.preview_panel, "plotter")
    assert hasattr(main_window.run_panel, "run_button")
    assert hasattr(main_window.run_panel, "status_log")


def test_dowel_switch_toggles_group_visibility(main_window: MainWindow) -> None:
    panel = main_window.parameter_panel
    assert not panel.dowel_group.isVisible()

    panel.use_dowels_checkbox.setChecked(True)
    assert panel.dowel_group.isVisible()

    panel.use_dowels_checkbox.setChecked(False)
    assert not panel.dowel_group.isVisible()


def test_spacer_switch_toggles_group_visibility(main_window: MainWindow) -> None:
    panel = main_window.parameter_panel
    assert not panel.gap_group.isVisible()

    panel.use_spacers_checkbox.setChecked(True)
    assert panel.gap_group.isVisible()


def test_backplate_switch_toggles_group_visibility(main_window: MainWindow) -> None:
    panel = main_window.parameter_panel
    assert not panel.backplate_group.isVisible()

    panel.use_backplate_checkbox.setChecked(True)
    assert panel.backplate_group.isVisible()


def test_run_button_missing_mesh_shows_configuration_error(
    main_window: MainWindow,
) -> None:
    main_window.run_panel.run_button.click()

    assert "Konfigurációs hiba" in main_window.run_panel.status_log.toPlainText()
    assert main_window.run_panel.run_button.isEnabled()


def test_run_button_success_updates_status_log(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_slice_set = SimpleNamespace(slice_count=7)
    fake_result = SimpleNamespace(
        slice_set=fake_slice_set,
        exports=(object(), object()),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_builder.build_pipeline_config",
        lambda parameter_panel, run_panel: object(),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.run_pipeline",
        lambda config: fake_result,
    )
    show_sliced_assembly_calls = []
    monkeypatch.setattr(
        main_window.preview_panel,
        "show_sliced_assembly",
        show_sliced_assembly_calls.append,
    )

    main_window.run_panel.run_button.click()

    status_text = main_window.run_panel.status_log.toPlainText()
    assert "sikeres" in status_text
    assert "7" in status_text
    assert "2" in status_text
    assert main_window.run_panel.run_button.isEnabled()
    assert show_sliced_assembly_calls == [fake_slice_set]


def test_run_button_engine_error_shows_processing_error(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    from slicedesigner.engines.exceptions import InvalidMeshError

    def _raise_invalid_mesh(config: object) -> None:
        raise InvalidMeshError("teszt-hiba")

    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_builder.build_pipeline_config",
        lambda parameter_panel, run_panel: object(),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.run_pipeline",
        _raise_invalid_mesh,
    )

    main_window.run_panel.run_button.click()

    status_text = main_window.run_panel.status_log.toPlainText()
    assert "Hiba a feldolgozás során" in status_text
    assert main_window.run_panel.run_button.isEnabled()


def test_mesh_file_selected_shows_mesh_preview(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_mesh = object()
    preview_calls = []
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.import_mesh_preview",
        lambda params: fake_mesh,
    )
    monkeypatch.setattr(main_window.preview_panel, "show_mesh", preview_calls.append)

    main_window.parameter_panel.mesh_file_selected.emit("C:/in/mesh.stl")

    assert preview_calls == [fake_mesh]
    assert main_window.run_panel.status_log.toPlainText() == ""


def test_mesh_file_selected_engine_error_shows_status_message(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    from slicedesigner.engines.exceptions import InvalidMeshError

    def _raise_invalid_mesh(params: object) -> None:
        raise InvalidMeshError("teszt-hiba")

    monkeypatch.setattr(
        "slicedesigner.gui.main_window.import_mesh_preview", _raise_invalid_mesh
    )
    preview_calls = []
    monkeypatch.setattr(main_window.preview_panel, "show_mesh", preview_calls.append)

    main_window.parameter_panel.mesh_file_selected.emit("C:/in/mesh.stl")

    status_text = main_window.run_panel.status_log.toPlainText()
    assert "Hiba az előnézet betöltése során" in status_text
    assert preview_calls == []
    assert main_window.run_panel.run_button.isEnabled()


def test_file_menu_has_save_and_open_actions(main_window: MainWindow) -> None:
    file_menu = _get_file_menu(main_window)
    action_texts = [action.text() for action in file_menu.actions()]
    assert "Projekt mentése..." in action_texts
    assert "Projekt megnyitása..." in action_texts


def test_save_project_cancelled_does_nothing(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: ("", ""),
    )
    save_calls = []
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.persistence.save_project_config",
        lambda *args, **kwargs: save_calls.append(True),
    )

    _get_file_menu_action(main_window, "Projekt mentése...").trigger()

    assert save_calls == []
    assert main_window.run_panel.status_log.toPlainText() == ""


def test_save_project_success_updates_status_log(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: ("C:/out/project.json", ""),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_builder.build_pipeline_config",
        lambda parameter_panel, run_panel, require_complete=False: object(),
    )
    save_calls = []
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.persistence.save_project_config",
        lambda config, file_path: save_calls.append(file_path),
    )

    _get_file_menu_action(main_window, "Projekt mentése...").trigger()

    assert save_calls == ["C:/out/project.json"]
    assert "Projekt elmentve." in main_window.run_panel.status_log.toPlainText()


def test_save_project_configuration_error_shows_message(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise(*args: object, **kwargs: object) -> None:
        raise PipelineConfigurationError("teszt-hiba")

    monkeypatch.setattr(
        "slicedesigner.gui.main_window.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: ("C:/out/project.json", ""),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_builder.build_pipeline_config",
        _raise,
    )

    _get_file_menu_action(main_window, "Projekt mentése...").trigger()

    assert "Konfigurációs hiba" in main_window.run_panel.status_log.toPlainText()


def test_open_project_cancelled_does_nothing(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: ("", ""),
    )
    load_calls = []
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.persistence.load_project_config",
        lambda *args, **kwargs: load_calls.append(True),
    )

    _get_file_menu_action(main_window, "Projekt megnyitása...").trigger()

    assert load_calls == []
    assert main_window.run_panel.status_log.toPlainText() == ""


def test_open_project_success_without_overrides_shows_no_warning(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_config = object()
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: ("C:/in/project.json", ""),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.persistence.load_project_config",
        lambda file_path: fake_config,
    )
    apply_calls = []
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_loader.apply_pipeline_config",
        lambda config, parameter_panel, run_panel: apply_calls.append(config) or 0,
    )

    _get_file_menu_action(main_window, "Projekt megnyitása...").trigger()

    assert apply_calls == [fake_config]
    status_text = main_window.run_panel.status_log.toPlainText()
    assert "Projekt betöltve." in status_text
    assert "Figyelem" not in status_text


def test_open_project_with_overrides_shows_warning(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: ("C:/in/project.json", ""),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.persistence.load_project_config",
        lambda file_path: object(),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_loader.apply_pipeline_config",
        lambda config, parameter_panel, run_panel: 3,
    )

    _get_file_menu_action(main_window, "Projekt megnyitása...").trigger()

    status_text = main_window.run_panel.status_log.toPlainText()
    assert "Projekt betöltve." in status_text
    assert "Figyelem: 3" in status_text


def test_open_project_configuration_error_shows_message(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise(file_path: str) -> None:
        raise PipelineConfigurationError("teszt-hiba")

    monkeypatch.setattr(
        "slicedesigner.gui.main_window.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: ("C:/in/project.json", ""),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.persistence.load_project_config",
        _raise,
    )

    _get_file_menu_action(main_window, "Projekt megnyitása...").trigger()

    assert "Konfigurációs hiba" in main_window.run_panel.status_log.toPlainText()


def test_close_event_saves_current_config(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    save_calls = []
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.app_settings.save_current_config",
        lambda parameter_panel, run_panel: save_calls.append(
            (parameter_panel, run_panel)
        ),
    )

    main_window.close()

    assert save_calls == [(main_window.parameter_panel, main_window.run_panel)]


def test_close_event_succeeds_even_if_settings_save_fails(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise(*args: object, **kwargs: object) -> None:
        raise OSError("teszt: írásvédett célútvonal")

    monkeypatch.setattr(
        "slicedesigner.gui.app_settings.persistence.save_project_config",
        _raise,
    )

    main_window.close()

    assert main_window.isVisible() is False
