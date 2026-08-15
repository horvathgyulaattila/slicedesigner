"""Nesting Engine (1. kör) — anyag-validálás, Spacer-korongok, csoportosítás, toldás.

Lásd: docs/specifications/NESTING_SPEC.md (6. szakasz, 1-5. lépés).
A tényleges lap-elrendezés (6. lépés) külön menetben készül.
"""

import logging
import math
from dataclasses import dataclass, replace
from enum import Enum

from shapely import affinity
from shapely.geometry import LineString, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.geometry.polygon import orient
from shapely.ops import split, unary_union

from slicedesigner.engines.backplate_engine import Backplate
from slicedesigner.engines.exceptions import InvalidNestingError
from slicedesigner.engines.gap_engine import Spacer
from slicedesigner.engines.slice_engine import (
    Contour,
    EngravingMark,
    SliceSet,
    is_ccw,
    reconstruct_islands,
)

logger = logging.getLogger(__name__)

# --- Hét-szegmenses stroke-font (a Numbering Engine-nel megegyező, önálló másolat,
# kiegészítve a "-" karakterrel a toldási utótaghoz) ---

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
_HYPHEN_STROKE: tuple[tuple[float, float], tuple[float, float]] = (
    (0.0, 0.5),
    (0.6, 0.5),
)

_CHAR_WIDTH_RATIO = 0.6
_CHAR_SPACING_RATIO = 0.2


def _char_strokes(
    char: str, height_mm: float
) -> tuple[tuple[tuple[float, float], ...], ...]:
    if char == "-":
        (x1, y1), (x2, y2) = _HYPHEN_STROKE
        return (
            (
                (x1 * height_mm, y1 * height_mm),
                (x2 * height_mm, y2 * height_mm),
            ),
        )
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


def _glyph_point_rect(
    gx: float,
    gy: float,
    upright: bool,
    anchor_x: float,
    anchor_y: float,
    width_mm: float,
) -> tuple[float, float]:
    if upright:
        return (anchor_x - gx, anchor_y - gy)
    return (anchor_x - gy, anchor_y + gx - width_mm)


def _build_text_strokes_rect(
    text: str, height_mm: float, upright: bool, anchor_x: float, anchor_y: float
) -> tuple[tuple[tuple[float, float], ...], ...]:
    char_width = _CHAR_WIDTH_RATIO * height_mm
    spacing = _CHAR_SPACING_RATIO * height_mm
    width_mm = _text_width_mm(text, height_mm)
    all_strokes: list[tuple[tuple[float, float], ...]] = []
    cursor = 0.0
    for char in text:
        for glyph_stroke in _char_strokes(char, height_mm):
            local_stroke = tuple(
                _glyph_point_rect(
                    cursor + gx, gy, upright, anchor_x, anchor_y, width_mm
                )
                for gx, gy in glyph_stroke
            )
            all_strokes.append(local_stroke)
        cursor += char_width + spacing
    return tuple(all_strokes)


class NestingRotationMode(Enum):
    """A csomagolás során megengedett forgatási szabadság."""

    NONE = "none"
    ORTHOGONAL = "orthogonal"
    FREE = "free"


@dataclass(frozen=True)
class MaterialDefinition:
    """Egy elérhető anyagtípus/vastagság, lapmérettel és kerf-fel."""

    material_id: str
    thickness_mm: float
    sheet_width_mm: float
    sheet_height_mm: float
    kerf_mm: float


class PartKind(Enum):
    """Egy Nesting-elem eredetének kategóriája."""

    SLICE_ISLAND = "slice_island"
    BACKPLATE = "backplate"
    SPACER_DISC = "spacer_disc"


@dataclass(frozen=True)
class PartReference:
    """Egy alkatrész eredetének azonosítása a pipeline korábbi kimeneteiben."""

    kind: PartKind
    slice_index: int | None = None
    island_index: int | None = None
    spacer_index: int | None = None
    disc_index: int | None = None
    sub_part_index: int | None = None


@dataclass(frozen=True)
class NestablePart:
    """Egy elrendezendő alkatrész: geometria + azonosító + anyag-hivatkozás.

    A `contours` az alkatrész saját 2D síkjában értendő (a `Contour`
    CCW/CW konvenciója szerint).

    Az `origin_seam_lines` — ha az alkatrész toldás eredménye — az EREDETI
    (fel nem osztott) alkatrész saját, helyi koordinátarendszerében adja
    meg a vágásvonal(ak) végpontjait; ugyanazon eredeti alkatrész minden
    darabja azonos listát hordoz. Nem toldott alkatrészeknél üres.
    """

    reference: PartReference
    contours: tuple[Contour, ...]
    numbering_marks: tuple[EngravingMark, ...]
    material_id: str
    origin_seam_lines: tuple[tuple[tuple[float, float], tuple[float, float]], ...] = ()


