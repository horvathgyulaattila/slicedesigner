"""Tiszta, Qt-független unit tesztek a `render_geometry.py` geometriai
segédfüggvényeihez (prompt 8. szakasz)."""

from __future__ import annotations

import math

import trimesh

from slicedesigner.engines.dowel_engine import DowelPosition
from slicedesigner.engines.gap_engine import Spacer
from slicedesigner.engines.mesh_import import BoundingBox, Mesh
from slicedesigner.engines.slice_engine import (
    Contour,
    HoleKind,
    Slice,
    SliceAxis,
    SliceSet,
)
from slicedesigner.gui.render_geometry import (
    dowel_hole_contours_to_polydata,
    dowel_positions_to_polydata,
    mesh_to_polydata,
    slice_set_to_polydata,
    spacers_to_polydata,
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


def _empty_mesh() -> Mesh:
    return Mesh(
        vertices=(),
        triangles=(),
        source_path="empty.stl",
        bounding_box=BoundingBox(min=(0.0, 0.0, 0.0), max=(0.0, 0.0, 0.0)),
        is_valid=True,
        warnings=(),
    )


def _ccw_square(cx: float, cy: float, half: float) -> Contour:
    return Contour(
        points=(
            (cx - half, cy - half),
            (cx + half, cy - half),
            (cx + half, cy + half),
            (cx - half, cy + half),
        )
    )


def _cw_square(cx: float, cy: float, half: float) -> Contour:
    return Contour(
        points=(
            (cx - half, cy - half),
            (cx - half, cy + half),
            (cx + half, cy + half),
            (cx + half, cy - half),
        )
    )


def _dowel_hole_cw_circle(
    cx: float, cy: float, radius: float, *, segments: int = 8
) -> Contour:
    points = tuple(
        (
            cx + radius * math.cos(-2 * math.pi * i / segments),
            cy + radius * math.sin(-2 * math.pi * i / segments),
        )
        for i in range(segments)
    )
    return Contour(points=points, hole_kind=HoleKind.DOWEL_THROUGH, depth_mm=3.0)


def _dowel_position(
    *,
    x_mm: float = 0.0,
    y_mm: float = 0.0,
    diameter_mm: float = 4.0,
    start_slice_index: int,
    end_slice_index: int,
) -> DowelPosition:
    return DowelPosition(
        x_mm=x_mm,
        y_mm=y_mm,
        diameter_mm=diameter_mm,
        # Szándékosan hibás/eltérő a ténylegesen elvártól — a tesztnek azt
        # kell igazolnia, hogy `dowel_positions_to_polydata()` a hosszt a
        # Slice-okból számolja újra, nem ezt a mezőt trusztolja.
        length_mm=-1.0,
        start_slice_index=start_slice_index,
        end_slice_index=end_slice_index,
        region_id=1,
    )


def _spacer(
    *,
    x_mm: float = 0.0,
    y_mm: float = 0.0,
    diameter_mm: float = 4.0,
    thickness_mm: float,
    start_slice_index: int,
) -> Spacer:
    return Spacer(
        shape="cylinder",
        x_mm=x_mm,
        y_mm=y_mm,
        diameter_mm=diameter_mm,
        thickness_mm=thickness_mm,
        start_slice_index=start_slice_index,
        region_id=1,
    )


def test_mesh_to_polydata_box_has_matching_vertex_and_triangle_counts() -> None:
    box = trimesh.creation.box(extents=(10.0, 20.0, 5.0))
    mesh = _mesh_from_trimesh(box)

    polydata = mesh_to_polydata(mesh)

    assert polydata.n_points == box.vertices.shape[0]
    assert polydata.n_cells == box.faces.shape[0]


def test_mesh_to_polydata_empty_mesh_returns_empty_polydata() -> None:
    polydata = mesh_to_polydata(_empty_mesh())

    assert polydata.n_points == 0
    assert polydata.n_cells == 0


def test_slice_set_to_polydata_empty_slice_set_returns_empty_polydata() -> None:
    slice_set = SliceSet(
        source_mesh=_empty_mesh(), gap_mm=0.0, slices=(), slice_count=0
    )

    polydata = slice_set_to_polydata(slice_set)

    assert polydata.n_points == 0
    assert polydata.n_cells == 0


def test_slice_set_to_polydata_single_slice_no_hole_extrudes_solid_bounds() -> None:
    thickness_mm = 3.0
    position_mm = thickness_mm / 2
    slice_ = Slice(
        thickness_mm=thickness_mm,
        contours=(_ccw_square(cx=0.0, cy=0.0, half=10.0),),
        position_mm=position_mm,
        index=1,
    )
    slice_set = SliceSet(
        source_mesh=_empty_mesh(),
        gap_mm=0.0,
        slices=(slice_,),
        slice_count=1,
        slice_axis=SliceAxis.Z,
    )

    polydata = slice_set_to_polydata(slice_set)

    assert polydata.n_points > 0
    bounds = polydata.bounds
    assert bounds.x_min == -10.0
    assert bounds.x_max == 10.0
    assert bounds.y_min == -10.0
    assert bounds.y_max == 10.0
    assert bounds.z_min == 0.0
    assert bounds.z_max == thickness_mm


def test_slice_set_to_polydata_ignores_hole_contour() -> None:
    thickness_mm = 3.0
    position_mm = thickness_mm / 2
    slice_with_hole = Slice(
        thickness_mm=thickness_mm,
        contours=(
            _ccw_square(cx=0.0, cy=0.0, half=10.0),
            _cw_square(cx=0.0, cy=0.0, half=3.0),
        ),
        position_mm=position_mm,
        index=1,
    )
    slice_without_hole = Slice(
        thickness_mm=thickness_mm,
        contours=(_ccw_square(cx=0.0, cy=0.0, half=10.0),),
        position_mm=position_mm,
        index=1,
    )
    slice_set_with_hole = SliceSet(
        source_mesh=_empty_mesh(),
        gap_mm=0.0,
        slices=(slice_with_hole,),
        slice_count=1,
        slice_axis=SliceAxis.Z,
    )
    slice_set_without_hole = SliceSet(
        source_mesh=_empty_mesh(),
        gap_mm=0.0,
        slices=(slice_without_hole,),
        slice_count=1,
        slice_axis=SliceAxis.Z,
    )

    with_hole = slice_set_to_polydata(slice_set_with_hole)
    without_hole = slice_set_to_polydata(slice_set_without_hole)

    assert with_hole.n_points == without_hole.n_points
    assert with_hole.n_cells == without_hole.n_cells
    assert with_hole.bounds == without_hole.bounds


def test_slice_set_to_polydata_respects_slice_axis_mapping() -> None:
    thickness_mm = 3.0
    position_mm = 5.0 + thickness_mm / 2
    slice_ = Slice(
        thickness_mm=thickness_mm,
        contours=(_ccw_square(cx=0.0, cy=0.0, half=10.0),),
        position_mm=position_mm,
        index=1,
    )
    slice_set = SliceSet(
        source_mesh=_empty_mesh(),
        gap_mm=0.0,
        slices=(slice_,),
        slice_count=1,
        slice_axis=SliceAxis.X,
    )

    polydata = slice_set_to_polydata(slice_set)

    bounds = polydata.bounds
    assert bounds.x_min == 5.0
    assert bounds.x_max == 5.0 + thickness_mm
    assert bounds.y_min == -10.0
    assert bounds.y_max == 10.0
    assert bounds.z_min == -10.0
    assert bounds.z_max == 10.0


def test_multiple_slices_merge_into_single_polydata() -> None:
    thickness_mm = 3.0
    slices = tuple(
        Slice(
            thickness_mm=thickness_mm,
            contours=(_ccw_square(cx=0.0, cy=0.0, half=10.0),),
            position_mm=(i - 0.5) * thickness_mm,
            index=i,
        )
        for i in (1, 2)
    )
    slice_set = SliceSet(
        source_mesh=_empty_mesh(),
        gap_mm=0.0,
        slices=slices,
        slice_count=2,
        slice_axis=SliceAxis.Z,
    )

    polydata = slice_set_to_polydata(slice_set)

    bounds = polydata.bounds
    assert bounds.z_min == 0.0
    assert bounds.z_max == 2 * thickness_mm


def _two_slice_slice_set(*, thickness_mm: float = 3.0) -> SliceSet:
    slices = tuple(
        Slice(
            thickness_mm=thickness_mm,
            contours=(_ccw_square(cx=0.0, cy=0.0, half=10.0),),
            position_mm=(i - 0.5) * thickness_mm,
            index=i,
        )
        for i in (1, 2)
    )
    return SliceSet(
        source_mesh=_empty_mesh(),
        gap_mm=0.0,
        slices=slices,
        slice_count=2,
        slice_axis=SliceAxis.Z,
    )


def test_dowel_positions_to_polydata_empty_input_returns_empty_polydata() -> None:
    polydata = dowel_positions_to_polydata((), _two_slice_slice_set())

    assert polydata.n_points == 0
    assert polydata.n_cells == 0


def test_dowel_positions_to_polydata_uses_slice_outer_planes_not_length_mm() -> None:
    thickness_mm = 3.0
    slice_set = _two_slice_slice_set(thickness_mm=thickness_mm)
    dowel = _dowel_position(
        x_mm=5.0, y_mm=7.0, diameter_mm=4.0, start_slice_index=1, end_slice_index=2
    )

    polydata = dowel_positions_to_polydata((dowel,), slice_set)

    bounds = polydata.bounds
    assert bounds.z_min == 0.0
    assert bounds.z_max == 2 * thickness_mm
    assert bounds.x_min == 3.0
    assert bounds.x_max == 7.0
    assert bounds.y_min == 5.0
    assert bounds.y_max == 9.0


def test_dowel_hole_contours_to_polydata_empty_slice_set_returns_empty_polydata() -> (
    None
):
    slice_set = SliceSet(
        source_mesh=_empty_mesh(), gap_mm=0.0, slices=(), slice_count=0
    )

    polydata = dowel_hole_contours_to_polydata(slice_set)

    assert polydata.n_points == 0
    assert polydata.n_cells == 0


def test_dowel_hole_contours_to_polydata_ignores_solid_only_slice() -> None:
    thickness_mm = 3.0
    position_mm = thickness_mm / 2
    slice_ = Slice(
        thickness_mm=thickness_mm,
        contours=(_ccw_square(cx=0.0, cy=0.0, half=10.0),),
        position_mm=position_mm,
        index=1,
    )
    slice_set = SliceSet(
        source_mesh=_empty_mesh(),
        gap_mm=0.0,
        slices=(slice_,),
        slice_count=1,
        slice_axis=SliceAxis.Z,
    )

    polydata = dowel_hole_contours_to_polydata(slice_set)

    assert polydata.n_points == 0
    assert polydata.n_cells == 0


def test_dowel_hole_contours_to_polydata_draws_lines_on_both_planes_only() -> None:
    thickness_mm = 3.0
    position_mm = thickness_mm / 2
    segments = 8
    hole = _dowel_hole_cw_circle(cx=0.0, cy=0.0, radius=2.0, segments=segments)
    slice_ = Slice(
        thickness_mm=thickness_mm,
        contours=(_ccw_square(cx=0.0, cy=0.0, half=10.0), hole),
        position_mm=position_mm,
        index=1,
    )
    slice_set = SliceSet(
        source_mesh=_empty_mesh(),
        gap_mm=0.0,
        slices=(slice_,),
        slice_count=1,
        slice_axis=SliceAxis.Z,
    )

    polydata = dowel_hole_contours_to_polydata(slice_set)

    assert polydata.n_faces == 0
    assert polydata.n_lines == 2
    assert polydata.n_points == 2 * segments
    bounds = polydata.bounds
    assert bounds.z_min == 0.0
    assert bounds.z_max == thickness_mm
    assert bounds.x_min == -2.0
    assert bounds.x_max == 2.0
    assert bounds.y_min == -2.0
    assert bounds.y_max == 2.0


def test_spacers_to_polydata_empty_input_returns_empty_polydata() -> None:
    polydata = spacers_to_polydata((), _two_slice_slice_set())

    assert polydata.n_points == 0
    assert polydata.n_cells == 0


def test_spacers_to_polydata_spans_gap_above_start_slice() -> None:
    thickness_mm = 3.0
    position_mm = thickness_mm / 2
    slice_ = Slice(
        thickness_mm=thickness_mm,
        contours=(_ccw_square(cx=0.0, cy=0.0, half=10.0),),
        position_mm=position_mm,
        index=1,
    )
    slice_set = SliceSet(
        source_mesh=_empty_mesh(),
        gap_mm=2.0,
        slices=(slice_,),
        slice_count=1,
        slice_axis=SliceAxis.Z,
    )
    spacer = _spacer(
        x_mm=1.0, y_mm=2.0, diameter_mm=4.0, thickness_mm=2.0, start_slice_index=1
    )

    polydata = spacers_to_polydata((spacer,), slice_set)

    bounds = polydata.bounds
    assert bounds.z_min == thickness_mm
    assert bounds.z_max == thickness_mm + 2.0
    assert bounds.x_min == -1.0
    assert bounds.x_max == 3.0
    assert bounds.y_min == 0.0
    assert bounds.y_max == 4.0
