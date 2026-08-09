"""Gap Engine — a Gap fizikai megvalósítását biztosító Spacer-ek elhelyezése.

Lásd: docs/specifications/GAP_SYSTEM_SPEC.md.
"""

import logging
from dataclasses import dataclass
from typing import Literal

from shapely.geometry import Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from slicedesigner.engines.dowel_engine import DowelPosition
from slicedesigner.engines.exceptions import InvalidGapError
from slicedesigner.engines.slice_engine import (
    Slice,
    SliceSet,
    is_ccw,
    reconstruct_islands,
)

logger = logging.getLogger(__name__)

# Rács-felbontás (mm) az automatikus Spacer-pozíció kereséshez — belső
# implementációs finomhangolás, nem a specifikáció szerinti üzleti
# paraméter (GAP_SYSTEM_SPEC.md 5. szakasza nem sorolja fel).
_PLACEMENT_GRID_STEP_MM = 2.0


@dataclass(frozen=True)
class Spacer:
    """Egy elhelyezett Spacer.

    Lásd: GAP_SYSTEM_SPEC.md 4. szakasz.

    A `dowel_diameter_mm` kizárólag a Dowel-re fűzött Spacer-eknél (6.
    szakasz 4/a. pont) kerül kitöltésre, a rajta átmenő Dowel
    `DowelPosition.diameter_mm` értékével — ez teszi lehetővé, hogy a
    Nesting Engine a korong közepén a Dowel-nek megfelelő furatot vágjon
    (NESTING_SPEC.md 6. szakasz 2. pont). Önálló (nem Dowel-re fűzött)
    Spacer-eknél `None` marad — ezek furat nélküli, tömör korongok.
    """

    shape: Literal["cylinder"]
    x_mm: float
    y_mm: float
    diameter_mm: float
    thickness_mm: float
    start_slice_index: int
    region_id: int
    dowel_diameter_mm: float | None = None


def _slice_solid_union(slice_: Slice) -> BaseGeometry:
    """A Slice szolid (CCW) kontúrjainak uniója, lyukak figyelembevétele nélkül.

    A régió-szétbontáshoz és a Dowel-pozíciók régióhoz rendeléséhez
    szükséges — egy lyuk (pl. már kivágott Dowel Hole) nem bontja szét a
    fizikai régiót, ezért itt szándékosan figyelmen kívül marad.
    """
    solids = [Polygon(c.points) for c in slice_.contours if is_ccw(c.points)]
    return unary_union(solids)


def _slice_material_union(slice_: Slice) -> BaseGeometry:
    """A Slice tényleges, lyukakkal (Dowel Hole-okkal is) csökkentett anyag-uniója.

    Az automatikus Spacer-elhelyezés fedettség-ellenőrzéséhez szükséges —
    új Spacer nem kerülhet meglévő lyuk fölé.
    """
    islands = reconstruct_islands(slice_)
    return unary_union([island.polygon for island in islands])


def _split_into_regions(geometry: BaseGeometry) -> list[BaseGeometry]:
    """A metszetgeometria szétbontása egyedi (esetlegesen nulla területű) darabokra.

    A nulla területű (pont/vonal) darabok szándékosan nem kerülnek
    kiszűrésre — ezek a "nulla átfedésű, lebegő kontúr" esetet
    képviselik (GAP_SYSTEM_SPEC.md 7. szakasz), és a hívó oldalon
    automatikusan buknak a `min_spacers_per_region` ellenőrzésen, mivel
    egyetlen Spacer sem fér el bennük.
    """
    if geometry.is_empty:
        return []
    if hasattr(geometry, "geoms"):
        return [g for g in geometry.geoms if not g.is_empty]
    return [geometry]


def _overlaps_any(
    x_mm: float, y_mm: float, radius_mm: float, placed: list[Spacer]
) -> bool:
    for p in placed:
        distance = ((x_mm - p.x_mm) ** 2 + (y_mm - p.y_mm) ** 2) ** 0.5
        if distance < 2 * radius_mm:
            return True
    return False


def _find_best_spacer_candidate(
    placeable_area: BaseGeometry, radius_mm: float, already_placed: list[Spacer]
) -> tuple[float, float] | None:
    min_x, min_y, max_x, max_y = placeable_area.bounds
    candidates: list[tuple[float, float]] = []
    y_mm = min_y
    while y_mm <= max_y:
        x_mm = min_x
        while x_mm <= max_x:
            if Point(x_mm, y_mm).buffer(radius_mm).within(placeable_area):
                candidates.append((y_mm, x_mm))
            x_mm += _PLACEMENT_GRID_STEP_MM
        y_mm += _PLACEMENT_GRID_STEP_MM

    candidates.sort()

    for cand_y, cand_x in candidates:
        if _overlaps_any(cand_x, cand_y, radius_mm, already_placed):
            continue
        return (cand_x, cand_y)
    return None


