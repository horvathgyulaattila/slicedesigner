"""Numbering Engine (1. kör) — szelet-szintű azonosítók meghatározása és elhelyezése.

Lásd: docs/specifications/NUMBERING_SPEC.md (6. szakasz, 1-5. lépés).
A Backplate-oldali jelölés (6. lépés) külön menetben készül.
"""

import logging
from dataclasses import dataclass, replace
from enum import Enum

from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from slicedesigner.engines.backplate_engine import Backplate, BackplateNormalAxis, Tab
from slicedesigner.engines.exceptions import InvalidNumberingError
from slicedesigner.engines.slice_engine import (
    EngravingMark,
    Slice,
    SliceAxis,
    SliceSet,
    is_ccw,
    reconstruct_islands,
)

logger = logging.getLogger(__name__)

_SEGMENT_POINTS: dict[str, tuple[tuple[float, float], tuple[float, float]]] = {
    "a": ((0.0, 1.0), (0.6, 1.0)),
    "b": ((0.6, 1.0), (0.6, 0.5)),
    "c": ((0.6, 0.5), (0.6, 0.0)),
    "d": ((0.0, 0.0), (0.6, 0.0)),
    "e": ((0.0, 0.5), (0.0, 0.0)),
    "f": ((0.0, 1.0), (0.0, 0.5)),
    "g": ((0.0, 0.5), (0.6, 0.5)),
}

_CHARACTER_SEGMENTS: dict[str, str] = {
    "0": "abcdef",
    "1": "bc",
    "2": "abged",
    "3": "abgcd",
    "4": "fgbc",
    "5": "afgcd",
    "6": "afgecd",
    "7": "abc",
    "8": "abcdefg",
    "9": "abcdfg",
    "A": "abcefg",
    "B": "cdefg",
    "C": "adef",
    "D": "bcdeg",
    "E": "adefg",
    "F": "aefg",
    "G": "acdef",
    "H": "bcefg",
    "I": "ef",
    "J": "bcd",
    "K": "cefg",
    "L": "def",
    "M": "abcef",
    "N": "ceg",
    "O": "abcdef",
    "P": "abefg",
    "Q": "abcfg",
    "R": "efg",
    "S": "afgcd",
    "T": "defg",
    "U": "bcdef",
    "V": "cde",
    "W": "bcde",
    "X": "bcefg",
    "Y": "bcdfg",
    "Z": "abged",
}

_SLASH_STROKE: tuple[tuple[float, float], tuple[float, float]] = (
    (0.0, 0.0),
    (0.6, 1.0),
)

# Font-metrika (nem üzleti paraméter): a glyph-cella szélessége és a
# karakterek közötti rés, a magasság arányában.
_CHAR_WIDTH_RATIO = 0.6
_CHAR_SPACING_RATIO = 0.2

# Rács-felbontás (mm) a szelet-oldali automatikus azonosító-pozíció
# kereséshez — belső implementációs finomhangolás, nem a specifikáció
# szerinti üzleti paraméter (NUMBERING_SPEC.md 5. szakasza nem sorolja
# fel).
_PLACEMENT_GRID_STEP_MM = 1.0


def _char_strokes(
    char: str, height_mm: float
) -> tuple[tuple[tuple[float, float], ...], ...]:
    """Egy karakter strokejai glyph-térben (0..0.6*height szélesség,
    0..height magasság)."""
    if char == "/":
        (x1, y1), (x2, y2) = _SLASH_STROKE
        return (
            (
                (x1 * height_mm, y1 * height_mm),
                (x2 * height_mm, y2 * height_mm),
            ),
        )
    segments = _CHARACTER_SEGMENTS[char]
    strokes = []
    for seg_id in segments:
        (x1, y1), (x2, y2) = _SEGMENT_POINTS[seg_id]
        strokes.append(
            ((x1 * height_mm, y1 * height_mm), (x2 * height_mm, y2 * height_mm))
        )
    return tuple(strokes)


def _text_width_mm(text: str, height_mm: float) -> float:
    char_width = _CHAR_WIDTH_RATIO * height_mm
    spacing = _CHAR_SPACING_RATIO * height_mm
    return len(text) * char_width + (len(text) - 1) * spacing


