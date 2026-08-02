"""Tesztek a Dowel Engine-hez (DOWEL_SYSTEM_SPEC.md)."""

import pytest
import trimesh

from slicedesigner.engines.dowel_engine import ManualDowelPosition, apply_dowels
from slicedesigner.engines.exceptions import InvalidDowelError
from slicedesigner.engines.mesh_import import BoundingBox, Mesh
from slicedesigner.engines.slice_engine import (
    Contour,
    HoleKind,
    Slice,
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
    extents: tuple[float, float, float], slice_thickness_mm: float
) -> SliceSet:
    box = trimesh.creation.box(extents=extents)
    mesh = _mesh_from_trimesh(box)
    return create_slice_set(mesh, slice_thickness_mm=slice_thickness_mm)


def _square_contour(cx: float, cy: float, half: float) -> Contour:
    return Contour(
        points=(
            (cx - half, cy - half),
            (cx + half, cy - half),
            (cx + half, cy + half),
            (cx - half, cy + half),
        )
    )


def _make_two_column_slice_set(thickness_mm: float = 3.0) -> SliceSet:
    columns = [(0.0, 0.0), (90.0, 0.0)]
    slices = []
    for index in (1, 2):
        contours = tuple(_square_contour(cx, cy, 10.0) for cx, cy in columns)
        slices.append(
            Slice(
                thickness_mm=thickness_mm,
                contours=contours,
                position_mm=(index - 0.5) * thickness_mm,
                index=index,
            )
        )
    bounding_box = BoundingBox(
        min=(-10.0, -10.0, 0.0), max=(100.0, 10.0, 2 * thickness_mm)
    )
    mesh = Mesh(
        vertices=((0.0, 0.0, 0.0),),
        triangles=(),
        source_path="hand-built.stl",
        bounding_box=bounding_box,
        is_valid=True,
        warnings=(),
    )
    return SliceSet(source_mesh=mesh, gap_mm=0.0, slices=tuple(slices), slice_count=2)


def test_apply_dowels_simple_box_places_default_count_spanning_full_stack() -> None:
    slice_set = _make_box_slice_set(extents=(30.0, 30.0, 15.0), slice_thickness_mm=3.0)

    modified, positions = apply_dowels(slice_set, dowel_diameter_mm=4.0)

    assert len(positions) == 3
    for dowel in positions:
        assert dowel.start_slice_index == 1
        assert dowel.end_slice_index == 5
        assert dowel.length_mm == pytest.approx(15.0)
        assert dowel.diameter_mm == 4.0
        assert dowel.region_id == 1
    assert len(modified.slices) == 5


def test_apply_dowels_accepts_manual_position() -> None:
    slice_set = _make_box_slice_set(extents=(30.0, 30.0, 15.0), slice_thickness_mm=3.0)
    manual = ManualDowelPosition(
        x_mm=0.0, y_mm=0.0, start_slice_index=1, end_slice_index=5
    )

    _modified, positions = apply_dowels(
        slice_set,
        dowel_diameter_mm=4.0,
        dowel_count_per_region=1,
        manual_dowel_positions=(manual,),
    )

    assert len(positions) == 1
    assert positions[0].x_mm == 0.0
    assert positions[0].y_mm == 0.0
    assert positions[0].start_slice_index == 1
    assert positions[0].end_slice_index == 5


def test_apply_dowels_invalid_manual_position_raises() -> None:
    slice_set = _make_box_slice_set(extents=(30.0, 30.0, 15.0), slice_thickness_mm=3.0)
    manual = ManualDowelPosition(
        x_mm=1000.0, y_mm=1000.0, start_slice_index=1, end_slice_index=5
    )

    with pytest.raises(InvalidDowelError):
        apply_dowels(slice_set, dowel_diameter_mm=4.0, manual_dowel_positions=(manual,))