def apply_gap(
    slice_set: SliceSet,
    spacer_diameter_mm: float,
    dowel_positions: tuple[DowelPosition, ...] = (),
    spacer_count_per_gap: int = 3,
    min_spacers_per_region: int = 1,
) -> tuple[SliceSet, tuple[Spacer, ...]]:
    """A Gap fizikai megvalósítását biztosító Spacer-ek elhelyezése.

    Args:
        slice_set: a Dowel Engine kimenete (a Dowel Hole-okkal már
            módosított geometriájú Slice Set, Gap-referenciával).
        spacer_diameter_mm: a henger alakú Spacer átmérője.
        dowel_positions: a Dowel Engine kimenete (üres, ha nem volt
            Dowel-elhelyezés).
        spacer_count_per_gap: az elhelyezendő Spacer-ek célszáma
            metszet-régiónként.
        min_spacers_per_region: a minimálisan elfogadható Spacer-szám egy
            metszet-régióban.

    Returns:
        A változatlan Slice Set, és a Spacer-ek listája.

    Raises:
        InvalidGapError: érvénytelen paraméter, vagy egy metszet-régió nem
            képes befogadni legalább `min_spacers_per_region` db Spacert.
    """
    if spacer_diameter_mm <= 0:
        raise InvalidGapError(
            "A spacer_diameter_mm értékének pozitívnak kell lennie: "
            f"{spacer_diameter_mm}"
        )
    if spacer_count_per_gap < 1:
        raise InvalidGapError(
            f"A spacer_count_per_gap legalább 1 kell legyen: {spacer_count_per_gap}"
        )
    if min_spacers_per_region < 0 or min_spacers_per_region > spacer_count_per_gap:
        raise InvalidGapError(
            "A min_spacers_per_region 0 és spacer_count_per_gap "
            f"({spacer_count_per_gap}) közé kell essen: {min_spacers_per_region}"
        )

    if slice_set.gap_mm == 0.0:
        return slice_set, ()

    spacer_radius_mm = spacer_diameter_mm / 2
    slices_by_index = {s.index: s for s in slice_set.slices}
    sorted_indices = sorted(slices_by_index.keys())

    all_spacers: list[Spacer] = []

    for start_index, end_index in zip(sorted_indices, sorted_indices[1:]):
        next_region_id = 1

        slice_a = slices_by_index[start_index]
        slice_b = slices_by_index[end_index]

        solid_intersection = _slice_solid_union(slice_a).intersection(
            _slice_solid_union(slice_b)
        )
        regions = _split_into_regions(solid_intersection)

        material_intersection = _slice_material_union(slice_a).intersection(
            _slice_material_union(slice_b)
        )

        for region in regions:
            placeable_area = region.intersection(material_intersection)

            dowel_based = [
                d
                for d in dowel_positions
                if d.start_slice_index <= start_index
                and d.end_slice_index >= end_index
                and Point(d.x_mm, d.y_mm).buffer(spacer_radius_mm).within(region)
            ]

            placed: list[Spacer] = [
                Spacer(
                    shape="cylinder",
                    x_mm=d.x_mm,
                    y_mm=d.y_mm,
                    diameter_mm=spacer_diameter_mm,
                    thickness_mm=slice_set.gap_mm,
                    start_slice_index=start_index,
                    region_id=next_region_id,
                    dowel_diameter_mm=d.diameter_mm,
                )
                for d in dowel_based
            ]

            while len(placed) < spacer_count_per_gap:
                candidate = _find_best_spacer_candidate(
                    placeable_area, spacer_radius_mm, placed
                )
                if candidate is None:
                    break
                x_mm, y_mm = candidate
                placed.append(
                    Spacer(
                        shape="cylinder",
                        x_mm=x_mm,
                        y_mm=y_mm,
                        diameter_mm=spacer_diameter_mm,
                        thickness_mm=slice_set.gap_mm,
                        start_slice_index=start_index,
                        region_id=next_region_id,
                    )
                )

            if len(placed) < min_spacers_per_region:
                raise InvalidGapError(
                    f"A(z) {start_index}-{end_index}. Gap {next_region_id}. régiójában "
                    f"legalább {min_spacers_per_region} Spacer nem helyezhető el "
                    f"(elért darabszám: {len(placed)})."
                )
            if len(placed) < spacer_count_per_gap:
                logger.warning(
                    "A(z) %s-%s. Gap %s. régiójában csak %d Spacer helyezhető el "
                    "a célzott %d helyett.",
                    start_index,
                    end_index,
                    next_region_id,
                    len(placed),
                    spacer_count_per_gap,
                )

            all_spacers.extend(placed)
            next_region_id += 1

    return slice_set, tuple(all_spacers)
