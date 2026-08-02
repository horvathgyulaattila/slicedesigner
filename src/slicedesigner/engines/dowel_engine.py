"""Dowel Engine — Dowel- és Dowel Hole-pozíciók számítása a szeletek illesztéséhez.

Lásd: docs/specifications/DOWEL_SYSTEM_SPEC.md.
"""

import logging
import math
from dataclasses import dataclass, replace

import networkx as nx
from shapely.geometry import LinearRing, Point, Polygon

from slicedesigner.engines.exceptions import InvalidDowelError
from slicedesigner.engines.slice_engine import Contour, HoleKind, Slice, SliceSet

logger = logging.getLogger(__name__)

# Rács-felbontás (mm) az automatikus Dowel-pozíció kereséshez — belső
# implementációs finomhangolás, nem a specifikáció szerinti üzleti
# paraméter (DOWEL_SYSTEM_SPEC.md 5. szakasza nem sorolja fel).
_PLACEMENT_GRID_STEP_MM = 2.0

# Az automatikus pozíciókeresésben egy futásnak minimálisan ennyi
# egymást követő szeleten át kell tartania (DOWEL_SYSTEM_SPEC.md 6.
# szakasz, 4. lépés).
_MIN_AUTO_RUN_LENGTH_SLICES = 2

# A Dowel Hole kontúrjának diszkretizálási felbontása (szegmensszám).
_CIRCLE_SEGMENT_COUNT = 32


@dataclass(frozen=True)
class ManualDowelPosition:
    """Kézzel megadott, elsőbbséget élvező Dowel-pozíció.

    Lásd: DOWEL_SYSTEM_SPEC.md 3. szakasz.
    """

    x_mm: float
    y_mm: float
    start_slice_index: int
    end_slice_index: int


@dataclass(frozen=True)
class DowelPosition:
    """Egy ténylegesen elhelyezett Dowel.

    Lásd: DOWEL_SYSTEM_SPEC.md 4. szakasz.
    """

    x_mm: float
    y_mm: float
    diameter_mm: float
    length_mm: float
    start_slice_index: int
    end_slice_index: int
    region_id: int


@dataclass(frozen=True)
class _Island:
    """Egy Slice-on belüli, geometriailag különálló anyagrész (belső segédtípus)."""

    slice_index: int
    solid: Contour
    holes: tuple[Contour, ...]
    polygon: Polygon


def _is_ccw(points: tuple[tuple[float, float], ...]) -> bool:
    return bool(LinearRing(points).is_ccw)


def _reconstruct_islands(slice_: Slice) -> list[_Island]:
    """Egy Slice lapos kontúrlistájából szigetek (szolid + hozzá tartozó lyukak)
    építése."""
    solids = [c for c in slice_.contours if _is_ccw(c.points)]
    holes = [c for c in slice_.contours if not _is_ccw(c.points)]

    islands: list[_Island] = []
    for solid in solids:
        solid_polygon = Polygon(solid.points)
        own_holes = [
            h
            for h in holes
            if solid_polygon.contains(Polygon(h.points).representative_point())
        ]
        island_polygon = Polygon(solid.points, holes=[h.points for h in own_holes])
        islands.append(
            _Island(
                slice_index=slice_.index,
                solid=solid,
                holes=tuple(own_holes),
                polygon=island_polygon,
            )
        )
    return islands


def _build_regions(all_islands: dict[int, list[_Island]]) -> dict[int, list[_Island]]:
    """Régió-azonosítás: szomszédos szeletek átfedő szigetei összefüggő komponensben."""
    graph: nx.Graph = nx.Graph()
    for slice_index, islands in all_islands.items():
        for island_pos in range(len(islands)):
            graph.add_node((slice_index, island_pos))

    sorted_slice_indices = sorted(all_islands.keys())
    for a, b in zip(sorted_slice_indices, sorted_slice_indices[1:]):
        for pos_a, island_a in enumerate(all_islands[a]):
            for pos_b, island_b in enumerate(all_islands[b]):
                if island_a.polygon.intersects(island_b.polygon):
                    graph.add_edge((a, pos_a), (b, pos_b))

    regions: dict[int, list[_Island]] = {}
    for region_id, component in enumerate(nx.connected_components(graph), start=1):
        regions[region_id] = [
            all_islands[slice_index][pos] for slice_index, pos in sorted(component)
        ]
    return regions


def _circle_fits(island: _Island, x_mm: float, y_mm: float, radius_mm: float) -> bool:
    return bool(Point(x_mm, y_mm).buffer(radius_mm).within(island.polygon))


def _region_islands_by_slice(region_islands: list[_Island]) -> dict[int, list[_Island]]:
    by_slice: dict[int, list[_Island]] = {}
    for island in region_islands:
        by_slice.setdefault(island.slice_index, []).append(island)
    return by_slice


