"""Image Interpretation — színkódolt régió-térkép alapú, ideiglenes
konkrét stratégia a Region-fa/-erdő előállítására.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_INTERPRETATION.md.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from PIL import Image

from plugins.relief_generator.domain.region import DepthBehavior, Region
from plugins.relief_generator.exceptions import ImageInterpretationError

_DEPTH_BEHAVIOR_BY_NAME = {
    "raised": DepthBehavior.RAISED,
    "recessed": DepthBehavior.RECESSED,
    "inherit": DepthBehavior.INHERIT,
}


@dataclass(frozen=True)
class PixelSetMask:
    """`Region.Mask`-megvalósítás: egy pixelkoordináta-halmaz.

    Egy adott hozzárendelt szín ÖSSZES, akár egymással nem összefüggő
    előfordulását egyetlen Mask fedi le (l.
    IMAGE_RELIEF_INTERPRETATION.md 3.3 szakasz).

    Ismert korlát: nagy képeknél a pixelenkénti halmaz memóriaigénye
    jelentős lehet — ez az ideiglenes (13.2), 13.9 által kiváltandó
    mechanizmus tudatosan vállalt egyszerűsítése.
    """

    pixels: frozenset[tuple[int, int]]

    def member(self, x: float, y: float) -> bool:
        """Lásd: `Region.Mask` Protocol (region.py)."""
        return (int(x), int(y)) in self.pixels


@dataclass(frozen=True)
class _RegionSpec:
    """Egy hozzárendelési-fájlbeli régió-bejegyzés feloldott alakja."""

    color: tuple[int, int, int]
    color_hex: str
    contribution: float
    depth_behavior: DepthBehavior
    parent_hex: str | None


def interpret_image(image_path: str, assignment_path: str) -> tuple[Region, ...]:
    """Színkódolt kép + hozzárendelési fájl alapján Region-erdőt épít.

    Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_INTERPRETATION.md.

    Args:
        image_path: a színkódolt régió-térkép fájlútvonala.
        assignment_path: a hozzárendelési JSON fájlútvonala (3.1 szakasz).

    Returns:
        A gyökér (`parent: null`) Regionök tuple-je — erdő, nem
        feltétlenül egyetlen fa.

    Raises:
        ImageInterpretationError: érvénytelen hozzárendelési fájl, a
            kép nem olvasható be, vagy a képen olyan pixel található,
            amely sem egy deklarált régiószínhez, sem a háttérhez nem
            rendelhető a tolerancián belül (kötegelt jelentés, l. 4.
            szakasz).
    """
    background, tolerance, specs = _load_assignment(assignment_path)

    try:
        image = Image.open(image_path).convert("RGB")
    except (OSError, ValueError) as error:
        raise ImageInterpretationError(
            f"A kép nem olvasható be: {image_path} ({error})"
        ) from error

    width, height = image.size
    pixel_access = image.load()

    pixels_by_color, unassigned = _quantize(
        pixel_access, width, height, specs, background, tolerance
    )

    if unassigned:
        raise ImageInterpretationError(_format_unassigned_report(unassigned))

    return _build_region_forest(specs, pixels_by_color)


def _load_assignment(
    assignment_path: str,
) -> tuple[tuple[int, int, int] | None, float, tuple[_RegionSpec, ...]]:
    """Beolvassa és validálja a hozzárendelési JSON fájlt.

    Raises:
        ImageInterpretationError: a fájl nem olvasható/nem érvényes
            JSON, üres `regions`, hiányzó kötelező mező, duplikált
            szín, negatív `color_tolerance`, hiányzó vagy köröket
            tartalmazó `parent`-hivatkozás.
    """
    try:
        with open(assignment_path, encoding="utf-8") as handle:
            data: dict[str, Any] = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        raise ImageInterpretationError(
            f"A hozzárendelési fájl nem olvasható be: {assignment_path} ({error})"
        ) from error

    raw_regions = data.get("regions", [])
    if not raw_regions:
        raise ImageInterpretationError(
            "A hozzárendelési fájl 'regions' listája nem lehet üres."
        )

    tolerance = float(data.get("color_tolerance", 0.0))
    if tolerance < 0.0:
        raise ImageInterpretationError(
            f"A color_tolerance nem lehet negatív, kapott érték: {tolerance}"
        )

    background_hex = data.get("background")
    background = _parse_hex_color(background_hex) if background_hex else None

    seen_colors: set[str] = set()
    specs: list[_RegionSpec] = []
    for entry in raw_regions:
        try:
            color_hex = entry["color"]
            depth_behavior_name = entry["depth_behavior"]
            contribution = float(entry["contribution"])
        except KeyError as error:
            raise ImageInterpretationError(
                f"Hiányzó kötelező mező egy régió-bejegyzésben: {error}"
            ) from error

        if color_hex in seen_colors:
            raise ImageInterpretationError(
                f"Duplikált szín a hozzárendelési fájlban: {color_hex}"
            )
        seen_colors.add(color_hex)

        if depth_behavior_name not in _DEPTH_BEHAVIOR_BY_NAME:
            raise ImageInterpretationError(
                f"Ismeretlen depth_behavior érték: {depth_behavior_name!r} "
                f"(szín: {color_hex})"
            )

        specs.append(
            _RegionSpec(
                color=_parse_hex_color(color_hex),
                color_hex=color_hex,
                contribution=contribution,
                depth_behavior=_DEPTH_BEHAVIOR_BY_NAME[depth_behavior_name],
                parent_hex=entry.get("parent"),
            )
        )

    known_colors = {spec.color_hex for spec in specs}
    for spec in specs:
        if spec.parent_hex is not None and spec.parent_hex not in known_colors:
            raise ImageInterpretationError(
                f"A(z) {spec.color_hex} szín 'parent' hivatkozása "
                f"({spec.parent_hex}) nem létező színre mutat."
            )

    _check_no_cycles(specs)

    return background, tolerance, tuple(specs)


def _parse_hex_color(color_hex: str) -> tuple[int, int, int]:
    """`#RRGGBB` alakú string RGB-hármassá alakítása.

    Raises:
        ImageInterpretationError: ha a formátum nem `#RRGGBB`.
    """
    text = color_hex.lstrip("#")
    if len(text) != 6:
        raise ImageInterpretationError(
            f"Érvénytelen szín-formátum, '#RRGGBB' várt: {color_hex!r}"
        )
    try:
        return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))
    except ValueError as error:
        raise ImageInterpretationError(
            f"Érvénytelen szín-formátum, '#RRGGBB' várt: {color_hex!r}"
        ) from error


def _check_no_cycles(specs: tuple[_RegionSpec, ...]) -> None:
    """Fail-fast ellenőrzi, hogy a `parent`-láncok nem alkotnak kört.

    Raises:
        ImageInterpretationError: ha kör található.
    """
    parent_by_color = {spec.color_hex: spec.parent_hex for spec in specs}
    for start_color in parent_by_color:
        visited: set[str] = set()
        current: str | None = start_color
        while current is not None:
            if current in visited:
                raise ImageInterpretationError(
                    f"Kör található a hierarchiában, érintve: {start_color}"
                )
            visited.add(current)
            current = parent_by_color.get(current)


def _color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    """Euklideszi távolság két RGB-szín között."""
    return sum((ac - bc) ** 2 for ac, bc in zip(a, b)) ** 0.5


def _quantize(
    pixel_access: Any,
    width: int,
    height: int,
    specs: tuple[_RegionSpec, ...],
    background: tuple[int, int, int] | None,
    tolerance: float,
) -> tuple[
    dict[str, frozenset[tuple[int, int]]],
    dict[tuple[int, int, int], list[tuple[int, int]]],
]:
    """Minden pixelt a hozzá legközelebbi deklarált színhez rendel.

    Egyenlő távolság esetén a `regions` lista bejárási sorrendje dönt;
    a `background` csak akkor kerül kiértékelésre, ha egyik
    `regions`-szín sem talált (l. IMAGE_RELIEF_INTERPRETATION.md 3.2).

    Returns:
        `(pixels_by_color, unassigned)` — a `pixels_by_color` egy
        `{color_hex: pixelhalmaz}` gyűjtemény (a `background`-hoz
        sorolt pixelek nem szerepelnek benne); az `unassigned` egy
        `{eredeti_szín: [(x, y), ...]}` gyűjtemény azokról a
        pixelekről, amelyek egyik deklarált színhez sem rendelhetők a
        toleranciával.
    """
    pixels_by_color: dict[str, list[tuple[int, int]]] = {
        spec.color_hex: [] for spec in specs
    }
    unassigned: dict[tuple[int, int, int], list[tuple[int, int]]] = {}

    for y in range(height):
        for x in range(width):
            pixel_color = pixel_access[x, y]

            best_spec: _RegionSpec | None = None
            best_distance = float("inf")
            for spec in specs:
                distance = _color_distance(pixel_color, spec.color)
                if distance <= tolerance and distance < best_distance:
                    best_spec = spec
                    best_distance = distance

            if best_spec is not None:
                pixels_by_color[best_spec.color_hex].append((x, y))
                continue

            if background is not None and _color_distance(
                pixel_color, background
            ) <= tolerance:
                continue

            unassigned.setdefault(pixel_color, []).append((x, y))

    return (
        {color_hex: frozenset(coords) for color_hex, coords in pixels_by_color.items()},
        unassigned,
    )


def _format_unassigned_report(
    unassigned: dict[tuple[int, int, int], list[tuple[int, int]]],
) -> str:
    """Kötegelt, olvasható hibaüzenetet állít elő az összes nem
    hozzárendelt színről, pixelszám szerint csökkenő sorrendben
    (azonos pixelszám esetén szín szerint, determinisztikusan)."""
    groups = sorted(unassigned.items(), key=lambda item: (-len(item[1]), item[0]))
    lines = [
        "A képen nem hozzárendelt színek találhatók (sem régióhoz, sem "
        "háttérhez nem rendelhetők a tolerancián belül):"
    ]
    for color, coordinates in groups:
        color_hex = "#{:02X}{:02X}{:02X}".format(*color)
        example_x, example_y = coordinates[0]
        lines.append(
            f"  {color_hex}: {len(coordinates)} pixel "
            f"(pl. ({example_x}, {example_y}))"
        )
    return "\n".join(lines)


def _build_region_forest(
    specs: tuple[_RegionSpec, ...],
    pixels_by_color: dict[str, frozenset[tuple[int, int]]],
) -> tuple[Region, ...]:
    """A `parent`-mutatókból felépíti a Region-erdőt, levelektől a
    gyökerek felé haladva (a `Region` immutábilis, a `children`-nek
    már készen kell lennie a szülő létrehozásakor)."""
    spec_by_color = {spec.color_hex: spec for spec in specs}
    children_of: dict[str, list[str]] = {spec.color_hex: [] for spec in specs}
    for spec in specs:
        if spec.parent_hex is not None:
            children_of[spec.parent_hex].append(spec.color_hex)

    built: dict[str, Region] = {}

    def build(color_hex: str) -> Region:
        if color_hex in built:
            return built[color_hex]
        spec = spec_by_color[color_hex]
        children = tuple(build(child_hex) for child_hex in children_of[color_hex])
        region = Region(
            mask=PixelSetMask(pixels_by_color[color_hex]),
            contribution=spec.contribution,
            depth_behavior=spec.depth_behavior,
            children=children,
        )
        built[color_hex] = region
        return region

    return tuple(build(spec.color_hex) for spec in specs if spec.parent_hex is None)