_NORMAL_AXIS_WORLD: dict[BackplateNormalAxis, tuple[str, float]] = {
    BackplateNormalAxis.PLUS_X: ("X", 1.0),
    BackplateNormalAxis.MINUS_X: ("X", -1.0),
    BackplateNormalAxis.PLUS_Y: ("Y", 1.0),
    BackplateNormalAxis.MINUS_Y: ("Y", -1.0),
    BackplateNormalAxis.PLUS_Z: ("Z", 1.0),
    BackplateNormalAxis.MINUS_Z: ("Z", -1.0),
}

_SLICE_AXIS_CONTOUR_ORDER: dict[SliceAxis, tuple[str, str]] = {
    SliceAxis.Z: ("X", "Y"),
    SliceAxis.X: ("Y", "Z"),
    SliceAxis.Y: ("Z", "X"),
}


def _resolve_numbering_axes(
    slice_axis: SliceAxis, numbering_normal_axis: BackplateNormalAxis
) -> tuple[int, float, int]:
    """(normal tengely kontúr-indexe, előjele, direction tengely kontúr-indexe)."""
    world_axis, sign = _NORMAL_AXIS_WORLD[numbering_normal_axis]
    contour_axes = _SLICE_AXIS_CONTOUR_ORDER[slice_axis]
    if world_axis == slice_axis.value:
        raise InvalidNumberingError(
            f"A numbering_normal_axis ({numbering_normal_axis.value}) nem eshet "
            f"egybe a slice_axis-szal ({slice_axis.value})."
        )
    normal_index = contour_axes.index(world_axis)
    direction_index = 1 - normal_index
    return normal_index, sign, direction_index


class NumberingDirectionSign(Enum):
    """A `numbering_direction_axis_sign` — a harmadik tengely előjele."""

    POSITIVE = "+"
    NEGATIVE = "-"


_DIRECTION_SIGN_VALUE: dict[NumberingDirectionSign, float] = {
    NumberingDirectionSign.POSITIVE: 1.0,
    NumberingDirectionSign.NEGATIVE: -1.0,
}


@dataclass(frozen=True)
class SliceNumberingOverride:
    """Szigetenkénti azonosító méret-/pozíció-felülbírálás.

    Ha `island_index` `None`, és a szeletnek egynél több szigete van, a
    felülbírálás a szelet MINDEN szigetére alkalmazódik.

    A `manual_position`, ha meg van adva, a sziget saját 2D kontúr-
    koordinátáiban (ugyanabban a térben, mint a `Contour.points`) adja
    meg az azonosító "hátulsó-alsó" horgonypontját — ilyenkor a
    margó-alapú automatikus sarokszámítás kimarad.
    """

    slice_index: int
    island_index: int | None = None
    numbering_height_mm: float | None = None
    numbering_min_height_mm: float | None = None
    numbering_margin_mm: float | None = None
    manual_position: tuple[float, float] | None = None


@dataclass(frozen=True)
class _NumberingParams:
    height_mm: float
    min_height_mm: float
    margin_mm: float
    manual_position: tuple[float, float] | None


def _resolve_numbering_params(
    slice_index: int,
    island_index: int,
    base_height_mm: float,
    base_min_height_mm: float,
    base_margin_mm: float,
    overrides: tuple[SliceNumberingOverride, ...],
) -> _NumberingParams:
    for override in overrides:
        if override.slice_index != slice_index:
            continue
        if override.island_index is not None and override.island_index != island_index:
            continue
        return _NumberingParams(
            height_mm=(
                override.numbering_height_mm
                if override.numbering_height_mm is not None
                else base_height_mm
            ),
            min_height_mm=(
                override.numbering_min_height_mm
                if override.numbering_min_height_mm is not None
                else base_min_height_mm
            ),
            margin_mm=(
                override.numbering_margin_mm
                if override.numbering_margin_mm is not None
                else base_margin_mm
            ),
            manual_position=override.manual_position,
        )
    return _NumberingParams(
        height_mm=base_height_mm,
        min_height_mm=base_min_height_mm,
        margin_mm=base_margin_mm,
        manual_position=None,
    )