def _longest_run(
    by_slice: dict[int, list[_Island]],
    slice_indices_sorted: list[int],
    x_mm: float,
    y_mm: float,
    radius_mm: float,
) -> tuple[int, int]:
    """A leghosszabb egymást követő szeletfutás (kezdő, záró sorszám), ahol a kör elfér.

    Nincs elfogadható (legalább `_MIN_AUTO_RUN_LENGTH_SLICES` hosszú) futás
    esetén (0, 0) az eredmény.
    """
    fits_by_index: dict[int, bool] = {
        slice_index: any(
            _circle_fits(island, x_mm, y_mm, radius_mm)
            for island in by_slice.get(slice_index, [])
        )
        for slice_index in slice_indices_sorted
    }

    best_start, best_end, best_length = 0, 0, 0
    current_start: int | None = None
    previous_index: int | None = None

    for slice_index in slice_indices_sorted:
        consecutive = previous_index is not None and slice_index == previous_index + 1
        if fits_by_index[slice_index]:
            if current_start is None or not consecutive:
                current_start = slice_index
            current_length = slice_index - current_start + 1
            if current_length > best_length:
                best_start, best_end, best_length = (
                    current_start,
                    slice_index,
                    current_length,
                )
        else:
            current_start = None
        previous_index = slice_index

    if best_length < _MIN_AUTO_RUN_LENGTH_SLICES:
        return (0, 0)
    return (best_start, best_end)


def _match_manual_position_to_region(
    manual: ManualDowelPosition,
    regions: dict[int, list[_Island]],
    check_radius_mm: float,
) -> int | None:
    """Egy kézi pozícióhoz tartozó régió azonosítása; None, ha egyik régióhoz sem
    illeszkedik."""
    if manual.end_slice_index < manual.start_slice_index:
        return None
    span = range(manual.start_slice_index, manual.end_slice_index + 1)

    for region_id, region_islands in regions.items():
        by_slice = _region_islands_by_slice(region_islands)
        if all(
            any(
                _circle_fits(island, manual.x_mm, manual.y_mm, check_radius_mm)
                for island in by_slice.get(slice_index, [])
            )
            for slice_index in span
        ):
            return region_id
    return None


def _check_manual_positions_do_not_overlap(
    positions: list[ManualDowelPosition], check_radius_mm: float
) -> None:
    for i, a in enumerate(positions):
        for b in positions[i + 1 :]:
            spans_overlap = not (
                a.end_slice_index < b.start_slice_index
                or b.end_slice_index < a.start_slice_index
            )
            if not spans_overlap:
                continue
            distance = ((a.x_mm - b.x_mm) ** 2 + (a.y_mm - b.y_mm) ** 2) ** 0.5
            if distance < 2 * check_radius_mm:
                raise InvalidDowelError(
                    f"Két kézi Dowel-pozíció egymást átfedi: ({a.x_mm}, {a.y_mm}) és "
                    f"({b.x_mm}, {b.y_mm})."
                )


def _overlaps_any(
    x_mm: float, y_mm: float, check_radius_mm: float, placed: list[DowelPosition]
) -> bool:
    for p in placed:
        distance = ((x_mm - p.x_mm) ** 2 + (y_mm - p.y_mm) ** 2) ** 0.5
        if distance < 2 * check_radius_mm:
            return True
    return False


def _find_best_auto_candidate(
    by_slice: dict[int, list[_Island]],
    slice_indices_sorted: list[int],
    check_radius_mm: float,
    already_placed: list[DowelPosition],
) -> tuple[float, float, int, int] | None:
    """A legjobb (leghosszabb futású) rács-jelölt keresése, amely nem fedi a már
    elhelyezetteket."""
    all_islands = [island for islands in by_slice.values() for island in islands]
    if not all_islands:
        return None

    min_x = min(island.polygon.bounds[0] for island in all_islands)
    min_y = min(island.polygon.bounds[1] for island in all_islands)
    max_x = max(island.polygon.bounds[2] for island in all_islands)
    max_y = max(island.polygon.bounds[3] for island in all_islands)

    candidates: list[tuple[int, float, float, int, int]] = []
    y_mm = min_y
    while y_mm <= max_y:
        x_mm = min_x
        while x_mm <= max_x:
            start_index, end_index = _longest_run(
                by_slice, slice_indices_sorted, x_mm, y_mm, check_radius_mm
            )
            if end_index >= start_index and start_index > 0:
                length = end_index - start_index + 1
                candidates.append((length, y_mm, x_mm, start_index, end_index))
            x_mm += _PLACEMENT_GRID_STEP_MM
        y_mm += _PLACEMENT_GRID_STEP_MM

    candidates.sort(key=lambda c: (-c[0], c[1], c[2]))

    for _length, cand_y, cand_x, start_index, end_index in candidates:
        if _overlaps_any(cand_x, cand_y, check_radius_mm, already_placed):
            continue
        return (cand_x, cand_y, start_index, end_index)
    return None


