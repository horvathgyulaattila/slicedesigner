"""Dune Generator — kétrétegű domb-alap (durva, lejtés-alapú
aszimmetria-warppal torzított réteg + finom, torzítás nélküli
textúra-réteg) és elülső/hátsó, kétszintű foltossággal modulált
hullámfodor összege — szélfútta homokdűnék, transzverzális
elrendezésben (a gerincek a széllel keresztben futnak).

Ez az ötödik tervezet, és teljes egészében felváltja a negyediket. Az
első három tervezet (koordináta-alapú fodor-fázis; magasság-alapú
fodor-fázis; szélirányú/lejtő-kitettségű fodor izotróp domb-alappal)
és a negyedik (periodikus, aszimmetrikus 1D gerinc-profil, szegmentáló
zajmezővel) mind élő tesztelés során bizonyult elégtelennek — l.
docs/plugins/relief_generator/DUNE_RELIEF_GENERATOR.md 2. szakasz a
teljes történethez.

A negyedik tervezet kulcshibája: egy periodikus, egyetlen 1D-
koordinátától függő profilfüggvény (bármennyire aszimmetrikus is) nem
tudja visszaadni egy 2D zajmező szerves, véletlenszerű karakterét — ez
alapvetően más matematikai objektum. Az ötödik tervezet ezért a
domb-ALAPOT is zajmezőre építi — anizotróp koordináta-torzítással (a
gerincek a szélirányra merőlegesen nyúlnak meg) és egy, KIZÁRÓLAG az
egyoktávos, durva rétegre alkalmazott, lejtés-alapú domain-warppal éri
el az aszimmetriát (a teljes, több-oktávos mezőn ez a warp élő
kísérletezés során összegyűrődést okozott).

A fodor-réteg elülső (lankás, szél felőli) és hátsó (meredek,
szélárnyékos) oldalon ELTÉRŐ irányban fodrozódik — nem egy
"exposure"-maszkkal nullázva az egyik oldalt (ez korábbi kísérletben
egy nagy, mesterségesen kopasz sávot eredményezett), hanem a
szélirányú lejtés ELŐJELE alapján, lágy átmenettel keverve a két
mintát. Mindkét oldalon KÉTSZINTŰ, egymástól független foltosság
tompítja/erősíti a fodrot: egy domb-szintű (amivel akár egy teljes
gerinc is kopasz maradhat) és egy dombon-belüli, finomabb réteg —
enélkül a fodrozódás egyenletes, mesterséges "pizsama"-mintázatot
adott volna.

Lásd: docs/plugins/relief_generator/DUNE_RELIEF_GENERATOR.md, ROADMAP
Phase 11.3.
"""

import math
from dataclasses import dataclass

from plugins.relief_generator.domain.dune_parameters import DuneParameters
from plugins.relief_generator.domain.height_field import HeightField
from plugins.relief_generator.domain.procedural_noise import GradientNoiseField

_SLOPE_SAMPLE_EPSILON = 0.001
"""A szélirányú lejtés (aszimmetria-warp és elülső/hátsó keverés)
véges differenciás becsléséhez használt lépésköz, normalizált
`[0,1]x[0,1]` koordinátában. Belső implementációs részlet."""


def _smoothstep01(t: float) -> float:
    """Sima, `[0,1]`-re vágott interpoláció — `0` alatt `0`, `1`
    fölött `1`, közte köbös simítással."""
    clipped = min(max(t, 0.0), 1.0)
    return clipped * clipped * (3.0 - 2.0 * clipped)