def _contours_to_geometry(contours: tuple[Contour, ...]) -> BaseGeometry:
    """Egy lapos Contour-lista (CCW szolid + CW lyuk) Shapely geometriává építése."""
    solids = [c for c in contours if is_ccw(c.points)]
    holes = [c for c in contours if not is_ccw(c.points)]
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


def _geometry_to_contours(geometry: BaseGeometry) -> tuple[Contour, ...]:
    """Egy (esetlegesen több darabból álló) geometria Contour-listává alakítása."""
    polygons = list(geometry.geoms) if hasattr(geometry, "geoms") else [geometry]
    contours: list[Contour] = []
    for polygon in polygons:
        if polygon.area <= 0:
            continue
        oriented = orient(polygon, sign=1.0)
        contours.append(
            Contour(
                points=tuple(
                    (float(x), float(y)) for x, y in oriented.exterior.coords[:-1]
                )
            )
        )
        for interior in oriented.interiors:
            contours.append(
                Contour(
                    points=tuple((float(x), float(y)) for x, y in interior.coords[:-1])
                )
            )
    return tuple(contours)


def _fits_sheet(
    width: float,
    height: float,
    sheet_width: float,
    sheet_height: float,
    allow_swap: bool,
) -> bool:
    if width <= sheet_width and height <= sheet_height:
        return True
    if allow_swap and height <= sheet_width and width <= sheet_height:
        return True
    return False


def _cut_line(
    axis: str, position: float, min_x: float, max_x: float, min_y: float, max_y: float
) -> LineString:
    margin = 1.0
    if axis == "x":
        return LineString([(position, min_y - margin), (position, max_y + margin)])
    return LineString([(min_x - margin, position), (max_x + margin, position)])


def _find_feature_avoiding_position(
    part: NestablePart,
    axis: str,
    raw_position: float,
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
) -> float:
    """Néhány közeli jelölt pozíció kipróbálása, hogy elkerülje a lyuk-kontúrokat
    (Dowel Hole, Backplate-fészek) — best-effort. A csap-protrúziók (szolid
    terület) és a Spacer-pozíciók elkerülése nem implementált."""
    hole_polygons = [Polygon(c.points) for c in part.contours if not is_ccw(c.points)]
    if not hole_polygons:
        return raw_position

    span = (max_x - min_x) if axis == "x" else (max_y - min_y)
    offsets = [0.0, span * 0.05, -span * 0.05, span * 0.1, -span * 0.1]
    for offset in offsets:
        candidate = raw_position + offset
        line = _cut_line(axis, candidate, min_x, max_x, min_y, max_y)
        if not any(line.intersects(hole) for hole in hole_polygons):
            return candidate
    return raw_position


def _split_polygon_at_line(
    geometry: BaseGeometry, line: LineString
) -> list[BaseGeometry]:
    result = split(geometry, line)
    return [g for g in result.geoms if g.area > 0]


def _split_geometry(
    part: NestablePart,
    geometry: BaseGeometry,
    sheet_width_mm: float,
    sheet_height_mm: float,
    allow_swap: bool,
    collected_lines: list[tuple[tuple[float, float], tuple[float, float]]],
) -> list[BaseGeometry]:
    min_x, min_y, max_x, max_y = geometry.bounds
    width, height = max_x - min_x, max_y - min_y
    if _fits_sheet(width, height, sheet_width_mm, sheet_height_mm, allow_swap):
        return [geometry]

    if width / sheet_width_mm >= height / sheet_height_mm:
        axis, count = "x", math.ceil(width / sheet_width_mm)
    else:
        axis, count = "y", math.ceil(height / sheet_height_mm)

    segment = (width if axis == "x" else height) / count
    start = min_x if axis == "x" else min_y
    cut_positions = [start + segment * i for i in range(1, count)]

    pieces: list[BaseGeometry] = [geometry]
    for raw_position in cut_positions:
        position = _find_feature_avoiding_position(
            part, axis, raw_position, min_x, max_x, min_y, max_y
        )
        line = _cut_line(axis, position, min_x, max_x, min_y, max_y)
        line_coords = tuple(line.coords)
        collected_lines.append((line_coords[0], line_coords[1]))
        pieces = [g for piece in pieces for g in _split_polygon_at_line(piece, line)]

    result: list[BaseGeometry] = []
    for piece in pieces:
        result.extend(
            _split_geometry(
                part,
                piece,
                sheet_width_mm,
                sheet_height_mm,
                allow_swap,
                collected_lines,
            )
        )
    return result


