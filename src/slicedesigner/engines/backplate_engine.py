"""Backplate Engine (1. kör) — érintkező szakasz azonosítás és csap-elhelyezés.

Lásd: docs/specifications/BACKPLATE_SPEC.md (6. szakasz, 1-8. lépés).
A margó-eltolás és a fészek-kivágás (11-12. lépés) külön menetben készül.
"""

import logging
from dataclasses import dataclass, replace
from enum import Enum

import trimesh
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

from slicedesigner.engines.exceptions import InvalidBackplateError
from slicedesigner.engines.slice_engine import (
    _SLICE_AXIS_CONTOUR_ORDER,
    Contour,
    EngravingMark,
    Island,
    Slice,
    SliceAxis,
    SliceSet,
    _compute_uniform_scale_factor,
    reconstruct_islands,
)

logger = logging.getLogger(__name__)


class BackplateNormalAxis(Enum):
    """A Backplate felé néző irány, a hozzá tartozó világtengellyel és előjellel."""

    PLUS_X = "+X"
    MINUS_X = "-X"
    PLUS_Y = "+Y"
    MINUS_Y = "-Y"
    PLUS_Z = "+Z"
    MINUS_Z = "-Z"


_NORMAL_AXIS_WORLD: dict[BackplateNormalAxis, tuple[str, float]] = {
    BackplateNormalAxis.PLUS_X: ("X", 1.0),
    BackplateNormalAxis.MINUS_X: ("X", -1.0),
    BackplateNormalAxis.PLUS_Y: ("Y", 1.0),
    BackplateNormalAxis.MINUS_Y: ("Y", -1.0),
    BackplateNormalAxis.PLUS_Z: ("Z", 1.0),
    BackplateNormalAxis.MINUS_Z: ("Z", -1.0),
}

# Világtengely-név → numpy-tengelyindex — a `_build_backplate_shape_from_mesh()`
# nyers Mesh-vertexeinek (world X/Y/Z oszlopainak) indexeléséhez. Ugyanaz a
# leképezés, mint amit a `render_geometry.py`/`numbering_engine.py` innen
# duplikál (l. `render_geometry.py` modul-docstringje).
_WORLD_AXIS_INDEX: dict[str, int] = {"X": 0, "Y": 1, "Z": 2}

_AXIS_CYCLE: tuple[str, str, str] = ("X", "Y", "Z")

# A csap-téglalap belső élének a sziget saját `local_extreme_mm` szélső
# koordinátáján túli, befelé irányuló ráhagyása (`_build_tab_rectangle()`).
#
# A `local_extreme_mm` a sziget kontúrjának globális szélsőértéke — de az
# érintkező szakaszt alkotó, "egy síkban lévőnek" tekintett pontok
# (`_find_contact_segments()` `in_plane` szűrője) csak `backplate_plane_
# tolerance_mm`-en BELÜL kell hogy essenek ehhez a szélsőértékhez, nem
# pontosan rajta. Egy nem tökéletesen egyenes (pl. lépcsős) érintkezési
# határnál ez azt jelenti, hogy a sziget tényleges pereme a szakasz egyes
# pontjai között akár `backplate_plane_tolerance_mm`-nyit is befelé
# hajolhat a csap-téglalap (korábban a `local_extreme_mm`-nél konstans)
# belső éléhez képest — a kettő között egy vékony, egyik alakzat által sem
# fedett sáv marad, ezért a `unary_union([island.polygon, rectangle])` a
# szigetet és a csapot csak érintkező, de nem ténylegesen egyesített
# `MultiPolygon`-ként adja vissza (l. `_apply_tab_geometry()` és a
# `test_place_backplate_tabs_stepped_contact_edge_merges_into_single_island()`
# regressziós teszt).
#
# A javítás: a téglalap belső élét nem `local_extreme_mm`-nél, hanem attól
# `backplate_plane_tolerance_mm + _TAB_OVERLAP_SAFETY_EPSILON_MM`-mel
# befelé húzzuk meg. Mivel az érintkezési határ ezen a tűréshatáron belüli
# eltérését a klaszterezési/érintkezés-azonosítási logika (6. szakasz
# 2-3. pont) már eleve "ugyanabban a síkban lévőnek" fogadja el, ez a
# ráhagyás nem vezet be új pontatlanságot — kizárólag garantálja, hogy a
# csap-téglalap ténylegesen ÁTFEDI (nem csak érinti) a sziget tényleges
# perem-geometriáját, a sziget-oldalon már eleve tolerált sávon belül. A
# csap látható (a szigeten túl kinyúló) mérete/mélysége (BACKPLATE_SPEC.md
# 6. szakasz 9. pont) nem változik, mert a ráhagyás kizárólag a sziget
# saját anyagával fedésbe kerülő, a végeredményben láthatatlan tartományt
# bővíti. A `_TAB_OVERLAP_SAFETY_EPSILON_MM` (a Dowel Engine
# `_EROSION_TANGENCY_EPSILON_MM`-mintájára, CODING_STANDARDS.md 7. szakasz)
# minden gyártási/geometriai pontosság alatt van, kizárólag a `<=`
# tűréshatár-egyenlőség (határeseti tangencia) ellen nyújt biztonsági
# ráhagyást.
_TAB_OVERLAP_SAFETY_EPSILON_MM = 1e-6


