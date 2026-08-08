"""Tesztek a Slice Engine-hez (SLICE_ENGINE_SPEC.md)."""

import logging

import pytest
import trimesh
from shapely.geometry import Polygon

from slicedesigner.engines.exceptions import InvalidSliceError
from slicedesigner.engines.mesh_import import BoundingBox, Mesh
from slicedesigner.engines.slice_engine import SliceAxis, create_slice_set


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


# Aszimmetrikus "L" alakú keresztmetszet: egy 20x20-as négyzetből a
# (15,15)-(20,20) saroknégyzet hiányzik. A hiányzó sarok a pozitív
# tartomány (nagy x, nagy y) felé esik — ha a kontúr tükröződne, a hiány
# a negatív (vagy más) sarokban jelenne meg, ami az alábbi tesztekben
# konkrétan ellenőrzött.
_L_SHAPE: tuple[tuple[float, float], ...] = (
    (0.0, 0.0),
    (20.0, 0.0),
    (20.0, 15.0),
    (15.0, 15.0),
    (15.0, 20.0),
    (0.0, 20.0),
)


def _extrude_l_shape(height: float) -> trimesh.Trimesh:
    """Az `_L_SHAPE` CCW sokszög +Z menti extrudálása watertight háromszög-hálóvá.

    Kézzel épített (nem `trimesh.creation.extrude_polygon`, mert az egy
    külső triangulációs motort igényelne, ami a teszt-környezetben nem
    elérhető).
    """
    n = len(_L_SHAPE)
    bottom = [(x, y, 0.0) for x, y in _L_SHAPE]
    top = [(x, y, height) for x, y in _L_SHAPE]
    vertices = bottom + top
    faces: list[tuple[int, int, int]] = []
    for i in range(1, n - 1):
        faces.append((0, i + 1, i))
    for i in range(1, n - 1):
        faces.append((n, n + i, n + i + 1))
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j))
        faces.append((i, n + j, n + i))
    return trimesh.Trimesh(vertices=vertices, faces=faces)


def _assert_l_shape_contour_not_mirrored(
    points: tuple[tuple[float, float], ...],
) -> None:
    """A kontúr valóban az `_L_SHAPE`-nek megfelelő, pozitív, nem tükrözött
    elhelyezkedésű-e."""
    polygon = Polygon(points)
    min_x, min_y, max_x, max_y = polygon.bounds
    assert min_x == pytest.approx(0.0, abs=1e-6)
    assert min_y == pytest.approx(0.0, abs=1e-6)
    assert max_x == pytest.approx(20.0)
    assert max_y == pytest.approx(20.0)

    # A hiányzó sarok (15,15)-(20,20) belseje: nem szabad, hogy anyag legyen.
    assert not polygon.contains(Polygon([(16, 16), (19, 16), (19, 19), (16, 19)]))
    # A megmaradt "L" szárak belseje: legyen anyag.
    assert polygon.contains(Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]))
    assert polygon.contains(Polygon([(18, 1), (19, 1), (19, 2), (18, 2)]))
    assert polygon.contains(Polygon([(1, 18), (2, 18), (2, 19), (1, 19)]))


def test_create_slice_set_x_axis_contour_not_mirrored() -> None:
    """X tengelyű szeletelésnél a kontúr két koordinátája világ +Y, +Z —
    nem tükrözött (l. a Slice Engine `_TO_2D_ROTATION` javítását)."""
    # Ciklikus permutáció (forgatás): world_x = local_z, world_y = local_x,
    # world_z = local_y — így az extrudálási tengely (local z) world X
    # lesz, a keresztmetszet (local x, local y) pedig world (Y, Z).
    extruded = _extrude_l_shape(height=10.0)
    extruded.apply_transform(
        [
            [0.0, 0.0, 1.0, 0.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    mesh = _mesh_from_trimesh(extruded)

    slice_set = create_slice_set(mesh, slice_thickness_mm=10.0, slice_axis=SliceAxis.X)

    assert slice_set.slice_count == 1
    contour = slice_set.slices[0].contours[0]
    _assert_l_shape_contour_not_mirrored(contour.points)


def test_create_slice_set_y_axis_contour_not_mirrored() -> None:
    """Y tengelyű szeletelésnél a kontúr két koordinátája világ +Z, +X —
    nem tükrözött (l. a Slice Engine `_TO_2D_ROTATION` javítását)."""
    # Ciklikus permutáció (forgatás): world_x = local_y, world_y = local_z,
    # world_z = local_x — így az extrudálási tengely (local z) world Y
    # lesz, a keresztmetszet (local x, local y) pedig world (Z, X).
    extruded = _extrude_l_shape(height=10.0)
    extruded.apply_transform(
        [
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    mesh = _mesh_from_trimesh(extruded)

    slice_set = create_slice_set(mesh, slice_thickness_mm=10.0, slice_axis=SliceAxis.Y)

    assert slice_set.slice_count == 1
    contour = slice_set.slices[0].contours[0]
    _assert_l_shape_contour_not_mirrored(contour.points)
