"""Tesztek a Backplate Engine 1. köréhez (BACKPLATE_SPEC.md 6. szakasz, 1-8. lépés)."""

import logging

import pytest
import trimesh
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

from slicedesigner.engines.backplate_engine import (
    Backplate,  # noqa: F401
    BackplateNormalAxis,
    ManualTabPosition,
    NonBackplateIsland,
    SliceTabOverride,
    _build_backplate_shape_from_mesh,  # a tűrés-sáv önálló ellenőrzéséhez, l. lent
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


def _stepped_solid_from_rects(
    rects: list[tuple[float, float, float, float]], thickness_mm: float
) -> trimesh.Trimesh:
    """Egy Z-menti "lépcsős" tömör test felépítése: szeletenként egy
    téglatest, pontosan a szelet saját Z-sávjával (`(i-1)*thickness_mm` –
    `i*thickness_mm`) és a hozzá tartozó (x_min, x_max, y_min, y_max)
    keresztmetszettel, Boole-unióba véve — így a valós Mesh geometria
    ténylegesen a kézzel megadott kontúroknak megfelelő keresztmetszetet
    adja vissza egy térbeli metszetnél is, nem csak a Slice Engine
    síkmetszeténél."""
    boxes = []
    for i, (x_min, x_max, y_min, y_max) in enumerate(rects, start=1):
        z_min, z_max = (i - 1) * thickness_mm, i * thickness_mm
        extents = (x_max - x_min, y_max - y_min, z_max - z_min)
        center = ((x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2)
        transform = [
            [1.0, 0.0, 0.0, center[0]],
            [0.0, 1.0, 0.0, center[1]],
            [0.0, 0.0, 1.0, center[2]],
            [0.0, 0.0, 0.0, 1.0],
        ]
        boxes.append(trimesh.creation.box(extents=extents, transform=transform))
    solid = boxes[0]
    for box in boxes[1:]:
        solid = solid.union(box)
    return solid


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
    solid = _stepped_solid_from_rects(rects, thickness_mm)
    mesh = _mesh_from_trimesh(solid)
    return SliceSet(
        source_mesh=mesh,
        slice_axis=SliceAxis.Z,
        gap_mm=0.0,
        slices=tuple(slices),
        slice_count=len(rects),
    )


def test_place_backplate_tabs_simple_box() -> None:
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    modified, tabs, _common_plane_mm, _backplate_shape = place_backplate_tabs(
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


def test_place_backplate_tabs_usable_length_non_positive_skipped_with_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """BACKPLATE_SPEC.md 6. szakasz 6. pont / 7. szakasz (2026-08-06-i
    pontosítás): egy `usable_length <= 0` érintkező szakasz NEM hibát dob —
    a szakasz (itt: minden szelet egyetlen szigetének egyetlen érintkező
    szakasza) csap nélkül marad, figyelmeztetéssel, a feldolgozás pedig
    végigfut. Mivel itt minden szeletnek egyetlen szigete és egyetlen,
    túl rövid szakasza van, egyik sziget sem kap csapot sehol, és a
    Slice Set geometriája (a kontúrok) teljesen változatlan marad."""
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)

    with caplog.at_level(logging.WARNING):
        modified, tabs, _common_plane_mm, _backplate_shape = place_backplate_tabs(
            slice_set,
            backplate_normal_axis=BackplateNormalAxis.PLUS_X,
            backplate_thickness_mm=3.0,
            tab_length_mm=5.0,
            tab_edge_margin_mm=20.0,
        )

    assert tabs == ()
    assert any(
        "nem kerül" in record.getMessage() and "csap" in record.getMessage()
        for record in caplog.records
    )
    for original_slice, modified_slice in zip(
        slice_set.slices, modified.slices, strict=True
    ):
        assert modified_slice.contours == original_slice.contours


def test_place_backplate_tabs_one_segment_too_short_others_unaffected(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """BACKPLATE_SPEC.md 6. szakasz 6. pont: egyetlen sziget (a 3. szelet
    szigete, `slice_tab_overrides`-szal mesterségesen túl nagy
    `tab_edge_margin_mm`-re állítva) `usable_length`-je nem pozitív — csak
    ezen a szigeten marad el a csap-elhelyezés, figyelmeztetéssel; a többi
    sziget csap-elhelyezése változatlanul, hiba nélkül folytatódik."""
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)
    override = SliceTabOverride(slice_index=3, tab_edge_margin_mm=20.0)

    with caplog.at_level(logging.WARNING):
        modified, tabs, _common_plane_mm, _backplate_shape = place_backplate_tabs(
            slice_set,
            backplate_normal_axis=BackplateNormalAxis.PLUS_X,
            backplate_thickness_mm=3.0,
            tab_length_mm=5.0,
            slice_tab_overrides=(override,),
        )

    assert all(t.slice_index != 3 for t in tabs)
    assert len(tabs) == 4
    assert any("3. szelet" in record.getMessage() for record in caplog.records)

    untouched_slice = next(s for s in modified.slices if s.index == 3)
    original_slice = next(s for s in slice_set.slices if s.index == 3)
    assert untouched_slice.contours == original_slice.contours

    other_slice = next(s for s in modified.slices if s.index != 3)
    island = reconstruct_islands(other_slice)[0]
    assert max(p[0] for p in island.solid.points) == pytest.approx(13.0)


def test_place_backplate_tabs_common_plane_violation_raises() -> None:
    """A 2 szigetes fixture-nél egyik csoport sem éri el a szakaszok
    szigorú (> 50%) többségét (1/2 <= 1) — az új, klaszterezés-alapú
    logika mellett ez ugyanúgy hibát dob, mint a korábbi, globális
    maximumhoz mért eltérés-ellenőrzés mellett (előre jelzett, változatlan
    viselkedés — BACKPLATE_SPEC.md 6. szakasz 3. pont, prompt 4. szakasz)."""
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


def test_place_backplate_tabs_outlier_island_excluded_with_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """BACKPLATE_SPEC.md 6. szakasz 4. pont: a domináns közös-sík
    csoporton kívül eső sziget NEM hibát dob — automatikusan, a
    `non_backplate_islands`-hez hasonlóan, figyelmeztetéssel kizárásra
    kerül a Backplate-kapcsolódásból (nem kap csapot).

    3 szelet, mindegyik egyetlen szigettel: az 1. és 3. szelet szigete
    x_max=10.0-nál éri el a Backplate síkját (közös, domináns csoport,
    2 a 3-ból > 50%), a 2. szeleté x_max=5.0-nál (a toleranciahatáron
    (0.1 mm) kívül eső, kilógó sziget)."""
    slice_set = _make_hand_slice_set(
        [
            (-10.0, 10.0, -15.0, 15.0),
            (-10.0, 5.0, -15.0, 15.0),
            (-10.0, 10.0, -15.0, 15.0),
        ]
    )

    with caplog.at_level(logging.WARNING):
        _modified, tabs, _common_plane_mm, _backplate_shape = place_backplate_tabs(
            slice_set,
            backplate_normal_axis=BackplateNormalAxis.PLUS_X,
            backplate_thickness_mm=3.0,
            tab_length_mm=5.0,
        )

    tab_slice_indices = {tab.slice_index for tab in tabs}
    assert tab_slice_indices == {1, 3}  # a 2. szelet szigete nem kap csapot
    assert any("2. szelet" in record.getMessage() for record in caplog.records)


def test_place_backplate_tabs_no_majority_raises() -> None:
    """BACKPLATE_SPEC.md 6. szakasz 3. pont / 7. szakasz: ha a legnagyobb
    csoport sem éri el az érintkező szakaszok szigorú többségét (> 50%),
    a feldolgozás hibát dob — akkor is, ha az összes csoport "egyformán
    kicsi" (itt: 3 szelet, mindhárom egymástól > 0.1 mm távolságra eső,
    külön csoportba eső x_max-szal, tehát 1/3 <= 1.5)."""
    slice_set = _make_hand_slice_set(
        [
            (-10.0, 10.0, -15.0, 15.0),
            (-10.0, 5.0, -15.0, 15.0),
            (-10.0, 0.0, -15.0, 15.0),
        ]
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

    modified, tabs, _common_plane_mm, _backplate_shape = place_backplate_tabs(
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

    _modified, tabs, _common_plane_mm, _backplate_shape = place_backplate_tabs(
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

    modified, tabs, _common_plane_mm, _backplate_shape = place_backplate_tabs(
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
    # A modell tényleges (Boole-metszet-alapú) geometriájából épített alak
    # a valós, folytonos test dobozát adja vissza — a `gap_mm` itt nem
    # egy ténylegesen a mesh-be vágott fizikai rés, hanem kizárólag a
    # szeletek `position_mm` szerinti (kivágásoknál használt) elhelyezési
    # távolsága (BACKPLATE_SPEC.md 6. szakasz 10. pont). Emiatt a
    # fészek-kivágások közül csak a két szélső (1. és 4. szelet, amelyek
    # a folytonos test Z-szélén ülnek) vágja ketté a külső kontúrt —
    # a 2. és 3. szelet kivágása a test belsejébe esik, ezért zárt
    # lyukként jelenik meg.
    assert len(exterior_contours) == 1
    assert len(hole_contours) == 2

    xs = [p[0] for c in exterior_contours for p in c.points]
    ys = [p[1] for c in exterior_contours for p in c.points]
    assert min(xs) == pytest.approx(-15.0)
    assert max(xs) == pytest.approx(15.0)
    # A szelet-tengely mentén a Slice Engine-nel megegyező módon skálázott
    # nyers Mesh saját (axis_min-nel rebázisolt) koordinátarendszere
    # érvényes (BACKPLATE_SPEC.md 6. szakasz 10. pont) — ezért 0..15.
    assert min(ys) == pytest.approx(0.0)
    assert max(ys) == pytest.approx(15.0)

    hole_z_ranges = sorted(
        (min(p[1] for p in c.points), max(p[1] for p in c.points))
        for c in hole_contours
    )
    # A 2. és 3. szelet saját (position_mm-alapú) Z-sávjával egyeznek.
    expected_hole_z_ranges = [(4.0, 7.0), (8.0, 11.0)]
    for (actual_min, actual_max), (expected_min, expected_max) in zip(
        hole_z_ranges, expected_hole_z_ranges, strict=True
    ):
        assert actual_min == pytest.approx(expected_min)
        assert actual_max == pytest.approx(expected_max)
    for c in hole_contours:
        xs_hole = [p[0] for p in c.points]
        assert min(xs_hole) == pytest.approx(-2.5)
        assert max(xs_hole) == pytest.approx(2.5)

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

    # A tényleges keresztmetszet-alapú alak margó nélkül (1 mm valós rés
    # a szeletek közt) 8 különálló darabra esik szét, míg 2 mm margóval
    # (> 1 mm rés) a margó-buffer áthidalja a réseket, és mind a 4
    # szelet egyetlen darabbá olvad össze — a darabszám (és ezzel az
    # "első CCW kontúr" azonossága) a két eset közt eltér, ezért az
    # összes külső kontúr együttes határdobozát kell összevetni, ami
    # darabszámtól függetlenül méri a margó tényleges hatását.
    xs_no_margin = [
        p[0] for c in backplate_no_margin.contours if is_ccw(c.points) for p in c.points
    ]
    xs_with_margin = [
        p[0]
        for c in backplate_with_margin.contours
        if is_ccw(c.points)
        for p in c.points
    ]

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

    # A modell tényleges (Boole-metszet-alapú) geometriájából épített
    # alap-alak folytonos (a `gap_mm` itt nem fizikai rés a mesh-ben,
    # csak a szeletek `position_mm` szerinti elhelyezési távolsága —
    # BACKPLATE_SPEC.md 6. szakasz 10. pont), ezért a fészek-kivágások
    # attól függően válnak a külső kontúrt kettévágó bevágássá vagy zárt
    # belső lyukká, hogy az adott szelet Z-sávja a folytonos test szélén
    # ül-e (l. test_apply_backplate_simple_box). A kivágás pontossága
    # (pontosan a szeletvastagságot fedi le Z mentén, pontosan a
    # csaphosszt Y mentén) ettől függetlenül, közvetlenül a
    # rekonstruált Shapely-geometrián próbapontokkal ellenőrizhető.
    solids = [c for c in backplate.contours if is_ccw(c.points)]
    holes = [c for c in backplate.contours if not is_ccw(c.points)]
    pieces = []
    for solid in solids:
        solid_polygon = Polygon(solid.points)
        own_holes = [
            h
            for h in holes
            if solid_polygon.contains(Polygon(h.points).representative_point())
        ]
        pieces.append(Polygon(solid.points, holes=[h.points for h in own_holes]))
    backplate_geometry = unary_union(pieces)

    for slice_ in slice_set.slices:
        z_min = slice_.position_mm - slice_.thickness_mm / 2
        z_max = slice_.position_mm + slice_.thickness_mm / 2
        z_mid = (z_min + z_max) / 2

        # A csap szélessége (5 mm) pontosan Y = [-2.5, 2.5]-t fedi le —
        # ezen belül nincs anyag, közvetlenül kívül (±3.0) van.
        assert not backplate_geometry.contains(Point(0.0, z_mid))
        assert backplate_geometry.contains(Point(-3.0, z_mid))
        assert backplate_geometry.contains(Point(3.0, z_mid))

        # A kivágás pontosan a szelet saját vastagságát fedi le Z
        # mentén — a sávon (kis ráhagyással) kívül, de a modell
        # Z-tartományán (0..15) belül eső pontnál újra van anyag.
        if z_min > 0.0:
            assert backplate_geometry.contains(Point(0.0, z_min - 0.1))
        if z_max < 15.0:
            assert backplate_geometry.contains(Point(0.0, z_max + 0.1))


def test_apply_backplate_nest_cutout_aligned_with_real_slice_position() -> None:
    slice_set = _make_box_slice_set(
        extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0, gap_mm=1.0
    )

    # backplate_margin_mm > 0 kell, hogy a margó-buffer áthidalja a
    # szeletek közti 1 mm-es valós réseket, és mind a 4 szelet egyetlen,
    # összefüggő darabbá olvadjon — így minden fészek valódi, zárt
    # lyukként, a saját szeletének valós pozíciójával ellenőrizhető.
    _modified, backplate = apply_backplate(
        slice_set,
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
        backplate_margin_mm=2.0,
    )

    hole_contours = [c for c in backplate.contours if not is_ccw(c.points)]
    hole_z_ranges = sorted(
        (min(p[1] for p in c.points), max(p[1] for p in c.points))
        for c in hole_contours
    )

    # Minden fészeknek pontosan a saját szeletének valós, újra-bázisolt
    # (position_mm-alapú) Z-tartományával kell egyeznie — nem egy
    # világ-koordinátás (bounding box `axis_min`-nel eltolt) sziluett
    # szélsőértékével, ami a korábbi, immár megszüntetett
    # `_compute_silhouette()`-alapú számítás sajátja volt.
    expected_z_ranges = sorted(
        (s.position_mm - s.thickness_mm / 2, s.position_mm + s.thickness_mm / 2)
        for s in slice_set.slices
    )
    assert len(hole_contours) == len(expected_z_ranges) == 4
    for (actual_min, actual_max), (expected_min, expected_max) in zip(
        hole_z_ranges, expected_z_ranges, strict=True
    ):
        assert actual_min == pytest.approx(expected_min, abs=1e-6)
        assert actual_max == pytest.approx(expected_max, abs=1e-6)


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
    # A szelet-tengely mentén immár a Slice Engine saját, újra-bázisolt
    # (position_mm-alapú) koordinátarendszere érvényes, nem a nyers Mesh
    # world-koordinátája — ezért 0..15, nem a világ -7.5..7.5 tartománya.
    assert min(all_ys) == pytest.approx(0.0)
    assert max(all_ys) == pytest.approx(15.0)


def test_apply_backplate_shape_excludes_outlier_island_extent() -> None:
    """BACKPLATE_SPEC.md 6. szakasz 10. pont: a Backplate alakja kizárólag
    a domináns közös síkba eső érintkező szakaszokból épül fel. Egy, a
    domináns csoporton kívül eső (kilógó) sziget kiterjedése — még ha a
    harmadik tengely mentén jóval szélesebb is, mint a domináns
    szigeteké — nem jelenik meg a kapott alakban, szemben egy
    hipotetikus, a teljes testet (a kilógó szigetet is) figyelembe vevő
    sziluettel."""
    slice_set = _make_hand_slice_set(
        [
            (-10.0, 10.0, -15.0, 15.0),
            (-10.0, 10.0, -15.0, 15.0),
            # Kilógó: nem éri el a közös síkot (x_max=5.0, a domináns
            # 10.0-hoz képest a 0.1 mm-es tűréshatáron kívül), de a
            # harmadik tengely (y) mentén sokkal szélesebb, mint a
            # domináns szigetek.
            (-10.0, 5.0, -30.0, 30.0),
        ]
    )

    _modified, backplate = apply_backplate(
        slice_set,
        backplate_normal_axis=BackplateNormalAxis.PLUS_X,
        backplate_thickness_mm=3.0,
        tab_length_mm=5.0,
    )

    all_third_axis_values = [p[0] for c in backplate.contours for p in c.points]
    # Egy hipotetikus, a teljes testet (a kilógó szigetet is) figyelembe
    # vevő sziluett a harmadik tengely mentén [-30, 30]-ig terjedne — a
    # tényleges keresztmetszet-alapú alak ehelyett a domináns szigetek
    # valós kiterjedésére, [-15, 15]-re szorítkozik.
    assert min(all_third_axis_values) == pytest.approx(-15.0)
    assert max(all_third_axis_values) == pytest.approx(15.0)


def _dome_capped_box_solid() -> trimesh.Trimesh:
    """Egy 20×20×20 mm doboz, aminek a +X lapján egy sekély (0.3 mm
    magas), kb. 5.5 mm sugarú, gömbfelület-szerűen kerekített dudor ül —
    a modell "enyhén nem-sík felülete" (pl. egy kerekített talp)
    BACKPLATE_SPEC.md 6. szakasz 10. pontjában leírt esetének minimális,
    kézzel ellenőrzött modellje. A dudor egy nagy sugarú (R=50 mm) gömb
    egy kis, a doboz lapjának közepére eső, levágott sapkája (Boole-
    metszettel kivágva, majd a dobozzal unióba véve) — így a doboz
    bounding boxa gyakorlatilag változatlan marad (csak a dudor csúcsáig,
    +0.3 mm-rel nő az X tartomány), nem egy hatalmas gömbtest.
    """
    box = trimesh.creation.box(extents=(20.0, 20.0, 20.0))
    sphere_radius_mm = 50.0
    bump_height_mm = 0.3
    sphere_center_x = 10.0 - sphere_radius_mm + bump_height_mm
    sphere = trimesh.creation.icosphere(subdivisions=5, radius=sphere_radius_mm)
    sphere.apply_translation([sphere_center_x, 0.0, 0.0])
    clip_box = trimesh.creation.box(extents=(4.0, 16.0, 16.0))
    clip_box.apply_translation([10.0, 0.0, 0.0])
    cap = sphere.intersection(clip_box)
    return box.union(cap)


def test_backplate_shape_tolerance_band_captures_non_flat_surface() -> None:
    """BACKPLATE_SPEC.md 6. szakasz 10. pont: a tűrés-sáv (nem egy
    nulla-vastagságú síkmetszet) szükséges, mert a modell tényleges
    felülete a közös sík magasságában nem feltétlenül tökéletesen sík.

    A `_dome_capped_box_solid()` dudorának csúcsa (`apex_x`) körüli
    tényleges Boole-metszet+vetítés (`_build_backplate_shape_from_mesh`)
    közvetlen, önálló ellenőrzése (a domináns-sík klaszterezésen kívül,
    amely ezen a fixture-ön a doboz sík lapját, nem a dudort választaná
    közös síknak) — determinisztikus, kézzel lefuttatott és leellenőrzött
    értékekkel:
    - egy tényleges, nulla-vastagságú síkmetszet a dudor csúcsánál
      (`Trimesh.section()`) semmit nem fog ki (a dudor a csúcsban csak
      érinti a síkot, a metszet üres/`None`) — ez pontosan az a hiba,
      amit a korábbi, téves nulla-vastagságú metszet-közelítés elkövetett;
    - egy szűk (0.1 mm) tűrés-sáv már egy kis, a dudor köré eső
      korong alakú területet fog ki (jóval nagyobbat, mint a nulla-
      vastagságú metszet "szinte semmi" eredménye);
    - egy szélesebb (1.0 mm) tűrés-sáv, mivel eléri a doboz sík lapját is
      (a dudor csúcsa a lap fölé csak 0.3 mm-rel emelkedik), a teljes
      20×20 mm-es lapot kifogja.
    """
    solid = _dome_capped_box_solid()
    apex_x = float(solid.bounds[1][0])
    assert apex_x == pytest.approx(10.3, abs=1e-6)

    bounds = solid.bounds
    bounding_box = BoundingBox(
        min=(float(bounds[0][0]), float(bounds[0][1]), float(bounds[0][2])),
        max=(float(bounds[1][0]), float(bounds[1][1]), float(bounds[1][2])),
    )
    mesh = Mesh(
        vertices=tuple(tuple(float(c) for c in v) for v in solid.vertices),
        triangles=tuple(tuple(int(i) for i in f) for f in solid.faces),
        source_path="dome.stl",
        bounding_box=bounding_box,
        is_valid=True,
        warnings=(),
    )
    slice_set = create_slice_set(mesh, slice_thickness_mm=2.0, gap_mm=0.0)

    # Egy tényleges, nulla-vastagságú síkmetszet a dudor csúcsánál: a
    # gömbfelület a csúcsban csak érinti a síkot, a metszet üres.
    trimesh_mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.triangles)
    zero_width_section = trimesh_mesh.section(
        plane_origin=[apex_x, 0.0, 0.0], plane_normal=[1.0, 0.0, 0.0]
    )
    assert zero_width_section is None

    narrow_shape = _build_backplate_shape_from_mesh(
        slice_set, apex_x, BackplateNormalAxis.PLUS_X, backplate_plane_tolerance_mm=0.1
    )
    wide_shape = _build_backplate_shape_from_mesh(
        slice_set, apex_x, BackplateNormalAxis.PLUS_X, backplate_plane_tolerance_mm=1.0
    )

    # A szűk tűrés-sáv egy kis, a dudor csúcsa körüli korongot fog ki —
    # jóval kevesebbet, mint a doboz teljes (20×20 mm = 400 mm²) lapja.
    assert narrow_shape.area == pytest.approx(28.527259, abs=1e-3)
    assert 0.0 < narrow_shape.area < 400.0

    # A szélesebb tűrés-sáv eléri a doboz sík lapját is — a teljes
    # 20×20 mm-es lapot kifogja.
    assert wide_shape.area == pytest.approx(400.0, abs=1e-3)

    # A tűrés-sáv szélesítése tehát ténylegesen szélesebb/teljesebb
    # alakot ad, mint a nulla-vastagságú metszet ("szinte semmi").
    assert wide_shape.area > narrow_shape.area > 0.0
