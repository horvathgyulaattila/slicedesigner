"""Smoke teszt: a `MainWindow` szerkezeti váza hibamentesen felépül, a
három összeépítési kapcsoló show/hide viselkedése működik, és a
"Futtatás" gomb ténylegesen bekötve fut le (prompt 8. szakasz)."""

from __future__ import annotations

import os
import threading
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QAction  # noqa: E402
from PySide6.QtWidgets import QMenu, QSplitter  # noqa: E402
from pytestqt.qtbot import QtBot  # noqa: E402

from slicedesigner.gui.examples_dialog import ExampleInfo  # noqa: E402
from slicedesigner.gui.main_window import MainWindow  # noqa: E402
from slicedesigner.project.exceptions import PipelineConfigurationError  # noqa: E402


def _select_tab(panel: object, title: str) -> None:
    """A Dowel/Gap/Backplate fülek show/hide-viselkedése csak akkor
    figyelhető meg `isVisible()`-lel, ha a fülük a `QTabWidget` aktuális
    (megjelenített) lapja — egy nem-aktuális fülön lévő widget mindig
    láthatatlan, függetlenül a saját `setVisible()`-állapotától (prompt
    7.4 GUI-átalakítás)."""
    for index in range(panel.count()):
        if panel.tabText(index) == title:
            panel.setCurrentIndex(index)
            return
    raise AssertionError(f"Fül nem található: {title!r}")


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


