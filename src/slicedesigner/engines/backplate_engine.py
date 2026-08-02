"""Backplate Engine (1. kör) — érintkező szakasz azonosítás és csap-elhelyezés.

Lásd: docs/specifications/BACKPLATE_SPEC.md (6. szakasz, 1-8. lépés).
A sziluett-számítás és a fészek-kivágás (9-11. lépés) külön menetben készül.
"""

import logging
from dataclasses import dataclass, replace
from enum import Enum

from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

from slicedesigner.engines.exceptions import InvalidBackplateError
from slicedesigner.engines.mesh_import import Mesh
from slicedesigner.engines.slice_engine import (
    Contour,
    Island,
    Slice,
    SliceAxis,
    SliceSet,
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

# A Slice Engine kontúr-koordinátáinak feltételezett világtengely-sorrendje.
# A slice_axis=Z eset ellenőrzött és tesztelt. A slice_axis=X/Y esetek
# ciklikus (jobbkéz-szabály-szerű) feltevésen alapulnak, NEM ellenőrzöttek.
_SLICE_AXIS_CONTOUR_ORDER: dict[SliceAxis, tuple[str, str]] = {
    SliceAxis.Z: ("X", "Y"),
    SliceAxis.X: ("Y", "Z"),
    SliceAxis.Y: ("Z", "X"),
}


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
) -> Polygon:
    """Egy csap-protrúzió téglalapjának felépítése kontúr-lokális koordinátákban.

    A belső él a sziget saját szélső koordinátájánál kezdődik (hogy a
    protrúzió biztosan érintkezzen a sziget geometriájával), a külső éle
    a validált közös Backplate-síktól számított `backplate_thickness_mm`.
    """
    inner_normal = local_extreme_mm * sign
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
) -> tuple[SliceSet, tuple[Tab, ...]]:
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
        A csapokkal kiegészített Slice Set, és az elhelyezett csapok listája.

    Raises:
        InvalidBackplateError: érvénytelen paraméter, érvénytelen
            `backplate_normal_axis`, egy sziget nem ér el egy közös
            Backplate-síkot (tűréshatáron belül), egy érintkező szakaszon
            `usable_length` nem pozitív, vagy egy kézi csap-pozíció nem
            fér el.
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

    all_local_extremes = [
        segment.local_extreme_mm
        for segments in per_island_segments.values()
        for segment in segments
    ]
    common_plane_mm = max(all_local_extremes)
    for extreme in all_local_extremes:
        if common_plane_mm - extreme > backplate_plane_tolerance_mm:
            raise InvalidBackplateError(
                "Egy sziget érintkező szakasza nem esik egy közös Backplate-síkba "
                f"(eltérés: {common_plane_mm - extreme:.4f} mm > "
                f"{backplate_plane_tolerance_mm} mm)."
            )

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
                raise InvalidBackplateError(
                    f"A(z) {slice_index}. szelet {island_index}. szigetének egy "
                    f"érintkező szakaszán a usable_length nem pozitív "
                    f"({usable_length:.4f} mm)."
                )

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
                )
                tab_rectangles_by_key.setdefault(key, []).append(rectangle)

    modified_slice_set = _apply_tab_geometry(
        slice_set, islands_by_key, tab_rectangles_by_key
    )

    return modified_slice_set, tuple(all_tabs)


_WORLD_AXIS_INDEX: dict[str, int] = {"X": 0, "Y": 1, "Z": 2}


def _resolve_silhouette_axes(
    slice_axis: SliceAxis, backplate_normal_axis: BackplateNormalAxis
) -> tuple[int, int]:
    """(harmadik tengely világindexe, slice_axis világindexe) — a Backplate
    saját síkja."""
    world_normal, _ = _NORMAL_AXIS_WORLD[backplate_normal_axis]
    all_axes = {"X", "Y", "Z"}
    third_axis = next(iter(all_axes - {world_normal, slice_axis.value}))
    return _WORLD_AXIS_INDEX[third_axis], _WORLD_AXIS_INDEX[slice_axis.value]


def _compute_silhouette(
    mesh: Mesh, third_world_index: int, slice_world_index: int
) -> BaseGeometry:
    """A Mesh sziluettje a Backplate saját (harmadik tengely, slice_axis) síkjában.

    A specifikáció "a teljes Slice Set sziluettje" megfogalmazását az
    eredeti (szeletelés előtti) 3D Mesh-ből, a háromszögek vetített
    uniójaként számítjuk — lásd a Kontextus szakaszt az indoklásért és a
    dokumentált korlátozásért (Dowel Hole-ok nem befolyásolják).
    """
    triangle_polygons = []
    for triangle in mesh.triangles:
        points_2d = [
            (mesh.vertices[i][third_world_index], mesh.vertices[i][slice_world_index])
            for i in triangle
        ]
        polygon = Polygon(points_2d)
        if polygon.area > 0:
            triangle_polygons.append(polygon)
    return unary_union(triangle_polygons)


@dataclass(frozen=True)
class Backplate:
    """A Backplate Engine kimenete: a hátlap geometriája.

    A `contours` a Backplate saját (harmadik tengely, `slice_axis`)
    síkjában értendő — 2D pontlista, ugyanazzal a CCW/CW
    körüljárás-konvencióval, mint a Slice Engine `Contour`-jai.

    Lásd: BACKPLATE_SPEC.md 4. szakasz.
    """

    contours: tuple[Contour, ...]
    thickness_mm: float
    material_reference: str | None


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

    Az érintkező szakaszok azonosítását és a csap-elhelyezést
    (`place_backplate_tabs()`) belsőleg meghívja, majd előállítja a
    Backplate sziluettjét, alkalmazza a margót, és kivágja a
    csapoknak megfelelő fészkeket.

    Args:
        slice_set: a pipeline addig lefutott lépéseinek kimenete.
        backplate_normal_axis: a Backplate felé néző irány.
        backplate_thickness_mm: a Backplate saját vastagsága.
        tab_length_mm: a csap alapértelmezett hossza.
        backplate_plane_tolerance_mm: a szigetek érintkező szakaszainak
            megengedett síkeltérése.
        backplate_margin_mm: a sziluett-kontúr eltolása (pozitív: kifelé,
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
    modified_slice_set, tabs = place_backplate_tabs(
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

    third_world_index, slice_world_index = _resolve_silhouette_axes(
        slice_set.slice_axis, backplate_normal_axis
    )

    silhouette = _compute_silhouette(
        slice_set.source_mesh, third_world_index, slice_world_index
    )
    silhouette_with_margin = silhouette.buffer(backplate_margin_mm)

    axis_min = slice_set.source_mesh.bounding_box.min[slice_world_index]
    slices_by_index = {s.index: s for s in modified_slice_set.slices}

    for tab in tabs:
        slice_ = slices_by_index[tab.slice_index]
        third_start, third_end = tab.third_axis_start_mm, tab.third_axis_end_mm
        slice_start = axis_min + slice_.position_mm - slice_.thickness_mm / 2
        slice_end = axis_min + slice_.position_mm + slice_.thickness_mm / 2
        nest_rectangle = Polygon(
            [
                (third_start, slice_start),
                (third_end, slice_start),
                (third_end, slice_end),
                (third_start, slice_end),
            ]
        )
        silhouette_with_margin = silhouette_with_margin.difference(nest_rectangle)

    backplate_contours = _polygon_to_contours(silhouette_with_margin)

    backplate = Backplate(
        contours=backplate_contours,
        thickness_mm=backplate_thickness_mm,
        material_reference=material_reference,
    )

    return modified_slice_set, backplate
