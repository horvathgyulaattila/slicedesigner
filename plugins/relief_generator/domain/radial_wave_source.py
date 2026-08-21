"""Radial Wave Source — pontszerű forrásból kiinduló hullámterjedés
(ROADMAP Phase 9.3: Radial wave source).

A `RadialPropagation` a `plugins.relief_generator.domain.wave.PropagationModel`
Protocol egy pontszerű forrásból kiinduló megvalósítása.

Lásd: docs/plugins/relief_generator/RADIAL_WAVE_SOURCE.md.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RadialPropagation:
    """Pontszerű forrásból kiinduló hullámterjedés:
    `P(x,y) = √((x−x_s)² + (y−y_s)²)`.

    Lásd: RADIAL_WAVE_SOURCE.md 2–3. szakasz. A
    `plugins.relief_generator.domain.wave.PropagationModel` Protocol
    megvalósítása. A source pozíciója független az `AmplitudeEnvelope`
    centerétől (l. AMPLITUDE_ENVELOPE.md 3. szakasz) — a két pozíció
    alapértelmezés szerint lehet azonos, de a domainmodell nem köti őket
    össze. A source a vizsgált felületen kívül is elhelyezhető; nincs rá
    invariáns megkötés.

    Attributes:
        source_x: a forrás X-koordinátája.
        source_y: a forrás Y-koordinátája.
    """

    source_x: float
    source_y: float

    def phase_position(self, x: float, y: float) -> float:
        """Kiszámítja a fázispozíciót egy adott térbeli koordinátán.

        Lásd: RADIAL_WAVE_SOURCE.md 3. szakasz: ha `x = x_s` és `y = y_s`,
        akkor `P(x,y) = 0` — érvényes állapot, nincs szingularitás.

        Args:
            x: X-koordináta.
            y: Y-koordináta.

        Returns:
            A `P(x,y)` fázispozíció (a forrástól mért euklideszi
            távolság).
        """
        return math.hypot(x - self.source_x, y - self.source_y)
