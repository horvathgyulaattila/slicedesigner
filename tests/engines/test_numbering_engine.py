"""Tesztek a Numbering Engine 1. köréhez (NUMBERING_SPEC.md 6. szakasz, 1-5. lépés)."""

import logging

import pytest
import trimesh

from slicedesigner.engines.backplate_engine import (
    BackplateNormalAxis,
    apply_backplate,
    place_backplate_tabs,
)
from slicedesigner.engines.exceptions import InvalidNumberingError
from slicedesigner.engines.mesh_import import BoundingBox, Mesh
from slicedesigner.engines.numbering_engine import (
    NumberingDirectionSign,
    SliceNumberingOverride,
    apply_numbering,
    apply_numbering_to_backplate,
)
from slicedesigner.engines.slice_engine import (
    Contour,
    Slice,
    SliceAxis,
    SliceSet,
    create_slice_set,
)


def _mesh_from_trimesh(tm: trimesh.Trimesh, source_path: str = "test.stl") -> Mesh:
    bounds = tm.bounds
    bounding_box = BoundingBox(
        min=(float(bounds[0][0]), float(bounds[0][1]), float(bounds[0][2])),
        max=(float(bounds[1][0]), float(bounds[1][1]), float(bounds[1][2])),
    )
    return Mesh(
        vertices=tuple(tuple(float(c) for c in v) for v in tm.vertices),
        triangles=tuple(tuple(int(i) for i in f) for f in tm.faces),
        source_path=source_path,
        bounding_box=bounding_box,
        is_valid=True,
        warnings=(),
    )


def _make_box_slice_set(
    extents: tuple[float, float, float], slice_thickness_mm: float, gap_mm: float = 0.0
) -> SliceSet:
    box = trimesh.creation.box(extents=extents)
    mesh = _mesh_from_trimesh(box)
    return create_slice_set(mesh, slice_thickness_mm=slice_thickness_mm, gap_mm=gap_mm)


def _rect_contour(x_min: float, x_max: float, y_min: float, y_max: float) -> Contour:
    return Contour(
        points=(
            (x_min, y_min),
            (x_max, y_min),
            (x_max, y_max),
            (x_min, y_max),
        )
    )


def _make_hand_slice_set_numbering(
    slices_rects: list[list[tuple[float, float, float, float]]],
    thickness_mm: float = 3.0,
) -> SliceSet:
    slices = [
        Slice(
            thickness_mm=thickness_mm,
            contours=tuple(_rect_contour(*r) for r in rects),
            position_mm=(i - 0.5) * thickness_mm,
            index=i,
        )
        for i, rects in enumerate(slices_rects, start=1)
    ]
    all_x = [v for rects in slices_rects for r in rects for v in (r[0], r[1])]
    all_y = [v for rects in slices_rects for r in rects for v in (r[2], r[3])]
    bounding_box = BoundingBox(
        min=(min(all_x), min(all_y), 0.0),
        max=(max(all_x), max(all_y), len(slices_rects) * thickness_mm),
    )
    mesh = Mesh(
        vertices=((0.0, 0.0, 0.0),),
        triangles=(),
        source_path="hand-built.stl",
        bounding_box=bounding_box,
        is_valid=True,
        warnings=(),
    )
    return SliceSet(
        source_mesh=mesh,
        slice_axis=SliceAxis.Z,
        gap_mm=0.0,
        slices=tuple(slices),
        slice_count=len(slices_rects),
    )


def test_apply_numbering_simple_box_single_island() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    result = apply_numbering(
        slice_set,
        numbering_normal_axis=BackplateNormalAxis.PLUS_X,
        numbering_direction_axis_sign=NumberingDirectionSign.POSITIVE,
        numbering_height_mm=5.0,
    )

    for slice_ in result.slices:
        assert len(slice_.numbering_marks) == 1
        mark = slice_.numbering_marks[0]
        assert mark.text == str(slice_.index)
        assert mark.height_mm == pytest.approx(5.0)
        assert len(mark.strokes) > 0