def _glyph_to_local(
    gx: float,
    gy: float,
    upright: bool,
    anchor_normal_oriented: float,
    anchor_direction_oriented: float,
    normal_index: int,
    normal_sign: float,
    direction_index: int,
    direction_sign: float,
) -> tuple[float, float]:
    """A glyph-tér (gx, gy) pontjának leképezése a kontúr-térbe.

    A horgonypont (`anchor_coords`) pozícióját a `normal_index`/
    `normal_sign`/`direction_index`/`direction_sign` határozza meg —
    ugyanúgy, mint eddig. A betű ALAKJA (az eltolás a horgonyponttól)
    viszont szándékosan FÜGGETLEN ezektől: mindig ugyanaz a rögzített
    `(gx, gy)` → `(offset0, offset1)` leképezés, `upright` szerint 0°
    vagy 90°-os elforgatással. Ez konstrukciósan kizárja a tükröződést
    (a betű alakja sosem függ attól, melyik kontúr-index/előjel
    kombináció van érvényben), és — mivel ez a rögzített leképezés
    vizuálisan ellenőrzött, helyesen álló, balról jobbra olvasható
    szöveget ad — a korábbi tájolási (fejjel lefelé) hibát is javítja.

    Elfogadott kompromisszum: a betű a horgonyponttól kifelé (nem
    befelé) növekszik, ezért a hívó (`_search_best_anchor`) gyors,
    egylépéses illeszkedés-tesztje gyakrabban eshet vissza a teljes
    rácsos keresésre — ez teljesítménybeli, nem helyességi hatás.
    """
    anchor_coords: list[float] = [0.0, 0.0]
    anchor_coords[normal_index] = anchor_normal_oriented * normal_sign
    anchor_coords[direction_index] = anchor_direction_oriented * direction_sign

    if upright:
        offset0, offset1 = gx, gy
    else:
        offset0, offset1 = -gy, gx

    return (anchor_coords[0] + offset0, anchor_coords[1] + offset1)


def _build_text_strokes(
    text: str,
    height_mm: float,
    upright: bool,
    anchor_normal_oriented: float,
    anchor_direction_oriented: float,
    normal_index: int,
    normal_sign: float,
    direction_index: int,
    direction_sign: float,
) -> tuple[tuple[tuple[float, float], ...], ...]:
    char_width = _CHAR_WIDTH_RATIO * height_mm
    spacing = _CHAR_SPACING_RATIO * height_mm

    all_strokes: list[tuple[tuple[float, float], ...]] = []
    cursor = 0.0
    for char in text:
        for glyph_stroke in _char_strokes(char, height_mm):
            local_stroke = tuple(
                _glyph_to_local(
                    cursor + gx,
                    gy,
                    upright,
                    anchor_normal_oriented,
                    anchor_direction_oriented,
                    normal_index,
                    normal_sign,
                    direction_index,
                    direction_sign,
                )
                for gx, gy in glyph_stroke
            )
            all_strokes.append(local_stroke)
        cursor += char_width + spacing

    return tuple(all_strokes)


def _text_footprint_polygon(
    text: str,
    height_mm: float,
    upright: bool,
    anchor_normal_oriented: float,
    anchor_direction_oriented: float,
    normal_index: int,
    normal_sign: float,
    direction_index: int,
    direction_sign: float,
) -> Polygon:
    width_mm = _text_width_mm(text, height_mm)
    corners_g = [(0.0, 0.0), (width_mm, 0.0), (width_mm, height_mm), (0.0, height_mm)]
    corners_local = [
        _glyph_to_local(
            gx,
            gy,
            upright,
            anchor_normal_oriented,
            anchor_direction_oriented,
            normal_index,
            normal_sign,
            direction_index,
            direction_sign,
        )
        for gx, gy in corners_g
    ]
    return Polygon(corners_local)


def _fits(
    text: str,
    height_mm: float,
    upright: bool,
    anchor_normal_oriented: float,
    anchor_direction_oriented: float,
    normal_index: int,
    normal_sign: float,
    direction_index: int,
    direction_sign: float,
    island_polygon: Polygon,
) -> bool:
    footprint = _text_footprint_polygon(
        text,
        height_mm,
        upright,
        anchor_normal_oriented,
        anchor_direction_oriented,
        normal_index,
        normal_sign,
        direction_index,
        direction_sign,
    )
    return bool(footprint.within(island_polygon))


