"""Wood Grain Parameters — a Wood Grain Generator felhasználói szintű
bemeneti paraméterei.

Lásd: docs/plugins/relief_generator/WOOD_GRAIN_RELIEF_GENERATOR.md,
docs/plugins/relief_generator/PROCEDURAL_NOISE.md (a `GradientNoiseField`
domain-contractja, amire ez a generátor épül), ROADMAP Phase 11.4.
"""

from dataclasses import dataclass

from plugins.relief_generator.exceptions import WoodGrainParametersValueError


@dataclass(frozen=True)
class WoodGrainParameters:
    """A Wood Grain Generator felhasználó által megadott bemeneti
    paraméterei.

    A létrehozott példány immutábilis (`frozen=True`); a mezők
    érvényességét a `__post_init__` fail-fast ellenőrzi.

    A modell a kereszt-szál koordinátát `board_width` szerinti
    "deszkákra" tagolja; minden deszka determinisztikusan, a
    `board_idx`-ből és a közös `seed`-ből hash-elt saját flóderosságot
    (`elongation`), "bél"-pozíciót és csomókat kap — l.
    WOOD_GRAIN_RELIEF_GENERATOR.md 3. szakasz a teljes képletért.

    Attributes:
        direction: a szálirány, fokban. Bármely valós érték érvényes.
        seed: a deszkánkénti/csomónkénti hash-elt jellemzők, valamint a
            "bél"-vonal enyhe zajos hullámzását adó `GradientNoiseField`
            közös magja. Bármely egész érték érvényes.
        board_width: egy "deszka" szélessége a kereszt-szál
            koordinátán. Szigorúan pozitív.
        ring_spacing: az évgyűrű-mintázat legdurvább (első) rétegének
            periódusa. Szigorúan pozitív.
        ring_octaves: az évgyűrű-mintázat fraktál-oktávjainak száma —
            ez adja a valós fán mért, erősen szórt gyűrűtávolságot.
            `1` vagy nagyobb egész.
        ring_persistence: az oktávok amplitúdó-csökkenési aránya.
            Szigorúan pozitív.
        ring_lacunarity: az oktávok frekvencia-növekedési aránya.
            Szigorúan nagyobb, mint `1`.
        elongation_min: a deszkánkénti flóderosság-tartomány alsó
            határa (kis érték = erősen íves, "flóderos" mintázat).
            Szigorúan pozitív, kisebb, mint `elongation_max`.
        elongation_max: a flóderosság-tartomány felső határa (nagy
            érték = nyugodt, majdnem egyenes szálirány). Nagyobb, mint
            `elongation_min`.
        warp_scale: a "bél"-vonal szerves hullámzását adó
            `GradientNoiseField` rácsmérete. Szigorúan pozitív.
        warp_strength: a hullámzás mértéke. Bármely valós érték lehet.
        knot_count_max: egy deszkán belül a csomók maximális száma (a
            tényleges szám deszkánként hash-elt, `0`-tól
            `knot_count_max`-ig egyenletesen). Nem lehet negatív.
        knot_size_min: a csomók magsugarának alsó határa. Szigorúan
            pozitív, kisebb, mint `knot_size_max`.
        knot_size_max: a csomók magsugarának felső határa. Nagyobb,
            mint `knot_size_min`. A tényleges méret négyzetesen a
            kicsi felé húzva sorsolódik (a valóságban a legtöbb csomó
            kicsi).
        knot_ghost_probability: annak valószínűsége, hogy egy csomó
            "szellem" — csak a fő rost gyűrődése látszik körülötte,
            saját mag/bütürepedés nélkül. `[0, 1]` tartományba eső.
        ring_contrast: az évgyűrű-mintázat (és a csomó-mélyedések)
            erőssége a `0.5` középérték körül — kisebb érték
            visszafogottabb, laposabb reliefet ad. Nem lehet negatív.
    """

    direction: float
    seed: int
    board_width: float
    ring_spacing: float
    ring_octaves: int
    ring_persistence: float
    ring_lacunarity: float
    elongation_min: float
    elongation_max: float
    warp_scale: float
    warp_strength: float
    knot_count_max: int
    knot_size_min: float
    knot_size_max: float
    knot_ghost_probability: float
    ring_contrast: float

    def __post_init__(self) -> None:
        if self.board_width <= 0.0:
            raise WoodGrainParametersValueError(
                "A board_width-nek szigorúan pozitívnak kell lennie, "
                f"a kapott érték: {self.board_width}."
            )
        if self.ring_spacing <= 0.0:
            raise WoodGrainParametersValueError(
                "A ring_spacing-nek szigorúan pozitívnak kell lennie, "
                f"a kapott érték: {self.ring_spacing}."
            )
        if self.ring_octaves < 1:
            raise WoodGrainParametersValueError(
                "A ring_octaves-nak legalább 1-nek kell lennie, "
                f"a kapott érték: {self.ring_octaves}."
            )
        if self.ring_persistence <= 0.0:
            raise WoodGrainParametersValueError(
                "A ring_persistence-nek szigorúan pozitívnak kell "
                f"lennie, a kapott érték: {self.ring_persistence}."
            )
        if self.ring_lacunarity <= 1.0:
            raise WoodGrainParametersValueError(
                "A ring_lacunarity-nak szigorúan 1-nél nagyobbnak kell "
                f"lennie, a kapott érték: {self.ring_lacunarity}."
            )
        if self.elongation_min <= 0.0:
            raise WoodGrainParametersValueError(
                "Az elongation_min-nek szigorúan pozitívnak kell "
                f"lennie, a kapott érték: {self.elongation_min}."
            )
        if self.elongation_max <= self.elongation_min:
            raise WoodGrainParametersValueError(
                "Az elongation_max-nak szigorúan nagyobbnak kell "
                "lennie, mint az elongation_min — kapott értékek: "
                f"elongation_min={self.elongation_min}, "
                f"elongation_max={self.elongation_max}."
            )
        if self.warp_scale <= 0.0:
            raise WoodGrainParametersValueError(
                "A warp_scale-nek szigorúan pozitívnak kell lennie, "
                f"a kapott érték: {self.warp_scale}."
            )
        if self.knot_count_max < 0:
            raise WoodGrainParametersValueError(
                "A knot_count_max nem lehet negatív, "
                f"a kapott érték: {self.knot_count_max}."
            )
        if self.knot_size_min <= 0.0:
            raise WoodGrainParametersValueError(
                "A knot_size_min-nek szigorúan pozitívnak kell lennie, "
                f"a kapott érték: {self.knot_size_min}."
            )
        if self.knot_size_max <= self.knot_size_min:
            raise WoodGrainParametersValueError(
                "A knot_size_max-nak szigorúan nagyobbnak kell lennie, "
                "mint a knot_size_min — kapott értékek: "
                f"knot_size_min={self.knot_size_min}, "
                f"knot_size_max={self.knot_size_max}."
            )
        if not (0.0 <= self.knot_ghost_probability <= 1.0):
            raise WoodGrainParametersValueError(
                "A knot_ghost_probability-nak a [0, 1] tartományba "
                f"kell esnie, a kapott érték: {self.knot_ghost_probability}."
            )
        if self.ring_contrast < 0.0:
            raise WoodGrainParametersValueError(
                "A ring_contrast nem lehet negatív, "
                f"a kapott érték: {self.ring_contrast}."
            )
