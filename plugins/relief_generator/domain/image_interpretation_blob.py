"""Image Interpretation — Blob — seed-pixel flood-fill alapú, a 13.2-es
színenkénti stratégiát kiegészítő (nem kiváltó) konkrét stratégia.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_BLOB_INTERPRETATION.md,
ADR-0021.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from PIL import Image

from plugins.relief_generator.domain.image_interpretation import PixelSetMask
from plugins.relief_generator.domain.region import DepthBehavior, Region
from plugins.relief_generator.exceptions import ImageInterpretationError

_NEIGHBOR_OFFSETS: tuple[tuple[int, int], ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


@dataclass(frozen=True)
class _BlobRegionSpec:
    """Egy blob-hozzárendelési bejegyzés feloldott alakja."""

    seed_pixel: tuple[int, int]
    color_tolerance: float
    contribution: float
    depth_behavior: DepthBehavior
    parent_seed: tuple[int, int] | None


def _color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    """Euklideszi RGB-távolság — l. `image_interpretation.py::_color_distance`
    azonos képlete; szándékosan önálló, modul-belső másolat, hogy a két
    modul ne ossza meg egymás private (aláhúzással jelzett) nevét."""
    return sum((ac - bc) ** 2 for ac, bc in zip(a, b, strict=True)) ** 0.5


def flood_fill_region(
    pixels: Any, width: int, height: int, seed: tuple[int, int], tolerance: float
) -> frozenset[tuple[int, int]]:
    """Iteratív (explicit verem, nem rekurzió), 4-szomszédos flood-fill,
    a `seed` pixel színéhez viszonyított toleranciával.

    Publikus — nemcsak `interpret_image_blob()` (batch) hívja belül,
    hanem a `RegionAssignmentDialog` (13.9, 2. rész) is, egyetlen
    seed-pixelre, kattintásonként, egy már megnyitott/betöltött képen
    (l. `docs/plugins/relief_generator/IMAGE_RELIEF_REGION_ASSIGNMENT_GUI.md`
    6. szakasz) — ezért nincs két, egymástól függetlenül karbantartott
    implementáció.

    Raises:
        ImageInterpretationError: ha a `seed` a kép határain kívül esik.
    """
    seed_x, seed_y = seed
    if not (0 <= seed_x < width and 0 <= seed_y < height):
        raise ImageInterpretationError(
            f"A seed_pixel {seed!r} a kép határain ({width}x{height}) kívül esik."
        )
    seed_color = pixels[seed]
    visited: set[tuple[int, int]] = {seed}
    stack: list[tuple[int, int]] = [seed]
    while stack:
        x, y = stack.pop()
        for dx, dy in _NEIGHBOR_OFFSETS:
            neighbor = (x + dx, y + dy)
            nx, ny = neighbor
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if neighbor in visited:
                continue
            if _color_distance(pixels[neighbor], seed_color) <= tolerance:
                visited.add(neighbor)
                stack.append(neighbor)
    return frozenset(visited)


def _parse_entries(data: dict[str, Any]) -> tuple[_BlobRegionSpec, ...]:
    raw_entries = data.get("regions")
    if not raw_entries:
        raise ImageInterpretationError(
            "A hozzárendelési fájl 'regions' mezője kötelező és nem lehet üres."
        )
    specs: list[_BlobRegionSpec] = []
    seen_seeds: set[tuple[int, int]] = set()
    for entry in raw_entries:
        try:
            seed = tuple(entry["seed_pixel"])
            contribution = entry["contribution"]
            depth_behavior = DepthBehavior(entry["depth_behavior"])
        except (KeyError, ValueError) as exc:
            raise ImageInterpretationError(
                f"Érvénytelen régió-bejegyzés: {entry!r} ({exc})."
            ) from exc
        if seed in seen_seeds:
            raise ImageInterpretationError(
                f"A(z) {seed!r} seed_pixel több bejegyzésben is szerepel."
            )
        seen_seeds.add(seed)
        tolerance = entry.get("color_tolerance", 0.0)
        if tolerance < 0.0:
            raise ImageInterpretationError(
                f"A(z) {seed!r} bejegyzés color_tolerance értéke "
                f"({tolerance}) nem lehet negatív."
            )
        parent_raw = entry.get("parent")
        parent_seed = tuple(parent_raw) if parent_raw is not None else None
        specs.append(
            _BlobRegionSpec(
                seed_pixel=seed,
                color_tolerance=tolerance,
                contribution=contribution,
                depth_behavior=depth_behavior,
                parent_seed=parent_seed,
            )
        )
    return tuple(specs)


def _build_region_forest(
    specs: tuple[_BlobRegionSpec, ...],
    masks_by_seed: dict[tuple[int, int], PixelSetMask],
) -> tuple[Region, ...]:
    """A `parent_seed`-mutatókból felépíti a Region-erdőt — az
    `image_interpretation.py::_build_region_forest` memoizált,
    rekurzív felépítési mintáját követi, `seed_pixel` kulcsokkal, de
    (szándékos, ADR-0021-ben indokolt eltérésként) explicit
    hiba-jelzéssel feloldhatatlan/körkörös `parent`-hivatkozásra."""
    spec_by_seed = {spec.seed_pixel: spec for spec in specs}
    children_of: dict[tuple[int, int], list[tuple[int, int]]] = {
        spec.seed_pixel: [] for spec in specs
    }
    for spec in specs:
        if spec.parent_seed is None:
            continue
        if spec.parent_seed not in spec_by_seed:
            raise ImageInterpretationError(
                f"A(z) {spec.seed_pixel!r} bejegyzés 'parent' mezője "
                f"({spec.parent_seed!r}) nem egyezik egyetlen másik "
                "bejegyzés seed_pixel-jével sem."
            )
        children_of[spec.parent_seed].append(spec.seed_pixel)

    built: dict[tuple[int, int], Region] = {}
    building: set[tuple[int, int]] = set()

    def build(seed: tuple[int, int]) -> Region:
        if seed in built:
            return built[seed]
        if seed in building:
            raise ImageInterpretationError(
                f"Körkörös 'parent' hivatkozás a(z) {seed!r} seed_pixel körül."
            )
        building.add(seed)
        spec = spec_by_seed[seed]
        children = tuple(build(child_seed) for child_seed in children_of[seed])
        region = Region(
            mask=masks_by_seed[seed],
            contribution=spec.contribution,
            depth_behavior=spec.depth_behavior,
            children=children,
        )
        built[seed] = region
        building.discard(seed)
        return region

    return tuple(build(spec.seed_pixel) for spec in specs if spec.parent_seed is None)


def interpret_image_blob(image_path: str, assignment_path: str) -> tuple[Region, ...]:
    """Kép + seed-pixel-alapú hozzárendelési fájl alapján Region-erdőt épít.

    Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_BLOB_INTERPRETATION.md.

    Args:
        image_path: a régió-térkép fájlútvonala.
        assignment_path: a hozzárendelési JSON fájlútvonala (2. szakasz).

    Returns:
        A gyökér (`parent: null`) Regionök tuple-je — erdő, nem
        feltétlenül egyetlen fa.

    Raises:
        ImageInterpretationError: érvénytelen hozzárendelési fájl, a kép
            nem olvasható be, kép határain kívüli `seed_pixel`,
            feloldhatatlan vagy körkörös `parent`-hivatkozás.
    """
    try:
        with open(assignment_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise ImageInterpretationError(
            f"A hozzárendelési fájl ('{assignment_path}') nem olvasható "
            f"vagy nem érvényes JSON: {exc}"
        ) from exc

    specs = _parse_entries(data)

    try:
        with Image.open(image_path) as image:
            rgb_image = image.convert("RGB")
            width, height = rgb_image.size
            pixels = rgb_image.load()
            masks_by_seed = {
                spec.seed_pixel: PixelSetMask(
                    flood_fill_region(
                        pixels, width, height, spec.seed_pixel, spec.color_tolerance
                    )
                )
                for spec in specs
            }
    except OSError as exc:
        raise ImageInterpretationError(
            f"A kép ('{image_path}') nem olvasható: {exc}"
        ) from exc

    return _build_region_forest(specs, masks_by_seed)