def test_apply_numbering_multi_island_lettering_order() -> None:
    slice_set = _make_hand_slice_set_numbering(
        [[(-10.0, 10.0, 5.0, 15.0), (-10.0, 10.0, -15.0, -5.0)]]
    )

    result = apply_numbering(
        slice_set,
        numbering_normal_axis=BackplateNormalAxis.PLUS_X,
        numbering_direction_axis_sign=NumberingDirectionSign.POSITIVE,
        numbering_height_mm=5.0,
    )

    marks = result.slices[0].numbering_marks
    assert len(marks) == 2
    texts = {m.island_index: m.text for m in marks}
    assert texts[0] == "1/A"
    assert texts[1] == "1/B"


def test_apply_numbering_falls_back_to_min_height() -> None:
    slice_set = _make_hand_slice_set_numbering([[(6.15, 10.0, 11.15, 15.0)]])

    result = apply_numbering(
        slice_set,
        numbering_normal_axis=BackplateNormalAxis.PLUS_X,
        numbering_direction_axis_sign=NumberingDirectionSign.POSITIVE,
        numbering_height_mm=5.0,
    )

    mark = result.slices[0].numbering_marks[0]
    assert mark.height_mm == pytest.approx(2.5)


def test_apply_numbering_logs_warning_when_insufficient_space(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """NUMBERING_SPEC.md 6. szakasz 4. lépés (2026-08-04-i módosítás): a
    Slice-oldali azonosító elférő hely hiánya immár ugyanúgy csak
    figyelmeztetés, mint a Backplate-oldali analóg eset (lásd
    `test_apply_numbering_to_backplate_logs_warning_when_insufficient_space`)
    — korábban ez `InvalidNumberingError`-t dobott."""
    slice_set = _make_hand_slice_set_numbering([[(9.0, 10.0, 14.0, 15.0)]])

    with caplog.at_level(logging.WARNING):
        result = apply_numbering(
            slice_set,
            numbering_normal_axis=BackplateNormalAxis.PLUS_X,
            numbering_direction_axis_sign=NumberingDirectionSign.POSITIVE,
            numbering_height_mm=5.0,
        )

    assert len(result.slices[0].numbering_marks) == 0
    assert any(
        "numbering_min_height_mm" in record.getMessage() for record in caplog.records
    )


def test_apply_numbering_manual_position_used() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)
    override = SliceNumberingOverride(slice_index=1, manual_position=(0.0, 0.0))

    result = apply_numbering(
        slice_set,
        numbering_normal_axis=BackplateNormalAxis.PLUS_X,
        numbering_direction_axis_sign=NumberingDirectionSign.POSITIVE,
        numbering_height_mm=5.0,
        slice_numbering_overrides=(override,),
    )

    mark = result.slices[0].numbering_marks[0]
    all_points = [p for stroke in mark.strokes for p in stroke]
    xs = [p[0] for p in all_points]
    assert max(xs) == pytest.approx(0.0, abs=1e-6)


def test_apply_numbering_invalid_height_raises() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidNumberingError):
        apply_numbering(
            slice_set,
            numbering_normal_axis=BackplateNormalAxis.PLUS_X,
            numbering_direction_axis_sign=NumberingDirectionSign.POSITIVE,
            numbering_height_mm=0.0,
        )


def test_apply_numbering_invalid_min_height_raises() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidNumberingError):
        apply_numbering(
            slice_set,
            numbering_normal_axis=BackplateNormalAxis.PLUS_X,
            numbering_direction_axis_sign=NumberingDirectionSign.POSITIVE,
            numbering_height_mm=5.0,
            numbering_min_height_mm=10.0,
        )