def _mock_show_sliced_assembly_succeeds(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> list[tuple[object, ...]]:
    """`PreviewPanel.show_sliced_assembly()` mockolása: az argumentumokat
    rögzíti, és — a valódi (ADR-0011 óta háttérszálas) geometria-építés/
    renderelés nélkül — azonnal kibocsátja az `assembly_render_succeeded`
    jelzést.

    A `MainWindow._finish_run()`-t immár ez a jelzés indítja el (l.
    `MainWindow.__init__`), nem közvetlenül `_on_pipeline_succeeded()` —
    enélkül a mockolt hívással a jelzés-lánc megszakadna, és a
    `qtbot.waitUntil(...)`-alapú tesztek (amik a Futtatás-gomb újra-
    engedélyezését várják) örökre elakadnának. `test_main_window.py`
    a `preview_panel` fixture dokumentált VTK/offscreen-instabilitása
    miatt sosem hívja a valódi `show_sliced_assembly()`-t — ez a mock a
    `MainWindow`-oldali orchestrálást attól függetlenül teszteli."""
    calls: list[tuple[object, ...]] = []

    def _fake(*args: object) -> None:
        calls.append(args)
        main_window.preview_panel.assembly_render_succeeded.emit()

    monkeypatch.setattr(main_window.preview_panel, "show_sliced_assembly", _fake)
    return calls


def _mock_show_nests(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> list[tuple[object, ...]]:
    """`PreviewPanel.show_nests()` mockolása: az argumentumokat rögzíti,
    a valódi (`Nest`-objektumok mezőire — `material_id`/`sheet_count` —
    támaszkodó) feldolgozás nélkül, hogy a teszt-fixture-ök egyszerű,
    nem valódi `Nest`-eket (pl. `object()`) is átadhassanak."""
    calls: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        main_window.preview_panel, "show_nests", lambda *args: calls.append(args)
    )
    return calls


def _fake_pipeline_config(
    *, material_definitions: tuple[object, ...] = ()
) -> SimpleNamespace:
    """A `_PipelineWorker.config` (`self._worker.config`) minimális,
    `_on_pipeline_succeeded()` által ténylegesen olvasott hamisítványa —
    `nesting.material_definitions` (2D export-előnézet) és `backplate`
    (Backplate 3D-előnézet)."""
    return SimpleNamespace(
        nesting=SimpleNamespace(material_definitions=material_definitions),
        backplate=None,
    )


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
    assert hasattr(main_window.run_panel, "export_dxf_button")


def test_parameter_panel_export_tab_contains_run_panel_export_widget(
    main_window: MainWindow,
) -> None:
    """A `RunPanel.export_settings_widget` ténylegesen a `ParameterPanel`
    Export fülébe kerül (prompt 2.4 szakasz, konstrukciós sorrend)."""
    panel = main_window.parameter_panel
    _select_tab(panel, "Export")
    export_scroll_area = panel.currentWidget()
    assert export_scroll_area.isAncestorOf(main_window.run_panel.export_settings_widget)


def test_action_container_is_at_the_bottom_of_the_parameter_panel_column(
    main_window: MainWindow,
) -> None:
    """A Futtatás/DXF Export gombok és a folyamatjelző a `ParameterPanel`
    oszlop aljára kerülnek."""
    action_container = main_window.run_panel.action_container
    left_column = action_container.parentWidget()
    assert left_column is not None

    layout = left_column.layout()
    assert layout is not None
    assert layout.indexOf(main_window.parameter_panel) < layout.indexOf(
        action_container
    )


def test_status_log_is_in_its_own_resizable_splitter_pane(
    main_window: MainWindow,
) -> None:
    """A log/állapot-terület (`status_log`) egy önálló, húzással
    állítható magasságú `QSplitter`-panelben jelenik meg, a `MainWindow`
    teljes szélességében (nem a bal oszlopban)."""
    status_log = main_window.run_panel.status_log
    outer_splitter = status_log.parentWidget()
    assert isinstance(outer_splitter, QSplitter)
    assert outer_splitter.orientation() == Qt.Orientation.Vertical
    assert outer_splitter.indexOf(status_log) >= 0

    # A `status_log` nincs a bal (paraméter-panel) oszlop leszármazottja.
    assert not main_window.parameter_panel.isAncestorOf(status_log)


def test_export_dxf_button_initially_disabled(main_window: MainWindow) -> None:
    assert main_window._last_nests is None
    assert not main_window.run_panel.export_dxf_button.isEnabled()


def test_dowel_switch_toggles_group_visibility(main_window: MainWindow) -> None:
    panel = main_window.parameter_panel
    _select_tab(panel, "Dowel")
    assert not panel.dowel_group.isVisible()

    panel.use_dowels_checkbox.setChecked(True)
    assert panel.dowel_group.isVisible()

    panel.use_dowels_checkbox.setChecked(False)
    assert not panel.dowel_group.isVisible()


def test_spacer_switch_toggles_group_visibility(main_window: MainWindow) -> None:
    panel = main_window.parameter_panel
    _select_tab(panel, "Gap")
    assert not panel.gap_group.isVisible()

    panel.use_spacers_checkbox.setChecked(True)
    assert panel.gap_group.isVisible()


def test_backplate_switch_toggles_group_visibility(main_window: MainWindow) -> None:
    panel = main_window.parameter_panel
    _select_tab(panel, "Backplate")
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
    main_window: MainWindow, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_slice_set = SimpleNamespace(slice_count=7)
    fake_dowel_positions = (object(),)
    fake_spacers = (object(),)
    fake_nests = (object(), object())
    fake_result = SimpleNamespace(
        slice_set=fake_slice_set,
        dowel_positions=fake_dowel_positions,
        spacers=fake_spacers,
        backplate=None,
        nests=fake_nests,
    )
    fake_material_definitions = (object(),)
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_builder.build_pipeline_config",
        lambda parameter_panel, run_panel: _fake_pipeline_config(
            material_definitions=fake_material_definitions
        ),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.run_pipeline",
        lambda config: fake_result,
    )
    show_sliced_assembly_calls = _mock_show_sliced_assembly_succeeds(
        main_window, monkeypatch
    )
    show_nests_calls = _mock_show_nests(main_window, monkeypatch)

    main_window.run_panel.run_button.click()
    # A tényleges `run_pipeline()`-hívás egy háttérszálon fut; a
    # `waitUntil` a Qt-eseményhurkot addig futtatja (nem `time.sleep()`),
    # amíg a `_on_pipeline_succeeded()` slot (a szál végén) vissza nem
    # engedélyezi a gombot.
    qtbot.waitUntil(lambda: main_window.run_panel.run_button.isEnabled(), timeout=2000)

    status_text = main_window.run_panel.status_log.toPlainText()
    assert "sikeres" in status_text
    assert "7" in status_text
    assert "2" in status_text
    assert main_window.run_panel.run_button.isEnabled()
    assert main_window.run_panel.export_dxf_button.isEnabled()
    assert main_window._last_nests == fake_nests
    assert show_sliced_assembly_calls == [
        (fake_slice_set, fake_dowel_positions, fake_spacers, None, None)
    ]
    assert show_nests_calls == [(fake_nests, fake_material_definitions)]