def _text_footprint_offset_bounds(
    width_mm: float, height_mm: float, upright: bool
) -> tuple[float, float, float, float]:
    """A szöveg-lenyomat (offset0, offset1) tartománya — (min0, max0, min1,
    max1) —, ugyanazzal a `(gx, gy) -> (offset0, offset1)` leképezéssel,
    amit a `_glyph_to_local()` használ a négy sarokpontra. A
    `_search_best_anchor()` gyors útjának négy sarok-illesztési
    jelöltjéhez szükséges.
    """
    corners_g = ((0.0, 0.0), (width_mm, 0.0), (width_mm, height_mm), (0.0, height_mm))
    if upright:
        offsets = [(gx, gy) for gx, gy in corners_g]
    else:
        offsets = [(-gy, gx) for gx, gy in corners_g]
    xs = [o[0] for o in offsets]
    ys = [o[1] for o in offsets]
    return min(xs), max(xs), min(ys), max(ys)


def _search_best_anchor(
    text: str,
    height_mm: float,
    upright: bool,
    target_normal: float,
    target_direction: float,
    normal_index: int,
    normal_sign: float,
    direction_index: int,
    direction_sign: float,
    island_polygon: Polygon,
    min_normal: float,
    max_normal: float,
    min_direction: float,
    max_direction: float,
) -> tuple[float, float] | None:
    """A `(target_normal, target_direction)` célponthoz legközelebbi olyan
    horgonypont keresése, ahol a szöveg-lenyomat teljes egészében a
    sziget anyagán belül marad (NUMBERING_SPEC.md 6. szakasz 3. pont).

    Először a szöveg-téglalap mind a négy lehetséges sarok-illesztését
    próbálja a célponthoz (olcsó, O(1) esetenként) — ez akkor talál
    találatot, ha a célpont a téglalap bármelyik sarkával illeszkedve
    a sziget anyagán belül esik, függetlenül attól, hogy a
    `normal_sign`/`direction_sign` melyik sarkot jelöli ki ehhez a
    konkrét híváshoz. Csak ha egyik gyors jelölt sem felel meg, fut le a
    teljes, rácsos bejárás a sziget befoglaló téglalapján, felső korlát
    vagy keresési sugár nélkül.
    """
    target_coords: list[float] = [0.0, 0.0]
    target_coords[normal_index] = target_normal * normal_sign
    target_coords[direction_index] = target_direction * direction_sign

    width_mm = _text_width_mm(text, height_mm)
    off_min0, off_max0, off_min1, off_max1 = _text_footprint_offset_bounds(
        width_mm, height_mm, upright
    )

    quick_candidates: list[tuple[float, float]] = []
    for off0 in (off_min0, off_max0):
        for off1 in (off_min1, off_max1):
            candidate_coords = [
                target_coords[0] - off0,
                target_coords[1] - off1,
            ]
            candidate = (
                candidate_coords[normal_index] * normal_sign,
                candidate_coords[direction_index] * direction_sign,
            )
            if candidate not in quick_candidates:
                quick_candidates.append(candidate)

    best: tuple[float, float] | None = None
    best_distance = float("inf")
    for anchor_normal, anchor_direction in quick_candidates:
        if _fits(
            text,
            height_mm,
            upright,
            anchor_normal,
            anchor_direction,
            normal_index,
            normal_sign,
            direction_index,
            direction_sign,
            island_polygon,
        ):
            distance = (
                (anchor_normal - target_normal) ** 2
                + (anchor_direction - target_direction) ** 2
            ) ** 0.5
            if distance < best_distance:
                best_distance = distance
                best = (anchor_normal, anchor_direction)
    if best is not None:
        return best

    anchor_direction = min_direction
    while anchor_direction <= max_direction:
        anchor_normal = min_normal
        while anchor_normal <= max_normal:
            if _fits(
                text,
                height_mm,
                upright,
                anchor_normal,
                anchor_direction,
                normal_index,
                normal_sign,
                direction_index,
                direction_sign,
                island_polygon,
            ):
                distance = (
                    (anchor_normal - target_normal) ** 2
                    + (anchor_direction - target_direction) ** 2
                ) ** 0.5
                if distance < best_distance:
                    best_distance = distance
                    best = (anchor_normal, anchor_direction)
            anchor_normal += _PLACEMENT_GRID_STEP_MM
        anchor_direction += _PLACEMENT_GRID_STEP_MM
    return best


