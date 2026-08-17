"""GUI widget-állapotok → `PipelineConfig` leképezés.

ROADMAP Phase 5, "teljes workflow" feladat, 1. rész: kizárólag a
`ParameterPanel`/`RunPanel` widget-értékeinek kiolvasásáért és a
`PipelineConfig` összeállításáért felel. A pipeline tényleges
validációja (`run_pipeline()` -> `_validate_config()`) és végrehajtása
nem e modul feladata.
"""

from __future__ import annotations

from PySide6.QtWidgets import QTableWidget

from slicedesigner.engines.mesh_import import Mesh
from slicedesigner.engines.nesting_engine import MaterialDefinition
from slicedesigner.gui.parameter_panel import ParameterPanel, _OptionalDoubleSpinBox
from slicedesigner.gui.run_panel import RunPanel
from slicedesigner.project.exceptions import PipelineConfigurationError
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

# A `_build_file_picker()`/`RunPanel` kimeneti könyvtár widget kezdeti,
# még ki nem választott állapotának szövege (lásd parameter_panel.py és
# run_panel.py) — ha ez a szöveg a leolvasáskor is jelen van, a kötelező
# fájl-/könyvtár-bemenet hiányzik.
_UNSET_PATH_PLACEHOLDER = "(nincs kiválasztva)"


def build_pipeline_config(
    parameter_panel: ParameterPanel,
    run_panel: RunPanel,
    *,
    require_complete: bool = True,
) -> PipelineConfig:
    """A paraméter- és futtatás-panel jelenlegi widget-állapotából
    `PipelineConfig` összeállítása.

    A négy felülbírálási tábla (`manual_dowel_positions_table`,
    `slice_tab_overrides_table`, `non_backplate_islands_table`,
    `slice_numbering_overrides_table`) tartalma ebben a körben nem kerül
    beolvasásra — a megfelelő `PipelineConfig`-mezők üres tuple
    alapértékkel maradnak (ROADMAP Phase 5, "teljes workflow" 1. rész).

    A `ParameterPanel` "Forrás" beállítása szerint a `mesh_import`/`mesh`
    közül pontosan az egyik kerül kitöltésre (ADR-0017): STL fájl
    választása esetén `mesh_import`, egy telepített MeshSource plugin
    választása esetén a `ParameterPanel.generated_mesh`-ben
    gyorsítótárazott, korábban a "Generálás" gombbal előállított `Mesh`
    (l. `main_window.py::_on_mesh_generation_succeeded()`) — a generálás
    NEM ismétlődik meg itt.

    Args:
        require_complete: `True` esetén (a "Futtatás" gomb útvonala)
            hiányzó mesh-fájl/kimeneti könyvtár/generált-modell hibát dob.
            `False` esetén (a "Mentés" útvonala) ezek az ellenőrzések
            kimaradnak, és a placeholder-szöveg/hiányzó generálás is
            érvényes, elmenthető értékként kerül a `PipelineConfig`-ba (a
            `persistence.py::save_project_config()` a `mesh`-sel
            rendelkező konfigurációt ettől függetlenül elutasítja, l.
            ADR-0017). A kimeneti könyvtár ellenőrzését ehhez a
            `require_complete` értékhez igazítva a `build_dxf_export_params()`
            végzi el.

    Raises:
        PipelineConfigurationError: `require_complete=True` mellett a
            mesh-fájl/generált-modell vagy a kimeneti könyvtár még nincs
            kiválasztva/előállítva, vagy (állapottól függetlenül) a
            materials-tábla egy cellája nem értelmezhető a várt típusként.
    """
    mesh_import, mesh = _build_mesh_source(
        parameter_panel, require_complete=require_complete
    )

    use_dowels = parameter_panel.use_dowels_checkbox.isChecked()
    use_spacers = parameter_panel.use_spacers_checkbox.isChecked()
    use_backplate = parameter_panel.use_backplate_checkbox.isChecked()

    return PipelineConfig(
        use_dowels=use_dowels,
        use_spacers=use_spacers,
        use_backplate=use_backplate,
        mesh_import=mesh_import,
        slicing=_build_slice_params(parameter_panel),
        numbering=_build_numbering_params(parameter_panel),
        nesting=_build_nesting_params(parameter_panel),
        dxf_export=build_dxf_export_params(
            run_panel, require_complete=require_complete
        ),
        dowel=_build_dowel_params(parameter_panel) if use_dowels else None,
        gap=_build_gap_params(parameter_panel) if use_spacers else None,
        backplate=(_build_backplate_params(parameter_panel) if use_backplate else None),
        mesh=mesh,
    )