def _dowel_length_mm(start_slice: Slice, end_slice: Slice) -> float:
    """A kezdő és záró szelet külső síkjai közti távolság (DOWEL_SYSTEM_SPEC.md 4.
    szakasz)."""
    start_outer = start_slice.position_mm - start_slice.thickness_mm / 2
    end_outer = end_slice.position_mm + end_slice.thickness_mm / 2
    return end_outer - start_outer


def _circle_contour_cw(
    x_mm: float, y_mm: float, radius_mm: float, hole_kind: HoleKind, depth_mm: float
) -> Contour:
    """Kör alakú Dowel Hole kontúr építése, CW körüljárással (lyuk-konvenció)."""
    points = tuple(
        (
            x_mm + radius_mm * math.cos(-2 * math.pi * i / _CIRCLE_SEGMENT_COUNT),
            y_mm + radius_mm * math.sin(-2 * math.pi * i / _CIRCLE_SEGMENT_COUNT),
        )
        for i in range(_CIRCLE_SEGMENT_COUNT)
    )
    return Contour(points=points, hole_kind=hole_kind, depth_mm=depth_mm)


def _cut_dowel_holes(
    slice_set: SliceSet,
    positions: tuple[DowelPosition, ...],
    dowel_diameter_mm: float,
    blind_hole_cap_mm: float,
) -> SliceSet:
    slices_by_index = {s.index: s for s in slice_set.slices}
    holes_by_slice_index: dict[int, list[Contour]] = {}

    for dowel in positions:
        for slice_index in range(dowel.start_slice_index, dowel.end_slice_index + 1):
            is_end_slice = slice_index in (
                dowel.start_slice_index,
                dowel.end_slice_index,
            )
            current_slice = slices_by_index[slice_index]
            if is_end_slice:
                hole_kind = HoleKind.DOWEL_BLIND
                depth_mm = current_slice.thickness_mm - blind_hole_cap_mm
            else:
                hole_kind = HoleKind.DOWEL_THROUGH
                depth_mm = current_slice.thickness_mm

            hole_contour = _circle_contour_cw(
                dowel.x_mm, dowel.y_mm, dowel_diameter_mm / 2, hole_kind, depth_mm
            )
            holes_by_slice_index.setdefault(slice_index, []).append(hole_contour)

    new_slices = tuple(
        replace(s, contours=s.contours + tuple(holes_by_slice_index[s.index]))
        if s.index in holes_by_slice_index
        else s
        for s in slice_set.slices
    )
    return replace(slice_set, slices=new_slices)