def _base_identifier_text(part: NestablePart) -> str:
    if len(part.numbering_marks) == 1:
        return part.numbering_marks[0].text
    if part.reference.kind == PartKind.BACKPLATE:
        return "Backplate"
    return "Resz"


def _build_seam_mark(
    text: str,
    piece: BaseGeometry,
    target_height_mm: float,
    min_height_mm: float,
    margin_mm: float,
) -> EngravingMark:
    min_x, min_y, max_x, max_y = piece.bounds
    anchor_x = max_x - margin_mm
    anchor_y = max_y - margin_mm

    for height in (target_height_mm, min_height_mm):
        for upright in (True, False):
            width = _text_width_mm(text, height)
            w, h = (width, height) if upright else (height, width)
            footprint = Polygon(
                [
                    (anchor_x, anchor_y),
                    (anchor_x - w, anchor_y),
                    (anchor_x - w, anchor_y - h),
                    (anchor_x, anchor_y - h),
                ]
            )
            if footprint.within(piece):
                strokes = _build_text_strokes_rect(
                    text, height, upright, anchor_x, anchor_y
                )
                return EngravingMark(
                    text=text, strokes=strokes, height_mm=height, island_index=-1
                )

    raise InvalidNestingError(
        f"A(z) '{text}' toldási al-azonosító egyik tájolásban sem éri el a "
        "seam_marking_min_height_mm-et."
    )


def _split_oversized_part(
    part: NestablePart,
    sheet_width_mm: float,
    sheet_height_mm: float,
    allow_swap: bool,
    seam_height_mm: float,
    seam_min_height_mm: float,
    seam_margin_mm: float,
) -> list[NestablePart]:
    geometry = _contours_to_geometry(part.contours)
    min_x, min_y, max_x, max_y = geometry.bounds
    if _fits_sheet(
        max_x - min_x, max_y - min_y, sheet_width_mm, sheet_height_mm, allow_swap
    ):
        return [part]

    collected_lines: list[tuple[tuple[float, float], tuple[float, float]]] = []
    pieces = _split_geometry(
        part, geometry, sheet_width_mm, sheet_height_mm, allow_swap, collected_lines
    )
    base_text = _base_identifier_text(part)
    seam_lines = tuple(collected_lines)

    result: list[NestablePart] = []
    for index, piece in enumerate(pieces, start=1):
        contours = _geometry_to_contours(piece)
        sub_text = f"{base_text}-{index}"
        seam_mark = _build_seam_mark(
            sub_text, piece, seam_height_mm, seam_min_height_mm, seam_margin_mm
        )
        result.append(
            NestablePart(
                reference=replace(part.reference, sub_part_index=index),
                contours=contours,
                numbering_marks=(seam_mark,),
                material_id=part.material_id,
                origin_seam_lines=seam_lines,
            )
        )
    return result


_DISC_SEGMENT_COUNT = 32


def _circle_contour(cx: float, cy: float, radius: float) -> Contour:
    points = tuple(
        (
            cx + radius * math.cos(2 * math.pi * i / _DISC_SEGMENT_COUNT),
            cy + radius * math.sin(2 * math.pi * i / _DISC_SEGMENT_COUNT),
        )
        for i in range(_DISC_SEGMENT_COUNT)
    )
    return Contour(points=points)


def _circle_contour_cw(cx: float, cy: float, radius: float) -> Contour:
    """Kör alakú furat-kontúr, CW körüljárással (ADR-0007 lyuk-konvenció).

    Dokumentált, szándékos duplikáció a Dowel Engine `_circle_contour_cw()`-
    jéhez képest (ADR-0007 szerint minden kontúr-előállító helyen explicit
    körüljárás-kikényszerítés szükséges). A `hole_kind`/`depth_mm`
    kitöltetlenül (`None`) marad — ez a Spacer-korong furata, NEM a Dowel
    Engine által vágott Dowel Hole, amelyre e két mező dokumentáltan
    korlátozódik (l. `slice_engine.Contour` docstringje).
    """
    points = tuple(
        (
            cx + radius * math.cos(-2 * math.pi * i / _DISC_SEGMENT_COUNT),
            cy + radius * math.sin(-2 * math.pi * i / _DISC_SEGMENT_COUNT),
        )
        for i in range(_DISC_SEGMENT_COUNT)
    )
    return Contour(points=points)