def _resolve_numbering(
    text: str,
    target_height_mm: float,
    min_height_mm: float,
    margin_mm: float,
    normal_index: int,
    normal_sign: float,
    direction_index: int,
    direction_sign: float,
    island_polygon: Polygon,
    solid_points: tuple[tuple[float, float], ...],
    manual_position: tuple[float, float] | None,
) -> tuple[float, bool, float, float] | None:
    """(alkalmazott magasság, upright?, anchor_normal, anchor_direction) vagy None."""
    oriented_normal = [p[normal_index] * normal_sign for p in solid_points]
    oriented_direction = [p[direction_index] * direction_sign for p in solid_points]
    target_normal = max(oriented_normal) - margin_mm
    target_direction = max(oriented_direction) - margin_mm

    if manual_position is not None:
        anchor_normal = manual_position[normal_index] * normal_sign
        anchor_direction = manual_position[direction_index] * direction_sign
        for height in (target_height_mm, min_height_mm):
            for upright in (True, False):
                if _fits(
                    text,
                    height,
                    upright,
                    anchor_normal,
                    anchor_direction,
                    normal_index,
                    normal_sign,
                    direction_index,
                    direction_sign,
                    island_polygon,
                ):
                    return height, upright, anchor_normal, anchor_direction
        return None

    min_normal, max_normal = min(oriented_normal), max(oriented_normal)
    min_direction, max_direction = min(oriented_direction), max(oriented_direction)

    for height in (target_height_mm, min_height_mm):
        candidates: list[tuple[float, bool, float, float]] = []
        for upright in (True, False):
            found = _search_best_anchor(
                text,
                height,
                upright,
                target_normal,
                target_direction,
                normal_index,
                normal_sign,
                direction_index,
                direction_sign,
                island_polygon,
                min_normal,
                max_normal,
                min_direction,
                max_direction,
            )
            if found is not None:
                anchor_normal, anchor_direction = found
                distance = (
                    (anchor_normal - target_normal) ** 2
                    + (anchor_direction - target_direction) ** 2
                ) ** 0.5
                candidates.append((distance, upright, anchor_normal, anchor_direction))
        if candidates:
            _distance, upright, anchor_normal, anchor_direction = min(
                candidates, key=lambda c: c[0]
            )
            return height, upright, anchor_normal, anchor_direction
    return None


def apply_numbering(
    slice_set: SliceSet,
    numbering_normal_axis: BackplateNormalAxis,
    numbering_direction_axis_sign: NumberingDirectionSign,
    numbering_height_mm: float,
    numbering_min_height_mm: float | None = None,
    numbering_margin_mm: float | None = None,
    slice_numbering_overrides: tuple[SliceNumberingOverride, ...] = (),
) -> SliceSet:
    """Minden szelet minden szigetének azonosítóval ellátása.

    Lásd: NUMBERING_SPEC.md 6. szakasz, 1-5. lépés.

    Args:
        slice_set: a pipeline addig lefutott lépéseinek kimenete.
        numbering_normal_axis: a "hátulsó" irány.
        numbering_direction_axis_sign: a harmadik tengely előjele (az
            "alsó" irány, és a szigetek A/B/C sorrendje).
        numbering_height_mm: az azonosító célzott magassága.
        numbering_min_height_mm: a minimálisan elfogadható magasság. Ha
            `None`, `numbering_height_mm / 2`.
        numbering_margin_mm: az azonosító távolsága a két legközelebbi
            éltől. Ha `None`, `numbering_height_mm / 4`.
        slice_numbering_overrides: szigetenkénti méret-/pozíció-
            felülbírálás.

    Returns:
        A gravírozási jelekkel kiegészített Slice Set.

    Raises:
        InvalidNumberingError: érvénytelen paraméter, vagy érvénytelen
            `numbering_normal_axis`. (Egy sziget azonosítója számára
            elférő hely hiánya csak figyelmeztetés, nem hiba —
            NUMBERING_SPEC.md 6. szakasz, 4. lépés.)
    """
    resolved_min_height_mm = (
        numbering_min_height_mm
        if numbering_min_height_mm is not None
        else numbering_height_mm / 2
    )
    resolved_margin_mm = (
        numbering_margin_mm
        if numbering_margin_mm is not None
        else numbering_height_mm / 4
    )

    if numbering_height_mm <= 0:
        raise InvalidNumberingError(
            "A numbering_height_mm értékének pozitívnak kell lennie: "
            f"{numbering_height_mm}"
        )
    if not (0 < resolved_min_height_mm <= numbering_height_mm):
        raise InvalidNumberingError(
            f"A numbering_min_height_mm-nek a (0, {numbering_height_mm}] tartományba "
            f"kell esnie: {resolved_min_height_mm}"
        )
    if resolved_margin_mm < 0:
        raise InvalidNumberingError(
            f"A numbering_margin_mm értéke nem lehet negatív: {resolved_margin_mm}"
        )

    normal_index, normal_sign, direction_index = _resolve_numbering_axes(
        slice_set.slice_axis, numbering_normal_axis
    )
    direction_sign = _DIRECTION_SIGN_VALUE[numbering_direction_axis_sign]

    new_slices: list[Slice] = []
    for slice_ in slice_set.slices:
        islands = reconstruct_islands(slice_)
        ordered_island_indices = sorted(
            range(len(islands)),
            key=lambda idx: (
                -max(
                    p[direction_index] * direction_sign
                    for p in islands[idx].solid.points
                )
            ),
        )

        marks: list[EngravingMark] = []
        for letter_position, island_index in enumerate(ordered_island_indices):
            island = islands[island_index]
            text = (
                str(slice_.index)
                if len(islands) == 1
                else f"{slice_.index}/{chr(ord('A') + letter_position)}"
            )

            params = _resolve_numbering_params(
                slice_.index,
                island_index,
                numbering_height_mm,
                resolved_min_height_mm,
                resolved_margin_mm,
                slice_numbering_overrides,
            )

            result = _resolve_numbering(
                text,
                params.height_mm,
                params.min_height_mm,
                params.margin_mm,
                normal_index,
                normal_sign,
                direction_index,
                direction_sign,
                island.polygon,
                island.solid.points,
                params.manual_position,
            )
            if result is None:
                logger.warning(
                    "A(z) %s. szelet %s. szigetének azonosítója (%s) egyik "
                    "tájolásban sem éri el a numbering_min_height_mm-et — a "
                    "jelölés kimarad.",
                    slice_.index,
                    island_index,
                    text,
                )
                continue
            height, upright, anchor_normal, anchor_direction = result

            strokes = _build_text_strokes(
                text,
                height,
                upright,
                anchor_normal,
                anchor_direction,
                normal_index,
                normal_sign,
                direction_index,
                direction_sign,
            )
            marks.append(
                EngravingMark(
                    text=text,
                    strokes=strokes,
                    height_mm=height,
                    island_index=island_index,
                )
            )

        new_slices.append(replace(slice_, numbering_marks=tuple(marks)))

    return replace(slice_set, slices=tuple(new_slices))


