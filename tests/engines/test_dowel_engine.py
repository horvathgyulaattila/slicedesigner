"""Tesztek a Dowel Engine-hez (DOWEL_SYSTEM_SPEC.md)."""

import logging

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


def _rect_contour(x_min: float, x_max: float, y_min: float, y_max: float) -> Contour:
    return Contour(
        points=(
            (x_min, y_min),
            (x_max, y_min),
            (x_max, y_max),
            (x_min, y_max),
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


def test_apply_dowels_auto_placement_matches_characterized_positions() -> None:
    """Karakterizációs regressziós teszt (bit-pontos Dowel-pozíciók).

    A korábbi (teljesítmény-javítási kör alatt felvett) verzió a rács-
    bejárás rögzített (-length, y, x) sorrendjén alapuló, kizárólag
    futáshossz szerinti kiválasztást rögzítette — ez a három Dowelt
    egyetlen él mentén klaszterezte ((-11,-11), (-3,-11), (5,-11), mind
    y=-11-en). A DOWEL_SYSTEM_SPEC.md 6. szakasz 4. pontjának módosítása
    (térbeli szórás: a 2., 3., ... automatikus Dowel a hozzá legközelebbi
    már elhelyezett Dowel-től mért távolságot maximalizálva kerül
    kiválasztásra) szándékosan megváltoztatja ezeket a pozíciókat — lásd
    `test_apply_dowels_auto_placement_spreads_across_region_not_clustered()`
    a viselkedés-változás indoklásáért. Ez az új várt érték az immár
    amendált spec szerinti, változatlan kódon mért karakterizációs alap.
    """
    slice_set = _make_box_slice_set(extents=(30.0, 30.0, 15.0), slice_thickness_mm=3.0)

    _modified, positions = apply_dowels(slice_set, dowel_diameter_mm=4.0)

    assert [
        (
            p.x_mm,
            p.y_mm,
            p.diameter_mm,
            p.length_mm,
            p.start_slice_index,
            p.end_slice_index,
            p.region_id,
        )
        for p in positions
    ] == [
        (-11.0, -11.0, 4.0, 15.0, 1, 5, 1),
        (11.0, 11.0, 4.0, 15.0, 1, 5, 1),
        (11.0, -11.0, 4.0, 15.0, 1, 5, 1),
    ]


def test_apply_dowels_auto_placement_spreads_across_region_not_clustered() -> None:
    """DOWEL_SYSTEM_SPEC.md 6. szakasz 4/b. pont: minden további automatikus
    Dowel a hozzá legközelebbi, már elhelyezett Dowel-től mért távolságot
    maximalizálva kerül kiválasztásra — a Dowelek így a régió teljes
    kiterjedésén szétosztva helyezkednek el, nem egyetlen sarok/él mentén
    klaszterezve (a korábbi, kizárólag futáshossz-rendezésen alapuló
    algoritmus jellemző hibája, lásd
    `test_apply_dowels_auto_placement_matches_characterized_positions()`).
    """
    slice_set = _make_box_slice_set(extents=(30.0, 30.0, 15.0), slice_thickness_mm=3.0)

    _modified, positions = apply_dowels(slice_set, dowel_diameter_mm=4.0)

    assert len(positions) == 3
    xs = [p.x_mm for p in positions]
    ys = [p.y_mm for p in positions]
    # A korábbi, klaszterezett elrendezésben mindhárom Dowel azonos
    # y-koordinátán ült (0 mm y-szórás) — az új elrendezésnek a
    # rendelkezésre álló teljes tartományt (kb. 22 mm, a 30 mm-es kocka
    # élhosszából a min_edge_clearance_mm/dowel_diameter_mm miatti
    # beszűkítéssel) kell lefednie mindkét tengelyen.
    assert max(xs) - min(xs) > 15.0
    assert max(ys) - min(ys) > 15.0

    pairwise_distances = [
        ((a.x_mm - b.x_mm) ** 2 + (a.y_mm - b.y_mm) ** 2) ** 0.5
        for i, a in enumerate(positions)
        for b in positions[i + 1 :]
    ]
    # Az átfedés-mentességi minimum (2 * check_radius_mm = dowel_diameter_mm
    # + 2 * min_edge_clearance_mm = 4 + 2*2 = 8 mm) messze alatta marad a
    # ténylegesen elért páronkénti távolságoknak.
    assert min(pairwise_distances) > 15.0


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


def _make_hand_built_slice_set(
    slices: tuple[Slice, ...], bounding_box: BoundingBox
) -> SliceSet:
    mesh = Mesh(
        vertices=((0.0, 0.0, 0.0),),
        triangles=(),
        source_path="hand-built.stl",
        bounding_box=bounding_box,
        is_valid=True,
        warnings=(),
    )
    return SliceSet(
        source_mesh=mesh, gap_mm=0.0, slices=slices, slice_count=len(slices)
    )


def _make_branching_slice_set(
    branch_a: tuple[float, float, float],
    branch_b: tuple[float, float, float],
    trunk_x_range: tuple[float, float],
    trunk_y_range: tuple[float, float] = (-12.0, 12.0),
    thickness_mm: float = 3.0,
) -> SliceSet:
    """Egy elágazó, összefüggő régió: egy "törzs" szelet (index 1), amely
    mindkét, egymástól térben távoli "ágra" (index 2, 3) rákapcsolódik
    (DOWEL_SYSTEM_SPEC.md 6. szakasz 4/a. pont, elágazó régió esete).

    `branch_a`/`branch_b`: `(cx, cy, half)` a két ág négyzetéhez.
    """
    trunk = _rect_contour(trunk_x_range[0], trunk_x_range[1], *trunk_y_range)
    branch_a_contour = _square_contour(*branch_a)
    branch_b_contour = _square_contour(*branch_b)

    slices = (
        Slice(thickness_mm=thickness_mm, contours=(trunk,), position_mm=1.5, index=1),
        Slice(
            thickness_mm=thickness_mm,
            contours=(branch_a_contour, branch_b_contour),
            position_mm=4.5,
            index=2,
        ),
        Slice(
            thickness_mm=thickness_mm,
            contours=(branch_a_contour, branch_b_contour),
            position_mm=7.5,
            index=3,
        ),
    )
    bounding_box = BoundingBox(
        min=(trunk_x_range[0], trunk_y_range[0], 0.0),
        max=(trunk_x_range[1], trunk_y_range[1], 3 * thickness_mm),
    )
    return _make_hand_built_slice_set(slices, bounding_box)


def test_apply_dowels_branching_region_covers_both_branches() -> None:
    """DOWEL_SYSTEM_SPEC.md 6. szakasz 4/a. pont: a lefedettségi szakasz
    minden, egyetlen Dowel-lel sem érintett szigetet lefed, a
    `dowel_count_per_region` célszámtól függetlenül is.

    Egy törzshöz kapcsolódó, egymástól 200 mm-re lévő két ág (egyenként
    2 szeleten át, 20x20 mm alapterülettel) mindegyike önmagában is
    lefedhető lenne — a korábbi, egyetlen célszámig töltő logika
    (`dowel_count_per_region=1`) csak az egyiket helyezte volna el.
    """
    slice_set = _make_branching_slice_set(
        branch_a=(0.0, 0.0, 10.0),
        branch_b=(200.0, 0.0, 10.0),
        trunk_x_range=(-15.0, 215.0),
        trunk_y_range=(-10.0, 10.0),
    )

    _modified, positions = apply_dowels(
        slice_set,
        dowel_diameter_mm=4.0,
        dowel_count_per_region=1,
        min_dowels_per_region=1,
    )

    assert any(-10.0 <= p.x_mm <= 10.0 and -10.0 <= p.y_mm <= 10.0 for p in positions)
    assert any(190.0 <= p.x_mm <= 210.0 and -10.0 <= p.y_mm <= 10.0 for p in positions)


def test_apply_dowels_scarcity_first_covers_scarce_and_abundant_islands() -> None:
    """DOWEL_SYSTEM_SPEC.md 6. szakasz 4/a. pont: a legkevesebb érvényes
    jelölttel rendelkező sziget kerül előbb feldolgozásra — a szűkösebb
    szigetet nem szorítja ki a bőségesebb jelölt-készlettel rendelkező
    másik sziget.

    A kisebb ág (12x12 mm) lényegesen kevesebb érvényes rácsponttal
    rendelkezik, mint a nagyobb, mellette lévő ág (24x24 mm) — mindkettő
    lefedését elvárjuk, `dowel_count_per_region=1` mellett is (amikor a
    korábbi, egyetlen célszámig töltő logika csak az egyiket, jellemzően
    a tágabb mozgásterű ágat helyezte volna el).
    """
    slice_set = _make_branching_slice_set(
        branch_a=(0.0, 0.0, 6.0),
        branch_b=(24.0, 0.0, 12.0),
        trunk_x_range=(-10.0, 40.0),
        trunk_y_range=(-12.0, 12.0),
    )

    _modified, positions = apply_dowels(
        slice_set,
        dowel_diameter_mm=4.0,
        dowel_count_per_region=1,
        min_dowels_per_region=1,
    )

    assert any(-6.0 <= p.x_mm <= 6.0 and -6.0 <= p.y_mm <= 6.0 for p in positions)
    assert any(12.0 <= p.x_mm <= 36.0 and -12.0 <= p.y_mm <= 12.0 for p in positions)


def test_apply_dowels_never_coverable_island_warns_without_raising(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """DOWEL_SYSTEM_SPEC.md 6. szakasz 8. pont: egy olyan szigetre, amelyen
    a `check_radius_mm` sugarú kör sehol nem fér el, figyelmeztetés
    kerül rögzítésre, de a régió (a többi szigete révén) sikeresnek
    számít — nincs hiba.

    A régió fő szigete (20x20 mm, 3 szeleten át) önmagában bőven
    lefedhető; a 2. szeleten hozzáadott, 0,5 mm széles "sliver" sziget
    (amely a fő szigettel érintkezve csatlakozik a régióhoz, de a
    4 mm sugarú kör sehol nem fér el rajta) sosem kaphat Dowelt.
    """
    main_island = _square_contour(0.0, 0.0, 10.0)
    sliver = _rect_contour(10.0, 10.5, -10.0, 10.0)
    thickness_mm = 3.0

    slices = (
        Slice(
            thickness_mm=thickness_mm, contours=(main_island,), position_mm=1.5, index=1
        ),
        Slice(
            thickness_mm=thickness_mm,
            contours=(main_island, sliver),
            position_mm=4.5,
            index=2,
        ),
        Slice(
            thickness_mm=thickness_mm, contours=(main_island,), position_mm=7.5, index=3
        ),
    )
    bounding_box = BoundingBox(min=(-10.0, -10.0, 0.0), max=(10.5, 10.0, 9.0))
    slice_set = _make_hand_built_slice_set(slices, bounding_box)

    with caplog.at_level(logging.WARNING, logger="slicedesigner.engines.dowel_engine"):
        _modified, positions = apply_dowels(
            slice_set,
            dowel_diameter_mm=4.0,
            dowel_count_per_region=1,
            min_dowels_per_region=1,
        )

    assert len(positions) >= 1
    assert any(
        "2. szelet 1. szigete" in record.getMessage()
        and "nem kaphat Dowelt" in record.getMessage()
        for record in caplog.records
    )