def _spacer_to_discs(
    spacer: Spacer, spacer_index: int, spacer_material: MaterialDefinition
) -> list[NestablePart]:
    """Lásd: NESTING_SPEC.md 6. szakasz 2. pont.

    Ha a Spacer Dowel-re fűzött (`dowel_diameter_mm is not None`,
    GAP_SYSTEM_SPEC.md 6. szakasz 4/a. pont), minden korong a külső (CCW)
    kontúr mellett egy második, CW körüljárású furat-kontúrt is kap,
    `dowel_diameter_mm / 2` sugárral, a korong középpontjával megegyező
    középponttal — ez a rajta ténylegesen átmenő Dowel helye. Önálló
    Spacer-eknél (`dowel_diameter_mm is None`) a korong változatlanul
    egyetlen, furat nélküli CCW kontúrt kap.
    """
    disc_count = math.ceil(spacer.thickness_mm / spacer_material.thickness_mm)
    discs = []
    for disc_index in range(disc_count):
        outer_contour = _circle_contour(
            spacer.x_mm, spacer.y_mm, spacer.diameter_mm / 2
        )
        contours: tuple[Contour, ...] = (outer_contour,)
        if spacer.dowel_diameter_mm is not None:
            hole_contour = _circle_contour_cw(
                spacer.x_mm, spacer.y_mm, spacer.dowel_diameter_mm / 2
            )
            contours = (outer_contour, hole_contour)
        discs.append(
            NestablePart(
                reference=PartReference(
                    kind=PartKind.SPACER_DISC,
                    spacer_index=spacer_index,
                    disc_index=disc_index,
                ),
                contours=contours,
                numbering_marks=(),
                material_id=spacer_material.material_id,
            )
        )
    return discs