def test_run_button_engine_error_shows_processing_error(
    main_window: MainWindow, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
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
    qtbot.waitUntil(lambda: main_window.run_panel.run_button.isEnabled(), timeout=2000)

    status_text = main_window.run_panel.status_log.toPlainText()
    assert "Hiba a feldolgozás során" in status_text
    assert main_window.run_panel.run_button.isEnabled()


def test_run_button_and_menu_disabled_while_pipeline_running(
    main_window: MainWindow, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A gomb és a két menü-akció a háttérszál futása *alatt* letiltva marad,
    utána visszaáll — a mesterséges blokkolás (`threading.Event`)
    determinisztikusan tartja nyitva ezt az ablakot `time.sleep()` nélkül."""
    release_event = threading.Event()
    fake_result = SimpleNamespace(
        slice_set=SimpleNamespace(slice_count=1),
        dowel_positions=(),
        spacers=(),
        backplate=None,
        nests=(),
    )

    def _blocking_run_pipeline(config: object) -> object:
        assert release_event.wait(timeout=2.0)
        return fake_result

    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_builder.build_pipeline_config",
        lambda parameter_panel, run_panel: _fake_pipeline_config(),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.run_pipeline", _blocking_run_pipeline
    )
    _mock_show_sliced_assembly_succeeds(main_window, monkeypatch)
    _mock_show_nests(main_window, monkeypatch)

    main_window.run_panel.run_button.click()

    assert not main_window.run_panel.run_button.isEnabled()
    assert not main_window.run_panel.export_dxf_button.isEnabled()
    assert not main_window._save_action.isEnabled()
    assert not main_window._open_action.isEnabled()
    assert main_window.run_panel.progress_bar.isVisible()

    release_event.set()
    qtbot.waitUntil(lambda: main_window.run_panel.run_button.isEnabled(), timeout=2000)

    assert main_window.run_panel.export_dxf_button.isEnabled()
    assert main_window._save_action.isEnabled()
    assert main_window._open_action.isEnabled()
    assert not main_window.run_panel.progress_bar.isVisible()


def test_export_dxf_clicked_without_last_nests_shows_message(
    main_window: MainWindow,
) -> None:
    main_window.run_panel.export_dxf_button.setEnabled(True)

    main_window.run_panel.export_dxf_button.click()

    assert (
        "Nincs friss futtatási eredmény"
        in main_window.run_panel.status_log.toPlainText()
    )


def test_export_dxf_clicked_success_updates_status_log(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_nests = (object(), object(), object())
    main_window._last_nests = fake_nests
    main_window.run_panel.export_dxf_button.setEnabled(True)
    fake_dxf_params = object()

    build_calls = []
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_builder.build_dxf_export_params",
        lambda run_panel: build_calls.append(run_panel) or fake_dxf_params,
    )
    export_calls = []
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.export_pipeline_result_to_dxf",
        lambda nests, dxf_export: (
            export_calls.append((nests, dxf_export)) or (object(), object(), object())
        ),
    )

    main_window.run_panel.export_dxf_button.click()

    assert build_calls == [main_window.run_panel]
    assert export_calls == [(fake_nests, fake_dxf_params)]
    status_text = main_window.run_panel.status_log.toPlainText()
    assert "3 DXF fájl exportálva." in status_text


def test_export_dxf_clicked_configuration_error_shows_message(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    main_window._last_nests = (object(),)
    main_window.run_panel.export_dxf_button.setEnabled(True)

    def _raise(run_panel: object) -> None:
        raise PipelineConfigurationError("teszt-hiba")

    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_builder.build_dxf_export_params",
        _raise,
    )

    main_window.run_panel.export_dxf_button.click()

    assert "Konfigurációs hiba" in main_window.run_panel.status_log.toPlainText()


def test_export_dxf_clicked_engine_error_shows_message(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    from slicedesigner.engines.exceptions import InvalidMeshError

    main_window._last_nests = (object(),)
    main_window.run_panel.export_dxf_button.setEnabled(True)
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_builder.build_dxf_export_params",
        lambda run_panel: object(),
    )

    def _raise(nests: object, dxf_export: object) -> None:
        raise InvalidMeshError("teszt-hiba")

    monkeypatch.setattr(
        "slicedesigner.gui.main_window.export_pipeline_result_to_dxf", _raise
    )

    main_window.run_panel.export_dxf_button.click()

    assert "Hiba a DXF Export során" in main_window.run_panel.status_log.toPlainText()


def test_new_run_resets_last_nests_and_disables_export_button(
    main_window: MainWindow, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    main_window._last_nests = (object(),)
    main_window.run_panel.export_dxf_button.setEnabled(True)
    fake_result = SimpleNamespace(
        slice_set=SimpleNamespace(slice_count=1),
        dowel_positions=(),
        spacers=(),
        backplate=None,
        nests=(),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_builder.build_pipeline_config",
        lambda parameter_panel, run_panel: _fake_pipeline_config(),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.run_pipeline",
        lambda config: fake_result,
    )
    _mock_show_sliced_assembly_succeeds(main_window, monkeypatch)
    _mock_show_nests(main_window, monkeypatch)

    main_window.run_panel.run_button.click()

    assert main_window._last_nests is None
    assert not main_window.run_panel.export_dxf_button.isEnabled()

    qtbot.waitUntil(lambda: main_window.run_panel.run_button.isEnabled(), timeout=2000)


def test_close_event_rejects_close_while_pipeline_running(
    main_window: MainWindow, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    release_event = threading.Event()
    fake_result = SimpleNamespace(
        slice_set=SimpleNamespace(slice_count=1),
        dowel_positions=(),
        spacers=(),
        backplate=None,
        nests=(),
    )

    def _blocking_run_pipeline(config: object) -> object:
        assert release_event.wait(timeout=2.0)
        return fake_result

    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_builder.build_pipeline_config",
        lambda parameter_panel, run_panel: _fake_pipeline_config(),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.run_pipeline", _blocking_run_pipeline
    )
    _mock_show_sliced_assembly_succeeds(main_window, monkeypatch)
    _mock_show_nests(main_window, monkeypatch)
    save_calls = []
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.app_settings.save_current_config",
        lambda parameter_panel, run_panel: save_calls.append(True),
    )

    main_window.run_panel.run_button.click()
    assert main_window._worker is not None

    main_window.close()

    assert main_window.isVisible()
    assert save_calls == []
    assert "Futtatás folyamatban" in main_window.run_panel.status_log.toPlainText()

    release_event.set()
    qtbot.waitUntil(lambda: main_window.run_panel.run_button.isEnabled(), timeout=2000)


def test_close_event_rejects_close_while_example_generation_running(
    main_window: MainWindow,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A `closeEvent()` a "Példák megnyitása" háttérszála alatt is védi az
    ablakbezárást (EXAMPLES_LAUNCHER_SPEC.md 6.5. pont) — ugyanaz a
    minta, mint `test_close_event_rejects_close_while_pipeline_running`."""
    example = _fake_example(tmp_path)
    _install_fake_examples_dialog(monkeypatch, example)
    release_event = threading.Event()

    def _blocking_run(*args: object, **kwargs: object) -> SimpleNamespace:
        assert release_event.wait(timeout=2.0)
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(
        "slicedesigner.gui.examples_dialog.subprocess.run", _blocking_run
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.persistence.load_project_config",
        lambda file_path: object(),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_loader.apply_pipeline_config",
        lambda config, parameter_panel, run_panel: 0,
    )
    save_calls = []
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.app_settings.save_current_config",
        lambda parameter_panel, run_panel: save_calls.append(True),
    )

    _get_file_menu_action(main_window, "Példák megnyitása...").trigger()
    assert main_window._examples_worker is not None

    main_window.close()

    assert main_window.isVisible()
    assert save_calls == []
    assert "Futtatás folyamatban" in main_window.run_panel.status_log.toPlainText()

    release_event.set()
    qtbot.waitUntil(lambda: main_window._open_examples_action.isEnabled(), timeout=5000)


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


def _install_fake_examples_dialog(
    monkeypatch: pytest.MonkeyPatch,
    example: ExampleInfo | None,
    *,
    accepted: bool = True,
) -> list[Path]:
    """`ExamplesDialog` mockolása a `main_window` modulnévtérben (ugyanaz
    a minta, mint a `QFileDialog.getOpenFileName`-nél a többi tesztnél)
    — a valódi, modális `QDialog.exec()` a tesztek alatt (nincs
    felhasználói interakció, ami elfogadná/elutasítaná) örökre
    blokkolna, ezért a teljes dialógus-osztály egy egyszerű hamisítvánnyal
    kerül helyettesítésre. Visszaadja a ténylegesen átadott
    `examples_root` értékeket, ellenőrzés céljából."""
    from PySide6.QtWidgets import QDialog

    seen_roots: list[Path] = []

    class _FakeExamplesDialog:
        def __init__(self, examples_root: Path, parent: object = None) -> None:
            seen_roots.append(examples_root)

        def exec(self) -> int:
            return int(
                QDialog.DialogCode.Accepted if accepted else QDialog.DialogCode.Rejected
            )

        @property
        def selected_example(self) -> ExampleInfo | None:
            return example

    monkeypatch.setattr(
        "slicedesigner.gui.main_window.ExamplesDialog", _FakeExamplesDialog
    )
    return seen_roots


def _fake_example(tmp_path: Path, directory_name: str = "basic_example") -> ExampleInfo:
    return ExampleInfo(
        directory=tmp_path / directory_name,
        name="Alap példaprojekt",
        description="",
    )


def test_file_menu_has_examples_action(main_window: MainWindow) -> None:
    file_menu = _get_file_menu(main_window)
    action_texts = [action.text() for action in file_menu.actions()]
    assert "Példák megnyitása..." in action_texts


def test_open_examples_cancelled_does_nothing(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_fake_examples_dialog(monkeypatch, _fake_example(tmp_path), accepted=False)

    _get_file_menu_action(main_window, "Példák megnyitása...").trigger()

    assert main_window._examples_worker is None
    assert main_window.run_panel.status_log.toPlainText() == ""
    assert main_window._open_examples_action.isEnabled()


def test_open_examples_no_selection_does_nothing(
    main_window: MainWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_fake_examples_dialog(monkeypatch, None, accepted=True)

    _get_file_menu_action(main_window, "Példák megnyitása...").trigger()

    assert main_window._examples_worker is None
    assert main_window.run_panel.status_log.toPlainText() == ""


def test_open_examples_success_loads_project(
    main_window: MainWindow,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    example = _fake_example(tmp_path)
    _install_fake_examples_dialog(monkeypatch, example)
    monkeypatch.setattr(
        "slicedesigner.gui.examples_dialog.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stderr=""),
    )
    fake_config = object()
    load_calls = []
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.persistence.load_project_config",
        lambda file_path: load_calls.append(file_path) or fake_config,
    )
    apply_calls = []
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_loader.apply_pipeline_config",
        lambda config, parameter_panel, run_panel: apply_calls.append(config) or 0,
    )

    _get_file_menu_action(main_window, "Példák megnyitása...").trigger()

    assert main_window._examples_worker is not None
    qtbot.waitUntil(lambda: main_window._open_examples_action.isEnabled(), timeout=5000)

    expected_project_path = str(example.directory / "basic_example.json")
    assert load_calls == [expected_project_path]
    assert apply_calls == [fake_config]
    status_text = main_window.run_panel.status_log.toPlainText()
    assert "Példa generálása: Alap példaprojekt" in status_text
    assert "Példa betöltve: Alap példaprojekt." in status_text
    assert main_window._examples_worker is None


def test_open_examples_and_run_button_disabled_during_generation(
    main_window: MainWindow,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    example = _fake_example(tmp_path)
    _install_fake_examples_dialog(monkeypatch, example)
    release_event = threading.Event()

    def _blocking_run(*args: object, **kwargs: object) -> SimpleNamespace:
        assert release_event.wait(timeout=2.0)
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(
        "slicedesigner.gui.examples_dialog.subprocess.run", _blocking_run
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.persistence.load_project_config",
        lambda file_path: object(),
    )
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.config_loader.apply_pipeline_config",
        lambda config, parameter_panel, run_panel: 0,
    )

    _get_file_menu_action(main_window, "Példák megnyitása...").trigger()

    assert not main_window.run_panel.run_button.isEnabled()
    assert not main_window._save_action.isEnabled()
    assert not main_window._open_action.isEnabled()
    assert not main_window._open_examples_action.isEnabled()

    release_event.set()
    qtbot.waitUntil(lambda: main_window._open_examples_action.isEnabled(), timeout=5000)

    assert main_window.run_panel.run_button.isEnabled()
    assert main_window._save_action.isEnabled()
    assert main_window._open_action.isEnabled()


def test_open_examples_generation_failure_shows_message(
    main_window: MainWindow,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    example = _fake_example(tmp_path)
    _install_fake_examples_dialog(monkeypatch, example)
    monkeypatch.setattr(
        "slicedesigner.gui.examples_dialog.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stderr="valami elszállt"),
    )
    load_calls = []
    monkeypatch.setattr(
        "slicedesigner.gui.main_window.persistence.load_project_config",
        lambda file_path: load_calls.append(file_path) or object(),
    )

    _get_file_menu_action(main_window, "Példák megnyitása...").trigger()

    qtbot.waitUntil(lambda: main_window._open_examples_action.isEnabled(), timeout=5000)

    assert load_calls == []
    status_text = main_window.run_panel.status_log.toPlainText()
    assert "Hiba a példa generálása során" in status_text
    assert "valami elszállt" in status_text
    assert main_window.run_panel.run_button.isEnabled()
    assert main_window._examples_worker is None


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
