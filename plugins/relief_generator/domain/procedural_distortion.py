"""Procedural Distortion — koordináta-torzítás Wave-komponensenként
(ROADMAP Phase 9.6: Controlled procedural distortion).

A `SwirlDistortion` a `plugins.relief_generator.domain.wave.Distortion`
Protocol középpont körüli, távolsággal csökkenő mértékű elforgatást
megvalósító implementációja.

Lásd: docs/plugins/relief_generator/PROCEDURAL_DISTORTION.md.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from plugins.relief_generator.exceptions import SwirlDistortionValueError


@dataclass(frozen=True)
class SwirlDistortion:
    """Középpont körüli, távolsággal csökkenő mértékű koordináta-elforgatás.

    Lásd: PROCEDURAL_DISTORTION.md 3–5. szakasz. A
    `plugins.relief_generator.domain.wave.Distortion` Protocol
    megvalósítása.

    Attributes:
        center_x: a forgatás középpontjának X-koordinátája.
        center_y: a forgatás középpontjának Y-koordinátája.
        radius: referencia-skála (nem hard cutoff), a lecsengés
            Gaussian-jellegű. Szigorúan pozitív.
        strength: a forgatás mértéke, bármely véges valós érték.
            Pozitív/negatív érték ellentétes körüljárási irányba forgat;
            `strength = 0` az identitás-transzformációval egyenértékű.
    """

    center_x: float
    center_y: float
    radius: float
    strength: float

    def __post_init__(self) -> None:
        """Fail-fast validálja a `radius` mezőt.

        Raises:
            SwirlDistortionValueError: ha `radius` nem szigorúan pozitív.
        """
        if not self.radius > 0.0:
            raise SwirlDistortionValueError(
                "A radius-nak szigorúan pozitívnak kell lennie, "
                f"kapott érték: {self.radius}"
            )

    def warp(self, x: float, y: float) -> tuple[float, float]:
        """Elforgatja a koordinátákat a center körül, távolsággal csökkenő
        mértékben.

        Lásd: PROCEDURAL_DISTORTION.md 3. szakasz:
        `α(d) = strength · e^(−(d/radius)²)`,
        `x' = x_c + (x−x_c)·cos(α) − (y−y_c)·sin(α)`,
        `y' = y_c + (x−x_c)·sin(α) + (y−y_c)·cos(α)`.

        Args:
            x: X-koordináta.
            y: Y-koordináta.

        Returns:
            A torzított `(x', y')` koordináták.
        """
        d = math.hypot(x - self.center_x, y - self.center_y)
        angle = self.strength * math.exp(-((d / self.radius) ** 2))
        dx = x - self.center_x
        dy = y - self.center_y
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        warped_x = self.center_x + dx * cos_a - dy * sin_a
        warped_y = self.center_y + dx * sin_a + dy * cos_a
        return warped_x, warped_y
