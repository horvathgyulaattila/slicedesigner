"""Tesztek a Slice Engine-hez (SLICE_ENGINE_SPEC.md)."""

import logging

import pytest
import trimesh

from slicedesigner.engines.exceptions import InvalidSliceError
from slicedesigner.engines.mesh_import import BoundingBox, Mesh
from slicedesigner.engines.slice_engine import create_slice_set


def _mesh_from_trimesh(tm: trimesh.Trimesh, source_path: str = "test.stl") -> Mesh:
    """Egy trimesh.Trimesh objektumból közvetlenül Mesh domain objektum építése."""
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


def _signed_area(points: tuple[tuple[float, float], ...]) -> float:
    """Előjeles terület (shoelace formula); pozitív = CCW, negatív = CW."""
    area = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return area / 2.0


def test_create_slice_set_no_scaling_needed_zero_gap(
    caplog: pytest.LogCaptureFixture,
) -> None:
    box = trimesh.creation.box(extents=(20.0, 20.0, 30.0))
    mesh = _mesh_from_trimesh(box)

    with caplog.at_level(logging.WARNING):
        slice_set = create_slice_set(mesh, slice_thickness_mm=3.0)

    assert slice_set.slice_count == 10
    assert slice_set.source_mesh is mesh
    assert slice_set.gap_mm == 0.0
    assert not any("átskálázva" in record.getMessage() for record in caplog.records)

    first_slice = slice_set.slices[0]
    assert first_slice.thickness_mm == 3.0
    assert first_slice.index == 1
    assert first_slice.position_mm == pytest.approx(1.5)
    assert len(first_slice.contours) == 1

    contour = first_slice.contours[0]
    xs = [p[0] for p in contour.points]
    ys = [p[1] for p in contour.points]
    assert min(xs) == pytest.approx(-10.0)
    assert max(xs) == pytest.approx(10.0)
    assert min(ys) == pytest.approx(-10.0)
    assert max(ys) == pytest.approx(10.0)
    assert _signed_area(contour.points) > 0  # CCW = szilárd anyag határa


def test_create_slice_set_positions_with_gap() -> None:
    box = trimesh.creation.box(extents=(20.0, 20.0, 14.0))
    mesh = _mesh_from_trimesh(box)

    slice_set = create_slice_set(mesh, slice_thickness_mm=2.0, gap_mm=1.0)

    assert slice_set.slice_count == 5
    assert slice_set.gap_mm == 1.0
    expected_positions = [1.0, 4.0, 7.0, 10.0, 13.0]
    actual_positions = [s.position_mm for s in slice_set.slices]
    assert actual_positions == pytest.approx(expected_positions)
    assert [s.index for s in slice_set.slices] == [1, 2, 3, 4, 5]


def test_create_slice_set_applies_scaling_within_tolerance(
    caplog: pytest.LogCaptureFixture,
) -> None:
    box = trimesh.creation.box(extents=(20.0, 20.0, 30.2))
    mesh = _mesh_from_trimesh(box)

    with caplog.at_level(logging.WARNING):
        slice_set = create_slice_set(mesh, slice_thickness_mm=3.0)

    assert slice_set.slice_count == 10
    assert any("átskálázva" in record.getMessage() for record in caplog.records)
    assert len(slice_set.slices) == 10


def test_create_slice_set_scaling_exceeds_tolerance_raises() -> None:
    box = trimesh.creation.box(extents=(20.0, 20.0, 40.0))
    mesh = _mesh_from_trimesh(box)

    with pytest.raises(InvalidSliceError):
        create_slice_set(mesh, slice_thickness_mm=3.0)


def test_create_slice_set_invalid_thickness_raises() -> None:
    box = trimesh.creation.box(extents=(10.0, 10.0, 10.0))
    mesh = _mesh_from_trimesh(box)

    with pytest.raises(InvalidSliceError):
        create_slice_set(mesh, slice_thickness_mm=0.0)


def test_create_slice_set_negative_gap_raises() -> None:
    box = trimesh.creation.box(extents=(10.0, 10.0, 10.0))
    mesh = _mesh_from_trimesh(box)

    with pytest.raises(InvalidSliceError):
        create_slice_set(mesh, slice_thickness_mm=2.0, gap_mm=-1.0)


def test_create_slice_set_empty_mesh_raises() -> None:
    empty_mesh = Mesh(
        vertices=(),
        triangles=(),
        source_path="empty.stl",
        bounding_box=BoundingBox(min=(0.0, 0.0, 0.0), max=(0.0, 0.0, 0.0)),
        is_valid=True,
        warnings=(),
    )

    with pytest.raises(InvalidSliceError):
        create_slice_set(empty_mesh, slice_thickness_mm=1.0)


def test_create_slice_set_zero_axis_size_raises() -> None:
    flat_mesh = Mesh(
        vertices=((0.0, 0.0, 5.0), (10.0, 0.0, 5.0), (0.0, 10.0, 5.0)),
        triangles=((0, 1, 2),),
        source_path="flat.stl",
        bounding_box=BoundingBox(min=(0.0, 0.0, 5.0), max=(10.0, 10.0, 5.0)),
        is_valid=True,
        warnings=(),
    )

    with pytest.raises(InvalidSliceError):
        create_slice_set(flat_mesh, slice_thickness_mm=1.0)


def test_create_slice_set_insufficient_slice_count_raises() -> None:
    box = trimesh.creation.box(extents=(10.0, 10.0, 1.0))
    mesh = _mesh_from_trimesh(box)

    with pytest.raises(InvalidSliceError):
        create_slice_set(mesh, slice_thickness_mm=10.0)
