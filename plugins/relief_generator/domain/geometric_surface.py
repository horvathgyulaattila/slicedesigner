"""Geometric Surface — a Relief Representation fizikai geometriává
alakítása: a híd a Relief World és a Geometry World között.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_GEOMETRIC_SURFACE.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from plugins.relief_generator.domain.relief_representation import (
    ReliefRepresentation,
)
from plugins.relief_generator.exceptions import GeometricSurfaceValueError


@dataclass(frozen=True)
class GeometricSurface:
    """A Relief Representationt fizikai `Z`-koordinátává leképező,
    fizikai méretekkel rendelkező domain modell.

    Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_GEOMETRIC_SURFACE.md.

    A réteg tudatosan kizárólag egyetlen fail-fast kényszert érvényesít
    (l. `__post_init__`); a `width`/`height`/`relief_height_raised`
    értékkészlete ezen a rétegen nincs korlátozva.

    Attributes:
        width: a felszín fizikai X-kiterjedése.
        height: a felszín fizikai Y-kiterjedése.
        base_thickness: a relief "nulla" síkjának `Z`-koordinátája.
        relief_height_raised: a Raised irány terjedelme.
        relief_height_recessed: a Recessed irány terjedelme.
        raw_relief: a Relief Representation — "pont → ReliefValue"
            függvény.
    """

    width: float
    height: float
    base_thickness: float
    relief_height_raised: float
    relief_height_recessed: float
    raw_relief: ReliefRepresentation

    def __post_init__(self) -> None:
        """Fail-fast validálja a réteg egyetlen kötelező fizikai kényszerét.

        Raises:
            GeometricSurfaceValueError: ha a `base_thickness -
                relief_height_recessed` különbség nem szigorúan
                pozitív (a relief a fizikai `Z = 0` alá kerülne).
        """
        if not self.base_thickness - self.relief_height_recessed > 0.0:
            raise GeometricSurfaceValueError(
                "A base_thickness - relief_height_recessed különbségnek "
                "szigorúan pozitívnak kell lennie, kapott "
                f"base_thickness={self.base_thickness}, "
                f"relief_height_recessed={self.relief_height_recessed}"
            )

    def physical_z(self, raw_value: float, v_min: float, v_max: float) -> float:
        """A `ReliefValue -> fizikai Z` leképezés, nullponthoz rögzített,
        kétirányú, egymástól független normalizálással.

        Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_GEOMETRIC_SURFACE.md
        5. szakasz.

        Args:
            raw_value: a `ReliefValue` az adott ponton
                (`raw_relief(x, y)` kimenete).
            v_min: a ténylegesen realizált `ReliefValue` minimuma
                (`<= 0`) — a hívó felelőssége előállítani (Phase 13.7).
            v_max: a ténylegesen realizált `ReliefValue` maximuma
                (`>= 0`) — a hívó felelőssége előállítani (Phase 13.7).

        Returns:
            A fizikai `Z`-koordináta.
        """
        if raw_value == 0.0:
            return self.base_thickness
        if raw_value > 0.0:
            return self.base_thickness + (raw_value / v_max) * self.relief_height_raised
        return self.base_thickness - (raw_value / v_min) * self.relief_height_recessed
