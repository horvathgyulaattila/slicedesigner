"""Tesztek a koordinációs réteg pipeline-vezérléséhez (ADR-0004)."""

from pathlib import Path

import pytest
import trimesh

from slicedesigner.engines.backplate_engine import BackplateNormalAxis
from slicedesigner.engines.exceptions import InvalidSliceError
from slicedesigner.engines.nesting_engine import MaterialDefinition, PartKind
from slicedesigner.engines.numbering_engine import NumberingDirectionSign
from slicedesigner.project import pipeline
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
    run_pipeline,
)

_BOX_EXTENTS = (30.0, 30.0, 15.0)


def _box_stl(tmp_path: Path, filename: str = "mesh.stl") -> str:
    box = trimesh.creation.box(extents=_BOX_EXTENTS)
    path = tmp_path / filename
    box.export(str(path), file_type="stl")
    return str(path)


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


def _numbering_params() -> NumberingParams:
    # A direction_axis_sign NEGATIVE, hogy az azonosító horgony-sarka a
    # Backplate csapjainak oldalával (PLUS_X) ellentétes (-X) oldalra
    # essen — a csap-protrúziók emiatt nem alakítják nem-téglalap alakúvá
    # az érintett sarkot (ugyanez a mintázat, mint a Numbering Engine
    # tesztjeiben, lásd test_numbering_engine.py).
    return NumberingParams(
        numbering_normal_axis=BackplateNormalAxis.PLUS_Y,
        numbering_direction_axis_sign=NumberingDirectionSign.NEGATIVE,
        numbering_height_mm=2.0,
    )


def _backplate_params() -> BackplateParams:
    return BackplateParams(
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
    )


def _spy(monkeypatch: pytest.MonkeyPatch, name: str) -> list[int]:
    """A `pipeline` modul egy engine-hívásának lecserélése egy számláló-wrapperre.

    A csomagolt (eredeti) függvényt továbbra is meghívja, csak a hívások
    számát rögzíti — így a pipeline downstream viselkedése valós marad,
    miközben ellenőrizhető, hogy egy adott engine-függvény lefutott-e.
    """
    calls: list[int] = []
    original = getattr(pipeline, name)

    def wrapper(*args: object, **kwargs: object) -> object:
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(pipeline, name, wrapper)
    return calls


def _placed_part_kinds(result: pipeline.PipelineResult) -> set[PartKind]:
    return {part.reference.kind for nest in result.nests for part in nest.placed_parts}


def test_run_pipeline_all_switches_true_produces_dxf_exports(tmp_path: Path) -> None:
    stl_path = _box_stl(tmp_path)
    output_dir = tmp_path / "out"
    output_dir.mkdir()

    config = PipelineConfig(
        use_dowels=True,
        use_spacers=True,
        use_backplate=True,
        mesh_import=MeshImportParams(file_path=stl_path),
        slicing=SliceParams(slice_thickness_mm=3.0, gap_mm=1.0),
        numbering=_numbering_params(),
        nesting=NestingParams(
            material_definitions=_materials(),
            slice_material_id="wood3",
            seam_marking_height_mm=2.0,
            backplate_material_id="wood3",
            spacer_material_id="wood1",
        ),
        dxf_export=DxfExportParams(output_directory=str(output_dir)),
        dowel=DowelParams(dowel_diameter_mm=4.0, spacer_diameter_mm=3.0),
        gap=GapParams(spacer_diameter_mm=3.0),
        backplate=_backplate_params(),
    )

    result = run_pipeline(config)

    assert len(result.dowel_positions) > 0
    assert len(result.spacers) > 0
    assert result.backplate is not None
    assert len(result.backplate.numbering_marks) > 0
    assert any(s.numbering_marks for s in result.slice_set.slices)
    assert len(result.nests) > 0
    assert len(result.exports) > 0
    for export in result.exports:
        assert (output_dir / export.filename).exists()


def test_run_pipeline_only_use_dowels_skips_gap_and_backplate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stl_path = _box_stl(tmp_path)
    gap_calls = _spy(monkeypatch, "apply_gap")
    backplate_calls = _spy(monkeypatch, "apply_backplate")
    tabs_calls = _spy(monkeypatch, "place_backplate_tabs")

    config = PipelineConfig(
        use_dowels=True,
        use_spacers=False,
        use_backplate=False,
        mesh_import=MeshImportParams(file_path=stl_path),
        slicing=SliceParams(slice_thickness_mm=3.0),
        numbering=_numbering_params(),
        nesting=NestingParams(
            material_definitions=_materials(),
            slice_material_id="wood3",
            seam_marking_height_mm=2.0,
        ),
        dxf_export=DxfExportParams(output_directory=str(tmp_path)),
        dowel=DowelParams(dowel_diameter_mm=4.0),
    )

    result = run_pipeline(config)

    assert gap_calls == []
    assert backplate_calls == []
    assert tabs_calls == []
    assert len(result.dowel_positions) > 0
    assert result.spacers == ()
    assert result.backplate is None
    assert _placed_part_kinds(result).isdisjoint(
        {PartKind.BACKPLATE, PartKind.SPACER_DISC}
    )
    assert len(result.exports) > 0