def _cyclic_parity(first: str, second: str) -> float:
    """+1.0, ha (first, second) az X→Y→Z→X kanonikus ciklikus sorrendet
    követi, -1.0 ellenkező esetben (first != second, mindkettő X/Y/Z
    valamelyike).
    """
    index = _AXIS_CYCLE.index(first)
    return 1.0 if _AXIS_CYCLE[(index + 1) % 3] == second else -1.0


def _backplate_third_axis_sign(
    slice_axis: SliceAxis, backplate_normal_axis: BackplateNormalAxis
) -> float:
    """Az előjel, amellyel a Backplate saját (harmadik tengely, slice_axis)
    síkjának harmadik-tengely koordinátáját (nyers world-érték) szorozni
    kell, hogy a beágyazás — a `backplate_normal_axis` felől, a
    normálvektorral szemben állva nézve — mindig tükrözés nélküli,
    helyesen álló képet adjon.

    Levezetés (ADR-0010, javítva a projektgazda 2026-08-08-i élő
    tesztelése alapján): a nézőpont-kamera "jobbra" iránya
    `slice_axis (mint "fel") × backplate_normal_axis (előjeles n̂)`
    keresztszorzat; ha ez egybeesik a harmadik tengely pozitív
    irányával, nincs szükség tükrözésre (+1), ellenkező esetben igen
    (-1). Az eredeti levezetés (ADR-0010) a nézőpont oldalát fordítva
    feltételezte — ezt egy konkrét, élőben tesztelt kombináció
    (`slice_axis=X`, `backplate_normal_axis=MINUS_Z`) cáfolta. Mivel a
    nézőpont oldalának megfordítása minden `(slice_axis,
    backplate_normal_axis)` kombinációra egységesen ható művelet, a
    javítás a teljes visszatérési érték előjelének megfordítása —
    nem kombinációnkénti hangolás. Ugyanezt az előjelet kell alkalmazni
    mindenhol, ahol a Backplate saját síkjának harmadik koordinátája
    később felhasználásra kerül: a sziluett (`_build_backplate_
    shape_from_mesh`), a hozzá tartozó fészek-kivágás
    (`apply_backplate`), és a Numbering Engine
    `apply_numbering_to_backplate()`-je.
    """
    normal_world_axis, sign = _NORMAL_AXIS_WORLD[backplate_normal_axis]
    return -sign * _cyclic_parity(slice_axis.value, normal_world_axis)


def _resolve_backplate_axes(
    slice_axis: SliceAxis, backplate_normal_axis: BackplateNormalAxis
) -> tuple[int, float, int]:
    """(normal tengely kontúr-indexe, előjele, harmadik tengely kontúr-indexe)."""
    world_axis, sign = _NORMAL_AXIS_WORLD[backplate_normal_axis]
    contour_axes = _SLICE_AXIS_CONTOUR_ORDER[slice_axis]
    if world_axis == slice_axis.value:
        raise InvalidBackplateError(
            f"A backplate_normal_axis ({backplate_normal_axis.value}) nem eshet "
            f"egybe a slice_axis-szal ({slice_axis.value})."
        )
    normal_index = contour_axes.index(world_axis)
    third_index = 1 - normal_index
    return normal_index, sign, third_index


@dataclass(frozen=True)
class NonBackplateIsland:
    """Egy szigetet azonosít, amelyet a Backplate Engine kizár a feldolgozásból."""

    slice_index: int
    island_index: int


@dataclass(frozen=True)
class ManualTabPosition:
    """Kézzel megadott csap-pozíció egy érintkező szakaszon belül.

    A `position_mm` a szakasz saját, harmadik tengely menti margóval
    csökkentett tartományának kezdetétől (a `tab_edge_margin_mm` utáni
    ponttól) mért távolság.
    """

    position_mm: float
    length_mm: float | None = None


