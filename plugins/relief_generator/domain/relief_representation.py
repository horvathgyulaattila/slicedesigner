"""Relief Representation — a hidat képező, "pont → ReliefValue"
funkcionális kontraktus az Effect Processing és a Geometry World
között.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_RELIEF_REPRESENTATION.md.
"""

from __future__ import annotations

from typing import Callable

from plugins.relief_generator.domain.effect_processing import combine
from plugins.relief_generator.domain.region_resolution import EffectSpec

ReliefRepresentation = Callable[[float, float], float]
"""Egy "pont → ReliefValue" függvény — reprezentációfüggetlen, nincs
materializált (raszter/rács) forma.

Lásd: IMAGE_RELIEF_RELIEF_REPRESENTATION.md 3. szakasz.
"""


def build_relief_representation(
    effect_specs: tuple[EffectSpec, ...],
) -> ReliefRepresentation:
    """Egy EffectSpec[]-ből felépíti a Relief Representation függvényt.

    Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_RELIEF_REPRESENTATION.md.

    Args:
        effect_specs: a Region Resolver (`resolve_regions`) teljes
            kimenete.

    Returns:
        Egy `(x, y) -> ReliefValue` függvény, amely minden híváskor a
        `combine`-ot hívja a rögzített `effect_specs` felett.
    """

    def relief_representation(x: float, y: float) -> float:
        return combine(effect_specs, x, y)

    return relief_representation
