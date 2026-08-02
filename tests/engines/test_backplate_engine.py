"""Tesztek a Backplate Engine 1. köréhez (BACKPLATE_SPEC.md 6. szakasz, 1-8. lépés)."""

import pytest
import trimesh

from slicedesigner.engines.backplate_engine import (
    Backplate,  # noqa: F401
    BackplateNormalAxis,
    ManualTabPosition,
    NonBackplateIsland,
    SliceTabOverride,
    apply_backplate,
    place_backplate_tabs,
)
from slicedesigner.engines.exceptions import InvalidBackplateError
from slicedesigner.engines.mesh_import import BoundingBox, Mesh
from slicedesigner.engines.slice_engine import (
    Contour,
    Slice,
    SliceAxis,
    SliceSet,
    create_slice_set,
    is_ccw,
    reconstruct_islands,
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


def _make_hand_slice_set(
    rects: list[tuple[float, float, float, float]], thickness_mm: float = 3.0
) -> SliceSet:
    slices = [
        Slice(
            thickness_mm=thickness_mm,
            contours=(_rect_contour(*rect),),
            position_mm=(i - 0.5) * thickness_mm,
            index=i,
        )
        for i, rect in enumerate(rects, start=1)
    ]
    all_x = [v for r in rects for v in (r[0], r[1])]
    all_y = [v for r in rects for v in (r[2], r[3])]
    bounding_box = BoundingBox(
        min=(min(all_x), min(all_y), 0.0),
        max=(max(all_x), max(all_y), len(rects) * thickness_mm),
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
        slice_count=len(rects),
    )


def test_place_backplate_tabs_simple_box() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    modified, tabs = place_backplate_tabs(
        slice_set,
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
    )

    assert len(tabs) == 5
    for tab in tabs:
        assert tab.third_axis_start_mm == pytest.approx(-2.5)
        assert tab.third_axis_end_mm == pytest.approx(2.5)

    for slice_ in modified.slices:
        island = reconstruct_islands(slice_)[0]
        assert max(p[0] for p in island.solid.points) == pytest.approx(13.0)


def test_place_backplate_tabs_matching_axis_raises() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidBackplateError):
        place_backplate_tabs(
            slice_set,
            backplate_normal_axis=BackplateNormalAxis.PLUS_Z,
            backplate_thickness_mm=3.0,
            tab_length_mm=5.0,
        )


def test_place_backplate_tabs_invalid_thickness_raises() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidBackplateError):
        place_backplate_tabs(
            slice_set,
            backplate_normal_axis=BackplateNormalAxis.PLUS_X,
            backplate_thickness_mm=0.0,
            tab_length_mm=5.0,
        )


def test_place_backplate_tabs_invalid_tab_length_raises() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidBackplateError):
        place_backplate_tabs(
            slice_set,
            backplate_normal_axis=BackplateNormalAxis.PLUS_X,
            backplate_thickness_mm=3.0,
            tab_length_mm=0.0,
        )


def test_place_backplate_tabs_invalid_tab_spacing_raises() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidBackplateError):
        place_backplate_tabs(
            slice_set,
            backplate_normal_axis=BackplateNormalAxis.PLUS_X,
            backplate_thickness_mm=3.0,
            tab_length_mm=5.0,
            tab_spacing_mm=0.0,
        )


def test_place_backplate_tabs_invalid_edge_margin_raises() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidBackplateError):
        place_backplate_tabs(
            slice_set,
            backplate_normal_axis=BackplateNormalAxis.PLUS_X,
            backplate_thickness_mm=3.0,
            tab_length_mm=5.0,
            tab_edge_margin_mm=0.0,
        )


def test_place_backplate_tabs_usable_length_non_positive_raises() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidBackplateError):
        place_backplate_tabs(
            slice_set,
            backplate_normal_axis=BackplateNormalAxis.PLUS_X,
            backplate_thickness_mm=3.0,
            tab_length_mm=5.0,
            tab_edge_margin_mm=20.0,
        )


