"""Dune Generator — anizotróp, szélirány-mentén aszimmetrikus
dűnegerinc-profil (lankás szél felőli emelkedés, meredek hátsó
csusszanó lap), véges "testekre" tagolva, és a szélirányra merőleges,
a gerincek szél felőli, emelkedő oldalain teljes erővel, a
szélárnyékos oldalakon elhalványuló hullámfodorral kiegészítve —
szélfútta homokdűnék.

Három korábbi tervezet is elégtelennek bizonyult, mindegyik élő
tesztelés során derült ki: (1) a fodor fázisa térbeli (x,y)
koordinátától függött, teljesen függetlenül a domb-alaktól; (2) a
fodor fázisa a domb-alap MAGASSÁGÁBÓL indult ki, ami koncentrikus
szintvonal-gyűrűkbe zárt minden dombot; (3) a fodor iránya és
erőssége már helyesen a szélhez kötődött, de maga a domb-ALAP egy
irány-független (izotróp) `GradientNoiseField` volt — a valódi
dűnéknek viszont a szél mentén nézve lankás/hosszú, arra merőlegesen
nézve éles/keskeny, ÉS aszimmetrikus (lankás elöl, meredek hátul)
alakjuk van, amit egy izotróp zajmező nem tud kifejezni.

A negyedik, jelenlegi tervezet a domb-ALAPOT is a szélirányhoz köti:
egy periodikus, aszimmetrikus profilfüggvény a szélirány menti
koordinátán (nem zajmező), egy második, nagy léptékű zajmezővel
véges "testekre" szegmentálva.

Lásd: docs/plugins/relief_generator/DUNE_RELIEF_GENERATOR.md, ROADMAP
Phase 11.3.
"""

import math
from dataclasses import dataclass

from plugins.relief_generator.domain.dune_parameters import DuneParameters
from plugins.relief_generator.domain.height_field import HeightField
from plugins.relief_generator.domain.procedural_noise import GradientNoiseField

_SLOPE_SAMPLE_EPSILON = 0.001
"""A szélirányú lejtés véges differenciás becsléséhez használt lépésköz,
normalizált `[0,1]x[0,1]` koordinátában. Belső implementációs részlet."""

_RIDGE_HEIGHT = 0.9
"""A dűnegerinc-profil teljes magasság-kilengése (a `0.5` körüli
maximális eltérés kétszerese) — belső, nem felhasználó által állítható
konstans; a `segment_scale` zajmező ennél kisebbre tompíthatja egy
adott ponton."""


class DuneGenerator:
    """Dune Generator: anizotróp, szegmentált dűnegerinc-profil +
    szélirányú, lejtő-kitettség szerint tompított hullámfodor összege.

    A `generate()` két `GradientNoiseField`-et épít egyszer (a
    dűnetest-szegmentálás és a fodor-fázis-zavarás), és előre
    kiszámolja a szélirány szinuszát/koszinuszát — majd minden
    lekérdezéskor a szélirány menti pozícióból egy aszimmetrikus,
    periodikus gerinc-profilt olvas ki, a szegmentáló zajmezővel
    tompítja, hozzáadja az irányított, lejtő-kitettséggel tompított
    hullámfodrot, és `[0,1]`-re vágja az eredményt.
    """

    def generate(self, parameters: DuneParameters) -> HeightField:
        """Előállít egy `HeightField`-et a megadott paraméterekből.

        Args:
            parameters: a Dune Generator érvényesített bemeneti
                paraméterei.

        Returns:
            A szegmentált dűnegerinc-profil és a szélirányú
            hullámfodor összegét, `[0,1]`-re vágva becsomagoló
            `HeightField`.
        """
        segment_noise = GradientNoiseField(
            scale=parameters.segment_scale, seed=parameters.seed
        )
        warp_noise = GradientNoiseField(
            scale=parameters.warp_scale, seed=parameters.seed + 1
        )
        dune_spacing = parameters.dune_spacing
        asymmetry = parameters.asymmetry
        wavelength = parameters.ripple_wavelength
        amplitude = parameters.ripple_amplitude
        warp_strength = parameters.warp_strength
        slope_sensitivity = parameters.slope_sensitivity
        direction_rad = math.radians(parameters.direction)
        cos_theta = math.cos(direction_rad)
        sin_theta = math.sin(direction_rad)
        eps = _SLOPE_SAMPLE_EPSILON

        def ridge_profile(u: float) -> float:
            t = (u / dune_spacing) % 1.0
            if t < 1.0 - asymmetry:
                local = t / (1.0 - asymmetry)
                return 0.5 - 0.5 * math.cos(math.pi * local)
            local = (t - (1.0 - asymmetry)) / asymmetry
            return 0.5 + 0.5 * math.cos(math.pi * local)

        def base_height(x: float, y: float) -> float:
            u = x * cos_theta + y * sin_theta
            ridge = ridge_profile(u)
            segment = 0.5 + 0.5 * segment_noise.sample(x, y)
            return 0.5 + _RIDGE_HEIGHT * (ridge - 0.5) * segment

        def height_function(x: float, y: float) -> float:
            base = base_height(x, y)

            forward = base_height(x + eps * cos_theta, y + eps * sin_theta)
            backward = base_height(x - eps * cos_theta, y - eps * sin_theta)
            slope = (forward - backward) / (2.0 * eps)
            wind_exposure = min(max(slope * slope_sensitivity, 0.0), 1.0)

            phase = (
                x * cos_theta + y * sin_theta + warp_strength * warp_noise.sample(x, y)
            )
            ripple = math.sin(2.0 * math.pi / wavelength * phase)

            raw = base + amplitude * wind_exposure * ripple
            return min(max(raw, 0.0), 1.0)

        return HeightField(height_function)


@dataclass(frozen=True)
class DuneHeightFieldSource:
    """A `HeightFieldSource` szerződés (ROADMAP Phase 11.1,
    `relief_generator_parameters.py`) Dune-megvalósítása — a
    `DuneParameters`-t és a `DuneGenerator`-t fogja össze, a
    `VoronoiHeightFieldSource`/`CraterHeightFieldSource` mintáját
    követve.
    """

    parameters: DuneParameters

    def build_height_field(self) -> HeightField:
        return DuneGenerator().generate(self.parameters)
