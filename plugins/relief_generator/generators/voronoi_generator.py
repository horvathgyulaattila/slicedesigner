"""Voronoi Generator — cellás/Worley-zaj alapú Height Field generátor.

A `VoronoiNoiseField.sample(x, y)` már `[0.0, 1.0]`-be esik (l.
docs/plugins/relief_generator/PROCEDURAL_NOISE.md), ezért — a
`WaveGenerator`-ral ellentétben — nincs szükség külön normalizálási
lépésre: a `HeightField` közvetlenül a zajmező mintavételező függvényét
csomagolja be.

Lásd: docs/plugins/relief_generator/VORONOI_RELIEF_GENERATOR.md,
ROADMAP Phase 11.1.
"""

from dataclasses import dataclass

from plugins.relief_generator.domain.height_field import HeightField
from plugins.relief_generator.domain.procedural_noise import VoronoiNoiseField
from plugins.relief_generator.domain.voronoi_parameters import VoronoiParameters


class VoronoiGenerator:
    """Voronoi Generator: cellás/Worley-zajból épített Height Field.

    A `generate()` egyetlen `VoronoiNoiseField`-et épít a megadott
    `scale`/`seed` alapján, és a mintavételező függvényét közvetlenül
    `HeightField`-ként adja vissza — nincs komponens-kombinálás, nincs
    normalizálás (a `VoronoiNoiseField` már `[0,1]`-be eső értéket ad).
    """

    def generate(self, parameters: VoronoiParameters) -> HeightField:
        """Előállít egy `HeightField`-et a megadott paraméterekből.

        Args:
            parameters: a Voronoi Generator érvényesített bemeneti
                paraméterei.

        Returns:
            A `VoronoiNoiseField.sample`-t közvetlenül becsomagoló
            `HeightField`.
        """
        noise = VoronoiNoiseField(scale=parameters.scale, seed=parameters.seed)
        return HeightField(noise.sample)


@dataclass(frozen=True)
class VoronoiHeightFieldSource:
    """A `HeightFieldSource` szerződés (ROADMAP Phase 11.1,
    `relief_generator_parameters.py`) Voronoi-megvalósítása — a
    `VoronoiParameters`-t és a `VoronoiGenerator`-t fogja össze, a
    `WaveHeightFieldSource` mintáját követve.
    """

    parameters: VoronoiParameters

    def build_height_field(self) -> HeightField:
        return VoronoiGenerator().generate(self.parameters)
