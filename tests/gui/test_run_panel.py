"""`RunPanel` tesztjei: a widgetek három, elkülönített konténerbe
szétválasztott felépítése (ROADMAP Phase 7 7.4 tétele, prompt 2.3
szakasz) — az attribútum-nevek/típusok VÁLTOZATLANok maradnak, csak a
konténer-struktúra új."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import (  # noqa: E402
    QGroupBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QWidget,
)
from pytestqt.qtbot import QtBot  # noqa: E402

from slicedesigner.gui.run_panel import RunPanel  # noqa: E402


def _make_panel(qtbot: QtBot) -> RunPanel:
    panel = RunPanel()
    qtbot.addWidget(panel)
    return panel


def test_export_settings_widget_is_a_dxf_export_group_box(qtbot: QtBot) -> None:
    panel = _make_panel(qtbot)
    assert isinstance(panel.export_settings_widget, QGroupBox)
    assert panel.export_settings_widget.title() == "DXF Export"


def test_export_settings_widget_contains_dxf_parameter_widgets(qtbot: QtBot) -> None:
    panel = _make_panel(qtbot)

    # Az összes DXF Export paraméter-widget a `export_settings_widget`
    # leszármazottja marad (ugyanaz az attribútum, csak a konténer más).
    for widget in (
        panel.output_directory_label,
        panel.output_directory_button,
        panel.dxf_version_combo,
        panel.cut_layer_name_edit,
        panel.cut_layer_color_spin,
        panel.engrave_layer_name_edit,
        panel.engrave_layer_color_spin,
        panel.output_filename_pattern_edit,
    ):
        assert panel.export_settings_widget.isAncestorOf(widget)


def test_action_container_holds_run_export_and_progress_widgets(qtbot: QtBot) -> None:
    panel = _make_panel(qtbot)
    assert isinstance(panel.action_container, QWidget)

    assert isinstance(panel.run_button, QPushButton)
    assert isinstance(panel.export_dxf_button, QPushButton)
    assert isinstance(panel.progress_bar, QProgressBar)
    for widget in (panel.run_button, panel.export_dxf_button, panel.progress_bar):
        assert panel.action_container.isAncestorOf(widget)


def test_run_button_and_export_button_labels_unchanged(qtbot: QtBot) -> None:
    panel = _make_panel(qtbot)
    assert panel.run_button.text() == "Futtatás"
    assert panel.export_dxf_button.text() == "DXF Export"
    assert not panel.export_dxf_button.isEnabled()


def test_progress_bar_starts_hidden_and_indeterminate(qtbot: QtBot) -> None:
    panel = _make_panel(qtbot)
    assert not panel.progress_bar.isVisible()
    assert panel.progress_bar.minimum() == 0
    assert panel.progress_bar.maximum() == 0


def test_status_log_is_a_readonly_text_edit(qtbot: QtBot) -> None:
    panel = _make_panel(qtbot)
    assert isinstance(panel.status_log, QTextEdit)
    assert panel.status_log.isReadOnly()


def test_the_three_containers_are_not_nested_in_each_other(qtbot: QtBot) -> None:
    """A három konténer (export-beállítások, akció, log) egymástól
    függetlenül helyezhető el különböző szülő-widgetekbe — egyik sem a
    másik leszármazottja."""
    panel = _make_panel(qtbot)

    assert not panel.export_settings_widget.isAncestorOf(panel.action_container)
    assert not panel.action_container.isAncestorOf(panel.export_settings_widget)
    assert not panel.export_settings_widget.isAncestorOf(panel.status_log)
    assert not panel.action_container.isAncestorOf(panel.status_log)
