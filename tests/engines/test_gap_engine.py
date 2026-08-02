"""Tesztek a Gap Engine-hez (GAP_SYSTEM_SPEC.md)."""

import pytest
import trimesh

from slicedesigner.engines.dowel_engine import apply_dowels
from slicedesigner.engines.exceptions import InvalidGapError
from slicedesigner.engines.gap_engine import apply_gap
from slicedesigner.engines.mesh_import import BoundingBox, Mesh
from slicedesigner.engines.slice_engine import SliceSet, create_slice_set


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


def test_apply_gap_zero_gap_returns_empty() -> None:
    slice_set = _make_box_slice_set(
        extents=(30.0, 30.0, 15.0), slice_thickness_mm=3.0, gap_mm=0.0
    )

    result_slice_set, spacers = apply_gap(slice_set, spacer_diameter_mm=3.0)

    assert spacers == ()
    assert result_slice_set is slice_set


def test_apply_gap_places_default_count_without_dowels() -> None:
    slice_set = _make_box_slice_set(
        extents=(30.0, 30.0, 14.0), slice_thickness_mm=2.0, gap_mm=1.0
    )

    _slice_set, spacers = apply_gap(slice_set, spacer_diameter_mm=3.0)

    assert len(spacers) == 12  # 5 szelet -> 4 Gap, egyenként 3 (alapértelmezett cél)
    start_indices = {s.start_slice_index for s in spacers}
    assert start_indices == {1, 2, 3, 4}
    for spacer in spacers:
        assert spacer.diameter_mm == 3.0
        assert spacer.thickness_mm == 1.0
        assert spacer.shape == "cylinder"


def test_apply_gap_reuses_dowel_position_despite_hole() -> None:
    slice_set = _make_box_slice_set(
        extents=(30.0, 30.0, 14.0), slice_thickness_mm=2.0, gap_mm=1.0
    )
    slice_set, dowel_positions = apply_dowels(
        slice_set, dowel_diameter_mm=3.0, dowel_count_per_region=1
    )

    assert len(dowel_positions) == 1
    dowel = dowel_positions[0]
    assert dowel.start_slice_index == 1
    assert dowel.end_slice_index == 5

    _final_slice_set, spacers = apply_gap(
        slice_set,
        spacer_diameter_mm=3.0,
        dowel_positions=dowel_positions,
        spacer_count_per_gap=1,
        min_spacers_per_region=1,
    )

    assert len(spacers) == 4  # 5 szelet -> 4 Gap
    for spacer in spacers:
        assert spacer.x_mm == pytest.approx(dowel.x_mm)
        assert spacer.y_mm == pytest.approx(dowel.y_mm)
        assert spacer.diameter_mm == 3.0
        assert spacer.thickness_mm == 1.0
    start_indices = sorted(s.start_slice_index for s in spacers)
    assert start_indices == [1, 2, 3, 4]


def test_apply_gap_insufficient_region_raises() -> None:
    slice_set = _make_box_slice_set(
        extents=(2.0, 2.0, 14.0), slice_thickness_mm=2.0, gap_mm=1.0
    )

    with pytest.raises(InvalidGapError):
        apply_gap(slice_set, spacer_diameter_mm=10.0)


def test_apply_gap_invalid_diameter_raises() -> None:
    slice_set = _make_box_slice_set(
        extents=(30.0, 30.0, 14.0), slice_thickness_mm=2.0, gap_mm=1.0
    )

    with pytest.raises(InvalidGapError):
        apply_gap(slice_set, spacer_diameter_mm=0.0)


def test_apply_gap_invalid_count_per_gap_raises() -> None:
    slice_set = _make_box_slice_set(
        extents=(30.0, 30.0, 14.0), slice_thickness_mm=2.0, gap_mm=1.0
    )

    with pytest.raises(InvalidGapError):
        apply_gap(slice_set, spacer_diameter_mm=3.0, spacer_count_per_gap=0)


def test_apply_gap_min_greater_than_count_raises() -> None:
    slice_set = _make_box_slice_set(
        extents=(30.0, 30.0, 14.0), slice_thickness_mm=2.0, gap_mm=1.0
    )

    with pytest.raises(InvalidGapError):
        apply_gap(
            slice_set,
            spacer_diameter_mm=3.0,
            spacer_count_per_gap=2,
            min_spacers_per_region=3,
        )