@dataclass(frozen=True)
class SliceTabOverride:
    """Szigetenkénti csap-paraméter- vagy pozíció-felülbírálás.

    Ha `island_index` `None`, és az adott szeletnek egynél több szigete
    van, a felülbírálás a szelet MINDEN szigetére alkalmazódik.
    """

    slice_index: int
    island_index: int | None = None
    tab_length_mm: float | None = None
    tab_spacing_mm: float | None = None
    tab_edge_margin_mm: float | None = None
    manual_tab_positions: tuple[ManualTabPosition, ...] = ()


@dataclass(frozen=True)
class Tab:
    """Egy ténylegesen elhelyezett csap.

    A `third_axis_start_mm`/`third_axis_end_mm` a harmadik tengely (sem
    nem `slice_axis`, sem nem `backplate_normal_axis`) menti kiterjedés —
    ezt használja majd a 2. kör (sziluett + fészek-kivágás).
    """

    slice_index: int
    island_index: int
    third_axis_start_mm: float
    third_axis_end_mm: float


@dataclass(frozen=True)
class _TabParams:
    tab_length_mm: float
    tab_spacing_mm: float
    tab_edge_margin_mm: float
    manual_tab_positions: tuple[ManualTabPosition, ...]


def _resolve_tab_params(
    slice_index: int,
    island_index: int,
    base: _TabParams,
    overrides: tuple[SliceTabOverride, ...],
) -> _TabParams:
    for override in overrides:
        if override.slice_index != slice_index:
            continue
        if override.island_index is not None and override.island_index != island_index:
            continue
        return _TabParams(
            tab_length_mm=(
                override.tab_length_mm
                if override.tab_length_mm is not None
                else base.tab_length_mm
            ),
            tab_spacing_mm=(
                override.tab_spacing_mm
                if override.tab_spacing_mm is not None
                else base.tab_spacing_mm
            ),
            tab_edge_margin_mm=(
                override.tab_edge_margin_mm
                if override.tab_edge_margin_mm is not None
                else base.tab_edge_margin_mm
            ),
            manual_tab_positions=override.manual_tab_positions,
        )
    return base


@dataclass(frozen=True)
class _ContactSegment:
    """Egy sziget kontúrján azonosított, a Backplate felé néző szakasz (belső típus)."""

    third_axis_min_mm: float
    third_axis_max_mm: float
    local_extreme_mm: float


def _build_segment(
    indices: list[int],
    solid_points: tuple[tuple[float, float], ...],
    third_index: int,
    local_extreme_mm: float,
) -> _ContactSegment:
    third_coords = [solid_points[i][third_index] for i in indices]
    return _ContactSegment(
        third_axis_min_mm=min(third_coords),
        third_axis_max_mm=max(third_coords),
        local_extreme_mm=local_extreme_mm,
    )


def _find_contact_segments(
    solid_points: tuple[tuple[float, float], ...],
    normal_index: int,
    sign: float,
    third_index: int,
    plane_tolerance_mm: float,
) -> list[_ContactSegment]:
    """A sziget szolid kontúrján a Backplate felé néző szakasz(ok) azonosítása."""
    oriented = [p[normal_index] * sign for p in solid_points]
    local_extreme = max(oriented)
    in_plane = [local_extreme - o <= plane_tolerance_mm for o in oriented]

    n = len(solid_points)
    if all(in_plane):
        third_coords = [p[third_index] for p in solid_points]
        return [
            _ContactSegment(
                third_axis_min_mm=min(third_coords),
                third_axis_max_mm=max(third_coords),
                local_extreme_mm=local_extreme,
            )
        ]

    start = next(i for i in range(n) if not in_plane[i])
    order = [(start + i) % n for i in range(n)]

    segments: list[_ContactSegment] = []
    current: list[int] = []
    for idx in order:
        if in_plane[idx]:
            current.append(idx)
        elif current:
            segments.append(
                _build_segment(current, solid_points, third_index, local_extreme)
            )
            current = []
    if current:
        segments.append(
            _build_segment(current, solid_points, third_index, local_extreme)
        )

    return segments


def _chain_cluster_by_extreme(
    entries: list[tuple[tuple[int, int], int, _ContactSegment]],
    tolerance_mm: float,
) -> list[list[tuple[tuple[int, int], int, _ContactSegment]]]:
    """A `(sziget-kulcs, szakasz-index, szakasz)` hármasok lánc-alapú
    csoportosítása a szakaszok `local_extreme_mm` értéke szerint —
    BACKPLATE_SPEC.md 6. szakasz 3. pont.

    A növekvő sorrendbe rendezett értékek egymást követő elemei egy
    csoportba kerülnek, ha köztük legfeljebb `tolerance_mm` az eltérés.
    A `szakasz-index` az adott sziget saját szakasz-listáján belüli
    pozíció — egy szigetnek elvben több érintkező szakasza is lehet
    (alávágott geometria), ezért a csoportosítás szakasz-, nem
    sziget-szinten történik.
    """
    ordered = sorted(entries, key=lambda e: e[2].local_extreme_mm)
    clusters: list[list[tuple[tuple[int, int], int, _ContactSegment]]] = [[ordered[0]]]
    for previous, item in zip(ordered, ordered[1:]):
        if item[2].local_extreme_mm - previous[2].local_extreme_mm <= tolerance_mm:
            clusters[-1].append(item)
        else:
            clusters.append([item])
    return clusters


