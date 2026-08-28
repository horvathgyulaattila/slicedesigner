"""Wave Generator — az első matematikai felületgenerátor (Directional Wave).

A determinisztikus komponens-előállítási szabály és a normalizálási
mintavételezés szó szerinti forrása:
docs/plugins/relief_generator/WAVE_FUNCTION_MODEL.md 22–23. szakasz. A
Phase 9.1 (ROADMAP, WAVE_DOMAIN_MODEL.md) óta a komponensek a
komponensalapú `Wave`/`WaveSet` modellen keresztül épülnek fel és
értékelődnek ki (Sinusoidal WaveFunction, DirectionalPropagation,
UniformEnvelope, weight=1.0) — a megfigyelhető viselkedés a Phase 8-cal
változatlan (backward compatibility, WAVE_DOMAIN_MODEL.md 15. szakasz).
A Phase 9.7.c óta a `WaveParameters.envelope`/`distortion`/`sources`
mezői (ha meg vannak adva) ténylegesen befolyásolják az automatikusan
generált komponenseket, illetve a végső `WaveSet`-et. A 2026-08-21-i
kiegészítés (MULTIPLE_WAVE_SOURCES.md 9. szakasz) óta az `envelope`/
`distortion` az explicit `sources`-ból épülő komponensekre IS
alkalmazódik (ugyanazzal a megosztott példánnyal), és a `WaveParameters.
include_automatic=False` esetén az automatikus komponens-generálás
teljesen kimarad — l.
docs/plugins/relief_generator/WAVE_EXTENSION_IMPLEMENTATION_PLAN.md.
"""

import math
from dataclasses import dataclass
from typing import Callable

from plugins.relief_generator.domain.deterministic_components import (
    AMPLITUDE_JITTER_SCALE,
    GOLDEN_ANGLE_RAD,
    LACUNARITY,
    PERSISTENCE,
    PHASE_JITTER_SCALE,
    WAVELENGTH_JITTER_SCALE,
    component_count,
    rho,
)
from plugins.relief_generator.domain.height_field import HeightField
from plugins.relief_generator.domain.multiple_wave_sources import (
    build_combined_wave_set,
)
from plugins.relief_generator.domain.wave import (
    AmplitudeEnvelope,
    DirectionalPropagation,
    UniformEnvelope,
    Wave,
    WaveSet,
    build_wave_function,
)
from plugins.relief_generator.domain.wave_parameters import WaveParameters
from plugins.relief_generator.exceptions import WaveGenerationError

# Komponensszám, több léptékű komponensek, determinisztikus perturbáció:
# l. plugins/relief_generator/domain/deterministic_components.py
# (WAVE_FUNCTION_MODEL.md 22. szakasz) — megosztva a
# multiple_wave_sources.build_waves()-szel (ROADMAP Phase 10.3).

# Normalizálási mintavételezés (WAVE_FUNCTION_MODEL.md 23. szakasz).
_NORMALIZATION_SAMPLE_RESOLUTION = 65
"""A nyers `F(x,y)` szélsőértékeinek becsléséhez használt, `[0,1]x[0,1]`-en
felvett négyzetrács oldalankénti pontszáma. Belső implementációs részlet,
független a Mesh Generator felhasználó által vezérelt mintavételi
felbontásától."""