def _build_mesh_source(
    parameter_panel: ParameterPanel, *, require_complete: bool
) -> tuple[MeshImportParams | None, Mesh | None]:
    """A `PipelineConfig.mesh_import`/`mesh` (egymást kölcsönösen kizáró,
    l. `pipeline.py::PipelineConfig`) előállítása a `ParameterPanel`
    "Forrás" beállítása szerint (ADR-0017)."""
    if (
        parameter_panel.mesh_source_combo is not None
        and parameter_panel.mesh_source_combo.currentData() is not None
    ):
        if require_complete and parameter_panel.generated_mesh is None:
            raise PipelineConfigurationError(
                "Nincs generált modell — előbb kattints a 'Generálás' gombra."
            )
        return None, parameter_panel.generated_mesh

    if require_complete:
        _require_selected_path(
            parameter_panel.mesh_file_path_label.text(), field_name="Mesh fájl"
        )
    return _build_mesh_import_params(parameter_panel), None


def _require_selected_path(value: str, *, field_name: str) -> None:
    """GUI-szintű "hiányzik a kötelező bemenet" ellenőrzés — nem a domain
    réteg validációjának duplikálása."""
    if value == _UNSET_PATH_PLACEHOLDER:
        raise PipelineConfigurationError(
            f"'{field_name}' kötelező, de még nincs kiválasztva."
        )


def _read_optional(widget: _OptionalDoubleSpinBox) -> float | None:
    """`_OptionalDoubleSpinBox` állapotának `float | None` értékké alakítása."""
    if widget.auto_checkbox.isChecked():
        return None
    return widget.spin_box.value()


def _build_mesh_import_params(panel: ParameterPanel) -> MeshImportParams:
    return MeshImportParams(
        file_path=panel.mesh_file_path_label.text(),
        origin_alignment=panel.origin_alignment_combo.currentData(),
        min_plausible_size_mm=panel.min_plausible_size_spin.value(),
        max_plausible_size_mm=panel.max_plausible_size_spin.value(),
    )


def _build_slice_params(panel: ParameterPanel) -> SliceParams:
    return SliceParams(
        slice_thickness_mm=panel.slice_thickness_spin.value(),
        slice_axis=panel.slice_axis_combo.currentData(),
        gap_mm=panel.slice_gap_spin.value(),
        max_scale_tolerance=panel.max_scale_tolerance_spin.value(),
    )


def _build_dowel_params(panel: ParameterPanel) -> DowelParams:
    # `manual_dowel_positions_table` tartalma nem kerül beolvasásra (lásd
    # a modul-docstringet) — `manual_dowel_positions` üres tuple marad.
    return DowelParams(
        dowel_diameter_mm=panel.dowel_diameter_spin.value(),
        spacer_diameter_mm=panel.dowel_spacer_diameter_spin.value(),
        min_edge_clearance_mm=_read_optional(panel.min_edge_clearance_optional),
        dowel_count_per_region=panel.dowel_count_per_region_spin.value(),
        min_dowels_per_region=panel.min_dowels_per_region_spin.value(),
        blind_hole_cap_mm=_read_optional(panel.blind_hole_cap_optional),
    )


def _build_gap_params(panel: ParameterPanel) -> GapParams:
    return GapParams(
        spacer_diameter_mm=panel.gap_spacer_diameter_spin.value(),
        spacer_count_per_gap=panel.spacer_count_per_gap_spin.value(),
        min_spacers_per_region=panel.min_spacers_per_region_spin.value(),
    )


def _build_backplate_params(panel: ParameterPanel) -> BackplateParams:
    # `slice_tab_overrides_table`/`non_backplate_islands_table` tartalma
    # nem kerül beolvasásra (lásd a modul-docstringet) — a megfelelő
    # mezők üres tuple-lel maradnak.
    material_reference = panel.material_reference_edit.text().strip()
    return BackplateParams(
        backplate_normal_axis=panel.backplate_normal_axis_combo.currentData(),
        backplate_thickness_mm=panel.backplate_thickness_spin.value(),
        tab_length_mm=panel.tab_length_spin.value(),
        backplate_plane_tolerance_mm=panel.backplate_plane_tolerance_spin.value(),
        backplate_margin_mm=panel.backplate_margin_spin.value(),
        tab_spacing_mm=panel.tab_spacing_spin.value(),
        tab_edge_margin_mm=_read_optional(panel.tab_edge_margin_optional),
        material_reference=material_reference or None,
    )