def test_run_pipeline_only_use_spacers_skips_dowel_and_backplate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stl_path = _box_stl(tmp_path)
    dowel_calls = _spy(monkeypatch, "apply_dowels")
    backplate_calls = _spy(monkeypatch, "apply_backplate")
    tabs_calls = _spy(monkeypatch, "place_backplate_tabs")

    config = PipelineConfig(
        use_dowels=False,
        use_spacers=True,
        use_backplate=False,
        mesh_import=MeshImportParams(file_path=stl_path),
        slicing=SliceParams(slice_thickness_mm=3.0, gap_mm=1.0),
        numbering=_numbering_params(),
        nesting=NestingParams(
            material_definitions=_materials(),
            slice_material_id="wood3",
            seam_marking_height_mm=2.0,
            spacer_material_id="wood1",
        ),
        dxf_export=DxfExportParams(output_directory=str(tmp_path)),
        gap=GapParams(spacer_diameter_mm=3.0),
    )

    result = run_pipeline(config)

    assert dowel_calls == []
    assert backplate_calls == []
    assert tabs_calls == []
    assert result.dowel_positions == ()
    assert len(result.spacers) > 0
    assert result.backplate is None
    assert PartKind.SPACER_DISC in _placed_part_kinds(result)
    assert PartKind.BACKPLATE not in _placed_part_kinds(result)


def test_run_pipeline_only_use_backplate_skips_dowel_and_gap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stl_path = _box_stl(tmp_path)
    dowel_calls = _spy(monkeypatch, "apply_dowels")
    gap_calls = _spy(monkeypatch, "apply_gap")

    config = PipelineConfig(
        use_dowels=False,
        use_spacers=False,
        use_backplate=True,
        mesh_import=MeshImportParams(file_path=stl_path),
        slicing=SliceParams(slice_thickness_mm=3.0),
        numbering=_numbering_params(),
        nesting=NestingParams(
            material_definitions=_materials(),
            slice_material_id="wood3",
            seam_marking_height_mm=2.0,
            backplate_material_id="wood3",
        ),
        dxf_export=DxfExportParams(output_directory=str(tmp_path)),
        backplate=_backplate_params(),
    )

    result = run_pipeline(config)

    assert dowel_calls == []
    assert gap_calls == []
    assert result.dowel_positions == ()
    assert result.spacers == ()
    assert result.backplate is not None
    assert len(result.backplate.numbering_marks) > 0
    assert any(s.numbering_marks for s in result.slice_set.slices)
    assert PartKind.BACKPLATE in _placed_part_kinds(result)
    assert PartKind.SPACER_DISC not in _placed_part_kinds(result)


def test_run_pipeline_all_switches_false_raises_before_any_engine_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stl_path = _box_stl(tmp_path)
    mesh_calls = _spy(monkeypatch, "import_mesh")

    config = PipelineConfig(
        use_dowels=False,
        use_spacers=False,
        use_backplate=False,
        mesh_import=MeshImportParams(file_path=stl_path),
        slicing=SliceParams(slice_thickness_mm=3.0),
        numbering=_numbering_params(),
        nesting=NestingParams(
            material_definitions=_materials(),
            slice_material_id="wood3",
            seam_marking_height_mm=2.0,
        ),
        dxf_export=DxfExportParams(output_directory=str(tmp_path)),
    )

    with pytest.raises(PipelineConfigurationError):
        run_pipeline(config)

    assert mesh_calls == []


def test_run_pipeline_use_dowels_without_dowel_params_raises(tmp_path: Path) -> None:
    stl_path = _box_stl(tmp_path)

    config = PipelineConfig(
        use_dowels=True,
        use_spacers=False,
        use_backplate=False,
        mesh_import=MeshImportParams(file_path=stl_path),
        slicing=SliceParams(slice_thickness_mm=3.0),
        numbering=_numbering_params(),
        nesting=NestingParams(
            material_definitions=_materials(),
            slice_material_id="wood3",
            seam_marking_height_mm=2.0,
        ),
        dxf_export=DxfExportParams(output_directory=str(tmp_path)),
        dowel=None,
    )

    with pytest.raises(PipelineConfigurationError):
        run_pipeline(config)


def test_run_pipeline_propagates_engine_exceptions_unmodified(tmp_path: Path) -> None:
    stl_path = _box_stl(tmp_path)

    config = PipelineConfig(
        use_dowels=True,
        use_spacers=False,
        use_backplate=False,
        mesh_import=MeshImportParams(file_path=stl_path),
        slicing=SliceParams(slice_thickness_mm=-1.0),
        numbering=_numbering_params(),
        nesting=NestingParams(
            material_definitions=_materials(),
            slice_material_id="wood3",
            seam_marking_height_mm=2.0,
        ),
        dxf_export=DxfExportParams(output_directory=str(tmp_path)),
        dowel=DowelParams(dowel_diameter_mm=4.0),
    )

    with pytest.raises(InvalidSliceError):
        run_pipeline(config)


def test_run_pipeline_mismatched_spacer_diameter_raises_before_any_engine_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stl_path = _box_stl(tmp_path)
    mesh_calls = _spy(monkeypatch, "import_mesh")

    config = PipelineConfig(
        use_dowels=True,
        use_spacers=True,
        use_backplate=False,
        mesh_import=MeshImportParams(file_path=stl_path),
        slicing=SliceParams(slice_thickness_mm=3.0, gap_mm=1.0),
        numbering=_numbering_params(),
        nesting=NestingParams(
            material_definitions=_materials(),
            slice_material_id="wood3",
            seam_marking_height_mm=2.0,
            spacer_material_id="wood1",
        ),
        dxf_export=DxfExportParams(output_directory=str(tmp_path)),
        dowel=DowelParams(dowel_diameter_mm=4.0, spacer_diameter_mm=3.0),
        gap=GapParams(spacer_diameter_mm=5.0),
    )

    with pytest.raises(PipelineConfigurationError):
        run_pipeline(config)

    assert mesh_calls == []