def _merge_overlapping_spans(
    spans: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    if not spans:
        return []
    ordered = sorted(spans)
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _resolve_tab_spans(
    params: _TabParams,
    segment_start: float,
    usable_length: float,
    segment: _ContactSegment,
) -> list[tuple[float, float]]:
    """Egy szakaszra eső csapok (kezdő, záró) harmadik tengely menti párjai,
    összeolvasztva."""
    relevant_manual = [
        m for m in params.manual_tab_positions if 0 <= m.position_mm <= usable_length
    ]

    if relevant_manual:
        spans = []
        for manual in relevant_manual:
            length = (
                manual.length_mm
                if manual.length_mm is not None
                else params.tab_length_mm
            )
            center = segment_start + manual.position_mm
            start, end = center - length / 2, center + length / 2
            if start < segment.third_axis_min_mm or end > segment.third_axis_max_mm:
                raise InvalidBackplateError(
                    f"Egy kézzel megadott csap-pozíció ({manual.position_mm} mm) nem "
                    "fér el a megadott érintkező szakaszon."
                )
            spans.append((start, end))
    else:
        count = max(1, round(usable_length / params.tab_spacing_mm))
        cell_width = usable_length / count
        spans = [
            (
                segment_start + cell_width * (i + 0.5) - params.tab_length_mm / 2,
                segment_start + cell_width * (i + 0.5) + params.tab_length_mm / 2,
            )
            for i in range(count)
        ]

    return _merge_overlapping_spans(spans)


def _build_tab_rectangle(
    local_extreme_mm: float,
    common_plane_mm: float,
    backplate_thickness_mm: float,
    third_start: float,
    third_end: float,
    normal_index: int,
    sign: float,
    third_index: int,
    plane_tolerance_mm: float,
) -> Polygon:
    """Egy csap-protrúzió téglalapjának felépítése kontúr-lokális koordinátákban.

    A belső él a sziget saját szélső koordinátájától
    `plane_tolerance_mm + _TAB_OVERLAP_SAFETY_EPSILON_MM`-mel befelé
    kezdődik — nem pontosan a szélső koordinátánál —, hogy a protrúzió a
    sziget geometriájával nem tökéletesen egyenes (pl. lépcsős) érintkezési
    határ esetén is garantáltan ÁTFEDJEN, ne csak érintkezzen (l.
    `_TAB_OVERLAP_SAFETY_EPSILON_MM` docstringje). A külső éle a validált
    közös Backplate-síktól számított `backplate_thickness_mm` — ez, és a
    csap látható mélysége/mérete, a ráhagyástól függetlenül változatlan.
    """
    inner_overlap_mm = plane_tolerance_mm + _TAB_OVERLAP_SAFETY_EPSILON_MM
    inner_normal = (local_extreme_mm - inner_overlap_mm) * sign
    outer_normal = (common_plane_mm + backplate_thickness_mm) * sign

    def _point(normal_value: float, third_value: float) -> tuple[float, float]:
        coords: list[float] = [0.0, 0.0]
        coords[normal_index] = normal_value
        coords[third_index] = third_value
        return (coords[0], coords[1])

    return Polygon(
        [
            _point(inner_normal, third_start),
            _point(inner_normal, third_end),
            _point(outer_normal, third_end),
            _point(outer_normal, third_start),
        ]
    )


def _polygon_to_contours(geometry: BaseGeometry) -> tuple[Contour, ...]:
    """Egy (union/difference utáni) Polygon vagy MultiPolygon Contour-listává alakítása.

    Több, egymással nem összefüggő darabra eső geometria (pl. ha a
    fészek-kivágások ténylegesen kettévágják a hátlapot) esetén minden
    darab saját külső (CCW) kontúrja és saját lyukai (CW) egyaránt a
    visszaadott, lapos listába kerülnek — ugyanazzal a konvencióval, mint
    egy Slice több szigete.
    """
    polygons = list(geometry.geoms) if hasattr(geometry, "geoms") else [geometry]
    contours: list[Contour] = []
    for polygon in polygons:
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


def _apply_tab_geometry(
    slice_set: SliceSet,
    islands_by_key: dict[tuple[int, int], Island],
    tab_rectangles_by_key: dict[tuple[int, int], list[Polygon]],
) -> SliceSet:
    """A csap-protrúziók hozzáadása az érintett szigetek geometriájához."""
    replacements_by_slice: dict[int, dict[int, tuple[Contour, ...]]] = {}

    for key, rectangles in tab_rectangles_by_key.items():
        slice_index, island_index = key
        island = islands_by_key[key]
        merged = unary_union([island.polygon, *rectangles])
        island_contours = _polygon_to_contours(merged)
        replacements_by_slice.setdefault(slice_index, {})[island_index] = (
            island_contours
        )

    new_slices: list[Slice] = []
    for slice_ in slice_set.slices:
        island_replacements = replacements_by_slice.get(slice_.index)
        if island_replacements is None:
            new_slices.append(slice_)
            continue

        islands = reconstruct_islands(slice_)
        new_contours: list[Contour] = []
        for island_index, island in enumerate(islands):
            if island_index in island_replacements:
                new_contours.extend(island_replacements[island_index])
            else:
                new_contours.append(island.solid)
                new_contours.extend(island.holes)
        new_slices.append(replace(slice_, contours=tuple(new_contours)))

    return replace(slice_set, slices=tuple(new_slices))


def _build_backplate_shape_from_mesh(
    slice_set: SliceSet,
    common_plane_world_mm: float,
    backplate_normal_axis: BackplateNormalAxis,
    backplate_plane_tolerance_mm: float,
) -> BaseGeometry:
    """A Backplate alakjának felépítése a modell tényleges geometriájából
    (BACKPLATE_SPEC.md 6. szakasz 10. pont): a Slice Engine-nel megegyező
    módon skálázott Mesh és a közös sík körüli, `backplate_plane_tolerance_mm`
    vastagságú "szeletlemez" térbeli (Boole-) metszete, a (harmadik
    tengely, szelet-tengely) síkra vetítve.

    A tűrés-sáv (nem egy nulla-vastagságú síkmetszet) szükséges, mert a
    modell tényleges felülete a közös sík magasságában nem feltétlenül
    tökéletesen sík — egy egzakt metszet ezt a gyakorlatilag hasznos
    érintkezési területet elvágólag figyelmen kívül hagyná.
    """
    mesh = slice_set.source_mesh
    slice_axis = slice_set.slice_axis
    slice_world_index = _WORLD_AXIS_INDEX[slice_axis.value]
    axis_size = (
        mesh.bounding_box.max[slice_world_index]
        - mesh.bounding_box.min[slice_world_index]
    )
    slice_thickness_mm = slice_set.slices[0].thickness_mm

    scale_factor = _compute_uniform_scale_factor(
        axis_size, slice_set.slice_count, slice_thickness_mm, slice_set.gap_mm
    )

    trimesh_mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.triangles)
    scale_matrix = [
        [scale_factor, 0.0, 0.0, 0.0],
        [0.0, scale_factor, 0.0, 0.0],
        [0.0, 0.0, scale_factor, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
    trimesh_mesh.apply_transform(scale_matrix)
    axis_min = float(trimesh_mesh.bounds[0][slice_world_index])

    normal_world_axis, _sign = _NORMAL_AXIS_WORLD[backplate_normal_axis]
    normal_world_index = _WORLD_AXIS_INDEX[normal_world_axis]
    third_world_axis = next(
        iter({"X", "Y", "Z"} - {normal_world_axis, slice_axis.value})
    )
    third_world_index = _WORLD_AXIS_INDEX[third_world_axis]
    third_axis_sign = _backplate_third_axis_sign(slice_axis, backplate_normal_axis)

    mesh_bounds = trimesh_mesh.bounds
    extents = [0.0, 0.0, 0.0]
    center = [0.0, 0.0, 0.0]
    for i in range(3):
        if i == normal_world_index:
            extents[i] = 2 * backplate_plane_tolerance_mm
            center[i] = common_plane_world_mm
        else:
            extents[i] = 2 * (mesh_bounds[1][i] - mesh_bounds[0][i])
            center[i] = (mesh_bounds[0][i] + mesh_bounds[1][i]) / 2
    translation_matrix = [
        [1.0, 0.0, 0.0, center[0]],
        [0.0, 1.0, 0.0, center[1]],
        [0.0, 0.0, 1.0, center[2]],
        [0.0, 0.0, 0.0, 1.0],
    ]
    slab = trimesh.creation.box(extents=extents, transform=translation_matrix)

    intersection = trimesh_mesh.intersection(slab)
    if intersection is None or len(intersection.vertices) == 0:
        return Polygon()

    triangles = intersection.vertices[intersection.faces]
    projected: list[Polygon] = []
    for triangle in triangles:
        points_2d = [
            (
                vertex[third_world_index] * third_axis_sign,
                vertex[slice_world_index] - axis_min,
            )
            for vertex in triangle
        ]
        polygon = Polygon(points_2d)
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
        if not polygon.is_empty:
            projected.append(polygon)

    if not projected:
        return Polygon()
    return unary_union(projected)


def place_backplate_tabs(
    slice_set: SliceSet,
    backplate_normal_axis: BackplateNormalAxis,
    backplate_thickness_mm: float,
    tab_length_mm: float,
    backplate_plane_tolerance_mm: float = 0.1,
    tab_spacing_mm: float = 700.0,
    tab_edge_margin_mm: float | None = None,
    slice_tab_overrides: tuple[SliceTabOverride, ...] = (),
    non_backplate_islands: tuple[NonBackplateIsland, ...] = (),
) -> tuple[SliceSet, tuple[Tab, ...], float, BaseGeometry]:
    """Érintkező szakaszok azonosítása és csapok elhelyezése.

    Lásd: BACKPLATE_SPEC.md 6. szakasz, 1-8. lépés.

    Args:
        slice_set: a pipeline addig lefutott lépéseinek kimenete.
        backplate_normal_axis: a Backplate felé néző irány.
        backplate_thickness_mm: a Backplate saját vastagsága (egyben a
            csapok mélysége is).
        tab_length_mm: a csap alapértelmezett hossza.
        backplate_plane_tolerance_mm: a szigetek érintkező szakaszainak
            megengedett síkeltérése.
        tab_spacing_mm: célzott csap-köz.
        tab_edge_margin_mm: a csap kezdete az érintkező szakasz végétől.
            Ha `None`, `= tab_length_mm`.
        slice_tab_overrides: szigetenkénti paraméter-/pozíció-felülbírálás.
        non_backplate_islands: a Backplate-kapcsolódásból kizárt szigetek.

    Returns:
        A csapokkal kiegészített Slice Set, az elhelyezett csapok listája,
        a validált közös Backplate-sík world-koordinátája
        (`backplate_normal_axis` mentén), és a Backplate nyers (margó
        előtti) alakja, a modell tényleges geometriájából, térbeli
        Boole-metszettel felépítve (`_build_backplate_shape_from_mesh()`,
        BACKPLATE_SPEC.md 6. szakasz 10. pont).

    Raises:
        InvalidBackplateError: érvénytelen paraméter, érvénytelen
            `backplate_normal_axis`, egy sziget nem ér el egy közös
            Backplate-síkot (tűréshatáron belül), vagy egy kézi csap-pozíció
            nem fér el. Egy érintkező szakaszon nem pozitív `usable_length`
            nem hiba — figyelmeztetés kerül naplózásra, és a szakasz csap
            nélkül marad.
    """
    resolved_tab_edge_margin_mm = (
        tab_edge_margin_mm if tab_edge_margin_mm is not None else tab_length_mm
    )

    if backplate_thickness_mm <= 0:
        raise InvalidBackplateError(
            "A backplate_thickness_mm értékének pozitívnak kell lennie: "
            f"{backplate_thickness_mm}"
        )
    if tab_length_mm <= 0:
        raise InvalidBackplateError(
            f"A tab_length_mm értékének pozitívnak kell lennie: {tab_length_mm}"
        )
    if tab_spacing_mm <= 0:
        raise InvalidBackplateError(
            f"A tab_spacing_mm értékének pozitívnak kell lennie: {tab_spacing_mm}"
        )
    if resolved_tab_edge_margin_mm <= 0:
        raise InvalidBackplateError(
            "A tab_edge_margin_mm értékének pozitívnak kell lennie: "
            f"{resolved_tab_edge_margin_mm}"
        )

    normal_index, sign, third_index = _resolve_backplate_axes(
        slice_set.slice_axis, backplate_normal_axis
    )

    excluded = {(n.slice_index, n.island_index) for n in non_backplate_islands}

    per_island_segments: dict[tuple[int, int], list[_ContactSegment]] = {}
    islands_by_key: dict[tuple[int, int], Island] = {}
    for slice_ in slice_set.slices:
        islands = reconstruct_islands(slice_)
        for island_index, island in enumerate(islands):
            key = (slice_.index, island_index)
            if key in excluded:
                continue
            segments = _find_contact_segments(
                island.solid.points,
                normal_index,
                sign,
                third_index,
                backplate_plane_tolerance_mm,
            )
            per_island_segments[key] = segments
            islands_by_key[key] = island

    all_entries: list[tuple[tuple[int, int], int, _ContactSegment]] = [
        (key, segment_index, segment)
        for key, segments in per_island_segments.items()
        for segment_index, segment in enumerate(segments)
    ]
    clusters = _chain_cluster_by_extreme(all_entries, backplate_plane_tolerance_mm)
    dominant = max(clusters, key=len)
    if len(dominant) <= len(all_entries) / 2:
        raise InvalidBackplateError(
            "Nem található egyértelmű közös Backplate-sík: a legnagyobb "
            f"csoport ({len(dominant)} szakasz) nem éri el az összes "
            f"érintkező szakasz ({len(all_entries)}) szigorú többségét."
        )
    common_plane_mm = max(segment.local_extreme_mm for _key, _idx, segment in dominant)
    common_plane_world_mm = common_plane_mm * sign
    backplate_shape = _build_backplate_shape_from_mesh(
        slice_set,
        common_plane_world_mm,
        backplate_normal_axis,
        backplate_plane_tolerance_mm,
    )

    dominant_membership = {(key, idx) for key, idx, _segment in dominant}
    filtered_per_island_segments: dict[tuple[int, int], list[_ContactSegment]] = {}
    for key, segments in per_island_segments.items():
        kept = [
            segment
            for segment_index, segment in enumerate(segments)
            if (key, segment_index) in dominant_membership
        ]
        if kept:
            filtered_per_island_segments[key] = kept
        else:
            slice_index, island_index = key
            logger.warning(
                "A(z) %s. szelet %s. szigete nem esik a Backplate domináns "
                "közös síkjába — a Backplate-kapcsolódásból automatikusan "
                "kizárva.",
                slice_index,
                island_index,
            )
    per_island_segments = filtered_per_island_segments

    base_params = _TabParams(
        tab_length_mm=tab_length_mm,
        tab_spacing_mm=tab_spacing_mm,
        tab_edge_margin_mm=resolved_tab_edge_margin_mm,
        manual_tab_positions=(),
    )

    all_tabs: list[Tab] = []
    tab_rectangles_by_key: dict[tuple[int, int], list[Polygon]] = {}

    for key, segments in per_island_segments.items():
        slice_index, island_index = key
        params = _resolve_tab_params(
            slice_index, island_index, base_params, slice_tab_overrides
        )

        for segment in segments:
            segment_length = segment.third_axis_max_mm - segment.third_axis_min_mm
            usable_length = segment_length - 2 * params.tab_edge_margin_mm
            if usable_length <= 0:
                logger.warning(
                    "A(z) %s. szelet %s. szigetének egy érintkező szakaszán "
                    "(hossz: %.4f mm) nem fér el csap a %.4f mm-es margóval "
                    "(hiányzó hely: %.4f mm) — ezen a szakaszon nem kerül "
                    "csap elhelyezésre.",
                    slice_index,
                    island_index,
                    segment_length,
                    params.tab_edge_margin_mm,
                    -usable_length,
                )
                continue

            segment_start = segment.third_axis_min_mm + params.tab_edge_margin_mm
            tab_spans = _resolve_tab_spans(
                params, segment_start, usable_length, segment
            )

            for span_start, span_end in tab_spans:
                all_tabs.append(
                    Tab(
                        slice_index=slice_index,
                        island_index=island_index,
                        third_axis_start_mm=span_start,
                        third_axis_end_mm=span_end,
                    )
                )
                rectangle = _build_tab_rectangle(
                    segment.local_extreme_mm,
                    common_plane_mm,
                    backplate_thickness_mm,
                    span_start,
                    span_end,
                    normal_index,
                    sign,
                    third_index,
                    backplate_plane_tolerance_mm,
                )
                tab_rectangles_by_key.setdefault(key, []).append(rectangle)

    modified_slice_set = _apply_tab_geometry(
        slice_set, islands_by_key, tab_rectangles_by_key
    )

    return modified_slice_set, tuple(all_tabs), common_plane_world_mm, backplate_shape


@dataclass(frozen=True)
class Backplate:
    """A Backplate Engine kimenete: a hátlap geometriája.

    A `contours` a Backplate saját (harmadik tengely, `slice_axis`)
    síkjában értendő — 2D pontlista, ugyanazzal a CCW/CW
    körüljárás-konvencióval, mint a Slice Engine `Contour`-jai.

    A `common_plane_mm` a domináns közös Backplate-sík (BACKPLATE_SPEC.md
    6. szakasz 3–5. pont) tényleges world-koordinátája
    `backplate_normal_axis` mentén — a Backplate belső (az összeállítás
    felé néző) síkjának pozíciója. Ezt tárolja explicit módon, hogy a
    fogyasztóknak (pl. a 3D előnézetnek) ne kelljen közelíteniük.

    A `numbering_marks` a Numbering Engine által a Backplate-hez
    kapcsolódó szigetekhez elhelyezett azonosító gravírozás-jeleit
    tartalmazza (alapértelmezetten üres — a Backplate Engine maga nem
    numeráz).

    Lásd: BACKPLATE_SPEC.md 4. szakasz.
    """

    contours: tuple[Contour, ...]
    thickness_mm: float
    common_plane_mm: float
    material_reference: str | None
    numbering_marks: tuple[EngravingMark, ...] = ()


def apply_backplate(
    slice_set: SliceSet,
    backplate_normal_axis: BackplateNormalAxis,
    backplate_thickness_mm: float,
    tab_length_mm: float,
    backplate_plane_tolerance_mm: float = 0.1,
    backplate_margin_mm: float = 0.0,
    tab_spacing_mm: float = 700.0,
    tab_edge_margin_mm: float | None = None,
    slice_tab_overrides: tuple[SliceTabOverride, ...] = (),
    non_backplate_islands: tuple[NonBackplateIsland, ...] = (),
    material_reference: str | None = None,
) -> tuple[SliceSet, Backplate]:
    """A Backplate Engine teljes folyamata (BACKPLATE_SPEC.md 6. szakasz, 1-12. lépés).

    Az érintkező szakaszok azonosítását, a csap-elhelyezést, és a
    Backplate nyers (margó előtti) alakjának felépítését
    (`place_backplate_tabs()`) belsőleg meghívja, majd alkalmazza a
    margót, és kivágja a csapoknak megfelelő fészkeket.

    Args:
        slice_set: a pipeline addig lefutott lépéseinek kimenete.
        backplate_normal_axis: a Backplate felé néző irány.
        backplate_thickness_mm: a Backplate saját vastagsága.
        tab_length_mm: a csap alapértelmezett hossza.
        backplate_plane_tolerance_mm: a szigetek érintkező szakaszainak
            megengedett síkeltérése.
        backplate_margin_mm: a Backplate-kontúr eltolása (pozitív: kifelé,
            negatív: befelé).
        tab_spacing_mm: célzott csap-köz.
        tab_edge_margin_mm: a csap kezdete az érintkező szakasz végétől.
        slice_tab_overrides: szigetenkénti paraméter-/pozíció-felülbírálás.
        non_backplate_islands: a Backplate-kapcsolódásból kizárt szigetek.
        material_reference: opcionális anyag-hivatkozás.

    Returns:
        A csapokkal kiegészített Slice Set, és a Backplate objektum.

    Raises:
        InvalidBackplateError: lásd `place_backplate_tabs()`.
    """
    modified_slice_set, tabs, common_plane_world_mm, backplate_shape = (
        place_backplate_tabs(
            slice_set,
            backplate_normal_axis=backplate_normal_axis,
            backplate_thickness_mm=backplate_thickness_mm,
            tab_length_mm=tab_length_mm,
            backplate_plane_tolerance_mm=backplate_plane_tolerance_mm,
            tab_spacing_mm=tab_spacing_mm,
            tab_edge_margin_mm=tab_edge_margin_mm,
            slice_tab_overrides=slice_tab_overrides,
            non_backplate_islands=non_backplate_islands,
        )
    )

    backplate_shape_with_margin = backplate_shape.buffer(backplate_margin_mm)

    slices_by_index = {s.index: s for s in modified_slice_set.slices}

    third_axis_sign = _backplate_third_axis_sign(
        modified_slice_set.slice_axis, backplate_normal_axis
    )
    for tab in tabs:
        slice_ = slices_by_index[tab.slice_index]
        third_start = tab.third_axis_start_mm * third_axis_sign
        third_end = tab.third_axis_end_mm * third_axis_sign
        slice_start = slice_.position_mm - slice_.thickness_mm / 2
        slice_end = slice_.position_mm + slice_.thickness_mm / 2
        nest_rectangle = Polygon(
            [
                (third_start, slice_start),
                (third_end, slice_start),
                (third_end, slice_end),
                (third_start, slice_end),
            ]
        )
        backplate_shape_with_margin = backplate_shape_with_margin.difference(
            nest_rectangle
        )

    backplate_contours = _polygon_to_contours(backplate_shape_with_margin)

    backplate = Backplate(
        contours=backplate_contours,
        thickness_mm=backplate_thickness_mm,
        common_plane_mm=common_plane_world_mm,
        material_reference=material_reference,
    )

    return modified_slice_set, backplate
