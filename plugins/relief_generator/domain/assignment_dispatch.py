"""Assignment Dispatch — a hozzárendelési fájl opcionális 'strategy'
mezője alapján a színenkénti (13.2) vagy a blob-alapú (13.9) Image
Interpretation stratégiához irányít.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_BLOB_INTERPRETATION.md
4. szakasz, ADR-0021.
"""

from __future__ import annotations

import json

from plugins.relief_generator.domain.image_interpretation import interpret_image
from plugins.relief_generator.domain.image_interpretation_blob import (
    interpret_image_blob,
)
from plugins.relief_generator.domain.region import Region
from plugins.relief_generator.exceptions import ImageInterpretationError

_KNOWN_STRATEGIES = ("color", "blob")


def interpret_assignment(image_path: str, assignment_path: str) -> tuple[Region, ...]:
    """A hozzárendelési fájl opcionális 'strategy' mezője (alapértelmezett
    'color') alapján `interpret_image()`-hez vagy `interpret_image_blob()`-
    hoz irányít.

    A döntéshez a fájlt egy második, redundáns olvasással nyitja meg — a
    kiválasztott stratégia a teljes, változatlan fájlt saját maga tölti be
    újra (a 13.8-nál már elfogadott, tudatosan vállalt redundáns-I/O
    mintát követve, l. `ImageReliefGeneratorMeshSource` docstringje).

    Args:
        image_path: a régió-térkép fájlútvonala.
        assignment_path: a hozzárendelési JSON fájlútvonala.

    Returns:
        A gyökér Regionök tuple-je — a kiválasztott stratégia adja vissza,
        változatlanul továbbítva.

    Raises:
        ImageInterpretationError: olvashatatlan/érvénytelen hozzárendelési
            fájl, ismeretlen 'strategy' érték, vagy a kiválasztott
            stratégia saját hibája.
    """
    try:
        with open(assignment_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise ImageInterpretationError(
            f"A hozzárendelési fájl ('{assignment_path}') nem olvasható "
            f"vagy nem érvényes JSON: {exc}"
        ) from exc

    strategy = data.get("strategy", "color")
    if strategy not in _KNOWN_STRATEGIES:
        raise ImageInterpretationError(
            f"Ismeretlen 'strategy' érték: {strategy!r} "
            f"(érvényes értékek: {_KNOWN_STRATEGIES})."
        )
    if strategy == "color":
        return interpret_image(image_path, assignment_path)
    return interpret_image_blob(image_path, assignment_path)
