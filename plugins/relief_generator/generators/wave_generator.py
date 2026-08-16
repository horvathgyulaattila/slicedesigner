"""Wave Generator — az első matematikai felületgenerátor (Directional Wave).

A determinisztikus komponens-előállítási szabály és a normalizálási
mintavételezés szó szerinti forrása:
docs/plugins/relief_generator/WAVE_FUNCTION_MODEL.md 22–23. szakasz.
"""

import math
from dataclasses import dataclass
from typing import Callable

from plugins.relief_generator.domain.height_field import HeightField
from plugins.relief_generator.domain.wave_parameters import WaveParameters
from plugins.relief_generator.exceptions import WaveGenerationError

# Komponensszám (WAVE_FUNCTION_MODEL.md 22. szakasz, "Komponensszám").
MIN_COMPONENTS = 1
"""A `complexity = 0.0`-hoz tartozó legkisebb komponensszám."""

MAX_COMPONENTS = 5
"""A `complexity = 1.0`-hoz tartozó legnagyobb komponensszám."""

# Több léptékű komponensek (WAVE_FUNCTION_MODEL.md 8. és 22. szakasz).
PERSISTENCE = 0.5
"""Az egymást követő komponensek amplitúdó-csökkenési aránya
(`A_i ∝ PERSISTENCE**i`)."""

LACUNARITY = 2.0
"""Az egymást követő komponensek hullámhossz-csökkenési aránya
(`λ_i ∝ 1/LACUNARITY**i`)."""

# Determinisztikus perturbáció (WAVE_FUNCTION_MODEL.md 22. szakasz, "ρ(i, salt)").
GOLDEN_RATIO = 1.618033988749895
"""Az aranymetszés-arány (φ), a `ρ(i, salt)` perturbációs segédfüggvény alapja."""

GOLDEN_ANGLE_RAD = 2.399963229728653
"""Az aranyszög radiánban, a fázisok determinisztikus, jól szóródó elosztásához."""

AMPLITUDE_JITTER_SCALE = 0.5
"""Az `irregularity` amplitúdóra gyakorolt hatásának skálázója (`A_JITTER`)."""

WAVELENGTH_JITTER_SCALE = 0.3
"""Az `irregularity` hullámhosszra gyakorolt hatásának skálázója (`λ_JITTER`)."""

PHASE_JITTER_SCALE = 1.0
"""Az `irregularity` fázisra gyakorolt hatásának skálázója (`φ_JITTER`)."""

# Normalizálási mintavételezés (WAVE_FUNCTION_MODEL.md 23. szakasz).
_NORMALIZATION_SAMPLE_RESOLUTION = 65
"""A nyers `F(x,y)` szélsőértékeinek becsléséhez használt, `[0,1]x[0,1]`-en
felvett négyzetrács oldalankénti pontszáma. Belső implementációs részlet,
független a Mesh Generator felhasználó által vezérelt mintavételi
felbontásától."""


@dataclass(frozen=True)
class _WaveComponent:
    """Egy már kiszámított, konkrét hullámkomponens.

    Belső implementációs részlet: a `WaveGenerator.generate` egyszer
    számítja ki a komponenseket, majd a visszaadott `HeightField` ezeket
    a már lezárt (closure-ben rögzített) értékeket használja minden
    egyes lekérdezéskor.

    Attributes:
        amplitude: a komponens amplitúdója (`A_i`).
        wavelength: a komponens hullámhossza (`λ_i`).
        direction_rad: a komponens iránya radiánban (`θ_i`, már fokból
            konvertálva).
        phase: a komponens fázisa radiánban, a `[0, 2π)` intervallumból
            (`φ_i`).
    """

    amplitude: float
    wavelength: float
    direction_rad: float
    phase: float