def _backplate_polygon(backplate: Backplate) -> BaseGeometry:
    """A Backplate kontúrjaiból egy (esetlegesen több darabból álló)
    Shapely geometria építése."""
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
    return unary_union(pieces)


def _glyph_point_rect(
    gx: float, gy: float, upright: bool, anchor_x: float, anchor_y: float
) -> tuple[float, float]:
    if upright:
        return (anchor_x + gx, anchor_y - gy)
    return (anchor_x + gy, anchor_y - gx)


def _build_text_strokes_rect(
    text: str, height_mm: float, upright: bool, anchor_x: float, anchor_y: float
) -> tuple[tuple[tuple[float, float], ...], ...]:
    char_width = _CHAR_WIDTH_RATIO * height_mm
    spacing = _CHAR_SPACING_RATIO * height_mm

    all_strokes: list[tuple[tuple[float, float], ...]] = []
    cursor = 0.0
    for char in text:
        for glyph_stroke in _char_strokes(char, height_mm):
            local_stroke = tuple(
                _glyph_point_rect(cursor + gx, gy, upright, anchor_x, anchor_y)
                for gx, gy in glyph_stroke
            )
            all_strokes.append(local_stroke)
        cursor += char_width + spacing
    return tuple(all_strokes)


def _fits_on_backplate(
    text: str,
    height_mm: float,
    upright: bool,
    anchor_x: float,
    anchor_y: float,
    backplate_geometry: BaseGeometry,
) -> bool:
    width_mm = _text_width_mm(text, height_mm)
    w, h = (width_mm, height_mm) if upright else (height_mm, width_mm)
    footprint = Polygon(
        [
            (anchor_x, anchor_y),
            (anchor_x + w, anchor_y),
            (anchor_x + w, anchor_y - h),
            (anchor_x, anchor_y - h),
        ]
    )
    return bool(footprint.within(backplate_geometry))


def _resolve_backplate_numbering(
    text: str,
    target_height_mm: float,
    min_height_mm: float,
    anchor_x: float,
    anchor_y: float,
    backplate_geometry: BaseGeometry,
) -> tuple[float, bool] | None:
    for height in (target_height_mm, min_height_mm):
        for upright in (True, False):
            if _fits_on_backplate(
                text, height, upright, anchor_x, anchor_y, backplate_geometry
            ):
                return height, upright
    return None


