"""Tesztek a DXF Export Engine-hez (DXF_EXPORT_SPEC.md 6. szakasz)."""

from pathlib import Path

import ezdxf
import pytest

from slicedesigner.engines.dxf_export_engine import export_nests_to_dxf
from slicedesigner.engines.exceptions import InvalidDxfExportError
from slicedesigner.engines.nesting_engine import (
    Nest,
    PartKind,
    PartReference,
    PlacedPart,
)
from slicedesigner.engines.slice_engine import Contour, EngravingMark


def _make_part(slice_index: int, sheet_number: int) -> PlacedPart:
    contour = Contour(points=((0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)))
    mark = EngravingMark(
        text=str(slice_index),
        strokes=(((1.0, 1.0), (2.0, 2.0)),),
        height_mm=2.0,
        island_index=0,
    )
    return PlacedPart(
        reference=PartReference(
            kind=PartKind.SLICE_ISLAND, slice_index=slice_index, island_index=0
        ),
        sheet_number=sheet_number,
        position=(0.0, 0.0),
        rotation_deg=0.0,
        contours=(contour,),
        numbering_marks=(mark,),
    )


def test_export_nests_to_dxf_creates_file(tmp_path: Path) -> None:
    nest = Nest(
        material_id="wood3", sheet_count=1, placed_parts=(_make_part(1, 1),), seams=()
    )

    exports = export_nests_to_dxf((nest,), output_directory=str(tmp_path))

    assert len(exports) == 1
    export = exports[0]
    assert export.material_id == "wood3"
    assert export.sheet_number == 1
    assert export.filename == "wood3_sheet1.dxf"
    assert export.layer_names == ("CUT", "ENGRAVE")
    assert export.dxf_version == "R12"
    assert (tmp_path / export.filename).exists()


def test_export_nests_to_dxf_content_has_correct_layers_and_entities(
    tmp_path: Path,
) -> None:
    nest = Nest(
        material_id="wood3", sheet_count=1, placed_parts=(_make_part(1, 1),), seams=()
    )

    exports = export_nests_to_dxf((nest,), output_directory=str(tmp_path))

    doc = ezdxf.readfile(str(tmp_path / exports[0].filename))
    layer_names = {layer.dxf.name for layer in doc.layers}
    assert "CUT" in layer_names
    assert "ENGRAVE" in layer_names

    msp = doc.modelspace()
    cut_entities = [e for e in msp if e.dxf.layer == "CUT"]
    engrave_entities = [e for e in msp if e.dxf.layer == "ENGRAVE"]
    assert len(cut_entities) == 1
    assert len(engrave_entities) == 1


def test_export_nests_to_dxf_empty_nests_raises(tmp_path: Path) -> None:
    with pytest.raises(InvalidDxfExportError):
        export_nests_to_dxf((), output_directory=str(tmp_path))


def test_export_nests_to_dxf_invalid_version_raises(tmp_path: Path) -> None:
    nest = Nest(
        material_id="wood3", sheet_count=1, placed_parts=(_make_part(1, 1),), seams=()
    )

    with pytest.raises(InvalidDxfExportError):
        export_nests_to_dxf(
            (nest,), output_directory=str(tmp_path), dxf_version="NOT_A_VERSION"
        )


def test_export_nests_to_dxf_filename_collision_raises(tmp_path: Path) -> None:
    nest = Nest(
        material_id="wood3",
        sheet_count=2,
        placed_parts=(_make_part(1, 1), _make_part(2, 2)),
        seams=(),
    )

    with pytest.raises(InvalidDxfExportError):
        export_nests_to_dxf(
            (nest,),
            output_directory=str(tmp_path),
            output_filename_pattern="fixed_name",
        )


def test_export_nests_to_dxf_multiple_sheets(tmp_path: Path) -> None:
    nest = Nest(
        material_id="wood3",
        sheet_count=2,
        placed_parts=(_make_part(1, 1), _make_part(2, 2)),
        seams=(),
    )

    exports = export_nests_to_dxf((nest,), output_directory=str(tmp_path))

    assert len(exports) == 2
    filenames = {e.filename for e in exports}
    assert filenames == {"wood3_sheet1.dxf", "wood3_sheet2.dxf"}
    for export in exports:
        assert (tmp_path / export.filename).exists()


def test_export_nests_to_dxf_custom_layer_names(tmp_path: Path) -> None:
    nest = Nest(
        material_id="wood3", sheet_count=1, placed_parts=(_make_part(1, 1),), seams=()
    )

    exports = export_nests_to_dxf(
        (nest,),
        output_directory=str(tmp_path),
        cut_layer_name="MYCUT",
        engrave_layer_name="MYENGRAVE",
    )

    assert exports[0].layer_names == ("MYCUT", "MYENGRAVE")
    doc = ezdxf.readfile(str(tmp_path / exports[0].filename))
    layer_names = {layer.dxf.name for layer in doc.layers}
    assert "MYCUT" in layer_names
    assert "MYENGRAVE" in layer_names