def prepare_nesting_parts(
    slice_set: SliceSet,
    material_definitions: tuple[MaterialDefinition, ...],
    slice_material_id: str,
    seam_marking_height_mm: float,
    backplate: Backplate | None = None,
    backplate_material_id: str | None = None,
    spacers: tuple[Spacer, ...] = (),
    spacer_material_id: str | None = None,
    nesting_rotation_mode: NestingRotationMode = NestingRotationMode.ORTHOGONAL,
    seam_marking_min_height_mm: float | None = None,
    seam_marking_margin_mm: float | None = None,
) -> dict[str, list[NestablePart]]:
    """Anyag-validálás, Spacer-korongok, anyagcsoportosítás, toldás-felosztás.

    Lásd: NESTING_SPEC.md 6. szakasz, 1-5. lépés.

    Args:
        slice_set: a Numbering Engine kimenete.
        material_definitions: az elérhető anyagtípusok/vastagságok.
        slice_material_id: a szeletek anyaga.
        seam_marking_height_mm: a toldási al-azonosító célzott magassága.
        backplate: a Numbering Engine kimenete (opcionális).
        backplate_material_id: a Backplate anyaga (kötelező, ha van
            Backplate).
        spacers: a Gap Engine kimenete (opcionális).
        spacer_material_id: a Spacer-ek anyaga (kötelező, ha van Spacer).
        nesting_rotation_mode: a megengedett forgatási szabadság.
        seam_marking_min_height_mm: a minimálisan elfogadható magasság.
            Ha `None`, `seam_marking_height_mm / 2`.
        seam_marking_margin_mm: az al-azonosító távolsága a varrattól.
            Ha `None`, `seam_marking_height_mm / 4`.

    Returns:
        `material_id -> NestablePart lista` — a tényleges lap-elrendezéshez
        (2. kör) készen álló, anyagonként csoportosított alkatrész-lista.

    Raises:
        InvalidNestingError: anyag-vastagság eltérés, hiányzó vagy
            ismeretlen anyag-hivatkozás, érvénytelen `kerf_mm`/paraméter,
            vagy egy toldott darab al-azonosítója sehogy sem fér el.
    """
    resolved_min_height_mm = (
        seam_marking_min_height_mm
        if seam_marking_min_height_mm is not None
        else seam_marking_height_mm / 2
    )
    resolved_margin_mm = (
        seam_marking_margin_mm
        if seam_marking_margin_mm is not None
        else seam_marking_height_mm / 4
    )

    if seam_marking_height_mm <= 0:
        raise InvalidNestingError(
            "A seam_marking_height_mm értékének pozitívnak kell lennie: "
            f"{seam_marking_height_mm}"
        )
    if not (0 < resolved_min_height_mm <= seam_marking_height_mm):
        raise InvalidNestingError(
            f"A seam_marking_min_height_mm-nek a (0, {seam_marking_height_mm}] "
            f"tartományba kell esnie: {resolved_min_height_mm}"
        )
    if resolved_margin_mm < 0:
        raise InvalidNestingError(
            f"A seam_marking_margin_mm értéke nem lehet negatív: {resolved_margin_mm}"
        )

    materials_by_id = {m.material_id: m for m in material_definitions}
    for material in material_definitions:
        if material.kerf_mm < 0:
            raise InvalidNestingError(
                f"A(z) '{material.material_id}' anyag kerf_mm értéke nem lehet "
                f"negatív: {material.kerf_mm}"
            )

    if slice_material_id not in materials_by_id:
        raise InvalidNestingError(
            f"A slice_material_id ('{slice_material_id}') nem szerepel a "
            "material_definitions listában."
        )
    slice_material = materials_by_id[slice_material_id]
    if slice_material.thickness_mm != slice_set.slices[0].thickness_mm:
        raise InvalidNestingError(
            f"A slice_material_id ('{slice_material_id}') vastagsága "
            f"({slice_material.thickness_mm} mm) nem egyezik a szeletvastagsággal "
            f"({slice_set.slices[0].thickness_mm} mm)."
        )

    if backplate is not None:
        if backplate_material_id is None:
            raise InvalidNestingError(
                "A backplate_material_id kötelező, ha van Backplate objektum."
            )
        if backplate_material_id not in materials_by_id:
            raise InvalidNestingError(
                f"A backplate_material_id ('{backplate_material_id}') nem szerepel a "
                "material_definitions listában."
            )
        backplate_material = materials_by_id[backplate_material_id]
        if backplate_material.thickness_mm != backplate.thickness_mm:
            raise InvalidNestingError(
                f"A backplate_material_id ('{backplate_material_id}') vastagsága "
                f"({backplate_material.thickness_mm} mm) nem egyezik a Backplate "
                f"vastagságával ({backplate.thickness_mm} mm)."
            )

    if spacers and spacer_material_id is None:
        raise InvalidNestingError("A spacer_material_id kötelező, ha van Spacer-lista.")
    if spacer_material_id is not None and spacer_material_id not in materials_by_id:
        raise InvalidNestingError(
            f"A spacer_material_id ('{spacer_material_id}') nem szerepel a "
            "material_definitions listában."
        )

    allow_swap = nesting_rotation_mode != NestingRotationMode.NONE

    raw_parts: list[NestablePart] = []

    for slice_ in slice_set.slices:
        islands = reconstruct_islands(slice_)
        marks_by_island = {m.island_index: m for m in slice_.numbering_marks}
        for island_index, island in enumerate(islands):
            contours = (island.solid, *island.holes)
            marks = (
                (marks_by_island[island_index],)
                if island_index in marks_by_island
                else ()
            )
            raw_parts.append(
                NestablePart(
                    reference=PartReference(
                        kind=PartKind.SLICE_ISLAND,
                        slice_index=slice_.index,
                        island_index=island_index,
                    ),
                    contours=contours,
                    numbering_marks=marks,
                    material_id=slice_material_id,
                )
            )

    if backplate is not None and backplate_material_id is not None:
        raw_parts.append(
            NestablePart(
                reference=PartReference(kind=PartKind.BACKPLATE),
                contours=backplate.contours,
                numbering_marks=backplate.numbering_marks,
                material_id=backplate_material_id,
            )
        )

    if spacer_material_id is not None:
        spacer_material = materials_by_id[spacer_material_id]
        for spacer_index, spacer in enumerate(spacers):
            raw_parts.extend(_spacer_to_discs(spacer, spacer_index, spacer_material))

    grouped: dict[str, list[NestablePart]] = {}
    for part in raw_parts:
        material = materials_by_id[part.material_id]
        split_parts = _split_oversized_part(
            part,
            material.sheet_width_mm,
            material.sheet_height_mm,
            allow_swap,
            seam_marking_height_mm,
            resolved_min_height_mm,
            resolved_margin_mm,
        )
        grouped.setdefault(part.material_id, []).extend(split_parts)

    return grouped


@dataclass(frozen=True)
class PlacedPart:
    """Egy anyaglapra ténylegesen elrendezett alkatrész.

    A `contours`/`numbering_marks` már a végleges, elforgatott és a lapon
    elhelyezett koordinátákat tartalmazzák — a `position`/`rotation_deg`
    dokumentációs célra, kiegészítésként szerepel (NESTING_SPEC.md 4.
    szakasz).
    """

    reference: PartReference
    sheet_number: int
    position: tuple[float, float]
    rotation_deg: float
    contours: tuple[Contour, ...]
    numbering_marks: tuple[EngravingMark, ...]


@dataclass(frozen=True)
class SeamRecord:
    """Egy toldott alkatrész varratainak és al-azonosítóinak összesítése.

    A `seam_lines` az EREDETI (fel nem osztott) alkatrész saját, helyi
    koordinátarendszerében értendő — dokumentációs/nyomonkövetési célra,
    nem a végleges lap-koordinátákban.
    """

    reference: PartReference
    seam_lines: tuple[tuple[tuple[float, float], tuple[float, float]], ...]
    sub_identifiers: tuple[EngravingMark, ...]