def test_place_backplate_tabs_common_plane_violation_raises() -> None:
    slice_set = _make_hand_slice_set(
        [(-10.0, 10.0, -15.0, 15.0), (-10.0, 3.0, -15.0, 15.0)]
    )

    with pytest.raises(InvalidBackplateError):
        place_backplate_tabs(
            slice_set,
            backplate_normal_axis=BackplateNormalAxis.PLUS_X,
            backplate_thickness_mm=3.0,
            tab_length_mm=5.0,
        )


def test_place_backplate_tabs_recessed_island_gets_longer_tab() -> None:
    slice_set = _make_hand_slice_set(
        [(-10.0, 10.0, -15.0, 15.0), (-10.0, 9.95, -15.0, 15.0)]
    )

    modified, tabs = place_backplate_tabs(
        slice_set,
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
    )

    assert len(tabs) == 2
    for slice_ in modified.slices:
        solid_points = reconstruct_islands(slice_)[0].solid.points
        assert max(p[0] for p in solid_points) == pytest.approx(13.0, abs=1e-6)


def test_place_backplate_tabs_manual_position_used() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)
    override = SliceTabOverride(
        slice_index=1,
        manual_tab_positions=(ManualTabPosition(position_mm=5.0, length_mm=4.0),),
    )

    _modified, tabs = place_backplate_tabs(
        slice_set,
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
        slice_tab_overrides=(override,),
    )

    slice_1_tabs = [t for t in tabs if t.slice_index == 1]
    assert len(slice_1_tabs) == 1
    assert slice_1_tabs[0].third_axis_start_mm == pytest.approx(-7.0)
    assert slice_1_tabs[0].third_axis_end_mm == pytest.approx(-3.0)

    other_tabs = [t for t in tabs if t.slice_index != 1]
    assert len(other_tabs) == 4


def test_place_backplate_tabs_non_backplate_island_excluded() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)
    excluded = NonBackplateIsland(slice_index=3, island_index=0)

    modified, tabs = place_backplate_tabs(
        slice_set,
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
        non_backplate_islands=(excluded,),
    )

    assert all(t.slice_index != 3 for t in tabs)
    assert len(tabs) == 4

    excluded_slice = next(s for s in modified.slices if s.index == 3)
    original_slice = next(s for s in slice_set.slices if s.index == 3)
    assert excluded_slice.contours == original_slice.contours


def test_apply_backplate_simple_box() -> None:
    slice_set = _make_box_slice_set(
        extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0, gap_mm=1.0
    )

    modified_slice_set, backplate = apply_backplate(
        slice_set,
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
    )

    assert backplate.thickness_mm == 3.0
    assert backplate.material_reference is None

    exterior_contours = [c for c in backplate.contours if is_ccw(c.points)]
    hole_contours = [c for c in backplate.contours if not is_ccw(c.points)]
    assert len(exterior_contours) == 1
    # A legszélső (első/utolsó) szelet fészke a sziluett szélén ér véget,
    # ezért azok bemetszésként a külső kontúrt alakítják, nem lyukat
    # képeznek — csak a belső 2 szelet fészke lesz valódi (zárt) lyuk.
    assert len(hole_contours) == 2

    xs = [p[0] for p in exterior_contours[0].points]
    ys = [p[1] for p in exterior_contours[0].points]
    assert min(xs) == pytest.approx(-15.0)
    assert max(xs) == pytest.approx(15.0)
    assert min(ys) == pytest.approx(-7.5)
    assert max(ys) == pytest.approx(7.5)

    assert len(modified_slice_set.slices) == 4


