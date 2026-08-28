"""Crater Generator — Voronoi-magpontoktól mért, radiálisan szimmetrikus
távolság `radius`-ra vágva és hatványfüggvénnyel torzítva, több, egyre
finomodó méretskálán rétegezve (`octaves`/`lacunarity`) és a rétegek
közül a legmélyebb ponttal kombinálva — változó méretű, egymásba
ágyazódó, holdkráter-szerű mélyedések, arányosan sekélyebb finom
kráterekkel.

**Miért nem elég a puszta `VoronoiNoiseField.sample(x,y) ** power`
(a legelső, hibás megközelítés):** a `VoronoiNoiseField.sample` a
teljes síkot hézagmentesen, a legközelebbi magponthoz rendelve osztja
fel ("F1" Worley-zaj) — a `[0,1]`-es tartomány mindig a Voronoi-cella
sokszögletű határáig tart. Ezt a `radius` küszöb oldja fel (l.
`CraterParameters.radius` docstringje): a kráter csak a küszöbig terjed,
ahol a távolság még tisztán radiálisan szimmetrikus.

**Miért `min`, nem összegzés (mint a `GradientNoiseField` fraktál-
kombinációja):** itt nem zajfinomításról van szó, hanem fizikailag
különálló kráter-generációk egymásra rétegezéséről — egy adott pontban
az számít, melyik réteg vágja legmélyebbre azt a pontot. Ez adja azt a
jelenséget, hogy egy nagy, sekélyebb kráter belsejében egy kisebb,
finomabb rétegből származó kráter "átüti" a nagy alját, ha ott mélyebb
értéket ad.

**Miért arányos a mélység a mérettel, külön paraméter nélkül:** a
valódi holdkráterek mélysége nagyjából arányos az átmérőjükkel — ezt a
tulajdonságot a már meglévő `lacunarity` fejezi ki, nem egy új,
felhasználó által állítandó paraméter: az `i`-edik réteg a méretét
`scale / lacunarity**i`-ként, a maximális mélységét (mennyire
közelítheti meg a réteg saját magpontján a `h=0`-t) pedig
`1 / lacunarity**i`-ként kapja — mindkettő ugyanattól a `lacunarity`-tól
függ, ugyanolyan mértékben zsugorodva rétegenként. `octaves=1` esetén
a mélység-szorzó mindig `1.0`, ezért ez visszamenőleg kompatibilis.

Lásd: docs/plugins/relief_generator/CRATER_RELIEF_GENERATOR.md,
ROADMAP Phase 11.2.
"""

from dataclasses import dataclass

from plugins.relief_generator.domain.crater_parameters import CraterParameters
from plugins.relief_generator.domain.height_field import HeightField
from plugins.relief_generator.domain.procedural_noise import VoronoiNoiseField


class CraterGenerator:
    """Crater Generator: rétegzett, `radius`-ra vágott, hatványfüggvénnyel
    torzított, mérettel arányosan sekélyedő Voronoi-távolság, a rétegek
    közül a legmélyebb (`min`) érték szerint kombinálva.

    A `generate()` `octaves` darab `VoronoiNoiseField`-et épít egyszer
    (nem lekérdezésenként), rétegenként `scale / lacunarity**i`
    rácsmérettel és `seed + i` maggal (a `GradientNoiseField`
    fraktál-kombinációjának mintáját követve), és ugyanehhez a réteghez
    egy `1 / lacunarity**i` mélység-szorzót rendel — majd minden
    lekérdezéskor a rétegek `radius`-ra vágott, `power`-re emelt, a
    saját mélység-szorzójukkal tompított értékei közül a legkisebbet
    (legmélyebbet) adja vissza.
    """

    def generate(self, parameters: CraterParameters) -> HeightField:
        """Előállít egy `HeightField`-et a megadott paraméterekből.

        Args:
            parameters: a Crater Generator érvényesített bemeneti
                paraméterei.

        Returns:
            A rétegzett, `radius`-ra vágott, `power`-re emelt és
            mérettel arányosan mélység-tompított profilok minimumát
            becsomagoló `HeightField`.
        """
        radius = parameters.radius
        power = parameters.power

        layers: list[tuple[VoronoiNoiseField, float]] = []
        layer_scale = parameters.scale
        depth = 1.0
        for i in range(parameters.octaves):
            noise = VoronoiNoiseField(scale=layer_scale, seed=parameters.seed + i)
            layers.append((noise, depth))
            layer_scale /= parameters.lacunarity
            depth /= parameters.lacunarity

        def height_function(x: float, y: float) -> float:
            best = 1.0
            for noise, layer_depth in layers:
                distance = noise.sample(x, y)
                if distance < radius:
                    normalized = distance / radius
                    # `float(...)`: a `float ** float` a typeshedben
                    # `Any`-t ad vissza (a komplex eredmény elméleti
                    # lehetősége miatt negatív bázis esetén) — a
                    # `normalized` viszont mindig [0,1)-be esik, ezért
                    # ez csak mypy --strict alatti típusjelölés,
                    # viselkedést nem változtat.
                    shape = float(normalized**power)
                    value = 1.0 - (1.0 - shape) * layer_depth
                    if value < best:
                        best = value
            return best

        return HeightField(height_function)


@dataclass(frozen=True)
class CraterHeightFieldSource:
    """A `HeightFieldSource` szerződés (ROADMAP Phase 11.1,
    `relief_generator_parameters.py`) Crater-megvalósítása — a
    `CraterParameters`-t és a `CraterGenerator`-t fogja össze, a
    `VoronoiHeightFieldSource` mintáját követve.
    """

    parameters: CraterParameters

    def build_height_field(self) -> HeightField:
        return CraterGenerator().generate(self.parameters)
