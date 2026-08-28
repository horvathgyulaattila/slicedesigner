"""Voronoi Parameters — a Voronoi Generator felhasználói szintű bemeneti
paraméterei.

Lásd: docs/plugins/relief_generator/VORONOI_RELIEF_GENERATOR.md,
docs/plugins/relief_generator/PROCEDURAL_NOISE.md (a `VoronoiNoiseField`
domain-contractja, amire ez a generátor épül), ROADMAP Phase 11.1.
"""

from dataclasses import dataclass

from plugins.relief_generator.exceptions import VoronoiParametersValueError


@dataclass(frozen=True)
class VoronoiParameters:
    """A Voronoi Generator felhasználó által megadott bemeneti paraméterei.

    A létrehozott példány immutábilis (`frozen=True`); a mezők
    érvényességét a `__post_init__` fail-fast ellenőrzi.

    Attributes:
        scale: a Voronoi-cellák mérete, normalizált koordinátaegységben
            (közvetlenül a `VoronoiNoiseField(scale=...)`-nek adva át).
            Szigorúan pozitív.
        seed: a cellaközéppontok determinisztikus elhelyezését vezérlő
            egész szám (közvetlenül a `VoronoiNoiseField(seed=...)`-nek
            adva át). Bármely egész érték érvényes.
    """

    scale: float
    seed: int

    def __post_init__(self) -> None:
        if self.scale <= 0.0:
            raise VoronoiParametersValueError(
                "A scale-nek szigorúan pozitívnak kell lennie, "
                f"a kapott érték: {self.scale}."
            )
