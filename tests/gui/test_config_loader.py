"""`apply_pipeline_config()` tesztjei: `PipelineConfig` -> widget-állapotok
leképezés — a `config_builder.build_pipeline_config()` fordítottja
(ROADMAP Phase 5, negyedik tétel, második rész)."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PySide6.QtWidgets import QTableWidgetItem  # noqa: E402
from pytestqt.qtbot import QtBot  # noqa: E402

from slicedesigner.engines.backplate_engine import (  # noqa: E402
    BackplateNormalAxis,
    ManualTabPosition,
    NonBackplateIsland,
    SliceTabOverride,
)
from slicedesigner.engines.dowel_engine import ManualDowelPosition  # noqa: E402
from slicedesigner.engines.nesting_engine import (  # noqa: E402
    MaterialDefinition,
    NestingRotationMode,
)
from slicedesigner.engines.numbering_engine import (  # noqa: E402
    NumberingDirectionSign,
    SliceNumberingOverride,
)
from slicedesigner.engines.slice_engine import SliceAxis  # noqa: E402
from slicedesigner.gui.config_builder import build_pipeline_config  # noqa: E402
from slicedesigner.gui.config_loader import apply_pipeline_config  # noqa: E402
from slicedesigner.gui.parameter_panel import ParameterPanel  # noqa: E402
from slicedesigner.gui.run_panel import RunPanel  # noqa: E402
from slicedesigner.project.persistence import (  # noqa: E402
    load_project_config,
    save_project_config,
)
from slicedesigner.project.pipeline import (  # noqa: E402
    BackplateParams,
    DowelParams,
    DxfExportParams,
    GapParams,
    MeshImportParams,
    NestingParams,
    NumberingParams,
    PipelineConfig,
    SliceParams,
)


def _make_panels(qtbot: QtBot) -> tuple[ParameterPanel, RunPanel]:
    parameter_panel = ParameterPanel()
    run_panel = RunPanel()
    qtbot.addWidget(parameter_panel)
    qtbot.addWidget(run_panel)
    return parameter_panel, run_panel


def _materials() -> tuple[MaterialDefinition, ...]:
    return (
        MaterialDefinition(
            material_id="wood3",
            thickness_mm=3.0,
            sheet_width_mm=1000.0,
            sheet_height_mm=1000.0,
            kerf_mm=0.2,
        ),
        MaterialDefinition(
            material_id="wood1",
            thickness_mm=1.0,
            sheet_width_mm=1000.0,
            sheet_height_mm=1000.0,
            kerf_mm=0.2,
        ),
    )


def _full_config() -> PipelineConfig:
    """Mindhárom kapcsoló bekapcsolva, minden paraméter-csoport (beleértve
    az opcionális mezőket, a beágyazott felülbírálás-tuple-öket és a
    materials-listát) kitöltve — lásd `tests/project/test_persistence.py`
    `_full_config()`-ját, azonos felépítéssel."""
    return PipelineConfig(
        use_dowels=True,
        use_spacers=True,
        use_backplate=True,
        mesh_import=MeshImportParams(
            file_path="mesh.stl",
            origin_alignment="none",
            min_plausible_size_mm=2.0,
            max_plausible_size_mm=2500.0,
        ),
        slicing=SliceParams(
            slice_thickness_mm=3.0,
            slice_axis=SliceAxis.X,
            gap_mm=1.0,
            max_scale_tolerance=0.05,
        ),
        numbering=NumberingParams(
            numbering_normal_axis=BackplateNormalAxis.PLUS_Y,
            numbering_direction_axis_sign=NumberingDirectionSign.NEGATIVE,
            numbering_height_mm=2.0,
            numbering_min_height_mm=1.0,
            numbering_margin_mm=0.5,
            slice_numbering_overrides=(
                SliceNumberingOverride(slice_index=1),
                SliceNumberingOverride(slice_index=2),
            ),
        ),
        nesting=NestingParams(
            material_definitions=_materials(),
            slice_material_id="wood3",
            seam_marking_height_mm=2.0,
            backplate_material_id="wood3",
            spacer_material_id="wood1",
            nesting_rotation_mode=NestingRotationMode.FREE,
            seam_marking_min_height_mm=1.0,
            seam_marking_margin_mm=0.5,
        ),
        dxf_export=DxfExportParams(
            output_directory="out",
            dxf_version="R2010",
            cut_layer_name="CUT2",
            cut_layer_color=2,
            engrave_layer_name="ENGRAVE2",
            engrave_layer_color=6,
            output_filename_pattern="{material_id}_p{sheet_number}",
        ),
        dowel=DowelParams(
            dowel_diameter_mm=4.0,
            spacer_diameter_mm=3.0,
            min_edge_clearance_mm=2.0,
            dowel_count_per_region=2,
            min_dowels_per_region=1,
            blind_hole_cap_mm=1.5,
            manual_dowel_positions=(
                ManualDowelPosition(
                    x_mm=0.0, y_mm=0.0, start_slice_index=1, end_slice_index=5
                ),
            ),
        ),
        gap=GapParams(
            spacer_diameter_mm=3.0, spacer_count_per_gap=2, min_spacers_per_region=1
        ),
        backplate=BackplateParams(
            backplate_normal_axis=BackplateNormalAxis.PLUS_X,
            backplate_thickness_mm=3.0,
            tab_length_mm=5.0,
            backplate_plane_tolerance_mm=0.2,
            backplate_margin_mm=1.0,
            tab_spacing_mm=500.0,
            tab_edge_margin_mm=10.0,
            slice_tab_overrides=(
                SliceTabOverride(
                    slice_index=1,
                    island_index=0,
                    manual_tab_positions=(ManualTabPosition(position_mm=10.0),),
                ),
            ),
            non_backplate_islands=(NonBackplateIsland(slice_index=3, island_index=1),),
            material_reference="ref-1",
        ),
    )


def _minimal_config() -> PipelineConfig:
    """Mindhárom kapcsoló kikapcsolva, kizárólag a kötelező mezők
    kitöltve — `dowel`/`gap`/`backplate` `None`."""
    return PipelineConfig(
        use_dowels=False,
        use_spacers=False,
        use_backplate=False,
        mesh_import=MeshImportParams(file_path="mesh.stl"),
        slicing=SliceParams(slice_thickness_mm=3.0),
        numbering=NumberingParams(
            numbering_normal_axis=BackplateNormalAxis.PLUS_Y,
            numbering_direction_axis_sign=NumberingDirectionSign.NEGATIVE,
            numbering_height_mm=2.0,
        ),
        nesting=NestingParams(
            material_definitions=_materials(),
            slice_material_id="wood3",
            seam_marking_height_mm=2.0,
        ),
        dxf_export=DxfExportParams(output_directory="out"),
    )


def test_apply_full_config_sets_switches_and_group_visibility(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)

    apply_pipeline_config(_full_config(), parameter_panel, run_panel)

    assert parameter_panel.use_dowels_checkbox.isChecked() is True
    assert parameter_panel.use_spacers_checkbox.isChecked() is True
    assert parameter_panel.use_backplate_checkbox.isChecked() is True
    assert parameter_panel.dowel_group.isHidden() is False
    assert parameter_panel.gap_group.isHidden() is False
    assert parameter_panel.backplate_group.isHidden() is False


def test_apply_minimal_config_leaves_optional_groups_hidden(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)

    apply_pipeline_config(_minimal_config(), parameter_panel, run_panel)

    assert parameter_panel.use_dowels_checkbox.isChecked() is False
    assert parameter_panel.use_spacers_checkbox.isChecked() is False
    assert parameter_panel.use_backplate_checkbox.isChecked() is False
    assert parameter_panel.dowel_group.isHidden() is True
    assert parameter_panel.gap_group.isHidden() is True
    assert parameter_panel.backplate_group.isHidden() is True


def test_apply_full_config_sets_widget_values(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)
    config = _full_config()

    apply_pipeline_config(config, parameter_panel, run_panel)

    assert parameter_panel.mesh_file_path_label.text() == "mesh.stl"
    assert parameter_panel.min_plausible_size_spin.value() == pytest.approx(2.0)
    assert parameter_panel.max_plausible_size_spin.value() == pytest.approx(2500.0)
    assert parameter_panel.slice_thickness_spin.value() == pytest.approx(3.0)
    assert parameter_panel.slice_axis_combo.currentData() == SliceAxis.X
    assert parameter_panel.slice_gap_spin.value() == pytest.approx(1.0)
    assert parameter_panel.max_scale_tolerance_spin.value() == pytest.approx(0.05)

    assert parameter_panel.dowel_diameter_spin.value() == pytest.approx(4.0)
    assert parameter_panel.dowel_spacer_diameter_spin.value() == pytest.approx(3.0)
    assert (
        parameter_panel.min_edge_clearance_optional.auto_checkbox.isChecked() is False
    )
    assert (
        parameter_panel.min_edge_clearance_optional.spin_box.value()
        == pytest.approx(2.0)
    )
    assert parameter_panel.dowel_count_per_region_spin.value() == 2
    assert parameter_panel.min_dowels_per_region_spin.value() == 1
    assert parameter_panel.blind_hole_cap_optional.auto_checkbox.isChecked() is False
    assert parameter_panel.blind_hole_cap_optional.spin_box.value() == pytest.approx(
        1.5
    )

    assert parameter_panel.gap_spacer_diameter_spin.value() == pytest.approx(3.0)
    assert parameter_panel.spacer_count_per_gap_spin.value() == 2
    assert parameter_panel.min_spacers_per_region_spin.value() == 1

    assert (
        parameter_panel.backplate_normal_axis_combo.currentData()
        == BackplateNormalAxis.PLUS_X
    )
    assert parameter_panel.backplate_thickness_spin.value() == pytest.approx(3.0)
    assert parameter_panel.tab_length_spin.value() == pytest.approx(5.0)
    assert parameter_panel.backplate_plane_tolerance_spin.value() == pytest.approx(0.2)
    assert parameter_panel.backplate_margin_spin.value() == pytest.approx(1.0)
    assert parameter_panel.tab_spacing_spin.value() == pytest.approx(500.0)
    assert parameter_panel.tab_edge_margin_optional.auto_checkbox.isChecked() is False
    assert parameter_panel.tab_edge_margin_optional.spin_box.value() == pytest.approx(
        10.0
    )
    assert parameter_panel.material_reference_edit.text() == "ref-1"

    assert (
        parameter_panel.numbering_normal_axis_combo.currentData()
        == BackplateNormalAxis.PLUS_Y
    )
    assert (
        parameter_panel.numbering_direction_sign_combo.currentData()
        == NumberingDirectionSign.NEGATIVE
    )
    assert parameter_panel.numbering_height_spin.value() == pytest.approx(2.0)
    assert (
        parameter_panel.numbering_min_height_optional.auto_checkbox.isChecked() is False
    )
    assert parameter_panel.numbering_margin_optional.auto_checkbox.isChecked() is False

    materials_table = parameter_panel.material_definitions_table
    assert materials_table.rowCount() == 2
    assert materials_table.item(0, 0).text() == "wood3"
    assert materials_table.item(0, 1).text() == "3.0"
    assert materials_table.item(1, 0).text() == "wood1"
    assert parameter_panel.slice_material_id_edit.text() == "wood3"
    assert parameter_panel.seam_marking_height_spin.value() == pytest.approx(2.0)
    assert parameter_panel.backplate_material_id_edit.text() == "wood3"
    assert parameter_panel.spacer_material_id_edit.text() == "wood1"
    assert (
        parameter_panel.nesting_rotation_mode_combo.currentData()
        == NestingRotationMode.FREE
    )

    assert run_panel.output_directory_label.text() == "out"
    assert run_panel.dxf_version_combo.currentText() == "R2010"
    assert run_panel.cut_layer_name_edit.text() == "CUT2"
    assert run_panel.cut_layer_color_spin.value() == 2
    assert run_panel.engrave_layer_name_edit.text() == "ENGRAVE2"
    assert run_panel.engrave_layer_color_spin.value() == 6
    assert (
        run_panel.output_filename_pattern_edit.text() == "{material_id}_p{sheet_number}"
    )


def test_apply_minimal_config_sets_auto_optional_fields(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)

    apply_pipeline_config(_minimal_config(), parameter_panel, run_panel)

    assert parameter_panel.mesh_file_path_label.text() == "mesh.stl"
    assert (
        parameter_panel.numbering_min_height_optional.auto_checkbox.isChecked() is True
    )
    assert parameter_panel.numbering_margin_optional.auto_checkbox.isChecked() is True
    assert (
        parameter_panel.seam_marking_min_height_optional.auto_checkbox.isChecked()
        is True
    )
    assert parameter_panel.backplate_material_id_edit.text() == ""
    assert parameter_panel.spacer_material_id_edit.text() == ""
    materials_table = parameter_panel.material_definitions_table
    assert materials_table.rowCount() == 2


def test_override_count_full_config_sums_all_four_groups(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)

    override_count = apply_pipeline_config(_full_config(), parameter_panel, run_panel)

    # manual_dowel_positions=1, slice_tab_overrides=1,
    # non_backplate_islands=1, slice_numbering_overrides=2
    assert override_count == 5


def test_override_count_minimal_config_is_zero(qtbot: QtBot) -> None:
    parameter_panel, run_panel = _make_panels(qtbot)

    override_count = apply_pipeline_config(
        _minimal_config(), parameter_panel, run_panel
    )

    assert override_count == 0


def test_round_trip_through_save_and_load_preserves_widget_state(
    qtbot: QtBot, tmp_path: Path
) -> None:
    source_panel, source_run_panel = _make_panels(qtbot)
    source_panel.use_dowels_checkbox.setChecked(True)
    source_panel.use_backplate_checkbox.setChecked(True)
    source_panel.dowel_diameter_spin.setValue(7.5)
    source_panel.min_edge_clearance_optional.auto_checkbox.setChecked(False)
    source_panel.min_edge_clearance_optional.spin_box.setValue(1.25)
    source_panel.material_reference_edit.setText("ref-x")
    table = source_panel.material_definitions_table
    table.insertRow(0)
    for column, value in enumerate(["ply3", "3.0", "1200.0", "2400.0", "0.2"]):
        table.setItem(0, column, QTableWidgetItem(value))
    source_run_panel.output_directory_label.setText("C:/out")
    source_run_panel.dxf_version_combo.setCurrentText("R2013")

    config = build_pipeline_config(
        source_panel, source_run_panel, require_complete=False
    )
    file_path = tmp_path / "project.json"
    save_project_config(config, str(file_path))
    loaded_config = load_project_config(str(file_path))

    target_panel, target_run_panel = _make_panels(qtbot)
    apply_pipeline_config(loaded_config, target_panel, target_run_panel)

    assert target_panel.use_dowels_checkbox.isChecked() is True
    assert target_panel.use_backplate_checkbox.isChecked() is True
    assert target_panel.dowel_diameter_spin.value() == pytest.approx(7.5)
    assert target_panel.min_edge_clearance_optional.auto_checkbox.isChecked() is False
    assert target_panel.min_edge_clearance_optional.spin_box.value() == pytest.approx(
        1.25
    )
    assert target_panel.material_reference_edit.text() == "ref-x"
    assert target_panel.material_definitions_table.rowCount() == 1
    assert target_panel.material_definitions_table.item(0, 0).text() == "ply3"
    assert target_run_panel.output_directory_label.text() == "C:/out"
    assert target_run_panel.dxf_version_combo.currentText() == "R2013"
