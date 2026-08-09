"""Tesztek a Numbering Engine 1. köréhez (NUMBERING_SPEC.md 6. szakasz, 1-5. lépés)."""

import logging

import pytest
import trimesh
from shapely.geometry import Polygon

from slicedesigner.engines import numbering_engine as numbering_engine_module
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
    _build_text_strokes,
    _resolve_numbering_axes,
    _search_best_anchor,
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


def _make_hand_slice_set_polygon_islands(
    slices_islands: list[list[tuple[tuple[float, float], ...]]],
    thickness_mm: float = 3.0,
) -> SliceSet:
    """`_make_hand_slice_set_numbering` általánosítása: tetszőleges (nem
    csak téglalap alakú) szigetkontúrok, közvetlenül pontlistaként
    megadva (CCW = szolid határ)."""
    slices = [
        Slice(
            thickness_mm=thickness_mm,
            contours=tuple(Contour(points=pts) for pts in islands),
            position_mm=(i - 0.5) * thickness_mm,
            index=i,
        )
        for i, islands in enumerate(slices_islands, start=1)
    ]
    all_x = [p[0] for islands in slices_islands for pts in islands for p in pts]
    all_y = [p[1] for islands in slices_islands for pts in islands for p in pts]
    bounding_box = BoundingBox(
        min=(min(all_x), min(all_y), 0.0),
        max=(max(all_x), max(all_y), len(slices_islands) * thickness_mm),
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
        slice_count=len(slices_islands),
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
    # Az új `_glyph_to_local()` a betű alakját a horgonyponttól KIFELÉ
    # (nem befelé) tolja el (l. a függvény docstringjét): a "1" karakter
    # egyetlen, gx=0.6*height_mm=3.0-nál futó függőleges száron áll, így
    # minden pontja anchor_x (0.0) + 3.0 = 3.0-nál van — nem az anchor
    # pontján (0.0), mint a korábbi, befelé-növekvő leképezésnél.
    assert max(xs) == pytest.approx(3.0, abs=1e-6)


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

    slice_set_with_tabs, tabs, _common_plane_mm, _backplate_shape = (
        place_backplate_tabs(
            slice_set,
            backplate_normal_axis=BackplateNormalAxis.PLUS_X,
            backplate_thickness_mm=3.0,
            tab_length_mm=5.0,
        )
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
        numbered_slice_set,
        backplate,
        BackplateNormalAxis.PLUS_X,
        tabs,
        numbering_height_mm=2.0,
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
            numbered_slice_set,
            backplate,
            BackplateNormalAxis.PLUS_X,
            tabs,
            numbering_height_mm=50.0,
        )

    assert len(result_backplate.numbering_marks) == 0
    assert any(
        "numbering_min_height_mm" in record.getMessage() for record in caplog.records
    )


def test_apply_numbering_to_backplate_invalid_height_raises() -> None:
    numbered_slice_set, backplate, tabs = _make_numbered_backplate_fixture(2.0)

    with pytest.raises(InvalidNumberingError):
        apply_numbering_to_backplate(
            numbered_slice_set,
            backplate,
            BackplateNormalAxis.PLUS_X,
            tabs,
            numbering_height_mm=0.0,
        )


def test_apply_numbering_to_backplate_invalid_min_height_raises() -> None:
    numbered_slice_set, backplate, tabs = _make_numbered_backplate_fixture(2.0)

    with pytest.raises(InvalidNumberingError):
        apply_numbering_to_backplate(
            numbered_slice_set,
            backplate,
            BackplateNormalAxis.PLUS_X,
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
            BackplateNormalAxis.PLUS_X,
            tabs,
            numbering_height_mm=2.0,
            numbering_margin_mm=-1.0,
        )


def test_apply_numbering_places_mark_on_notched_island() -> None:
    """ "L" alakú sziget: a befoglaló téglalap "hátulsó-alsó" sarka (a
    kimetszett saroknégyzet miatt) a sziget anyagán kívülre esik.
    Korábban ez azt jelentette, hogy az azonosító a szigetről teljesen
    kimaradt, annak ellenére, hogy a szigeten bőven lenne hely máshol
    (NUMBERING_SPEC.md 6. szakasz, 2-4. pont — keresés-alapú
    pozícionálás)."""
    l_shape = (
        (0.0, 0.0),
        (20.0, 0.0),
        (20.0, 15.0),
        (15.0, 15.0),
        (15.0, 20.0),
        (0.0, 20.0),
    )
    slice_set = _make_hand_slice_set_polygon_islands([[l_shape]])

    result = apply_numbering(
        slice_set,
        numbering_normal_axis=BackplateNormalAxis.PLUS_X,
        numbering_direction_axis_sign=NumberingDirectionSign.POSITIVE,
        numbering_height_mm=5.0,
    )

    marks = result.slices[0].numbering_marks
    assert len(marks) == 1
    assert marks[0].height_mm == pytest.approx(5.0)
    assert len(marks[0].strokes) > 0


def test_search_best_anchor_finds_closest_valid_position() -> None:
    """A `_search_best_anchor` a célponthoz legközelebbi, ténylegesen
    elférő pozíciót adja vissza, nem egy tetszőleges/távoli helyet.

    Az új `_glyph_to_local()` a betű (illetve a footprint-téglalap)
    lenyomatát a horgonyponttól mindkét tengelyen KIFELÉ (a nagyobb
    koordináták felé) tolja el (`upright=True` esetén: `anchor + (gx,
    gy)`) — l. a `_glyph_to_local` docstringjét. Emiatt a footprint
    `[anchor_normal, anchor_normal + width_mm] x [anchor_direction,
    anchor_direction + height_mm]` (itt `width_mm = 0.6 * 5.0 = 3.0`,
    `height_mm = 5.0`). Az "L" alakú sziget befoglaló tartománya
    [0, 20] mindkét tengelyen, kivéve a [15, 20] x [15, 20] kimetszett
    sarkot — így a footprint csak akkor fér el, ha egyszerre:
    `anchor_normal <= 17` és `anchor_direction <= 15` (a [0,20]
    tartományon belül marad), ÉS (`anchor_normal <= 12` VAGY
    `anchor_direction <= 10`) (elkerüli a kimetszett sarkot).

    A célponthoz (`target_normal = target_direction = 18.75`)
    legközelebbi, ezt kielégítő rácspont (1.0 mm-es lépésekkel)
    `(anchor_normal, anchor_direction) = (12.0, 15.0)` — ez az
    `anchor_normal <= 12` ágat választja (a 17-es korlátot kihasználó
    ág, `anchor_direction <= 10`, ennél távolabb esne a célponttól)."""
    l_shape_polygon = Polygon(
        [
            (0.0, 0.0),
            (20.0, 0.0),
            (20.0, 15.0),
            (15.0, 15.0),
            (15.0, 20.0),
            (0.0, 20.0),
        ]
    )
    # text="1", height_mm=5.0 -> width_mm = 0.6 * 5.0 = 3.0
    target_normal = 20.0 - 1.25
    target_direction = 20.0 - 1.25

    result = _search_best_anchor(
        "1",
        5.0,
        True,
        target_normal,
        target_direction,
        0,
        1.0,
        1,
        1.0,
        l_shape_polygon,
        0.0,
        20.0,
        0.0,
        20.0,
    )

    assert result is not None
    anchor_normal, anchor_direction = result
    assert anchor_normal == pytest.approx(12.0)
    assert anchor_direction == pytest.approx(15.0)

    # A talált pozíció a kimetszett sarok elkerülése miatt kényszerűen
    # távol esik a célponttól (l. a docstringet) — ez a "kifelé
    # növekvő" leképezés elfogadott, teljesítménybeli (nem
    # helyességi) következménye, nem a keresés hibája: a tényleges
    # távolság pontosan a fenti (12.0, 15.0) horgonyból adódik.
    distance = (
        (anchor_normal - target_normal) ** 2
        + (anchor_direction - target_direction) ** 2
    ) ** 0.5
    assert distance == pytest.approx(7.721722605740251)


def test_search_best_anchor_quick_path_finds_inward_corner_without_full_scan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A gyors út a szöveg-téglalap mind a négy lehetséges sarok-
    illesztését kipróbálja, mielőtt a teljes rácsos keresésre esne —
    így akkor is O(1) hívással talál megoldást, ha a célpont a
    lenyomat "befelé eső" (nem a "kifelé eső") sarkát reprezentálja.

    A sziget itt PONTOSAN a szöveg-lenyomat méretével egyezik (3.0 x
    5.0 mm — text="1", height_mm=5.0), az origóban:
    (0,0)-(3,0)-(3,5)-(0,5). A célpont a lenyomat "kifelé eső" sarka
    (target_normal=3.0, target_direction=5.0): a lenyomatot közvetlenül
    a célpontra próbálva [3,6] x [5,10]-re esne, teljesen a sziget
    anyagán KÍVÜL. A négy sarok-illesztési jelölt közül csak az,
    amelyik a célpontot a lenyomat jobb-felső sarkával illeszti (azaz
    a lenyomatot a "befelé eső" (0,0)-(3,5) téglalapra helyezi),
    esik a sziget anyagán belülre — ezt a gyors útnak a teljes,
    [-100, 100] tartományú rácsos bejárás (több ezer `_fits()` hívás)
    nélkül kell megtalálnia."""
    island_polygon = Polygon([(0.0, 0.0), (3.0, 0.0), (3.0, 5.0), (0.0, 5.0)])

    call_count = 0
    original_fits = numbering_engine_module._fits

    def _counting_fits(*args: object, **kwargs: object) -> bool:
        nonlocal call_count
        call_count += 1
        return bool(original_fits(*args, **kwargs))

    monkeypatch.setattr(numbering_engine_module, "_fits", _counting_fits)

    result = _search_best_anchor(
        "1",
        5.0,
        True,
        3.0,
        5.0,
        0,
        1.0,
        1,
        1.0,
        island_polygon,
        -100.0,
        100.0,
        -100.0,
        100.0,
    )

    assert result is not None
    anchor_normal, anchor_direction = result
    assert anchor_normal == pytest.approx(0.0)
    assert anchor_direction == pytest.approx(0.0)

    # A négy gyors jelölt mindegyike pontosan egy `_fits()` hívást
    # jelent — ha ennél sokkal több hívás történt, az azt jelentené,
    # hogy a teljes, [-100, 100] tartományú rácsos bejárás is lefutott.
    assert call_count <= 4


def test_search_best_anchor_exhaustive_branch_avoids_full_grid_scan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A kimerítő ág (amikor a gyors sarok-jelöltek egyike sem talál
    érvényes pozíciót) a célponttól táguló sorrendben, NEM a rács rögzített
    bejárási sorrendjében vizsgálja a rácspontokat — az első megfelelő
    találatnál megáll, mert az garantáltan a legközelebbi (l.
    `_iter_grid_points_by_distance()` docstringje).

    Ugyanaz az L-alakú sziget és célpont, mint
    `test_search_best_anchor_finds_closest_valid_position`-ban (a gyors
    sarok-jelöltek ugyanúgy elbuknak, mert a célpont a kimetszett sarokba
    esne) — DE a keresési tartomány (`min_normal`..`max_normal`,
    `min_direction`..`max_direction`) itt szándékosan sokkal nagyobb
    (0..2000 mind a két tengelyen, szemben a sziget tényleges 0..20
    kiterjedésével), hogy a teljes rács mérete (2001 x 2001 =
    4 004 001 rácspont) egyértelműen elváljon a ténylegesen szükséges
    `_fits()`-hívások számától. A visszaadott horgonypontnak a tágabb
    tartomány ellenére is ugyanannak (12.0, 15.0) kell lennie, mint a
    kisebb tartománnyal — a keresési tartomány mérete nem befolyásolja a
    helyességet (NUMBERING_SPEC.md 6. szakasz 3. pont: nincs felső korlát
    vagy keresési sugár), csak a bejárás sorrendjét/korai megállását."""
    l_shape_polygon = Polygon(
        [
            (0.0, 0.0),
            (20.0, 0.0),
            (20.0, 15.0),
            (15.0, 15.0),
            (15.0, 20.0),
            (0.0, 20.0),
        ]
    )

    call_count = 0
    original_fits = numbering_engine_module._fits

    def _counting_fits(*args: object, **kwargs: object) -> bool:
        nonlocal call_count
        call_count += 1
        return bool(original_fits(*args, **kwargs))

    monkeypatch.setattr(numbering_engine_module, "_fits", _counting_fits)

    result = _search_best_anchor(
        "1",
        5.0,
        True,
        18.75,
        18.75,
        0,
        1.0,
        1,
        1.0,
        l_shape_polygon,
        0.0,
        2000.0,
        0.0,
        2000.0,
    )

    assert result is not None
    anchor_normal, anchor_direction = result
    assert anchor_normal == pytest.approx(12.0)
    assert anchor_direction == pytest.approx(15.0)

    # A teljes rács mérete ezzel a tartománnyal (2001 x 2001 rácspont)
    # ~4 millió `_fits()`-hívást jelentene egy sorrend-vak, kimerítő
    # bejárásnál. A távolság szerint táguló bejárás ennek töredékét —
    # nagyságrendekkel kevesebb hívást — igényel, mert a legközelebbi
    # érvényes pozíció a célponthoz közel van, nem a rács túlsó szélén.
    full_grid_upper_bound = 2001 * 2001
    assert call_count < full_grid_upper_bound / 1000


def test_build_text_strokes_not_mirrored_for_normal_index_zero() -> None:
    """Regressziós teszt az új `_glyph_to_local()`-ra — élő eset:
    `slice_axis=X`, `numbering_normal_axis=+Z`, ami `normal_index=0`-t
    eredményez (ld. ADR-0010: a `_SLICE_AXIS_CONTOUR_ORDER[SliceAxis.X]`
    a tükrözés bevezetése miatt `("Z", "Y")`-ra változott — korábban ezt
    a kombinációt `numbering_normal_axis=+Y` adta).

    Az új leképezésnél a betű ALAKJA (a `(gx, gy)` -> `(offset0,
    offset1)` eltolás) szándékosan FÜGGETLEN a `normal_index`/
    `direction_index` hozzárendeléstől: `upright=True` esetén mindig
    `offset0 = gx`, `offset1 = gy` — tehát a `direction_index` szerinti
    koordináta immár NEM feltétlenül hordozza a gx-eredetű (vízszintes)
    kiterjedést (ez itt `direction_index=1`, ami csak gy-t hordoz —
    l. lejjebb). A tükrözés-ellenőrzést ezért a 0. (nem a
    `direction_index` szerinti) koordinátán végezzük, amely
    `upright=True`-nál mindig a gx-eredetű kiterjedést hordozza,
    a `normal_index`/`direction_index` hozzárendelésétől függetlenül.

    A "7" karakter aszimmetrikus: egy teljes szélességű vízszintes
    felső vonalból (glyph-tér gx: 0 -> `0.6*height_mm`) és egy, a
    *nagyobb* gx-oldalon (gx = `0.6*height_mm`) végigfutó függőleges
    szárból áll. Helyes (nem tükrözött) leképezésnél a szárnak a 0.
    koordinátán a vízszintes vonal *nagyobbik* végpontjával azonos
    oldalra kell esnie — egy tükrözött leképezésnél a kisebbik oldalra
    esne."""
    normal_index, normal_sign, direction_index = _resolve_numbering_axes(
        SliceAxis.X, BackplateNormalAxis.PLUS_Z
    )
    assert normal_index == 0
    assert direction_index == 1

    strokes = _build_text_strokes(
        "7",
        10.0,
        True,
        50.0,
        50.0,
        normal_index,
        normal_sign,
        direction_index,
        1.0,
    )

    # "7" szegmensei ("abc"): "a" a felső vízszintes vonal (gx: 0 ->
    # 0.6*height), "b"/"c" együtt a jobb oldali függőleges szár
    # (gx = 0.6*height, gy: height -> 0).
    top_stroke, stem_upper_stroke, stem_lower_stroke = strokes
    top_start_x = top_stroke[0][0]
    top_end_x = top_stroke[1][0]
    stem_x = stem_upper_stroke[0][0]

    # A szár a vízszintes vonal *nagyobbik* végpontjával azonos
    # oldalon van — nem a kisebbiken (ami tükrözést jelentene).
    assert stem_x == pytest.approx(max(top_start_x, top_end_x))
    assert stem_x != pytest.approx(min(top_start_x, top_end_x))

    # A szár mindkét fél-szegmense (b, c) ugyanazon a 0. koordinátán
    # fut (függőleges vonal) — ez csak a geometria integritását
    # igazolja.
    assert stem_upper_stroke[1][0] == pytest.approx(stem_x)
    assert stem_lower_stroke[0][0] == pytest.approx(stem_x)
    assert stem_lower_stroke[1][0] == pytest.approx(stem_x)


def test_build_text_strokes_f_stands_upright_and_unmirrored() -> None:
    """Regressziós teszt az új `_glyph_to_local()`-ra (a prompt 7.
    szakasza szerinti elfogadási kritérium): az "F" karakter a
    tényleges stroke-koordinátái alapján helyesen áll — nem tükrözött
    ÉS nem fejjel lefelé.

    Az "F" ("aefg" szegmensek) egy teljes magasságú, BAL oldali
    (gx=0) függőleges szárból (f: felső fél, e: alsó fél) és két,
    a szártól JOBBRA kinyúló vízszintes vonalból áll: "a" a tetején
    (gy=height), "g" középen (gy=height/2).

    `upright=True` esetén `offset0=gx`, `offset1=gy` (l. a
    `_glyph_to_local` docstringjét) — ez a betű alakját a
    horgonyponttól (10.0, 10.0) függetlenül, mindig ugyanígy rögzíti,
    normal/direction-index-hozzárendeléstől függetlenül."""
    strokes = _build_text_strokes(
        "F",
        10.0,
        True,
        10.0,
        10.0,
        0,
        1.0,
        1,
        1.0,
    )
    top_stroke, e_stroke, f_stroke, middle_stroke = strokes

    # Nem tükrözött: a függőleges szár (f, e) a horgonypont SAJÁT
    # oldalán (0. koordináta = 10.0, a gx=0-nak megfelelően) marad —
    # nem tolódik el a szemközti oldalra —, és a vízszintes vonalak
    # ettől JOBBRA (nagyobb 0. koordináta felé) nyúlnak ki.
    assert f_stroke[0][0] == pytest.approx(10.0)
    assert f_stroke[1][0] == pytest.approx(10.0)
    assert e_stroke[0][0] == pytest.approx(10.0)
    assert e_stroke[1][0] == pytest.approx(10.0)
    assert top_stroke[1][0] > f_stroke[0][0]
    assert middle_stroke[1][0] > f_stroke[0][0]

    # Nem fejjel lefelé: a felső vonal (a) magasabban van (nagyobb 1.
    # koordináta), mint a középső (g) — nem megfordítva.
    assert top_stroke[0][1] > middle_stroke[0][1]


def test_build_text_strokes_rect_seven_not_mirrored_on_backplate() -> None:
    """Regressziós teszt a Backplate-oldali `_glyph_point_rect()`/
    `_build_text_strokes_rect()`-re (ADR-0010, prompt 8. szakasz): a "7"
    karakter (aszimmetrikus: teljes szélességű felső vízszintes vonal +
    a *nagyobb* gx-oldalon futó függőleges szár, ld. `_CHARACTER_SEGMENTS`)
    tényleges stroke-koordinátái alapján helyesen áll — nem tükrözött.

    A hibás (`upright=True`) ág `(anchor_x + gx, anchor_y - gy)` volt —
    ez a magasság (gy) tengelyén tükrözött, mert a glyph-tér `gy=height`
    (a karakter TETEJE) az `anchor_y - height`-hoz (a horgonypont ALATT,
    a `_fits_on_backplate()` téglalap-kontraktusa szerint a szövegdoboz
    ALJÁN) képeződött le, `gy=0` (a karakter ALJA) pedig `anchor_y`-hoz
    (a doboz TETEJÉN) — fejjel lefelé. A javított leképezés
    (`anchor_x + gx, anchor_y - height_mm + gy`) ezt megfordítja: a
    karakter teteje a doboz tetejénél (`anchor_y`), az alja a doboz
    alján (`anchor_y - height_mm`) van."""
    anchor_x, anchor_y, height_mm = 10.0, 10.0, 10.0
    strokes = numbering_engine_module._build_text_strokes_rect(
        "7", height_mm, True, anchor_x, anchor_y
    )

    # "7" szegmensei ("abc"): "a" a felső vízszintes vonal (gx: 0 ->
    # 0.6*height), "b"/"c" együtt a jobb oldali (nagyobb gx) függőleges
    # szár (gx = 0.6*height, gy: height -> 0).
    top_stroke, stem_upper_stroke, stem_lower_stroke = strokes

    # A felső vízszintes vonal a doboz TETEJÉN van (0. koord = anchor_y),
    # nem az alján — ez a lényegi, korábban tükrözött viselkedés.
    assert top_stroke[0] == pytest.approx((anchor_x, anchor_y))
    assert top_stroke[1] == pytest.approx((anchor_x + 0.6 * height_mm, anchor_y))

    # A szár a vízszintes vonal nagyobbik (jobb oldali) végpontjától
    # indul, és a doboz ALJÁIG (anchor_y - height_mm) fut LEFELÉ — nem
    # felfelé, a doboz fölé.
    stem_x = anchor_x + 0.6 * height_mm
    assert stem_upper_stroke[0] == pytest.approx((stem_x, anchor_y))
    assert stem_upper_stroke[1] == pytest.approx((stem_x, anchor_y - height_mm / 2))
    assert stem_lower_stroke[0] == pytest.approx((stem_x, anchor_y - height_mm / 2))
    assert stem_lower_stroke[1] == pytest.approx((stem_x, anchor_y - height_mm))

    # Minden pont a `_fits_on_backplate()` téglalap-kontraktusa szerinti
    # dobozon belül van: x in [anchor_x, anchor_x+w], y in
    # [anchor_y-h, anchor_y] — nem azon kívül, ami tükrözésnél előfordulna.
    all_points = [p for stroke in strokes for p in stroke]
    assert all(
        anchor_y - height_mm - 1e-9 <= p[1] <= anchor_y + 1e-9 for p in all_points
    )


def test_apply_numbering_manual_position_does_not_search(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Kézi `manual_position` felülbírálás esetén nincs automatikus
    keresés: ha a megadott ponton egyik tájolásban/méretben sem fér el
    az azonosító, a jelölés kimarad figyelmeztetéssel — annak
    ellenére, hogy a szigeten (mint azt
    `test_apply_numbering_manual_position_used` ugyanezen a
    fixture-ön demonstrálja) bőven lenne hely máshol."""
    slice_set = _make_box_slice_set(extents=(20.0, 30.0, 15.0), slice_thickness_mm=3.0)
    override = SliceNumberingOverride(slice_index=1, manual_position=(1000.0, 1000.0))

    with caplog.at_level(logging.WARNING):
        result = apply_numbering(
            slice_set,
            numbering_normal_axis=BackplateNormalAxis.PLUS_X,
            numbering_direction_axis_sign=NumberingDirectionSign.POSITIVE,
            numbering_height_mm=5.0,
            slice_numbering_overrides=(override,),
        )

    assert len(result.slices[0].numbering_marks) == 0
    assert any(
        "numbering_min_height_mm" in record.getMessage() for record in caplog.records
    )
