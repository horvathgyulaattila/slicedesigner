"""Dune Parameters — a Dune Generator felhasználói szintű bemeneti
paraméterei.

Ötödik, jóváhagyott tervezet (ROADMAP Phase 11.3) — a korábbi,
negyedik (periodikus, aszimmetrikus 1D gerinc-profilú) tervezetet
teljes egészében felváltja: l. docs/plugins/relief_generator/
DUNE_RELIEF_GENERATOR.md a négy elutasított korábbi tervezet
tanulságaihoz és a jelenlegi, kétrétegű (durva + finom domb-alap,
elülső/hátsó fodor, kétszintű foltosság) modellhez.

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

    A modell két fő rétegből áll — a domb-ALAPBÓL (durva + finom
    zajréteg, anizotróp koordináta-torzítással és lejtés-alapú
    aszimmetria-warppal) és a FODOR-rétegből (elülső/hátsó,
    kétszintű foltossággal) —, l. DUNE_RELIEF_GENERATOR.md 4. szakasz
    a teljes képletért.

    Attributes:
        direction: a szélirány, fokban — mind a domb-alap, mind a
            fodor erre az irányra épül. Bármely valós érték érvényes.
        seed: közös mag, amiből a nyolc belső `GradientNoiseField`
            (durva domb-alap, finomréteg, elülső/hátsó fodor-fázis-
            zavarás, elülső/hátsó domb-szintű foltosság, elülső/hátsó
            dombon-belüli foltosság) `seed`, `seed+1`, ..., `seed+7`
            értékeket kap, ebben a sorrendben. Bármely egész érték
            érvényes.
        coarse_scale: a durva domb-alap `GradientNoiseField`
            rácsmérete, az anizotróp torzítás UTÁN mintavételezve.
            Szigorúan pozitív.
        ridge_spacing: a domb-alap koordinátájának szorzója
            szélirányban — nagyobb érték sűrűbben egymás után
            következő gerinceket ad. Szigorúan pozitív.
        ridge_length: a domb-alap koordinátájának osztója
            keresztirányban — nagyobb érték hosszabban elnyúló
            (transzverzális) gerinceket ad. Szigorúan pozitív.
        asymmetry_strength: a domb-alap lejtés-alapú aszimmetria-
            warpjának erőssége — az ELŐJELE dönti el, melyik oldal
            lankás/meredek; `0` esetén a domb-alap szimmetrikus.
            Bármely valós érték érvényes.
        fine_scale: a finomréteg `GradientNoiseField` rácsmérete.
            Szigorúan pozitív.
        fine_octaves: a finomréteg fraktál-oktávjainak száma. `1`
            vagy nagyobb egész.
        fine_persistence: a finomréteg fraktál-kombinációjának
            amplitúdó-csökkenési aránya oktávonként. Szigorúan
            pozitív.
        fine_lacunarity: a finomréteg fraktál-kombinációjának
            frekvencia-növekedési aránya oktávonként. Szigorúan
            nagyobb, mint `1`.
        detail_weight: a finomréteg súlya a durva réteghez képest.
            Nem lehet negatív (`0` esetén a finomréteg nem
            érvényesül).
        ripple_wavelength_front: az elülső (lankás oldali) fodor
            hullámhossza. Szigorúan pozitív.
        ripple_amplitude_front: az elülső fodor mértéke. Nem lehet
            negatív.
        ripple_wavelength_back: a hátsó (meredek oldali) fodor
            hullámhossza. Szigorúan pozitív.
        ripple_amplitude_back: a hátsó fodor mértéke. Nem lehet
            negatív.
        ripple_warp_scale: mindkét fodor fázisát enyhén megzavaró
            `GradientNoiseField` rácsmérete. Szigorúan pozitív.
        ripple_warp_strength: a fázis-zavarás mértéke. Bármely valós
            érték lehet.
        blend_low: az elülső/hátsó fodor közti átmenet alsó
            (szélirányú lejtés-) küszöbe — ennél kisebb lejtésnél a
            fodor teljesen a hátsó mintát használja. Szigorúan
            kisebb, mint `blend_high`.
        blend_high: az átmenet felső küszöbe — ennél nagyobb
            lejtésnél a fodor teljesen az elülső mintát használja.
            Szigorúan nagyobb, mint `blend_low`.
        patch_dune_scale: a domb-szintű foltosság `GradientNoiseField`
            rácsmérete — ugyanabban az anizotróp koordináta-térben
            mintavételezve, mint a domb-alap. Szigorúan pozitív.
        patch_dune_low: a domb-szintű foltosság alsó küszöbe — ennél
            kisebb zajértéknél az adott gerinc(szakasz) teljesen
            kopasz. Szigorúan kisebb, mint `patch_dune_high`.
        patch_dune_high: a domb-szintű foltosság felső küszöbe —
            ennél nagyobb zajértéknél az adott gerinc(szakasz) a
            fodor teljes erősségét kapja. Szigorúan nagyobb, mint
            `patch_dune_low`.
        patch_within_scale: a dombon-belüli, finomabb foltosság-
            modulálás `GradientNoiseField` rácsmérete — önmagában
            sosem nullázza le a fodrot, csak ±50%-ban modulálja.
            Szigorúan pozitív.
    """

    direction: float
    seed: int
    coarse_scale: float
    ridge_spacing: float
    ridge_length: float
    asymmetry_strength: float
    fine_scale: float
    fine_octaves: int
    fine_persistence: float
    fine_lacunarity: float
    detail_weight: float
    ripple_wavelength_front: float
    ripple_amplitude_front: float
    ripple_wavelength_back: float
    ripple_amplitude_back: float
    ripple_warp_scale: float
    ripple_warp_strength: float
    blend_low: float
    blend_high: float
    patch_dune_scale: float
    patch_dune_low: float
    patch_dune_high: float
    patch_within_scale: float

    def __post_init__(self) -> None:
        if self.coarse_scale <= 0.0:
            raise DuneParametersValueError(
                "A coarse_scale-nek szigorúan pozitívnak kell lennie, "
                f"a kapott érték: {self.coarse_scale}."
            )
        if self.ridge_spacing <= 0.0:
            raise DuneParametersValueError(
                "A ridge_spacing-nek szigorúan pozitívnak kell lennie, "
                f"a kapott érték: {self.ridge_spacing}."
            )
        if self.ridge_length <= 0.0:
            raise DuneParametersValueError(
                "A ridge_length-nek szigorúan pozitívnak kell lennie, "
                f"a kapott érték: {self.ridge_length}."
            )
        if self.fine_scale <= 0.0:
            raise DuneParametersValueError(
                "A fine_scale-nek szigorúan pozitívnak kell lennie, "
                f"a kapott érték: {self.fine_scale}."
            )
        if self.fine_octaves < 1:
            raise DuneParametersValueError(
                "A fine_octaves-nak legalább 1-nek kell lennie, "
                f"a kapott érték: {self.fine_octaves}."
            )
        if self.fine_persistence <= 0.0:
            raise DuneParametersValueError(
                "A fine_persistence-nek szigorúan pozitívnak kell "
                f"lennie, a kapott érték: {self.fine_persistence}."
            )
        if self.fine_lacunarity <= 1.0:
            raise DuneParametersValueError(
                "A fine_lacunarity-nek szigorúan 1-nél nagyobbnak "
                f"kell lennie, a kapott érték: {self.fine_lacunarity}."
            )
        if self.detail_weight < 0.0:
            raise DuneParametersValueError(
                "A detail_weight nem lehet negatív, "
                f"a kapott érték: {self.detail_weight}."
            )
        if self.ripple_wavelength_front <= 0.0:
            raise DuneParametersValueError(
                "A ripple_wavelength_front-nak szigorúan pozitívnak "
                f"kell lennie, a kapott érték: {self.ripple_wavelength_front}."
            )
        if self.ripple_amplitude_front < 0.0:
            raise DuneParametersValueError(
                "A ripple_amplitude_front nem lehet negatív, "
                f"a kapott érték: {self.ripple_amplitude_front}."
            )
        if self.ripple_wavelength_back <= 0.0:
            raise DuneParametersValueError(
                "A ripple_wavelength_back-nak szigorúan pozitívnak "
                f"kell lennie, a kapott érték: {self.ripple_wavelength_back}."
            )
        if self.ripple_amplitude_back < 0.0:
            raise DuneParametersValueError(
                "A ripple_amplitude_back nem lehet negatív, "
                f"a kapott érték: {self.ripple_amplitude_back}."
            )
        if self.ripple_warp_scale <= 0.0:
            raise DuneParametersValueError(
                "A ripple_warp_scale-nek szigorúan pozitívnak kell "
                f"lennie, a kapott érték: {self.ripple_warp_scale}."
            )
        if self.blend_low >= self.blend_high:
            raise DuneParametersValueError(
                "A blend_low-nak szigorúan kisebbnek kell lennie, "
                "mint a blend_high — kapott értékek: "
                f"blend_low={self.blend_low}, blend_high={self.blend_high}."
            )
        if self.patch_dune_scale <= 0.0:
            raise DuneParametersValueError(
                "A patch_dune_scale-nek szigorúan pozitívnak kell "
                f"lennie, a kapott érték: {self.patch_dune_scale}."
            )
        if self.patch_dune_low >= self.patch_dune_high:
            raise DuneParametersValueError(
                "A patch_dune_low-nak szigorúan kisebbnek kell lennie, "
                "mint a patch_dune_high — kapott értékek: "
                f"patch_dune_low={self.patch_dune_low}, "
                f"patch_dune_high={self.patch_dune_high}."
            )
        if self.patch_within_scale <= 0.0:
            raise DuneParametersValueError(
                "A patch_within_scale-nek szigorúan pozitívnak kell "
                f"lennie, a kapott érték: {self.patch_within_scale}."
            )
