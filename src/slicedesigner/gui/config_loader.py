"""`PipelineConfig` → GUI widget-állapotok leképezés.

ROADMAP Phase 5, negyedik tétel, második rész: a `config_builder.py`
2.1 szakaszának (widget → `PipelineConfig`) pontos fordítottja, mezőnként
tükrözve — a "Megnyitás" útvonal widget-visszatöltéséért felel. A négy
felülbírálási tábla (`manual_dowel_positions_table`,
`slice_tab_overrides_table`, `non_backplate_islands_table`,
`slice_numbering_overrides_table`) tartalmi visszatöltése továbbra sem e
modul feladata — csak az elemszámuk összesítése, hogy a hívó (`MainWindow`)
figyelmeztethessen a "csendben elveszett" felülbírálásokra.
"""

from __future__ import annotations

from PySide6.QtWidgets import QTableWidgetItem

from slicedesigner.engines.nesting_engine import MaterialDefinition
from slicedesigner.gui.parameter_panel import ParameterPanel, _OptionalDoubleSpinBox
from slicedesigner.gui.run_panel import RunPanel
from slicedesigner.project.pipeline import (
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


def apply_pipeline_config(
    config: PipelineConfig, parameter_panel: ParameterPanel, run_panel: RunPanel
) -> int:
    """A `config` tartalmának alkalmazása a paraméter- és futtatás-panel
    widgetjeire.

    A három kapcsoló (`use_dowels_checkbox` stb.) elsőként kerül
    beállításra, hogy a Dowel/Gap/Backplate csoportok show/hide állapota
    rögtön a helyes legyen. Ha `config.dowel`/`gap`/`backplate` `None`
    (a megfelelő kapcsoló mentéskor ki volt kapcsolva), a hozzá tartozó
    csoport widgetjei a jelenlegi állapotukban maradnak.

    Returns:
        A betöltött `config`-ban jelen lévő, a GUI táblái által jelenleg
        nem szerkeszthető felülbírálási bejegyzések összesített száma
        (`manual_dowel_positions` + `slice_tab_overrides` +
        `non_backplate_islands` + `slice_numbering_overrides`
        elemszáma összesen, a megfelelő csoport `None` esetén 0-val
        számolva).
    """
    parameter_panel.use_dowels_checkbox.setChecked(config.use_dowels)
    parameter_panel.use_spacers_checkbox.setChecked(config.use_spacers)
    parameter_panel.use_backplate_checkbox.setChecked(config.use_backplate)

    _apply_mesh_import_params(config.mesh_import, parameter_panel)
    _apply_slice_params(config.slicing, parameter_panel)
    _apply_numbering_params(config.numbering, parameter_panel)
    _apply_nesting_params(config.nesting, parameter_panel)
    _apply_dxf_export_params(config.dxf_export, run_panel)

    if config.dowel is not None:
        _apply_dowel_params(config.dowel, parameter_panel)
    if config.gap is not None:
        _apply_gap_params(config.gap, parameter_panel)
    if config.backplate is not None:
        _apply_backplate_params(config.backplate, parameter_panel)

    return (
        (len(config.dowel.manual_dowel_positions) if config.dowel is not None else 0)
        + (
            len(config.backplate.slice_tab_overrides)
            if config.backplate is not None
            else 0
        )
        + (
            len(config.backplate.non_backplate_islands)
            if config.backplate is not None
            else 0
        )
        + len(config.numbering.slice_numbering_overrides)
    )


def _apply_optional(widget: _OptionalDoubleSpinBox, value: float | None) -> None:
    """`float | None` érték visszaállítása `_OptionalDoubleSpinBox`
    állapotára — `_read_optional()` fordítottja."""
    if value is None:
        widget.auto_checkbox.setChecked(True)
        return
    widget.auto_checkbox.setChecked(False)
    widget.spin_box.setValue(value)


def _apply_mesh_import_params(params: MeshImportParams, panel: ParameterPanel) -> None:
    panel.mesh_file_path_label.setText(params.file_path)
    panel.origin_alignment_combo.setCurrentIndex(
        panel.origin_alignment_combo.findData(params.origin_alignment)
    )
    panel.min_plausible_size_spin.setValue(params.min_plausible_size_mm)
    panel.max_plausible_size_spin.setValue(params.max_plausible_size_mm)


def _apply_slice_params(params: SliceParams, panel: ParameterPanel) -> None:
    panel.slice_thickness_spin.setValue(params.slice_thickness_mm)
    panel.slice_axis_combo.setCurrentIndex(
        panel.slice_axis_combo.findData(params.slice_axis)
    )
    panel.slice_gap_spin.setValue(params.gap_mm)
    panel.max_scale_tolerance_spin.setValue(params.max_scale_tolerance)


def _apply_dowel_params(params: DowelParams, panel: ParameterPanel) -> None:
    panel.dowel_diameter_spin.setValue(params.dowel_diameter_mm)
    panel.dowel_spacer_diameter_spin.setValue(params.spacer_diameter_mm)
    _apply_optional(panel.min_edge_clearance_optional, params.min_edge_clearance_mm)
    panel.dowel_count_per_region_spin.setValue(params.dowel_count_per_region)
    panel.min_dowels_per_region_spin.setValue(params.min_dowels_per_region)
    _apply_optional(panel.blind_hole_cap_optional, params.blind_hole_cap_mm)


def _apply_gap_params(params: GapParams, panel: ParameterPanel) -> None:
    panel.gap_spacer_diameter_spin.setValue(params.spacer_diameter_mm)
    panel.spacer_count_per_gap_spin.setValue(params.spacer_count_per_gap)
    panel.min_spacers_per_region_spin.setValue(params.min_spacers_per_region)


def _apply_backplate_params(params: BackplateParams, panel: ParameterPanel) -> None:
    panel.backplate_normal_axis_combo.setCurrentIndex(
        panel.backplate_normal_axis_combo.findData(params.backplate_normal_axis)
    )
    panel.backplate_thickness_spin.setValue(params.backplate_thickness_mm)
    panel.tab_length_spin.setValue(params.tab_length_mm)
    panel.backplate_plane_tolerance_spin.setValue(params.backplate_plane_tolerance_mm)
    panel.backplate_margin_spin.setValue(params.backplate_margin_mm)
    panel.tab_spacing_spin.setValue(params.tab_spacing_mm)
    _apply_optional(panel.tab_edge_margin_optional, params.tab_edge_margin_mm)
    panel.material_reference_edit.setText(params.material_reference or "")


def _apply_numbering_params(params: NumberingParams, panel: ParameterPanel) -> None:
    panel.numbering_normal_axis_combo.setCurrentIndex(
        panel.numbering_normal_axis_combo.findData(params.numbering_normal_axis)
    )
    panel.numbering_direction_sign_combo.setCurrentIndex(
        panel.numbering_direction_sign_combo.findData(
            params.numbering_direction_axis_sign
        )
    )
    panel.numbering_height_spin.setValue(params.numbering_height_mm)
    _apply_optional(panel.numbering_min_height_optional, params.numbering_min_height_mm)
    _apply_optional(panel.numbering_margin_optional, params.numbering_margin_mm)


def _apply_nesting_params(params: NestingParams, panel: ParameterPanel) -> None:
    _apply_material_definitions(panel, params.material_definitions)
    panel.slice_material_id_edit.setText(params.slice_material_id)
    panel.seam_marking_height_spin.setValue(params.seam_marking_height_mm)
    panel.backplate_material_id_edit.setText(params.backplate_material_id or "")
    panel.spacer_material_id_edit.setText(params.spacer_material_id or "")
    panel.nesting_rotation_mode_combo.setCurrentIndex(
        panel.nesting_rotation_mode_combo.findData(params.nesting_rotation_mode)
    )
    _apply_optional(
        panel.seam_marking_min_height_optional, params.seam_marking_min_height_mm
    )
    _apply_optional(panel.seam_marking_margin_optional, params.seam_marking_margin_mm)


def _apply_dxf_export_params(params: DxfExportParams, run_panel: RunPanel) -> None:
    run_panel.output_directory_label.setText(params.output_directory)
    run_panel.dxf_version_combo.setCurrentText(params.dxf_version)
    run_panel.cut_layer_name_edit.setText(params.cut_layer_name)
    run_panel.cut_layer_color_spin.setValue(params.cut_layer_color)
    run_panel.engrave_layer_name_edit.setText(params.engrave_layer_name)
    run_panel.engrave_layer_color_spin.setValue(params.engrave_layer_color)
    run_panel.output_filename_pattern_edit.setText(params.output_filename_pattern)


def _apply_material_definitions(
    panel: ParameterPanel, material_definitions: tuple[MaterialDefinition, ...]
) -> None:
    """A materials-tábla feltöltése — ugyanazzal a "minden cellába
    `QTableWidgetItem`" mintával, mint amit a "Hozzáadás" gomb használ
    (`parameter_panel._build_placeholder_table`)."""
    table = panel.material_definitions_table
    table.setRowCount(0)
    for row, material in enumerate(material_definitions):
        table.insertRow(row)
        values = (
            material.material_id,
            str(material.thickness_mm),
            str(material.sheet_width_mm),
            str(material.sheet_height_mm),
            str(material.kerf_mm),
        )
        for column, value in enumerate(values):
            table.setItem(row, column, QTableWidgetItem(value))