def _build_numbering_params(panel: ParameterPanel) -> NumberingParams:
    # `slice_numbering_overrides_table` tartalma nem kerül beolvasásra
    # (lásd a modul-docstringet) — `slice_numbering_overrides` üres
    # tuple marad.
    return NumberingParams(
        numbering_normal_axis=panel.numbering_normal_axis_combo.currentData(),
        numbering_direction_axis_sign=(
            panel.numbering_direction_sign_combo.currentData()
        ),
        numbering_height_mm=panel.numbering_height_spin.value(),
        numbering_min_height_mm=_read_optional(panel.numbering_min_height_optional),
        numbering_margin_mm=_read_optional(panel.numbering_margin_optional),
    )


def _build_nesting_params(panel: ParameterPanel) -> NestingParams:
    backplate_material_id = panel.backplate_material_id_edit.text().strip()
    spacer_material_id = panel.spacer_material_id_edit.text().strip()
    return NestingParams(
        material_definitions=_read_material_definitions(
            panel.material_definitions_table
        ),
        slice_material_id=panel.slice_material_id_edit.text(),
        seam_marking_height_mm=panel.seam_marking_height_spin.value(),
        backplate_material_id=backplate_material_id or None,
        spacer_material_id=spacer_material_id or None,
        nesting_rotation_mode=panel.nesting_rotation_mode_combo.currentData(),
        seam_marking_min_height_mm=_read_optional(
            panel.seam_marking_min_height_optional
        ),
        seam_marking_margin_mm=_read_optional(panel.seam_marking_margin_optional),
    )


def build_dxf_export_params(
    run_panel: RunPanel, *, require_complete: bool = True
) -> DxfExportParams:
    """A futtatás-panel jelenlegi widget-állapotából `DxfExportParams`
    összeállítása.

    Ezt `build_pipeline_config()` is hívja (a "Futtatás" útvonal
    részeként), és a `MainWindow` az önálló "DXF Export" gomb kattintás-
    eseményében is (ADR-0009) — utóbbi esetben nem a teljes
    `PipelineConfig`, csak a DXF Export paraméterek szükségesek.

    Args:
        require_complete: `True` esetén hiányzó kimeneti könyvtár esetén
            hibát dob (a "Futtatás" és a "DXF Export" gomb útvonala).
            `False` esetén (a "Mentés" útvonala) ez az ellenőrzés kimarad,
            és a placeholder-szöveg is érvényes, elmenthető értékként
            kerül a visszaadott objektumba.

    Raises:
        PipelineConfigurationError: `require_complete=True` mellett a
            kimeneti könyvtár még nincs kiválasztva.
    """
    if require_complete:
        _require_selected_path(
            run_panel.output_directory_label.text(), field_name="Kimeneti könyvtár"
        )
    return DxfExportParams(
        output_directory=run_panel.output_directory_label.text(),
        dxf_version=run_panel.dxf_version_combo.currentText(),
        cut_layer_name=run_panel.cut_layer_name_edit.text(),
        cut_layer_color=run_panel.cut_layer_color_spin.value(),
        engrave_layer_name=run_panel.engrave_layer_name_edit.text(),
        engrave_layer_color=run_panel.engrave_layer_color_spin.value(),
        output_filename_pattern=run_panel.output_filename_pattern_edit.text(),
    )


def _read_material_definitions(
    table: QTableWidget,
) -> tuple[MaterialDefinition, ...]:
    """A materials-tábla sorainak `MaterialDefinition`-ökké alakítása.

    Ez az egyetlen tábla, amelynek tartalma ebben a körben ténylegesen
    beolvasásra kerül (lásd a modul-docstringet).

    Raises:
        PipelineConfigurationError: egy numerikus cella nem értelmezhető
            számként.
    """
    definitions: list[MaterialDefinition] = []
    for row in range(table.rowCount()):
        definitions.append(
            MaterialDefinition(
                material_id=_cell_text(table, row, 0),
                thickness_mm=_cell_float(table, row, 1, column_name="thickness_mm"),
                sheet_width_mm=_cell_float(table, row, 2, column_name="sheet_width_mm"),
                sheet_height_mm=_cell_float(
                    table, row, 3, column_name="sheet_height_mm"
                ),
                kerf_mm=_cell_float(table, row, 4, column_name="kerf_mm"),
            )
        )
    return tuple(definitions)


def _cell_text(table: QTableWidget, row: int, column: int) -> str:
    item = table.item(row, column)
    return item.text() if item is not None else ""


def _cell_float(
    table: QTableWidget, row: int, column: int, *, column_name: str
) -> float:
    text = _cell_text(table, row, column)
    try:
        return float(text)
    except ValueError as error:
        raise PipelineConfigurationError(
            f"Az Anyagok táblázat {row + 1}. sorának '{column_name}' oszlopa "
            f"nem értelmezhető számként: {text!r}."
        ) from error
