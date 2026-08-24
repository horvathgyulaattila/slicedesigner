"""Amplitude Envelope — térbeli, középpont körüli amplitúdómoduláció
(ROADMAP Phase 9.2: Spatial amplitude envelope).

A `RadialAmplitudeEnvelope` a `plugins.relief_generator.domain.wave.AmplitudeEnvelope`
Protocol egy középpont körüli, cserélhető `Falloff`-modellel (Linear, Smooth,
Gaussian) paraméterezett megvalósítása.

Lásd: docs/plugins/relief_generator/AMPLITUDE_ENVELOPE.md.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from plugins.relief_generator.exceptions import (
    GaussianFalloffValueError,
    NoiseAmplitudeEnvelopeValueError,
    RadialAmplitudeEnvelopeValueError,
)


class Falloff(Protocol):
    """A távolság→amplitúdó lecsengést meghatározó komponens.

    Lásd: AMPLITUDE_ENVELOPE.md 4. szakasz.
    """

    def factor(self, d: float, radius: float) -> float:
        """Kiszámítja a lecsengési szorzót egy adott távolságon.

        Args:
            d: a centerhez viszonyított távolság.
            radius: a referencia-sugár.

        Returns:
            A lecsengési szorzó.
        """
        ...


@dataclass(frozen=True)
class LinearFalloff:
    """Lineáris lecsengés: `t = clamp(d/R, 0, 1)`, `M(t) = 1 − t`.

    Lásd: AMPLITUDE_ENVELOPE.md 5. szakasz. A radiuson kívül `M = 0`
    (véges támogatású).
    """

    def factor(self, d: float, radius: float) -> float:
        t = min(max(d / radius, 0.0), 1.0)
        return 1.0 - t


@dataclass(frozen=True)
class SmoothFalloff:
    """Smoothstep-alapú lecsengés: `t = clamp(d/R, 0, 1)`,
    `M(t) = 1 − (3t² − 2t³)`.

    Lásd: AMPLITUDE_ENVELOPE.md 6. szakasz. A radiuson kívül `M = 0`;
    a Linear-nél lágyabb amplitúdóátmenet.
    """

    def factor(self, d: float, radius: float) -> float:
        t = min(max(d / radius, 0.0), 1.0)
        smoothstep = 3.0 * t**2 - 2.0 * t**3
        return 1.0 - smoothstep


@dataclass(frozen=True)
class GaussianFalloff:
    """Gauss-lecsengés: `t = d/R` (clamp nélkül), `M(t) = e^(−k·t²)`.

    Lásd: AMPLITUDE_ENVELOPE.md 7–9. szakasz. A `radius` referencia-skála,
    nem hard cutoff — `d > R` esetén is `M(d) > 0` véges `d`-re.

    Attributes:
        sharpness: a Gauss-lecsengés élessége (`k`). Szigorúan pozitív;
            kisebb érték szélesebb, `k → 0+` esetén egyre inkább Uniform
            viselkedéshez tart.
    """

    sharpness: float

    def __post_init__(self) -> None:
        """Fail-fast validálja a `sharpness` mezőt.

        Raises:
            GaussianFalloffValueError: ha `sharpness` nem szigorúan
                pozitív.
        """
        if not self.sharpness > 0.0:
            raise GaussianFalloffValueError(
                "A sharpness-nek szigorúan pozitívnak kell lennie, "
                f"kapott érték: {self.sharpness}"
            )

    def factor(self, d: float, radius: float) -> float:
        t = d / radius
        return math.exp(-self.sharpness * t**2)


@dataclass(frozen=True)
class RadialAmplitudeEnvelope:
    """Középpont körüli, `Falloff`-fal paraméterezett amplitúdómoduláció.

    Lásd: AMPLITUDE_ENVELOPE.md 2–3. szakasz. A
    `plugins.relief_generator.domain.wave.AmplitudeEnvelope` Protocol
    megvalósítása. A center önálló domainparaméter — nem azonos
    automatikusan más domainobjektum középpontjával (pl.
    `RadialPropagation` source-ával), és a vizsgált domainen kívül is
    elhelyezhető.

    Attributes:
        center_x: a középpont X-koordinátája.
        center_y: a középpont Y-koordinátája.
        radius: a referencia-sugár. Szigorúan pozitív; lehet nagyobb a
            teljes panel méreténél.
        falloff: a távolság→amplitúdó lecsengést meghatározó komponens.
    """

    center_x: float
    center_y: float
    radius: float
    falloff: Falloff

    def __post_init__(self) -> None:
        """Fail-fast validálja a `radius` mezőt.

        Raises:
            RadialAmplitudeEnvelopeValueError: ha `radius` nem szigorúan
                pozitív.
        """
        if not self.radius > 0.0:
            raise RadialAmplitudeEnvelopeValueError(
                "A radius-nak szigorúan pozitívnak kell lennie, "
                f"kapott érték: {self.radius}"
            )

    def amplitude_factor(self, x: float, y: float) -> float:
        """Kiszámítja az amplitúdómodulációs szorzót egy adott koordinátán.

        Lásd: AMPLITUDE_ENVELOPE.md 2. szakasz:
        `d = √((x−x_c)² + (y−y_c)²)`.

        Args:
            x: X-koordináta.
            y: Y-koordináta.

        Returns:
            A `falloff` szerinti amplitúdómodulációs szorzó.
        """
        d = math.hypot(x - self.center_x, y - self.center_y)
        return self.falloff.factor(d, self.radius)


class NoiseSource(Protocol):
    """Egy determinisztikus 2D zajmező-mintavételező komponens.

    Lásd: AMPLITUDE_ENVELOPE.md 11. szakasz (ROADMAP Phase 10.5). A
    `plugins.relief_generator.domain.procedural_noise.GradientNoiseField`
    és `VoronoiNoiseField` (Phase 10.4) mindkettő már kielégíti ezt a
    Protocolt, módosítás nélkül — tisztán structural typing, a
    `Falloff`/`AmplitudeEnvelope`/`Distortion`/`PropagationModel` mintáját
    követve.
    """

    def sample(self, x: float, y: float) -> float:
        """Mintavételezi a zajmezőt egy adott térbeli koordinátán.

        Args:
            x: X-koordináta.
            y: Y-koordináta.

        Returns:
            A zajmező mintavételezett értéke (a konkrét megvalósítás
            saját tartományában — l. `input_min`/`input_max` a
            `NoiseAmplitudeEnvelope`-on).
        """
        ...


@dataclass(frozen=True)
class NoiseAmplitudeEnvelope:
    """Eljárásos zajmező-alapú amplitúdómoduláció.

    Lásd: AMPLITUDE_ENVELOPE.md 11. szakasz (ROADMAP Phase 10.5). A
    `plugins.relief_generator.domain.wave.AmplitudeEnvelope` Protocol
    megvalósítása — a `noise` mezőt egy `[input_min, input_max]`
    tartományból lineárisan `[0.0, 1.0]`-ra képezi, `[0.0, 1.0]`-ra
    vágva (numerikus biztonsági háló).

    Attributes:
        noise: a mintavételezendő zajmező-forrás (bármely `NoiseSource`
            Protocolt kielégítő objektum — pl. `GradientNoiseField` vagy
            `VoronoiNoiseField`, Phase 10.4).
        input_min: a `noise.sample()` elméleti alsó korlátja.
            Alapértelmezett: `0.0` (a `VoronoiNoiseField` natív
            tartománya — nem igényel remapet).
        input_max: a `noise.sample()` elméleti felső korlátja.
            Alapértelmezett: `1.0`. `GradientNoiseField`-hez
            `input_min=-1.0` adandó meg a hívó által.
    """

    noise: NoiseSource
    input_min: float = 0.0
    input_max: float = 1.0

    def __post_init__(self) -> None:
        """Fail-fast validálja az `input_min`/`input_max` mezőket.

        Raises:
            NoiseAmplitudeEnvelopeValueError: ha `input_max` nem
                szigorúan nagyobb, mint `input_min`.
        """
        if not self.input_max > self.input_min:
            raise NoiseAmplitudeEnvelopeValueError(
                "Az input_max-nak szigorúan nagyobbnak kell lennie, mint "
                f"az input_min, kapott érték: input_min={self.input_min}, "
                f"input_max={self.input_max}"
            )

    def amplitude_factor(self, x: float, y: float) -> float:
        """Kiszámítja az amplitúdómodulációs szorzót egy adott koordinátán.

        Args:
            x: X-koordináta.
            y: Y-koordináta.

        Returns:
            A `[0.0, 1.0]` zárt intervallumba eső amplitúdómodulációs
            szorzó.
        """
        raw = self.noise.sample(x, y)
        normalized = (raw - self.input_min) / (self.input_max - self.input_min)
        return min(max(normalized, 0.0), 1.0)