class WaveGenerator:
    """Directional Wave Generator: hullámkomponensekből épített Height Field.

    A `generate()` a `WaveParameters`-ből determinisztikusan, `random`
    modul vagy bármilyen implicit véletlenszám-állapot nélkül állítja
    elő a hullámkomponenseket `Wave` objektumokként, egy `WaveSet`-be
    gyűjtve (WAVE_FUNCTION_MODEL.md 22. szakasz; WAVE_DOMAIN_MODEL.md),
    majd ezek összegét normalizálja egy `[0,1]`-be eső `HeightField`-dé
    (WAVE_FUNCTION_MODEL.md 23. szakasz).
    """

    def generate(self, parameters: WaveParameters) -> HeightField:
        """Előállít egy normalizált `HeightField`-et a megadott paraméterekből.

        A komponensek egyszer kerülnek kiszámításra ezen hívás során; a
        visszaadott `HeightField` ezeket a már felépített `WaveSet`-et
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
            WaveSetValueError: ha `parameters.include_automatic` `False`
                ÉS `parameters.sources` üres — ekkor a végső `WaveSet`
                nulla komponenst tartalmazna, ami érvénytelen (l.
                `WaveSet.__post_init__`).
        """
        wave_set = self._build_wave_set(parameters)
        raw_height_function = self._make_raw_height_function(wave_set)

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

    def _build_wave_set(self, parameters: WaveParameters) -> WaveSet:
        """Kiszámítja a determinisztikus komponenslistát (ha
        `include_automatic`), majd az explicit forráslistával összefűzve
        épít `WaveSet`-et.

        Minden automatikusan generált komponens a `parameters.function`
        szerinti `WaveFunction`-nel (alapértelmezetten Sinusoidal),
        `DirectionalPropagation`-nel és `weight=1.0`-val épül. Ha
        `parameters.include_automatic` hamis, egyetlen automatikus
        komponens sem épül — a végső `WaveSet` kizárólag a
        `parameters.sources`-ból áll.

        Az `envelope` a `parameters.envelope`, ha meg van adva — ekkor
        egységesen minden komponensre (automatikus ÉS explicit)
        alkalmazódik —, különben `UniformEnvelope()`. A `distortion`
        hasonlóan a `parameters.distortion` (lehet `None`), szintén
        mindkét komponens-csoportra. Ez biztosítja a Phase 8 azonos
        konfigurációjú viselkedésével való egyezést, ha `envelope=None`
        és `distortion=None` (WAVE_DOMAIN_MODEL.md 15. szakasz).

        A `parameters.sources` az automatikusan generált komponensek
        UTÁN kerül a végső `WaveSet`-be (MULTIPLE_WAVE_SOURCES.md 5.
        szakasz sorrendje); üres `sources` és `include_automatic=True`
        esetén ez pontosan a korábbi, Phase 8/9.1–9.6-kompatibilis
        eredményt adja.

        Lásd: WAVE_FUNCTION_MODEL.md 22. szakasz,
        MULTIPLE_WAVE_SOURCES.md 9. szakasz (2026-08-21-i kiegészítés).
        """
        envelope: AmplitudeEnvelope = (
            parameters.envelope
            if parameters.envelope is not None
            else UniformEnvelope()
        )

        waves: list[Wave] = []
        if parameters.include_automatic:
            n = component_count(parameters.complexity)
            spread = parameters.direction_spread

            for i in range(n):
                amplitude = (
                    parameters.amplitude
                    * PERSISTENCE**i
                    * (
                        1.0
                        + parameters.irregularity * AMPLITUDE_JITTER_SCALE * rho(i, 0)
                    )
                )
                wavelength = (
                    parameters.wavelength
                    / LACUNARITY**i
                    * (
                        1.0
                        + parameters.irregularity * WAVELENGTH_JITTER_SCALE * rho(i, 1)
                    )
                )
                if n == 1:
                    direction_deg = parameters.direction
                else:
                    direction_deg = (parameters.direction - spread) + i * (
                        2.0 * spread / (n - 1)
                    )
                phase_jitter = (
                    parameters.irregularity
                    * PHASE_JITTER_SCALE
                    * rho(i, 2)
                    * 2.0
                    * math.pi
                )
                phase = (i * GOLDEN_ANGLE_RAD + phase_jitter) % (2.0 * math.pi)

                waves.append(
                    Wave(
                        amplitude=amplitude,
                        wavelength=wavelength,
                        phase=phase,
                        function=build_wave_function(parameters.function),
                        propagation=DirectionalPropagation(
                            direction_rad=math.radians(direction_deg)
                        ),
                        envelope=envelope,
                        weight=1.0,
                        distortion=parameters.distortion,
                    )
                )
        return build_combined_wave_set(
            tuple(waves),
            parameters.sources,
            envelope=envelope,
            distortion=parameters.distortion,
        )

    def _make_raw_height_function(
        self, wave_set: WaveSet
    ) -> Callable[[float, float], float]:
        """Becsomagolja a `WaveSet` kiértékelését egy nyers `F(x,y)` függvénybe.

        Lásd: WAVE_DOMAIN_MODEL.md 9.1 szakasz.
        """
        return wave_set.evaluate_raw

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


@dataclass(frozen=True)
class WaveHeightFieldSource:
    """A `HeightFieldSource` szerződés (ROADMAP Phase 11.1,
    `relief_generator_parameters.py`) Wave-megvalósítása — a
    `WaveParameters`-t és a `WaveGenerator`-t fogja össze.
    """

    parameters: WaveParameters

    def build_height_field(self) -> HeightField:
        return WaveGenerator().generate(self.parameters)
