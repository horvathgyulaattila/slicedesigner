"""Tiszta, Qt-független unit tesztek a `render_geometry.py` geometriai
segédfüggvényeihez (prompt 8. szakasz)."""

from __future__ import annotations

import math

import pytest
import trimesh

from slicedesigner.engines.backplate_engine import Backplate, BackplateNormalAxis
from slicedesigner.engines.backplate_engine import (
    _backplate_third_axis_sign as _engine_backplate_third_axis_sign,
)
from slicedesigner.engines.dowel_engine import DowelPosition
from slicedesigner.engines.gap_engine import Spacer
from slicedesigner.engines.mesh_import import BoundingBox, Mesh
from slicedesigner.engines.slice_engine import (
    _SLICE_AXIS_CONTOUR_ORDER,
    Contour,
    HoleKind,
    Slice,
    SliceAxis,
    SliceSet,
    create_slice_set,
)
from slicedesigner.gui.render_geometry import (
    _AXIS_MAPPING,
    _WORLD_AXIS_INDEX,
    _backplate_third_axis_sign as _gui_backplate_third_axis_sign,
    backplate_to_polydata,
    dowel_hole_contours_to_polydata,
    dowel_positions_to_polydata,
    mesh_to_polydata,
    single_slice_to_polydata,
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


def _ccw_rect(u_min: float, u_max: float, v_min: float, v_max: float) -> Contour:
    return Contour(
        points=(
            (u_min, v_min),
            (u_max, v_min),
            (u_max, v_max),
            (u_min, v_max),
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


def test_slice_set_to_polydata_exclude_none_matches_default_behavior() -> None:
    slice_set = _two_slice_slice_set()

    default = slice_set_to_polydata(slice_set)
    explicit_none = slice_set_to_polydata(slice_set, exclude_slice_index=None)

    assert default.n_points == explicit_none.n_points
    assert default.n_cells == explicit_none.n_cells
    assert default.bounds == explicit_none.bounds


def test_slice_set_to_polydata_excludes_given_slice_index() -> None:
    thickness_mm = 3.0
    slice_set = _two_slice_slice_set(thickness_mm=thickness_mm)

    full = slice_set_to_polydata(slice_set)
    without_first = slice_set_to_polydata(slice_set, exclude_slice_index=1)

    assert without_first.n_points < full.n_points
    assert without_first.n_cells < full.n_cells
    bounds = without_first.bounds
    assert bounds.z_min == thickness_mm
    assert bounds.z_max == 2 * thickness_mm


def test_single_slice_to_polydata_matches_own_axis_band() -> None:
    thickness_mm = 3.0
    slice_set = _two_slice_slice_set(thickness_mm=thickness_mm)

    first = single_slice_to_polydata(slice_set, slice_index=1)
    second = single_slice_to_polydata(slice_set, slice_index=2)

    assert first.n_points > 0
    first_bounds = first.bounds
    assert first_bounds.x_min == -10.0
    assert first_bounds.x_max == 10.0
    assert first_bounds.y_min == -10.0
    assert first_bounds.y_max == 10.0
    assert first_bounds.z_min == 0.0
    assert first_bounds.z_max == thickness_mm

    assert second.n_points > 0
    second_bounds = second.bounds
    assert second_bounds.z_min == thickness_mm
    assert second_bounds.z_max == 2 * thickness_mm


def test_single_slice_to_polydata_missing_index_returns_empty_polydata() -> None:
    slice_set = _two_slice_slice_set()

    polydata = single_slice_to_polydata(slice_set, slice_index=99)

    assert polydata.n_points == 0
    assert polydata.n_cells == 0


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
    # ADR-0010 utáni `_AXIS_MAPPING` javítás: `slice_axis=Z`-re a kontúr
    # (u, v) = (Y, X), nem (X, Y) — a `DowelPosition.x_mm`/`y_mm` a Slice
    # kontúrjaival azonos (u, v) térben él (`dowel_engine.py` a
    # `Contour.points`-ból épített `island.polygon`-on dolgozik), ezért
    # `x_mm` a world Y-ba, `y_mm` a world X-be ágyazódik be.
    assert bounds.x_min == 5.0
    assert bounds.x_max == 9.0
    assert bounds.y_min == 3.0
    assert bounds.y_max == 7.0


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
    # ADR-0010 utáni `_AXIS_MAPPING` javítás: `slice_axis=Z`-re a kontúr
    # (u, v) = (Y, X), nem (X, Y) — a `Spacer.x_mm`/`y_mm` a Slice
    # kontúrjaival azonos (u, v) térben él, ezért `x_mm` a world Y-ba,
    # `y_mm` a world X-be ágyazódik be (l. a Dowel-teszt azonos okú
    # frissítését fentebb).
    assert bounds.x_min == 0.0
    assert bounds.x_max == 4.0
    assert bounds.y_min == -1.0
    assert bounds.y_max == 3.0


def _z_axis_square_assembly(
    *, half: float = 10.0, thickness_mm: float = 3.0
) -> SliceSet:
    """Egy szolid (CCW), négyzet alaprajzú, `slice_axis=Z` szerint szeletelt
    összeállítás — a Backplate-tesztek "assembly" oldala."""
    slice_ = Slice(
        thickness_mm=thickness_mm,
        contours=(_ccw_square(cx=0.0, cy=0.0, half=half),),
        position_mm=thickness_mm / 2,
        index=1,
    )
    return SliceSet(
        source_mesh=_empty_mesh(),
        gap_mm=0.0,
        slices=(slice_,),
        slice_count=1,
        slice_axis=SliceAxis.Z,
    )


def _backplate(
    *, thickness_mm: float = 2.0, half: float = 5.0, common_plane_mm: float = 0.0
) -> Backplate:
    return Backplate(
        contours=(_ccw_square(cx=0.0, cy=0.0, half=half),),
        thickness_mm=thickness_mm,
        common_plane_mm=common_plane_mm,
        material_reference=None,
    )


def test_backplate_to_polydata_none_returns_empty_polydata() -> None:
    slice_set = _z_axis_square_assembly()

    polydata = backplate_to_polydata(None, slice_set, BackplateNormalAxis.PLUS_X)

    assert polydata.n_points == 0
    assert polydata.n_cells == 0


def test_backplate_to_polydata_plus_axis_matches_assembly_extreme() -> None:
    slice_set = _z_axis_square_assembly(half=10.0)
    backplate = _backplate(thickness_mm=2.0, half=5.0, common_plane_mm=10.0)

    polydata = backplate_to_polydata(backplate, slice_set, BackplateNormalAxis.PLUS_X)

    assert polydata.n_points > 0
    bounds = polydata.bounds
    # A belső (összeállítás felé néző) sík illeszkedik az összeállítás
    # PLUS_X szerinti szélsőértékéhez (a négyzet alaprajz x_max=10.0) —
    # ez a 7. szakasz legfontosabb ellenőrzése: a Backplate nem lóg el a
    # levegőben.
    assert bounds.x_min == 10.0
    # ...és a vastagság kifelé (a `PLUS_X` előjele szerint, +X irányba)
    # extrudálódik, nem az összeállítás felé.
    assert bounds.x_max == 12.0
    assert bounds.y_min == -5.0
    assert bounds.y_max == 5.0
    assert bounds.z_min == -5.0
    assert bounds.z_max == 5.0


def test_backplate_to_polydata_minus_axis_matches_assembly_extreme() -> None:
    slice_set = _z_axis_square_assembly(half=10.0)
    backplate = _backplate(thickness_mm=2.0, half=5.0, common_plane_mm=-10.0)

    polydata = backplate_to_polydata(backplate, slice_set, BackplateNormalAxis.MINUS_X)

    bounds = polydata.bounds
    # A belső sík itt az összeállítás MINUS_X szerinti szélsőértékéhez
    # (x_min=-10.0) illeszkedik, a vastagság pedig -X irányba (kifelé)
    # extrudálódik.
    assert bounds.x_max == -10.0
    assert bounds.x_min == -12.0


def test_backplate_to_polydata_ignores_hole_contour() -> None:
    slice_set = _z_axis_square_assembly(half=10.0)
    backplate_without_hole = _backplate(
        thickness_mm=2.0, half=5.0, common_plane_mm=10.0
    )
    backplate_with_hole = Backplate(
        contours=(
            _ccw_square(cx=0.0, cy=0.0, half=5.0),
            _cw_square(cx=0.0, cy=0.0, half=1.0),
        ),
        thickness_mm=2.0,
        common_plane_mm=10.0,
        material_reference=None,
    )

    without_hole = backplate_to_polydata(
        backplate_without_hole, slice_set, BackplateNormalAxis.PLUS_X
    )
    with_hole = backplate_to_polydata(
        backplate_with_hole, slice_set, BackplateNormalAxis.PLUS_X
    )

    assert with_hole.n_points == without_hole.n_points
    assert with_hole.n_cells == without_hole.n_cells
    assert with_hole.bounds == without_hole.bounds


def test_axis_mapping_matches_slice_engine_contour_order() -> None:
    """`_AXIS_MAPPING` (a `render_geometry.py` önálló, GUI-oldali
    duplikátuma) minden `SliceAxis`-ra pontosan a
    `slice_engine.py::_SLICE_AXIS_CONTOUR_ORDER` (ADR-0010 utáni)
    világtengely-neveinek megfelelő indexeket kell, hogy adja — ez a
    regresszió gyökér-okának (a két, egymástól függetlenül karbantartott
    tábla szétcsúszása) közvetlen, automatizált zárása."""
    for axis in SliceAxis:
        _axis_index, (u_index, v_index) = _AXIS_MAPPING[axis]
        u_name, v_name = _SLICE_AXIS_CONTOUR_ORDER[axis]
        assert u_index == _WORLD_AXIS_INDEX[u_name]
        assert v_index == _WORLD_AXIS_INDEX[v_name]


def test_slice_set_to_polydata_matches_mesh_axes_after_create_slice_set() -> None:
    """A projektgazda jelentette regresszió reprodukciója és lezárása:
    egy valódi, aszimmetrikus (X != Y != Z méretű) téglatest Meshből,
    ténylegesen meghívott `create_slice_set()`-tel (nem kézzel épített
    fixture-rel, hogy a valódi `_TO_2D_ROTATION` érvényesüljön) épített
    SliceSet `slice_set_to_polydata()` kimenete ugyanazon a tengelyen,
    egymással átfedésben helyezkedjen el, mint az eredeti Mesh
    `mesh_to_polydata()` kimenete — nem X/Y tengelyt felcserélve.

    A Mesh a Z tengely mentén [0, 9] tartományba van tolva (a `box()`
    alapból X/Y/Z mindhárom tengelyen középre igazít), hogy a Slice
    Engine szándékos, 0-bázisú újrapozicionálása (külön, e hibától
    független, dokumentált viselkedés) ne okozzon hamis eltérést a
    szeletelési tengelyen — a teszt kizárólag a kontúr (u, v) →
    world-tengely leképezés helyességét vizsgálja."""
    box = trimesh.creation.box(extents=(30.0, 10.0, 9.0))
    box.apply_translation((0.0, 0.0, 4.5))
    mesh = _mesh_from_trimesh(box)

    slice_set = create_slice_set(
        mesh, slice_thickness_mm=3.0, slice_axis=SliceAxis.Z, gap_mm=0.0
    )

    mesh_bounds = mesh_to_polydata(mesh).bounds
    assembly_bounds = slice_set_to_polydata(slice_set).bounds

    assert assembly_bounds.x_min == pytest.approx(mesh_bounds.x_min, abs=1e-6)
    assert assembly_bounds.x_max == pytest.approx(mesh_bounds.x_max, abs=1e-6)
    assert assembly_bounds.y_min == pytest.approx(mesh_bounds.y_min, abs=1e-6)
    assert assembly_bounds.y_max == pytest.approx(mesh_bounds.y_max, abs=1e-6)
    assert assembly_bounds.z_min == pytest.approx(mesh_bounds.z_min, abs=1e-6)
    assert assembly_bounds.z_max == pytest.approx(mesh_bounds.z_max, abs=1e-6)


def test_backplate_to_polydata_third_axis_sign_mirrors_with_normal_sign() -> None:
    """`backplate_to_polydata()`-nak a `_backplate_third_axis_sign()`-t
    kell alkalmaznia: egy aszimmetrikus (nem a v-tengelyre szimmetrikus)
    Backplate-kontúr esetén az ellentétes előjelű normal-tengelyek
    (`PLUS_X`/`MINUS_X`) a harmadik (itt: Y) tengelyen egymáshoz képest
    tükrözött, nem azonos pozícióban helyezik el a Backplate-et — a
    korábbi, előjel nélküli leképezés ezt a tükrözést figyelmen kívül
    hagyta."""
    slice_set = _z_axis_square_assembly(half=10.0)
    # Aszimmetrikus (u_min=2, u_max=6, azaz nem szimmetrikus u=0-ra)
    # téglalap-kontúr — csak így különböztethető meg az előjeles és az
    # előjel nélküli leképezés eredménye.
    plus_backplate = Backplate(
        contours=(_ccw_rect(u_min=2.0, u_max=6.0, v_min=-3.0, v_max=3.0),),
        thickness_mm=2.0,
        common_plane_mm=10.0,
        material_reference=None,
    )
    minus_backplate = Backplate(
        contours=(_ccw_rect(u_min=2.0, u_max=6.0, v_min=-3.0, v_max=3.0),),
        thickness_mm=2.0,
        common_plane_mm=-10.0,
        material_reference=None,
    )

    plus_x = backplate_to_polydata(plus_backplate, slice_set, BackplateNormalAxis.PLUS_X)
    minus_x = backplate_to_polydata(
        minus_backplate, slice_set, BackplateNormalAxis.MINUS_X
    )

    plus_bounds = plus_x.bounds
    minus_bounds = minus_x.bounds
    # `_backplate_third_axis_sign()` globális előjel-megfordítása (ADR-0010
    # 2. utókövetés, 2026-08-08-i élő tesztelés) miatt PLUS_X most a
    # negatív, MINUS_X a pozitív Y-oldalra helyezi a kontúrt — a lényeg
    # (a két eset egymás tükörképe) a megfordítás előtt/után is igaz.
    assert plus_bounds.y_min == pytest.approx(-6.0)
    assert plus_bounds.y_max == pytest.approx(-2.0)
    assert minus_bounds.y_min == pytest.approx(2.0)
    assert minus_bounds.y_max == pytest.approx(6.0)


def test_gui_backplate_third_axis_sign_matches_engine_for_all_valid_combinations() -> (
    None
):
    """A `render_geometry.py` GUI-oldali `_backplate_third_axis_sign()`
    duplikátumának minden érvényes `(slice_axis, backplate_normal_axis)`
    kombinációra (a `slice_axis`-szal megegyező tengelyű normal kivételével
    — az érvénytelen) pontosan ugyanazt kell adnia, mint a
    `backplate_engine.py` kanonikus forrásának — ez zárja le annak
    kockázatát, hogy a két, egymástól függetlenül karbantartott
    duplikátum a globális előjel-megfordítás után szétcsússzon."""
    for slice_axis in SliceAxis:
        for backplate_normal_axis in BackplateNormalAxis:
            normal_world_axis = backplate_normal_axis.value.lstrip("+-")
            if normal_world_axis == slice_axis.value:
                continue  # érvénytelen kombináció, ld. InvalidBackplateError

            engine_sign = _engine_backplate_third_axis_sign(
                slice_axis, backplate_normal_axis
            )
            gui_sign = _gui_backplate_third_axis_sign(slice_axis, backplate_normal_axis)

            assert gui_sign == pytest.approx(engine_sign)