@dataclass(frozen=True)
class Nest:
    """A Nesting Engine kimenete: egy anyaghoz tartozó, laponkénti elrendezés.

    Lásd: NESTING_SPEC.md 4. szakasz.
    """

    material_id: str
    sheet_count: int
    placed_parts: tuple[PlacedPart, ...]
    seams: tuple[SeamRecord, ...]


def _transform_point(
    point: tuple[float, float],
    origin: tuple[float, float],
    angle_deg: float,
    offset: tuple[float, float],
) -> tuple[float, float]:
    angle_rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    ox, oy = origin
    x, y = point[0] - ox, point[1] - oy
    rx = x * cos_a - y * sin_a
    ry = x * sin_a + y * cos_a
    return (rx + ox + offset[0], ry + oy + offset[1])


def _transform_contour(
    contour: Contour,
    origin: tuple[float, float],
    angle_deg: float,
    offset: tuple[float, float],
) -> Contour:
    return replace(
        contour,
        points=tuple(
            _transform_point(p, origin, angle_deg, offset) for p in contour.points
        ),
    )


def _transform_mark(
    mark: EngravingMark,
    origin: tuple[float, float],
    angle_deg: float,
    offset: tuple[float, float],
) -> EngravingMark:
    new_strokes = tuple(
        tuple(_transform_point(p, origin, angle_deg, offset) for p in stroke)
        for stroke in mark.strokes
    )
    return replace(mark, strokes=new_strokes)


# Bottom-Left Fill (BLF) csomagolás — ADR-0013. A lap szélétől nem követel
# kerf-nyi margót (a kerf kizárólag alkatrészek között érvényesül), de a
# lánc-szerűen felhalmozódó lebegőpontos kerekítési hibák miatt egy apró
# tűréssel dolgozik a lap-határ és a kerf ellenőrzésekor is.
_BOUNDS_EPSILON_MM = 1e-9


def _rotation_angles(rotation_mode: NestingRotationMode) -> tuple[float, ...]:
    """ADR-0013 szerinti szögkészlet: NONE={0}, ORTHOGONAL={0,90},
    FREE={0,45,90,135,180,225,270,315} — ebben a sorrendben (a sorrend
    maga determinálja a keresés bejárási sorrendjét)."""
    if rotation_mode == NestingRotationMode.NONE:
        return (0.0,)
    if rotation_mode == NestingRotationMode.ORTHOGONAL:
        return (0.0, 90.0)
    return (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)


def _rotated_bounds(
    geometry: BaseGeometry, origin: tuple[float, float], angle_deg: float
) -> tuple[float, float]:
    """(szélesség, magasság) — a geometria `origin` körüli `angle_deg`-os
    elforgatása utáni befoglaló téglalap mérete."""
    rotated = affinity.rotate(geometry, angle_deg, origin=origin, use_radians=False)
    min_x, min_y, max_x, max_y = rotated.bounds
    return (max_x - min_x, max_y - min_y)


def _candidate_positions(
    placed: list[BaseGeometry],
    sheet_width: float,
    sheet_height: float,
    kerf_mm: float,
) -> list[tuple[float, float]]:
    """A lapon már elhelyezett geometriák befoglaló téglalap-sarkaiból képzett
    jelölt-rács, kiegészítve a lap (0, 0) sarkával — determinisztikusan
    dedupolva és (y, x) szerint növekvő sorrendbe rendezve (bottom-left
    bejárás). Ha `placed` üres, kizárólag `[(0.0, 0.0)]`-t ad vissza.

    A jobbra/fölé/átlósan eső ("kifelé néző") sarkak `kerf_mm`-mel eltolva
    szerepelnek a rácsban — enélkül egy új alkatrész bal-alsó sarka pontosan
    az őt generáló alkatrész szélén ülne (0 távolság), ami `kerf_mm > 0`
    mellett `_fits_at()`-ban SOHA nem teljesülne, azaz a szomszédos
    elhelyezés elvi lehetetlenné válna. A bal-alsó sarok (a generáló
    alkatrész saját origója) eltolás nélkül is szerepel — ütközés miatt úgyis
    érvénytelen lesz, de ez ártalmatlan, a teljesség kedvéért benne marad.

    A lapon kívül eső sarokpontok (egy korábban elhelyezett alkatrész a lap
    szélén túlnyúló sarka nem lehet, de kerekítési hiba miatt előfordulhat)
    kiszűrésre kerülnek."""
    if not placed:
        return [(0.0, 0.0)]

    positions: set[tuple[float, float]] = {(0.0, 0.0)}
    for geometry in placed:
        min_x, min_y, max_x, max_y = geometry.bounds
        positions.add((min_x, min_y))
        positions.add((max_x + kerf_mm, min_y))
        positions.add((min_x, max_y + kerf_mm))
        positions.add((max_x + kerf_mm, max_y + kerf_mm))

    in_bounds = [
        (x, y)
        for x, y in positions
        if -_BOUNDS_EPSILON_MM <= x <= sheet_width + _BOUNDS_EPSILON_MM
        and -_BOUNDS_EPSILON_MM <= y <= sheet_height + _BOUNDS_EPSILON_MM
    ]
    return sorted(in_bounds, key=lambda p: (p[1], p[0]))