def apply_dowels(
    slice_set: SliceSet,
    dowel_diameter_mm: float,
    spacer_diameter_mm: float = 0.0,
    min_edge_clearance_mm: float | None = None,
    dowel_count_per_region: int = 3,
    min_dowels_per_region: int = 1,
    blind_hole_cap_mm: float | None = None,
    manual_dowel_positions: tuple[ManualDowelPosition, ...] = (),
) -> tuple[SliceSet, tuple[DowelPosition, ...]]:
    """Dowel- és Dowel Hole-pozíciók számítása, a Slice Set módosítása a furatokkal.

    Args:
        slice_set: a Slice Engine kimenete.
        dowel_diameter_mm: a Dowel (és a hozzá tartozó furatok) átmérője.
        spacer_diameter_mm: csak a `min_edge_clearance_mm` alapértékének
            számításához.
        min_edge_clearance_mm: biztonsági távolság a szelet külső szélétől.
            Ha `None`, `max(dowel_diameter_mm, spacer_diameter_mm) / 2`.
        dowel_count_per_region: az elhelyezendő Dowel-ek célszáma
            régiónként.
        min_dowels_per_region: a minimálisan elfogadható Dowel-szám egy
            régióban.
        blind_hole_cap_mm: a vak furat lezáró oldalán megmaradó
            anyagvastagság. Ha `None`, a szeletvastagság 30%-a.
        manual_dowel_positions: kézzel megadott, elsőbbséget élvező
            Dowel-pozíciók.

    Returns:
        A Dowel Hole-okkal módosított Slice Set, és a Dowel-pozíciók listája.

    Raises:
        InvalidDowelError: érvénytelen paraméter, érvénytelen vagy
            egymást átfedő kézi pozíció, vagy egy régió nem képes
            befogadni legalább `min_dowels_per_region` db Dowel-t.
    """
    if dowel_diameter_mm <= 0:
        raise InvalidDowelError(
            f"A dowel_diameter_mm értékének pozitívnak kell lennie: {dowel_diameter_mm}"
        )
    if spacer_diameter_mm < 0:
        raise InvalidDowelError(
            f"A spacer_diameter_mm értéke nem lehet negatív: {spacer_diameter_mm}"
        )

    resolved_clearance_mm = (
        min_edge_clearance_mm
        if min_edge_clearance_mm is not None
        else max(dowel_diameter_mm, spacer_diameter_mm) / 2
    )
    if resolved_clearance_mm < 0:
        raise InvalidDowelError(
            f"A min_edge_clearance_mm értéke nem lehet negatív: {resolved_clearance_mm}"
        )

    if dowel_count_per_region < 1:
        raise InvalidDowelError(
            f"A dowel_count_per_region legalább 1 kell legyen: {dowel_count_per_region}"
        )
    if min_dowels_per_region < 1 or min_dowels_per_region > dowel_count_per_region:
        raise InvalidDowelError(
            "A min_dowels_per_region 1 és dowel_count_per_region "
            f"({dowel_count_per_region}) közé kell essen: {min_dowels_per_region}"
        )

    slice_thickness_mm = slice_set.slices[0].thickness_mm
    resolved_blind_hole_cap_mm = (
        blind_hole_cap_mm if blind_hole_cap_mm is not None else 0.3 * slice_thickness_mm
    )
    if not (0 < resolved_blind_hole_cap_mm < slice_thickness_mm):
        raise InvalidDowelError(
            f"A blind_hole_cap_mm-nek a (0, {slice_thickness_mm}) tartományba "
            f"kell esnie: {resolved_blind_hole_cap_mm}"
        )

    check_radius_mm = dowel_diameter_mm / 2 + resolved_clearance_mm

    all_islands = {s.index: _reconstruct_islands(s) for s in slice_set.slices}
    regions = _build_regions(all_islands)
    slices_by_index = {s.index: s for s in slice_set.slices}

    manual_by_region: dict[int, list[ManualDowelPosition]] = {
        region_id: [] for region_id in regions
    }
    for manual in manual_dowel_positions:
        matched_region_id = _match_manual_position_to_region(
            manual, regions, check_radius_mm
        )
        if matched_region_id is None:
            raise InvalidDowelError(
                f"A megadott kézi Dowel-pozíció ({manual.x_mm}, {manual.y_mm}, "
                f"{manual.start_slice_index}-{manual.end_slice_index}) nem fér el "
                "teljes egészében a jelölt szeletsáv anyagán belül."
            )
        manual_by_region[matched_region_id].append(manual)

    for positions_in_region in manual_by_region.values():
        _check_manual_positions_do_not_overlap(positions_in_region, check_radius_mm)

    all_positions: list[DowelPosition] = []
    for region_id, region_islands in regions.items():
        placed: list[DowelPosition] = [
            DowelPosition(
                x_mm=m.x_mm,
                y_mm=m.y_mm,
                diameter_mm=dowel_diameter_mm,
                length_mm=_dowel_length_mm(
                    slices_by_index[m.start_slice_index],
                    slices_by_index[m.end_slice_index],
                ),
                start_slice_index=m.start_slice_index,
                end_slice_index=m.end_slice_index,
                region_id=region_id,
            )
            for m in manual_by_region[region_id]
        ]

        by_slice = _region_islands_by_slice(region_islands)
        slice_indices_sorted = sorted(by_slice.keys())

        while len(placed) < dowel_count_per_region:
            candidate = _find_best_auto_candidate(
                by_slice, slice_indices_sorted, check_radius_mm, placed
            )
            if candidate is None:
                break
            x_mm, y_mm, start_index, end_index = candidate
            placed.append(
                DowelPosition(
                    x_mm=x_mm,
                    y_mm=y_mm,
                    diameter_mm=dowel_diameter_mm,
                    length_mm=_dowel_length_mm(
                        slices_by_index[start_index], slices_by_index[end_index]
                    ),
                    start_slice_index=start_index,
                    end_slice_index=end_index,
                    region_id=region_id,
                )
            )

        if len(placed) < min_dowels_per_region:
            raise InvalidDowelError(
                f"A(z) {region_id}. régióban legalább {min_dowels_per_region} Dowel "
                f"nem helyezhető el (elért darabszám: {len(placed)})."
            )
        if len(placed) < dowel_count_per_region:
            logger.warning(
                "A(z) %s. régióban csak %d Dowel helyezhető el a célzott %d helyett.",
                region_id,
                len(placed),
                dowel_count_per_region,
            )

        all_positions.extend(placed)

    final_positions = tuple(all_positions)
    modified_slice_set = _cut_dowel_holes(
        slice_set, final_positions, dowel_diameter_mm, resolved_blind_hole_cap_mm
    )

    return modified_slice_set, final_positions