class WaveGenerator:
    """Directional Wave Generator: hullámkomponensekből épített Height Field.

    A `generate()` a `WaveParameters`-ből determinisztikusan, `random`
    modul vagy bármilyen implicit véletlenszám-állapot nélkül állítja
    elő a hullámkomponenseket (WAVE_FUNCTION_MODEL.md 22. szakasz), majd
    ezek összegét normalizálja egy `[0,1]`-be eső `HeightField`-dé
    (WAVE_FUNCTION_MODEL.md 23. szakasz).
    """

    def generate(self, parameters: WaveParameters) -> HeightField:
        """Előállít egy normalizált `HeightField`-et a megadott paraméterekből.

        A komponensek egyszer kerülnek kiszámításra ezen hívás során; a
        visszaadott `HeightField` ezeket a már kiszámított komponenseket
        lezáró (closure) függvényt csomagol be, nem számítja újra őket
        lekérdezésenként.

        Args:
            parameters: a Directional Wave Generator érvényesített
                bemeneti paraméterei.

        Returns:
            A komponensek összegéből, a felület tényleges mintavételezett
            minimum- és maximumértéke alapján `[0,1]`-re normalizált
            `HeightField`.

        Raises:
            WaveGenerationError: ha a normalizáláshoz mintavételezett
                felület degenerált (a mintavételezett maximum és minimum
                megegyezik). Érvényes `WaveParameters` mellett elméletileg
                nem fordulhat elő, mivel `amplitude > 0` validált.
        """
        components = self._build_components(parameters)
        raw_height_function = self._make_raw_height_function(components)

        raw_min, raw_max = self._sample_extrema(raw_height_function)
        if raw_max == raw_min:
            raise WaveGenerationError(
                "A mintavételezett felület degenerált: a becsült minimum és "
                f"maximum egyaránt {raw_min}. Normalizálás nem végezhető el."
            )

        def normalized_height_function(x: float, y: float) -> float:
            raw = raw_height_function(x, y)
            normalized = (raw - raw_min) / (raw_max - raw_min)
            return min(max(normalized, 0.0), 1.0)

        return HeightField(normalized_height_function)

    def _build_components(self, parameters: WaveParameters) -> list[_WaveComponent]:
        """Kiszámítja a determinisztikus komponenslistát.

        Lásd: WAVE_FUNCTION_MODEL.md 22. szakasz.
        """
        component_count = MIN_COMPONENTS + round(
            parameters.complexity * (MAX_COMPONENTS - MIN_COMPONENTS)
        )
        spread = parameters.direction_spread

        components: list[_WaveComponent] = []
        for i in range(component_count):
            amplitude = (
                parameters.amplitude
                * PERSISTENCE**i
                * (1.0 + parameters.irregularity * AMPLITUDE_JITTER_SCALE * _rho(i, 0))
            )
            wavelength = (
                parameters.wavelength
                / LACUNARITY**i
                * (1.0 + parameters.irregularity * WAVELENGTH_JITTER_SCALE * _rho(i, 1))
            )
            if component_count == 1:
                direction_deg = parameters.direction
            else:
                direction_deg = (parameters.direction - spread) + i * (
                    2.0 * spread / (component_count - 1)
                )
            phase_jitter = (
                parameters.irregularity
                * PHASE_JITTER_SCALE
                * _rho(i, 2)
                * 2.0
                * math.pi
            )
            phase = (i * GOLDEN_ANGLE_RAD + phase_jitter) % (2.0 * math.pi)

            components.append(
                _WaveComponent(
                    amplitude=amplitude,
                    wavelength=wavelength,
                    direction_rad=math.radians(direction_deg),
                    phase=phase,
                )
            )
        return components

    def _make_raw_height_function(
        self, components: list[_WaveComponent]
    ) -> Callable[[float, float], float]:
        """Becsomagolja a komponensek összegét egy nyers `F(x,y)` függvénybe.

        Lásd: WAVE_FUNCTION_MODEL.md 2. szakasz.
        """

        def raw_height_function(x: float, y: float) -> float:
            total = 0.0
            for component in components:
                projection = x * math.cos(component.direction_rad) + y * math.sin(
                    component.direction_rad
                )
                total += component.amplitude * math.sin(
                    2.0 * math.pi / component.wavelength * projection + component.phase
                )
            return total

        return raw_height_function

    def _sample_extrema(
        self, raw_height_function: Callable[[float, float], float]
    ) -> tuple[float, float]:
        """Becsli `F_min`/`F_max`-ot egy fix `65x65` rácson.

        Lásd: WAVE_FUNCTION_MODEL.md 23. szakasz.
        """
        resolution = _NORMALIZATION_SAMPLE_RESOLUTION
        step = 1.0 / (resolution - 1)

        raw_min = math.inf
        raw_max = -math.inf
        for row in range(resolution):
            y = row * step
            for col in range(resolution):
                x = col * step
                value = raw_height_function(x, y)
                raw_min = min(raw_min, value)
                raw_max = max(raw_max, value)
        return raw_min, raw_max


def _rho(index: int, salt: int) -> float:
    """Determinisztikus, `[-1,1]`-be eső perturbációs érték (`ρ(i, salt)`).

    Lásd: WAVE_FUNCTION_MODEL.md 22. szakasz. `random` modult vagy
    bármilyen implicit véletlenszám-állapotot nem használ: kizárólag az
    `index` és a `salt` értékétől függő, aranymetszés-arányon alapuló,
    jól szóródó sorozat.

    Args:
        index: a komponens indexe (`i >= 0`).
        salt: a felhasználási helyet megkülönböztető konstans (amplitúdó:
            `0`, hullámhossz: `1`, fázis: `2`).

    Returns:
        A `[-1.0, 1.0]` zárt intervallumba eső, determinisztikus érték.
    """
    scaled = (index + 1 + salt) * GOLDEN_RATIO
    fractional_part = scaled - math.floor(scaled)
    return 2.0 * fractional_part - 1.0
