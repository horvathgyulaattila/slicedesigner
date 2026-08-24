"""Megosztott, determinisztikus 2D eljárásos zajmező-primitívek
(ROADMAP Phase 10.4).

Lásd: docs/plugins/relief_generator/PROCEDURAL_NOISE.md. Két, egymástól
független primitívum:

* `GradientNoiseField` — Perlin-szerű, gradiens-alapú zaj, `[-1.0, 1.0]`
  tartományba képez.
* `VoronoiNoiseField` — cellás/Worley-zaj (legközelebbi mag-pont
  távolsága), `[0.0, 1.0]` tartományba képez.

Mindkettő tisztán aritmetikai — nem használ `random` modult vagy
bármilyen implicit véletlenszám-állapotot (WAVE_DOMAIN_MODEL.md 14.
szakasz determinizmus-elve): azonos `(x, y, seed)` bemenetre mindig
azonos kimenetet ad.

Ez a modul a `plugins/relief_generator/domain/`-hoz tartozik (nem a
`generators/`-hoz), hogy a jövőbeli `AmplitudeEnvelope`/`Distortion`
becsomagolások (ROADMAP Phase 10.5/10.6) mindkét oldalról importálhassák,
körkörös import nélkül — a `deterministic_components.py` (Phase 10.3)
mintáját követve.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from plugins.relief_generator.exceptions import ProceduralNoiseValueError


def _hash(ix: int, iy: int, seed: int) -> float:
    """Determinisztikus, `[0.0, 1.0)`-be eső hash egy rácsponthoz.

    Tisztán aritmetikai ("GLSL-hash" trükk) — nem `random` modul.
    """
    raw = math.sin(ix * 127.1 + iy * 311.7 + seed * 74.7) * 43758.5453123
    return raw - math.floor(raw)


def _smoothstep(t: float) -> float:
    """Köbös simítógörbe: `3t² − 2t³`, `t ∈ [0,1]`-re."""
    return t * t * (3.0 - 2.0 * t)


def _lerp(a: float, b: float, t: float) -> float:
    """Lineáris interpoláció `a` és `b` között, `t ∈ [0,1]`-re."""
    return a + t * (b - a)


_GRADIENT_NORMALIZATION = math.sqrt(2.0) / 2.0


def _gradient(ix: int, iy: int, seed: int) -> tuple[float, float]:
    """Egységnyi hosszú, determinisztikus gradiens-vektor egy rácsponthoz."""
    angle = _hash(ix, iy, seed) * 2.0 * math.pi
    return math.cos(angle), math.sin(angle)


@dataclass(frozen=True)
class GradientNoiseField:
    """Perlin-szerű, gradiens-alapú determinisztikus 2D zajmező.

    Lásd: docs/plugins/relief_generator/PROCEDURAL_NOISE.md 2. szakasz.
    A rácspontokon egységnyi hosszú, determinisztikus gradiens-vektorok
    ülnek (nem puszta érték); a `sample()` a rácspont és a lekérdezett
    pont közti vektor gradienssel vett skaláris szorzatát interpolálja
    simított (`smoothstep`) súlyokkal — ez adja a folytonos, "áramló"
    jelleget.

    Attributes:
        scale: a zaj-rács alapmérete (a `Wave.wavelength`-hez hasonló
            egységben). Szigorúan pozitív.
        seed: a gradiens-mező determinisztikus változatosságát biztosító
            egész szám — azonos `scale`/`octaves` mellett más `seed`
            teljesen más, de ugyanúgy determinisztikus mintázatot ad.
        octaves: az összegzett zaj-rétegek száma (fraktál/fBm-kombináció,
            PROCEDURAL_NOISE.md 2.3 szakasz). `1` esetén nincs
            réteg-kombináció (alapértelmezett). Szigorúan pozitív egész.
        persistence: rétegankénti amplitúdó-csökkenés (`octaves > 1`
            esetén releváns).
        lacunarity: rétegankénti frekvencia-növekedés (`octaves > 1`
            esetén releváns).
    """

    scale: float
    seed: int = 0
    octaves: int = 1
    persistence: float = 0.5
    lacunarity: float = 2.0

    def __post_init__(self) -> None:
        if not self.scale > 0.0:
            raise ProceduralNoiseValueError(
                "A scale-nek szigorúan pozitívnak kell lennie, "
                f"kapott érték: {self.scale}"
            )
        if not self.octaves >= 1:
            raise ProceduralNoiseValueError(
                "Az octaves-nek legalább 1-nek kell lennie, "
                f"kapott érték: {self.octaves}"
            )

    def sample(self, x: float, y: float) -> float:
        """A zajmező értéke az `(x, y)` ponton, `[-1.0, 1.0]`-be vágva.

        Args:
            x: az x-koordináta.
            y: az y-koordináta.

        Returns:
            A `[-1.0, 1.0]` zárt intervallumba eső zajérték.
        """
        if self.octaves == 1:
            return self._sample_single(x, y, self.scale, self.seed)

        total = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_amplitude = 0.0
        for i in range(self.octaves):
            total += (
                self._sample_single(
                    x * frequency, y * frequency, self.scale, self.seed + i
                )
                * amplitude
            )
            max_amplitude += amplitude
            amplitude *= self.persistence
            frequency *= self.lacunarity
        normalized = total / max_amplitude
        return max(-1.0, min(1.0, normalized))

    def _sample_single(self, x: float, y: float, scale: float, seed: int) -> float:
        gx = x / scale
        gy = y / scale
        ix0 = math.floor(gx)
        iy0 = math.floor(gy)
        ix1 = ix0 + 1
        iy1 = iy0 + 1
        fx = gx - ix0
        fy = gy - iy0

        def dot_grid_gradient(ix: int, iy: int) -> float:
            grad_x, grad_y = _gradient(ix, iy, seed)
            dx = gx - ix
            dy = gy - iy
            return grad_x * dx + grad_y * dy

        n00 = dot_grid_gradient(ix0, iy0)
        n10 = dot_grid_gradient(ix1, iy0)
        n01 = dot_grid_gradient(ix0, iy1)
        n11 = dot_grid_gradient(ix1, iy1)

        sx = _smoothstep(fx)
        sy = _smoothstep(fy)

        top = _lerp(n00, n10, sx)
        bottom = _lerp(n01, n11, sx)
        value = _lerp(top, bottom, sy)

        normalized = value / _GRADIENT_NORMALIZATION
        return max(-1.0, min(1.0, normalized))


_VORONOI_NORMALIZATION = math.sqrt(2.0)


@dataclass(frozen=True)
class VoronoiNoiseField:
    """Cellás/Worley-zaj: a legközelebbi determinisztikus mag-pont távolsága.

    Lásd: docs/plugins/relief_generator/PROCEDURAL_NOISE.md 3. szakasz.
    Minden rácscellához egy, a cellán belül determinisztikusan eltolt
    mag-pont tartozik; a `sample()` a lekérdezett ponthoz legközelebbi
    mag-pont távolságát adja vissza (klasszikus "F1" Worley-zaj), a 3×3
    szomszédos cella figyelembevételével.

    Attributes:
        scale: a zaj-rács alapmérete. Szigorúan pozitív.
        seed: a mag-pontok determinisztikus elhelyezését befolyásoló
            egész szám.
    """

    scale: float
    seed: int = 0

    def __post_init__(self) -> None:
        if not self.scale > 0.0:
            raise ProceduralNoiseValueError(
                "A scale-nek szigorúan pozitívnak kell lennie, "
                f"kapott érték: {self.scale}"
            )

    def sample(self, x: float, y: float) -> float:
        """A legközelebbi mag-pont távolsága `(x, y)`-tól, `[0.0, 1.0]`-be vágva.

        Args:
            x: az x-koordináta.
            y: az y-koordináta.

        Returns:
            A `[0.0, 1.0]` zárt intervallumba eső, nem-negatív távolság-érték.
        """
        gx = x / self.scale
        gy = y / self.scale
        cell_x = math.floor(gx)
        cell_y = math.floor(gy)

        min_distance = math.inf
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cix = cell_x + dx
                ciy = cell_y + dy
                seed_x = cix + _hash(cix, ciy, self.seed)
                seed_y = ciy + _hash(cix, ciy, self.seed + 1)
                distance = math.hypot(gx - seed_x, gy - seed_y)
                min_distance = min(min_distance, distance)

        normalized = min_distance / _VORONOI_NORMALIZATION
        return max(0.0, min(1.0, normalized))