def _fits_at(
    rotated_translated_geometry: BaseGeometry,
    sheet_width: float,
    sheet_height: float,
    placed: list[BaseGeometry],
    kerf_mm: float,
) -> bool:
    """Igaz, ha a geometria (a) teljes egészében a [0, sheet_width] x
    [0, sheet_height] tartományon belül esik, ÉS (b) minden `placed`-beli
    geometriától `distance()` szerint legalább `kerf_mm` távolságra van."""
    min_x, min_y, max_x, max_y = rotated_translated_geometry.bounds
    if (
        min_x < -_BOUNDS_EPSILON_MM
        or min_y < -_BOUNDS_EPSILON_MM
        or max_x > sheet_width + _BOUNDS_EPSILON_MM
        or max_y > sheet_height + _BOUNDS_EPSILON_MM
    ):
        return False
    return all(
        rotated_translated_geometry.distance(other) >= kerf_mm - _BOUNDS_EPSILON_MM
        for other in placed
    )


def _place_part(
    part: NestablePart,
    geometry: BaseGeometry,
    rotation_deg: float,
    target_x: float,
    target_y: float,
    sheet_number: int,
) -> PlacedPart:
    centroid = geometry.centroid
    origin = (centroid.x, centroid.y)

    rotated_points = [
        _transform_point(p, origin, rotation_deg, (0.0, 0.0))
        for contour in part.contours
        for p in contour.points
    ]
    min_x = min(p[0] for p in rotated_points)
    min_y = min(p[1] for p in rotated_points)
    offset = (target_x - min_x, target_y - min_y)

    new_contours = tuple(
        _transform_contour(c, origin, rotation_deg, offset) for c in part.contours
    )
    new_marks = tuple(
        _transform_mark(m, origin, rotation_deg, offset) for m in part.numbering_marks
    )

    return PlacedPart(
        reference=part.reference,
        sheet_number=sheet_number,
        position=(target_x, target_y),
        rotation_deg=rotation_deg,
        contours=new_contours,
        numbering_marks=new_marks,
    )


def _find_placement(
    geometry: BaseGeometry,
    origin: tuple[float, float],
    angles: tuple[float, ...],
    sheets: list[list[BaseGeometry]],
    sheet_w: float,
    sheet_h: float,
    kerf: float,
) -> tuple[int, BaseGeometry, float, float, float] | None:
    """Az első illeszkedő (lap-index, elforgatott+eltolt geometria, szög,
    x, y) ötös megkeresése a megadott lap-listán — laponként, azon belül
    szögönként (mindkettő a bejárási sorrendjükben), azon belül bottom-left
    sorrendben bejárt jelölt-pozíciónként. `None`, ha egyetlen lapon,
    szögben, pozícióban sem illeszkedik."""
    for sheet_index, sheet_geoms in enumerate(sheets):
        for angle_deg in angles:
            width, height = _rotated_bounds(geometry, origin, angle_deg)
            if width > sheet_w or height > sheet_h:
                continue
            for target_x, target_y in _candidate_positions(
                sheet_geoms, sheet_w, sheet_h, kerf
            ):
                if target_x + width > sheet_w or target_y + height > sheet_h:
                    continue
                rotated = affinity.rotate(geometry, angle_deg, origin=origin)
                min_x, min_y = rotated.bounds[0], rotated.bounds[1]
                translated = affinity.translate(
                    rotated, target_x - min_x, target_y - min_y
                )
                if _fits_at(translated, sheet_w, sheet_h, sheet_geoms, kerf):
                    return sheet_index, translated, angle_deg, target_x, target_y
    return None


