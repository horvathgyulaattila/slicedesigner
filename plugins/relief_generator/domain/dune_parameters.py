"""Dune Parameters — a Dune Generator felhasználói szintű bemeneti
paraméterei.

Lásd: docs/plugins/relief_generator/DUNE_RELIEF_GENERATOR.md,
docs/plugins/relief_generator/PROCEDURAL_NOISE.md (a `GradientNoiseField`
domain-contractja, amire ez a generátor épül), ROADMAP Phase 11.3.
"""

from dataclasses import dataclass

from plugins.relief_generator.exceptions import DuneParametersValueError


@dataclass(frozen=True)
class DuneParameters:
    """A Dune Generator felhasználó által megadott bemeneti paraméterei.

    A létrehozott példány immutábilis (`frozen=True`); a mezők
    érvényességét a `__post_init__` fail-fast ellenőrzi.

    Attributes:
        dune_spacing: a dűnegerincek távolsága a szélirány mentén.
            Szigorúan pozitív.
        asymmetry: a gerinc-ciklus meredek (szélárnyékos, "hátsó")
            szakaszának aránya — pl. `0.25` esetén a ciklus 75%-a
            lankás emelkedés (szél felől), 25%-a meredek zuhanás
            (szél mögötti csusszanó lap). Szigorúan `(0, 1)` közötti.
        segment_scale: a gerinceket véges "testekre" tagoló
            `GradientNoiseField` rácsmérete — enélkül a gerincek
            végtelen, egyenletes hullámlemezként futnának; ez adja a
            valódi dűnemezőkre jellemző, egyedi, változó erősségű
            dűnetesteket. Szigorúan pozitív.
        ripple_wavelength: a hullámfodor térbeli hullámhossza, a
            szélirányra merőleges vetületi koordinátán mérve.
            Szigorúan pozitív.
        ripple_amplitude: a hullámfodor mértéke a domb-alap
            magasságtartományához képest — ténylegesen ennél kisebb
            mértékben érvényesül, mivel a szél-kitettséggel (l.
            `slope_sensitivity`) tompítva jelenik meg. Szigorúan
            pozitív.
        warp_scale: a fodor fázisát enyhén megzavaró
            `GradientNoiseField` rácsmérete — ez adja a fodor-vonalak
            szerves, nem tökéletesen egyenes lefutását. Szigorúan
            pozitív.
        warp_strength: a fázis-zavarás mértéke — bármely véges valós
            érték lehet; `0` esetén a fodor-vonalak tökéletesen
            egyenesek, a szélirányra merőlegesen.
        direction: a szélirány, fokban — mind a dűnegerincek, mind a
            hullámfodor erre az irányra épül (a gerincek erre
            merőlegesen futnak, a lejtés-számítás ebben az irányban
            történik). Bármely valós érték érvényes (nem normalizált
            `[0,360)`-ra).
        slope_sensitivity: mennyire élesen kapcsol be/ki a fodor a
            szélirányú lejtés alapján. Bármely valós érték érvényes
            (`0` esetén a fodor sehol sem jelenik meg).
        seed: a két belső zajmező (dűnetest-szegmentálás,
            fodor-fázis-zavarás) determinisztikus elhelyezését vezérlő
            egész szám — rendre `seed`, `seed+1` seeddel. Bármely
            egész érték érvényes.
    """

    dune_spacing: float
    asymmetry: float
    segment_scale: float
    ripple_wavelength: float
    ripple_amplitude: float
    warp_scale: float
    warp_strength: float
    direction: float
    slope_sensitivity: float
    seed: int

    def __post_init__(self) -> None:
        if self.dune_spacing <= 0.0:
            raise DuneParametersValueError(
                "A dune_spacing-nek szigorúan pozitívnak kell lennie, "
                f"a kapott érték: {self.dune_spacing}."
            )
        if not (0.0 < self.asymmetry < 1.0):
            raise DuneParametersValueError(
                "Az asymmetry-nek a (0, 1) tartományba kell esnie, "
                f"a kapott érték: {self.asymmetry}."
            )
        if self.segment_scale <= 0.0:
            raise DuneParametersValueError(
                "A segment_scale-nek szigorúan pozitívnak kell lennie, "
                f"a kapott érték: {self.segment_scale}."
            )
        if self.ripple_wavelength <= 0.0:
            raise DuneParametersValueError(
                "A ripple_wavelength-nek szigorúan pozitívnak kell "
                f"lennie, a kapott érték: {self.ripple_wavelength}."
            )
        if self.ripple_amplitude <= 0.0:
            raise DuneParametersValueError(
                "A ripple_amplitude-nek szigorúan pozitívnak kell "
                f"lennie, a kapott érték: {self.ripple_amplitude}."
            )
        if self.warp_scale <= 0.0:
            raise DuneParametersValueError(
                "A warp_scale-nek szigorúan pozitívnak kell lennie, "
                f"a kapott érték: {self.warp_scale}."
            )