def test_apply_numbering_negative_margin_raises() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidNumberingError):
        apply_numbering(
            slice_set,
            numbering_normal_axis=BackplateNormalAxis.PLUS_X,
            numbering_direction_axis_sign=NumberingDirectionSign.POSITIVE,
            numbering_height_mm=5.0,
            numbering_margin_mm=-1.0,
        )


def test_apply_numbering_matching_axis_raises() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidNumberingError):
        apply_numbering(
            slice_set,
            numbering_normal_axis=BackplateNormalAxis.PLUS_Z,
            numbering_direction_axis_sign=NumberingDirectionSign.POSITIVE,
            numbering_height_mm=5.0,
        )


def _make_numbered_backplate_fixture(
    numbering_height_mm: float,
) -> tuple[SliceSet, object, tuple[object, ...]]:
    """Segédfüggvény: Backplate + Tab-lista + Slice-oldali numerázott Slice Set."""
    slice_set = _make_box_slice_set(
        extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0, gap_mm=1.0
    )

    slice_set_with_tabs, tabs = place_backplate_tabs(
        slice_set,
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
    )
    _slice_set_dup, backplate = apply_backplate(
        slice_set,
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
    )

    # A Slice-oldali azonosító tengelye szándékosan eltér a Backplate
    # csapjainak tengelyétől (PLUS_X) — a kettő a specifikáció szerint
    # független, és a csap-módosított sziget geometriájának PLUS_X-oldali
    # sarka a fészek-protrúzió miatt nem egyenletes téglalap többé.
    numbered_slice_set = apply_numbering(
        slice_set_with_tabs,
        numbering_normal_axis=BackplateNormalAxis.PLUS_Y,
        numbering_direction_axis_sign=NumberingDirectionSign.NEGATIVE,
        numbering_height_mm=numbering_height_mm,
    )

    return numbered_slice_set, backplate, tabs


def test_apply_numbering_to_backplate_marks_connected_islands() -> None:
    numbered_slice_set, backplate, tabs = _make_numbered_backplate_fixture(2.0)

    result_backplate = apply_numbering_to_backplate(
        numbered_slice_set, backplate, tabs, numbering_height_mm=2.0
    )

    assert len(result_backplate.numbering_marks) == 4
    for mark in result_backplate.numbering_marks:
        assert len(mark.strokes) > 0


def test_apply_numbering_to_backplate_logs_warning_when_insufficient_space(
    caplog: pytest.LogCaptureFixture,
) -> None:
    numbered_slice_set, backplate, tabs = _make_numbered_backplate_fixture(2.0)

    with caplog.at_level(logging.WARNING):
        result_backplate = apply_numbering_to_backplate(
            numbered_slice_set, backplate, tabs, numbering_height_mm=50.0
        )

    assert len(result_backplate.numbering_marks) == 0
    assert any(
        "numbering_min_height_mm" in record.getMessage() for record in caplog.records
    )


def test_apply_numbering_to_backplate_invalid_height_raises() -> None:
    numbered_slice_set, backplate, tabs = _make_numbered_backplate_fixture(2.0)

    with pytest.raises(InvalidNumberingError):
        apply_numbering_to_backplate(
            numbered_slice_set, backplate, tabs, numbering_height_mm=0.0
        )


def test_apply_numbering_to_backplate_invalid_min_height_raises() -> None:
    numbered_slice_set, backplate, tabs = _make_numbered_backplate_fixture(2.0)

    with pytest.raises(InvalidNumberingError):
        apply_numbering_to_backplate(
            numbered_slice_set,
            backplate,
            tabs,
            numbering_height_mm=2.0,
            numbering_min_height_mm=5.0,
        )


def test_apply_numbering_to_backplate_negative_margin_raises() -> None:
    numbered_slice_set, backplate, tabs = _make_numbered_backplate_fixture(2.0)

    with pytest.raises(InvalidNumberingError):
        apply_numbering_to_backplate(
            numbered_slice_set,
            backplate,
            tabs,
            numbering_height_mm=2.0,
            numbering_margin_mm=-1.0,
        )