def _pack_material_group(
    parts: list[NestablePart],
    material: MaterialDefinition,
    rotation_mode: NestingRotationMode,
) -> tuple[list[PlacedPart], int]:
    """Egy anyagcsoport alkatrészeinek Bottom-Left Fill (BLF) elrendezése
    lapokra, valódi Shapely-kontúr-ütközéssel (ADR-0013)."""
    angles = _rotation_angles(rotation_mode)
    sheet_w, sheet_h = material.sheet_width_mm, material.sheet_height_mm
    kerf = material.kerf_mm

    entries = [(part, _contours_to_geometry(part.contours)) for part in parts]
    entries.sort(key=lambda entry: entry[1].area, reverse=True)

    sheets: list[list[BaseGeometry]] = [[]]
    placed_parts: list[PlacedPart] = []

    for part, geometry in entries:
        centroid = geometry.centroid
        origin = (centroid.x, centroid.y)

        placement = _find_placement(
            geometry, origin, angles, sheets, sheet_w, sheet_h, kerf
        )
        if placement is None:
            # Egyetlen meglévő lapon sem fér el — nyiss egy újat, és próbáld
            # KIZÁRÓLAG azon. Ha az is sikertelen, az alkatrész (a Phase 6
            # felosztás után is) elférhetetlen ebben az anyagban.
            sheets.append([])
            placement = _find_placement(
                geometry, origin, angles, sheets[-1:], sheet_w, sheet_h, kerf
            )
            if placement is None:
                min_x, min_y, max_x, max_y = geometry.bounds
                raise InvalidNestingError(
                    f"Egy alkatrész ({max_x - min_x:.2f}x{max_y - min_y:.2f} mm) a "
                    f"felosztás után sem fér el a(z) '{material.material_id}' anyag "
                    f"lapméretén ({sheet_w}x{sheet_h} mm) belül."
                )
            sheet_index = len(sheets) - 1
            _, translated, angle_deg, target_x, target_y = placement
        else:
            sheet_index, translated, angle_deg, target_x, target_y = placement

        placed_parts.append(
            _place_part(part, geometry, angle_deg, target_x, target_y, sheet_index + 1)
        )
        sheets[sheet_index].append(translated)

    return placed_parts, len(sheets)


def _original_reference_key(
    reference: PartReference,
) -> tuple[PartKind, int | None, int | None, int | None, int | None]:
    return (
        reference.kind,
        reference.slice_index,
        reference.island_index,
        reference.spacer_index,
        reference.disc_index,
    )


def _collect_seams(parts: list[NestablePart]) -> tuple[SeamRecord, ...]:
    groups: dict[
        tuple[PartKind, int | None, int | None, int | None, int | None],
        list[NestablePart],
    ] = {}
    for part in parts:
        if part.reference.sub_part_index is None:
            continue
        key = _original_reference_key(part.reference)
        groups.setdefault(key, []).append(part)

    seams = []
    for group_parts in groups.values():
        seam_lines = group_parts[0].origin_seam_lines
        sub_identifiers = tuple(m for p in group_parts for m in p.numbering_marks)
        original_reference = replace(group_parts[0].reference, sub_part_index=None)
        seams.append(
            SeamRecord(
                reference=original_reference,
                seam_lines=seam_lines,
                sub_identifiers=sub_identifiers,
            )
        )
    return tuple(seams)


def create_nests(
    parts_by_material: dict[str, list[NestablePart]],
    material_definitions: tuple[MaterialDefinition, ...],
    nesting_rotation_mode: NestingRotationMode = NestingRotationMode.ORTHOGONAL,
) -> tuple[Nest, ...]:
    """A `prepare_nesting_parts()` kimenetének tényleges lapokra rendezése.

    Lásd: NESTING_SPEC.md 6. szakasz, 6-7. lépés.

    Args:
        parts_by_material: a `prepare_nesting_parts()` kimenete.
        material_definitions: az elérhető anyagtípusok/vastagságok.
        nesting_rotation_mode: a megengedett forgatási szabadság.

    Returns:
        Nest-ek listája, anyagonként egy — a lapok száma nyitott végű, a
        tényleges kihasználtság alapján.

    Raises:
        InvalidNestingError: ha egy alkatrész (a felosztás után is) nem
            fér el a hozzá rendelt anyag lapméretén belül — ez rendes
            körülmények között nem fordulhat elő (az 1. kör már
            biztosítja), csak a `FREE` forgatási mód eltérő, pontosabb
            befoglaló-téglalap-számítása miatt, ritka határesetben.
    """
    materials_by_id = {m.material_id: m for m in material_definitions}

    nests = []
    for material_id, parts in parts_by_material.items():
        material = materials_by_id[material_id]
        placed_parts, sheet_count = _pack_material_group(
            parts, material, nesting_rotation_mode
        )
        seams = _collect_seams(parts)
        nests.append(
            Nest(
                material_id=material_id,
                sheet_count=sheet_count,
                placed_parts=tuple(placed_parts),
                seams=seams,
            )
        )
    return tuple(nests)
