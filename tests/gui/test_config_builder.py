"""`build_pipeline_config()` tesztjei: widget-állapotok → `PipelineConfig`
leképezés (ROADMAP Phase 5, "teljes workflow" 1. rész)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PySide6.QtWidgets import QTableWidgetItem  # noqa: E402
from pytestqt.qtbot import QtBot  # noqa: E402

from slicedesigner.engines.nesting_engine import MaterialDefinition  # noqa: E402
from slicedesigner.gui.config_builder import (  # noqa: E402
    build_dxf_export_params,
    build_pipeline_config,
)
from slicedesigner.gui.parameter_panel import ParameterPanel  # noqa: E402
from slicedesigner.gui.run_panel import RunPanel  # noqa: E402
from slicedesigner.project.exceptions import PipelineConfigurationError  # noqa: E402


def _make_panels(qtbot: QtBot) -> tuple[ParameterPanel, RunPanel]:
    parameter_panel = ParameterPanel()
    run_panel = RunPanel()
    qtbot.addWidget(parameter_panel)
    qtbot.addWidget(run_panel)
    return parameter_panel, run_panel


def _fill_required_paths(parameter_panel: ParameterPanel, run_panel: RunPanel) -> None:
    parameter_panel.mesh_file_path_label.setText("C:/models/example.stl")
    run_panel.output_directory_label.setText("C:/exports")


def _fill_materials_table(
    parameter_panel: ParameterPanel,
    *,
    material_id: str = "plywood_3mm",
    thickness_mm: str = "3.0",
    sheet_width_mm: str = "1200.0",
    sheet_height_mm: str = "2400.0",
    kerf_mm: str = "0.2",
) -> None:
    table = parameter_panel.material_definitions_table
    row = table.rowCount()
    table.insertRow(row)
    values = [material_id, thickness_mm, sheet_width_mm, sheet_height_mm, kerf_mm]
    for column, value in enumerate(values):
        table.setItem(row, column, QTableWidgetItem(value))


def test_missing_mesh_file_raises(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)
    run_panel.output_directory_label.setText("C:/exports")
    _fill_materials_table(parameter_panel)

    with pytest.raises(PipelineConfigurationError):
        build_pipeline_config(parameter_panel, run_panel)


def test_missing_output_directory_raises(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)
    parameter_panel.mesh_file_path_label.setText("C:/models/example.stl")
    _fill_materials_table(parameter_panel)

    with pytest.raises(PipelineConfigurationError):
        build_pipeline_config(parameter_panel, run_panel)


def test_all_switches_off_produce_none_params(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)
    _fill_required_paths(parameter_panel, run_panel)
    _fill_materials_table(parameter_panel)

    config = build_pipeline_config(parameter_panel, run_panel)

    assert config.use_dowels is False
    assert config.use_spacers is False
    assert config.use_backplate is False
    assert config.dowel is None
    assert config.gap is None
    assert config.backplate is None


def test_all_switches_on_produce_params(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)
    _fill_required_paths(parameter_panel, run_panel)
    _fill_materials_table(parameter_panel)

    parameter_panel.use_dowels_checkbox.setChecked(True)
    parameter_panel.use_spacers_checkbox.setChecked(True)
    parameter_panel.use_backplate_checkbox.setChecked(True)

    config = build_pipeline_config(parameter_panel, run_panel)

    assert config.use_dowels is True
    assert config.dowel is not None
    assert config.use_spacers is True
    assert config.gap is not None
    assert config.use_backplate is True
    assert config.backplate is not None


def test_full_pipeline_config_builds_with_new_tabbed_layout(qtbot: QtBot) -> None:
    """A `ParameterPanel`/`RunPanel` fülsávos, szétválasztott elrendezése
    (ROADMAP Phase 7 7.4 tétele) mellett is helyesen épül fel egy teljes
    `PipelineConfig` — a `RunPanel.export_settings_widget`-et ténylegesen
    beillesztve a `ParameterPanel` Export fülébe (a `MainWindow`-beli
    vezetékezést tükrözve), bizonyítva, hogy az áthelyezés (reparent egy
    fülönkénti `QScrollArea`-ba) nem változtat a `config_builder.py`-ból
    elért widget-attribútumok azonosságán/értékén — ez az invariáns teszi
    lehetővé, hogy `config_builder.py`/`config_loader.py` egyáltalán ne
    kelljen módosítani."""
    parameter_panel, run_panel = _make_panels(qtbot)
    parameter_panel.set_export_tab_content(run_panel.export_settings_widget)
    _fill_required_paths(parameter_panel, run_panel)
    _fill_materials_table(parameter_panel)
    parameter_panel.use_dowels_checkbox.setChecked(True)
    parameter_panel.use_spacers_checkbox.setChecked(True)
    parameter_panel.use_backplate_checkbox.setChecked(True)

    config = build_pipeline_config(parameter_panel, run_panel)

    assert config.use_dowels is True
    assert config.dowel is not None
    assert config.use_spacers is True
    assert config.gap is not None
    assert config.use_backplate is True
    assert config.backplate is not None
    assert config.mesh_import.file_path == "C:/models/example.stl"
    assert config.dxf_export.output_directory == "C:/exports"
    assert config.nesting.material_definitions != ()


def test_material_definitions_table_is_read_correctly(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)
    _fill_required_paths(parameter_panel, run_panel)
    _fill_materials_table(
        parameter_panel,
        material_id="acrylic_5mm",
        thickness_mm="5.0",
        sheet_width_mm="1000.0",
        sheet_height_mm="2000.0",
        kerf_mm="0.15",
    )

    config = build_pipeline_config(parameter_panel, run_panel)

    assert config.nesting.material_definitions == (
        MaterialDefinition(
            material_id="acrylic_5mm",
            thickness_mm=5.0,
            sheet_width_mm=1000.0,
            sheet_height_mm=2000.0,
            kerf_mm=0.15,
        ),
    )


def test_material_definitions_invalid_number_raises(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)
    _fill_required_paths(parameter_panel, run_panel)
    _fill_materials_table(parameter_panel, thickness_mm="not-a-number")

    with pytest.raises(PipelineConfigurationError):
        build_pipeline_config(parameter_panel, run_panel)


def test_optional_field_auto_state_maps_to_none(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)
    _fill_required_paths(parameter_panel, run_panel)
    _fill_materials_table(parameter_panel)
    parameter_panel.use_dowels_checkbox.setChecked(True)
    parameter_panel.min_edge_clearance_optional.auto_checkbox.setChecked(True)

    config = build_pipeline_config(parameter_panel, run_panel)

    assert config.dowel is not None
    assert config.dowel.min_edge_clearance_mm is None


def test_optional_field_manual_value_is_used(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)
    _fill_required_paths(parameter_panel, run_panel)
    _fill_materials_table(parameter_panel)
    parameter_panel.use_dowels_checkbox.setChecked(True)
    parameter_panel.min_edge_clearance_optional.auto_checkbox.setChecked(False)
    parameter_panel.min_edge_clearance_optional.spin_box.setValue(2.5)

    config = build_pipeline_config(parameter_panel, run_panel)

    assert config.dowel is not None
    assert config.dowel.min_edge_clearance_mm == pytest.approx(2.5)


def test_require_complete_false_allows_missing_mesh_file(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)
    run_panel.output_directory_label.setText("C:/exports")
    _fill_materials_table(parameter_panel)

    config = build_pipeline_config(parameter_panel, run_panel, require_complete=False)

    assert config.mesh_import.file_path == "(nincs kiválasztva)"


def test_require_complete_false_allows_missing_output_directory(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)
    parameter_panel.mesh_file_path_label.setText("C:/models/example.stl")
    _fill_materials_table(parameter_panel)

    config = build_pipeline_config(parameter_panel, run_panel, require_complete=False)

    assert config.dxf_export.output_directory == "(nincs kiválasztva)"


def test_require_complete_false_still_raises_on_invalid_material_cell(
    qtbot: QtBot,
) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)
    _fill_materials_table(parameter_panel, thickness_mm="not-a-number")

    with pytest.raises(PipelineConfigurationError):
        build_pipeline_config(parameter_panel, run_panel, require_complete=False)


def test_build_dxf_export_params_missing_output_directory_raises(
    qtbot: QtBot,
) -> None:
    _, run_panel = _make_panels(qtbot)

    with pytest.raises(PipelineConfigurationError):
        build_dxf_export_params(run_panel)


def test_build_dxf_export_params_require_complete_false_allows_missing_output_directory(
    qtbot: QtBot,
) -> None:
    _, run_panel = _make_panels(qtbot)

    params = build_dxf_export_params(run_panel, require_complete=False)

    assert params.output_directory == "(nincs kiválasztva)"


def test_build_dxf_export_params_reads_widget_values(qtbot: QtBot) -> None:
    _, run_panel = _make_panels(qtbot)
    run_panel.output_directory_label.setText("C:/exports")
    run_panel.dxf_version_combo.setCurrentText("R2010")
    run_panel.cut_layer_name_edit.setText("MYCUT")
    run_panel.cut_layer_color_spin.setValue(2)
    run_panel.engrave_layer_name_edit.setText("MYENGRAVE")
    run_panel.engrave_layer_color_spin.setValue(6)
    run_panel.output_filename_pattern_edit.setText("{material_id}")

    params = build_dxf_export_params(run_panel)

    assert params.output_directory == "C:/exports"
    assert params.dxf_version == "R2010"
    assert params.cut_layer_name == "MYCUT"
    assert params.cut_layer_color == 2
    assert params.engrave_layer_name == "MYENGRAVE"
    assert params.engrave_layer_color == 6
    assert params.output_filename_pattern == "{material_id}"
