"""Tesztek a `PipelineConfig` projektmentés (de)szerializálásához."""

import json
from pathlib import Path

import pytest

from slicedesigner.engines.backplate_engine import (
    BackplateNormalAxis,
    ManualTabPosition,
    NonBackplateIsland,
    SliceTabOverride,
)
from slicedesigner.engines.dowel_engine import ManualDowelPosition
from slicedesigner.engines.nesting_engine import (
    MaterialDefinition,
    NestingRotationMode,
)
from slicedesigner.engines.numbering_engine import (
    NumberingDirectionSign,
    SliceNumberingOverride,
)
from slicedesigner.engines.slice_engine import SliceAxis
from slicedesigner.project.exceptions import PipelineConfigurationError
from slicedesigner.project.persistence import load_project_config, save_project_config
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
    materials-listát) kitöltve."""
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
                SliceNumberingOverride(
                    slice_index=1,
                    island_index=0,
                    numbering_height_mm=3.0,
                    numbering_min_height_mm=1.5,
                    numbering_margin_mm=0.3,
                    manual_position=(4.0, 5.0),
                ),
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
                    tab_length_mm=6.0,
                    tab_spacing_mm=400.0,
                    tab_edge_margin_mm=8.0,
                    manual_tab_positions=(
                        ManualTabPosition(position_mm=10.0, length_mm=5.0),
                        ManualTabPosition(position_mm=20.0),
                    ),
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


def test_round_trip_full_config_is_equal(tmp_path: Path) -> None:
    config = _full_config()
    file_path = tmp_path / "project.json"

    save_project_config(config, str(file_path))
    loaded = load_project_config(str(file_path))

    assert loaded == config


def test_round_trip_minimal_config_is_equal(tmp_path: Path) -> None:
    config = _minimal_config()
    file_path = tmp_path / "project.json"

    save_project_config(config, str(file_path))
    loaded = load_project_config(str(file_path))

    assert loaded == config


def test_save_writes_expected_schema_root_structure(tmp_path: Path) -> None:
    file_path = tmp_path / "project.json"

    save_project_config(_minimal_config(), str(file_path))

    payload = json.loads(file_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert isinstance(payload["config"], dict)
    assert payload["config"]["use_dowels"] is False


def test_load_missing_file_raises_configuration_error(tmp_path: Path) -> None:
    missing_path = tmp_path / "does-not-exist.json"

    with pytest.raises(PipelineConfigurationError):
        load_project_config(str(missing_path))


def test_load_invalid_json_raises_configuration_error(tmp_path: Path) -> None:
    file_path = tmp_path / "project.json"
    file_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(PipelineConfigurationError):
        load_project_config(str(file_path))


def test_load_missing_schema_version_raises_configuration_error(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "project.json"
    file_path.write_text(json.dumps({"config": {}}), encoding="utf-8")

    with pytest.raises(PipelineConfigurationError):
        load_project_config(str(file_path))


def test_load_unsupported_schema_version_raises_configuration_error(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "project.json"
    file_path.write_text(
        json.dumps({"schema_version": 2, "config": {}}), encoding="utf-8"
    )

    with pytest.raises(PipelineConfigurationError):
        load_project_config(str(file_path))


def test_load_missing_required_field_raises_configuration_error(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "project.json"
    save_project_config(_minimal_config(), str(file_path))
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    del payload["config"]["use_dowels"]
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PipelineConfigurationError):
        load_project_config(str(file_path))


def test_load_invalid_enum_value_raises_configuration_error(tmp_path: Path) -> None:
    file_path = tmp_path / "project.json"
    save_project_config(_minimal_config(), str(file_path))
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    payload["config"]["slicing"]["slice_axis"] = "not-an-axis"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PipelineConfigurationError):
        load_project_config(str(file_path))