class DuneGenerator:
    """Dune Generator: kétrétegű, anizotróp domb-alap + elülső/hátsó,
    kétszintű foltossággal modulált hullámfodor.

    A `generate()` nyolc `GradientNoiseField`-et épít egyszer (durva
    domb-alap, finomréteg, elülső/hátsó fodor-fázis-zavarás,
    elülső/hátsó domb-szintű foltosság, elülső/hátsó dombon-belüli
    foltosság), és előre kiszámolja a szélirány szinuszát/koszinuszát
    — majd minden lekérdezéskor a domb-alapból (véges differenciával)
    kiszámolt előjeles lejtés dönti el, mennyire érvényesül az
    elülső, illetve a hátsó fodor-minta, mindkettőt a saját,
    kétszintű foltosságával szorozva.
    """

    def generate(self, parameters: DuneParameters) -> HeightField:
        """Előállít egy `HeightField`-et a megadott paraméterekből.

        Args:
            parameters: a Dune Generator érvényesített bemeneti
                paraméterei.

        Returns:
            A kétrétegű domb-alap és az elülső/hátsó, foltosan
            modulált hullámfodor összegét, `[0,1]`-re vágva
            becsomagoló `HeightField`.
        """
        seed = parameters.seed
        coarse = GradientNoiseField(scale=parameters.coarse_scale, seed=seed)
        fine = GradientNoiseField(
            scale=parameters.fine_scale,
            seed=seed + 1,
            octaves=parameters.fine_octaves,
            persistence=parameters.fine_persistence,
            lacunarity=parameters.fine_lacunarity,
        )
        warp_front = GradientNoiseField(
            scale=parameters.ripple_warp_scale, seed=seed + 2
        )
        warp_back = GradientNoiseField(
            scale=parameters.ripple_warp_scale, seed=seed + 3
        )
        patch_dune_front = GradientNoiseField(
            scale=parameters.patch_dune_scale, seed=seed + 4
        )
        patch_dune_back = GradientNoiseField(
            scale=parameters.patch_dune_scale, seed=seed + 5
        )
        patch_within_front = GradientNoiseField(
            scale=parameters.patch_within_scale, seed=seed + 6
        )
        patch_within_back = GradientNoiseField(
            scale=parameters.patch_within_scale, seed=seed + 7
        )

        ridge_spacing = parameters.ridge_spacing
        ridge_length = parameters.ridge_length
        asymmetry_strength = parameters.asymmetry_strength
        detail_weight = parameters.detail_weight
        ripple_wavelength_front = parameters.ripple_wavelength_front
        ripple_amplitude_front = parameters.ripple_amplitude_front
        ripple_wavelength_back = parameters.ripple_wavelength_back
        ripple_amplitude_back = parameters.ripple_amplitude_back
        ripple_warp_strength = parameters.ripple_warp_strength
        blend_low = parameters.blend_low
        blend_high = parameters.blend_high
        patch_dune_low = parameters.patch_dune_low
        patch_dune_high = parameters.patch_dune_high
        direction_rad = math.radians(parameters.direction)
        cos_theta = math.cos(direction_rad)
        sin_theta = math.sin(direction_rad)
        eps = _SLOPE_SAMPLE_EPSILON

        def base_height(x: float, y: float) -> float:
            u = x * cos_theta + y * sin_theta
            v = -x * sin_theta + y * cos_theta
            uu = u * ridge_spacing
            vv = v / ridge_length
            if asymmetry_strength != 0.0:
                slope = (
                    coarse.sample(uu + eps, vv) - coarse.sample(uu - eps, vv)
                ) / (2.0 * eps)
                uu = uu - asymmetry_strength * slope
            base = coarse.sample(uu, vv)
            detail = fine.sample(u * ridge_spacing, v / ridge_length)
            return base + detail_weight * detail

        def height_function(x: float, y: float) -> float:
            base = base_height(x, y)

            forward = base_height(x + eps * cos_theta, y + eps * sin_theta)
            backward = base_height(x - eps * cos_theta, y - eps * sin_theta)
            slope = (forward - backward) / (2.0 * eps)
            blend = _smoothstep01((slope - blend_low) / (blend_high - blend_low))

            u = x * cos_theta + y * sin_theta
            v = -x * sin_theta + y * cos_theta
            uu_patch = u * ridge_spacing
            vv_patch = v / ridge_length

            dune_front = _smoothstep01(
                (patch_dune_front.sample(uu_patch, vv_patch) - patch_dune_low)
                / (patch_dune_high - patch_dune_low)
            )
            dune_back = _smoothstep01(
                (patch_dune_back.sample(uu_patch, vv_patch) - patch_dune_low)
                / (patch_dune_high - patch_dune_low)
            )
            within_front = 0.5 + 0.5 * patch_within_front.sample(x, y)
            within_back = 0.5 + 0.5 * patch_within_back.sample(x, y)
            patch_front = dune_front * within_front
            patch_back = dune_back * within_back

            phase_front = v + ripple_warp_strength * warp_front.sample(x, y)
            phase_back = u + ripple_warp_strength * warp_back.sample(x, y)
            ripple_front = math.sin(
                2.0 * math.pi / ripple_wavelength_front * phase_front
            )
            ripple_back = math.sin(2.0 * math.pi / ripple_wavelength_back * phase_back)

            raw = (
                base
                + blend * ripple_amplitude_front * patch_front * ripple_front
                + (1.0 - blend) * ripple_amplitude_back * patch_back * ripple_back
            )
            normalized = 0.5 + 0.5 * raw
            return min(max(normalized, 0.0), 1.0)

        return HeightField(height_function)


@dataclass(frozen=True)
class DuneHeightFieldSource:
    """A `HeightFieldSource` szerződés (ROADMAP Phase 11.1,
    `relief_generator_parameters.py`) Dune-megvalósítása — a
    `VoronoiHeightFieldSource`/`CraterHeightFieldSource` mintáját
    követve.
    """

    parameters: DuneParameters

    def build_height_field(self) -> HeightField:
        return DuneGenerator().generate(self.parameters)