def apply_numbering_to_backplate(
    slice_set: SliceSet,
    backplate: Backplate,
    tabs: tuple[Tab, ...],
    numbering_height_mm: float,
    numbering_min_height_mm: float | None = None,
    numbering_margin_mm: float | None = None,
) -> Backplate:
    """A Backplate-hez kapcsolódó szigetek azonosítóinak elhelyezése a Backplate-en.

    Lásd: NUMBERING_SPEC.md 6. szakasz, 6. lépés.

    A `slice_set`-nek már a Slice-oldali `apply_numbering()` kimenetének
    kell lennie (a `Slice.numbering_marks` adja az egyes szigetek
    azonosító-szövegét). A `tabs` a Backplate Engine
    `place_backplate_tabs()` kimenete — ebből azonosítjuk, mely szigetek
    kapcsolódnak ténylegesen a Backplate-hez, és hol.

    Args:
        slice_set: a Numbering Engine (1. kör) kimenete.
        backplate: a Backplate Engine kimenete.
        tabs: a Backplate Engine `place_backplate_tabs()` csap-pozíciói.
        numbering_height_mm: az azonosító célzott magassága.
        numbering_min_height_mm: a minimálisan elfogadható magasság. Ha
            `None`, `numbering_height_mm / 2`.
        numbering_margin_mm: az azonosító távolsága a két legközelebbi
            éltől. Ha `None`, `numbering_height_mm / 4`.

    Returns:
        A gravírozási jelekkel kiegészített Backplate objektum.

    Raises:
        InvalidNumberingError: érvénytelen paraméter. (A Backplate-en
            elférő hely hiánya csak figyelmeztetés, nem hiba —
            NUMBERING_SPEC.md 6. szakasz, 6. lépés.)
    """
    resolved_min_height_mm = (
        numbering_min_height_mm
        if numbering_min_height_mm is not None
        else numbering_height_mm / 2
    )
    resolved_margin_mm = (
        numbering_margin_mm
        if numbering_margin_mm is not None
        else numbering_height_mm / 4
    )

    if numbering_height_mm <= 0:
        raise InvalidNumberingError(
            "A numbering_height_mm értékének pozitívnak kell lennie: "
            f"{numbering_height_mm}"
        )
    if not (0 < resolved_min_height_mm <= numbering_height_mm):
        raise InvalidNumberingError(
            f"A numbering_min_height_mm-nek a (0, {numbering_height_mm}] tartományba "
            f"kell esnie: {resolved_min_height_mm}"
        )
    if resolved_margin_mm < 0:
        raise InvalidNumberingError(
            f"A numbering_margin_mm értéke nem lehet negatív: {resolved_margin_mm}"
        )

    backplate_geometry = _backplate_polygon(backplate)

    marks: list[EngravingMark] = []
    for slice_ in slice_set.slices:
        for mark in slice_.numbering_marks:
            island_tabs = [
                t
                for t in tabs
                if t.slice_index == slice_.index and t.island_index == mark.island_index
            ]
            if not island_tabs:
                continue

            third_axis_max = max(t.third_axis_end_mm for t in island_tabs)
            slice_axis_max = slice_.position_mm + slice_.thickness_mm / 2

            anchor_x = third_axis_max + resolved_margin_mm
            anchor_y = slice_axis_max - resolved_margin_mm

            result = _resolve_backplate_numbering(
                mark.text,
                numbering_height_mm,
                resolved_min_height_mm,
                anchor_x,
                anchor_y,
                backplate_geometry,
            )
            if result is None:
                logger.warning(
                    "A(z) %s. szelet %s. szigetének Backplate-oldali azonosítója "
                    "(%s) egyik tájolásban sem éri el a numbering_min_height_mm-et "
                    "— a jelölés kimarad.",
                    slice_.index,
                    mark.island_index,
                    mark.text,
                )
                continue

            height, upright = result
            strokes = _build_text_strokes_rect(
                mark.text, height, upright, anchor_x, anchor_y
            )
            marks.append(
                EngravingMark(
                    text=mark.text,
                    strokes=strokes,
                    height_mm=height,
                    island_index=mark.island_index,
                )
            )

    return replace(backplate, numbering_marks=tuple(marks))