def test_apply_backplate_margin_expands_silhouette() -> None:
    slice_set = _make_box_slice_set(
        extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0, gap_mm=1.0
    )

    _modified, backplate_no_margin = apply_backplate(
        slice_set,
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
    )
    _modified, backplate_with_margin = apply_backplate(
        slice_set,
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
        backplate_margin_mm=2.0,
    )

    exterior_no_margin = next(
        c for c in backplate_no_margin.contours if is_ccw(c.points)
    )
    exterior_with_margin = next(
        c for c in backplate_with_margin.contours if is_ccw(c.points)
    )

    xs_no_margin = [p[0] for p in exterior_no_margin.points]
    xs_with_margin = [p[0] for p in exterior_with_margin.points]

    assert max(xs_with_margin) - max(xs_no_margin) == pytest.approx(2.0, abs=0.1)
    assert min(xs_no_margin) - min(xs_with_margin) == pytest.approx(2.0, abs=0.1)


def test_apply_backplate_material_reference_passed_through() -> None:
    slice_set = _make_box_slice_set(
        extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0, gap_mm=1.0
    )

    _modified, backplate = apply_backplate(
        slice_set,
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
        material_reference="plywood_3mm",
    )

    assert backplate.material_reference == "plywood_3mm"


def test_apply_backplate_propagates_invalid_thickness() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with pytest.raises(InvalidBackplateError):
        apply_backplate(
            slice_set,
            backplate_normal_axis=BackplateNormalAxis.PLUS_X,
            backplate_thickness_mm=0.0,
            tab_length_mm=5.0,
        )


def test_apply_backplate_nest_cutouts_span_slice_thickness() -> None:
    slice_set = _make_box_slice_set(
        extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0, gap_mm=1.0
    )

    _modified, backplate = apply_backplate(
        slice_set,
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
    )

    hole_contours = [c for c in backplate.contours if not is_ccw(c.points)]
    # Csak a belső 2 szelet fészke lesz valódi lyuk, ugyanazon okból,
    # mint a test_apply_backplate_simple_box-ban.
    assert len(hole_contours) == 2

    for hole in hole_contours:
        ys = [p[1] for p in hole.points]
        assert max(ys) - min(ys) == pytest.approx(3.0, abs=1e-6)
        xs = [p[0] for p in hole.points]
        assert max(xs) - min(xs) == pytest.approx(5.0, abs=1e-6)


def test_apply_backplate_nest_cutout_aligned_with_real_slice_position() -> None:
    slice_set = _make_box_slice_set(
        extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0, gap_mm=1.0
    )

    # backplate_margin_mm > 0 kell, hogy a legszélső szeletek fészke is
    # a sziluett belsejébe essen (ne a szélén metssze be a kontúrt) — így
    # mind a 4 fészek valódi, zárt lyukként ellenőrizhető a valós
    # world-koordinátás igazítás szempontjából.
    _modified, backplate = apply_backplate(
        slice_set,
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
        backplate_margin_mm=2.0,
    )

    hole_contours = [c for c in backplate.contours if not is_ccw(c.points)]
    z_ranges = sorted(
        (min(p[1] for p in c.points), max(p[1] for p in c.points))
        for c in hole_contours
    )

    # A box Z-tartománya [-7.5, 7.5]; a legszélső szeletek valós
    # Z-tartománya a bounding box szélén kell kezdődjön/végződjön.
    assert z_ranges[0][0] == pytest.approx(-7.5, abs=1e-6)
    assert z_ranges[-1][1] == pytest.approx(7.5, abs=1e-6)


def test_apply_backplate_handles_split_silhouette() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    _modified, backplate = apply_backplate(
        slice_set,
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
    )

    # 0 gap-pel, szimmetrikus dobozon minden csap azonos Y-pozíción,
    # egymást követő szeleteken -> a fészek-kivágások egyetlen, teljes
    # magasságú, folytonos réssé állnak össze, ami ténylegesen kettévágja
    # a hátlapot. Ez helyes, fizikailag pontos kimenet, nem hiba.
    exterior_contours = [c for c in backplate.contours if is_ccw(c.points)]
    hole_contours = [c for c in backplate.contours if not is_ccw(c.points)]
    assert len(exterior_contours) == 2
    assert len(hole_contours) == 0

    all_ys = [p[1] for c in exterior_contours for p in c.points]
    assert min(all_ys) == pytest.approx(-7.5)
    assert max(all_ys) == pytest.approx(7.5)