def test_apply_dowels_overlapping_manual_positions_raise() -> None:
    slice_set = _make_box_slice_set(extents=(30.0, 30.0, 15.0), slice_thickness_mm=3.0)
    manual_a = ManualDowelPosition(
        x_mm=0.0, y_mm=0.0, start_slice_index=1, end_slice_index=3
    )
    manual_b = ManualDowelPosition(
        x_mm=0.0, y_mm=0.0, start_slice_index=2, end_slice_index=4
    )

    with pytest.raises(InvalidDowelError):
        apply_dowels(
            slice_set,
            dowel_diameter_mm=4.0,
            manual_dowel_positions=(manual_a, manual_b),
        )


def test_apply_dowels_insufficient_region_raises() -> None:
    slice_set = _make_box_slice_set(extents=(30.0, 30.0, 3.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidDowelError):
        apply_dowels(slice_set, dowel_diameter_mm=4.0)


def test_apply_dowels_two_disconnected_regions() -> None:
    slice_set = _make_two_column_slice_set()

    _modified, positions = apply_dowels(
        slice_set,
        dowel_diameter_mm=4.0,
        dowel_count_per_region=1,
        min_dowels_per_region=1,
    )

    assert len(positions) == 2
    region_ids = {p.region_id for p in positions}
    assert len(region_ids) == 2
    for dowel in positions:
        assert dowel.start_slice_index == 1
        assert dowel.end_slice_index == 2


def test_apply_dowels_cuts_blind_and_through_holes() -> None:
    slice_set = _make_box_slice_set(extents=(30.0, 30.0, 15.0), slice_thickness_mm=3.0)

    modified, _positions = apply_dowels(
        slice_set, dowel_diameter_mm=4.0, dowel_count_per_region=1
    )

    slices_by_index = {s.index: s for s in modified.slices}
    first_slice_holes = [
        c for c in slices_by_index[1].contours if c.hole_kind is not None
    ]
    middle_slice_holes = [
        c for c in slices_by_index[3].contours if c.hole_kind is not None
    ]
    last_slice_holes = [
        c for c in slices_by_index[5].contours if c.hole_kind is not None
    ]

    assert len(first_slice_holes) == 1
    assert first_slice_holes[0].hole_kind == HoleKind.DOWEL_BLIND
    assert first_slice_holes[0].depth_mm == pytest.approx(3.0 - 0.3 * 3.0)

    assert len(middle_slice_holes) == 1
    assert middle_slice_holes[0].hole_kind == HoleKind.DOWEL_THROUGH
    assert middle_slice_holes[0].depth_mm == pytest.approx(3.0)

    assert len(last_slice_holes) == 1
    assert last_slice_holes[0].hole_kind == HoleKind.DOWEL_BLIND


def test_apply_dowels_invalid_diameter_raises() -> None:
    slice_set = _make_box_slice_set(extents=(30.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidDowelError):
        apply_dowels(slice_set, dowel_diameter_mm=0.0)


def test_apply_dowels_negative_spacer_diameter_raises() -> None:
    slice_set = _make_box_slice_set(extents=(30.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidDowelError):
        apply_dowels(slice_set, dowel_diameter_mm=4.0, spacer_diameter_mm=-1.0)


def test_apply_dowels_invalid_dowel_count_per_region_raises() -> None:
    slice_set = _make_box_slice_set(extents=(30.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidDowelError):
        apply_dowels(slice_set, dowel_diameter_mm=4.0, dowel_count_per_region=0)


def test_apply_dowels_min_dowels_greater_than_count_raises() -> None:
    slice_set = _make_box_slice_set(extents=(30.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidDowelError):
        apply_dowels(
            slice_set,
            dowel_diameter_mm=4.0,
            dowel_count_per_region=2,
            min_dowels_per_region=3,
        )


def test_apply_dowels_invalid_blind_hole_cap_raises() -> None:
    slice_set = _make_box_slice_set(extents=(30.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidDowelError):
        apply_dowels(slice_set, dowel_diameter_mm=4.0, blind_hole_cap_mm=100.0)
