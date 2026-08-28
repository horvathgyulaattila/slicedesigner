"""Crater Parameters — a Crater Generator felhasználói szintű bemeneti
paraméterei.

Lásd: docs/plugins/relief_generator/CRATER_RELIEF_GENERATOR.md,
docs/plugins/relief_generator/PROCEDURAL_NOISE.md (a `VoronoiNoiseField`
domain-contractja, amire ez a generátor épül), ROADMAP Phase 11.2.
"""

from dataclasses import dataclass

from plugins.relief_generator.exceptions import CraterParametersValueError


@dataclass(frozen=True)
class CraterParameters:
    """A Crater Generator felhasználó által megadott bemeneti paraméterei.

    A létrehozott példány immutábilis (`frozen=True`); a mezők
    érvényességét a `__post_init__` fail-fast ellenőrzi.

    Attributes:
        scale: a legdurvább (első) réteg Voronoi-magpontjainak
            rácsmérete, normalizált koordinátaegységben. A finomabb
            rétegek (`octaves > 1`) ebből a `lacunarity` szerint,
            rétegenként zsugorodó rácsméretet kapnak. Szigorúan
            pozitív.
        seed: a magpontok determinisztikus elhelyezését vezérlő egész
            szám — a `i`-edik réteg `seed + i`-t kap, a
            `GradientNoiseField` fraktál-kombinációjának mintáját
            követve. Bármely egész érték érvényes.
        radius: egy réteg kráterének tényleges kiterjedése, AZ ADOTT
            RÉTEG saját, normalizált `[0,1]` táv-értékén mérve — ezen a
            küszöbön túl az adott réteg nem ad mélyedést. Mivel a
            küszöb mindig a réteg saját rácsméretéhez relatív, a
            rétegenként zsugorodó rácsmérettel a kráterek abszolút
            mérete is arányosan zsugorodik — nincs szükség külön
            méret-szórás paraméterre. Szigorúan `0`-nál nagyobb és
            legfeljebb `1.0`.
        power: a kráterprofil élességét vezérlő kitevő — minden
            rétegre azonosan alkalmazva. Szigorúan pozitív.
        octaves: a rétegzett méretskálák száma (`1` esetén nincs
            rétegzés — pontosan az eredeti, egyrétegű viselkedés).
            Szigorúan pozitív egész.
        lacunarity: a rétegenkénti rácsméret-ÉS-mélység-zsugorodás
            mértéke (`scale_i = scale / lacunarity^i`,
            `depth_i = 1 / lacunarity^i`) — a `GradientNoiseField`
            azonos nevű mezőjének mintáját követi. Nincs külön
            "mélység-csillapítás" paraméter: mivel a valódi
            holdkráterek mélysége nagyjából arányos az átmérőjükkel, a
            méretskálát vezérlő `lacunarity` a mélységskálát is egyben
            vezérli — a finomabb (kisebb) rétegek krátere arányosan
            sekélyebb is. Szigorúan `1.0`-nál nagyobb.
    """

    scale: float
    seed: int
    radius: float
    power: float
    octaves: int = 1
    lacunarity: float = 2.0

    def __post_init__(self) -> None:
        if self.scale <= 0.0:
            raise CraterParametersValueError(
                "A scale-nek szigorúan pozitívnak kell lennie, "
                f"a kapott érték: {self.scale}."
            )
        if not (0.0 < self.radius <= 1.0):
            raise CraterParametersValueError(
                "A radius-nak a (0, 1] tartományba kell esnie, "
                f"a kapott érték: {self.radius}."
            )
        if self.power <= 0.0:
            raise CraterParametersValueError(
                "A power-nek szigorúan pozitívnak kell lennie, "
                f"a kapott érték: {self.power}."
            )
        if self.octaves < 1:
            raise CraterParametersValueError(
                "Az octaves-nek legalább 1-nek kell lennie, "
                f"a kapott érték: {self.octaves}."
            )
        if self.lacunarity <= 1.0:
            raise CraterParametersValueError(
                "A lacunarity-nak szigorúan 1.0-nál nagyobbnak kell "
                f"lennie, a kapott érték: {self.lacunarity}."
            )
