"""Tesztek a `WaveGenerator`-hoz.

Lásd: docs/plugins/relief_generator/WAVE_FUNCTION_MODEL.md 22–23. szakasz
(determinisztikus komponens-előállítás, normalizálási mintavételezés),
docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 21. szakasz
(2. tétel: Wave Generator).
"""

import math
import sys
from pathlib import Path

import pytest

# A `plugins/` névtér PEP 420 namespace package (l. ADR-0016: nincs
# `plugins/__init__.py`, hogy az egyes pluginok később önálló csomagként
# leválaszthatók legyenek). A meglévő `tests/gui/` és `tests/project/`
# csomagok (saját `__init__.py`-jal) miatt a teljes tesztkészlet együttes
# futtatásakor a pytest a repo gyökér előtt a `tests/` könyvtárat is
# felveszi a `sys.path`-ra, ami egy azonos nevű, üres `tests/plugins/`
# namespace-szegmenst hoz létre — enélkül a `plugins.relief_generator`
# tévesen a tesztfa alá, nem a valódi forráscsomagba oldódna fel. Ezért a
# repo gyökeret explicit módon a `sys.path` elejére kell tenni, mielőtt a
# `plugins.relief_generator` névtér először importálásra kerül.
_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from plugins.relief_generator.domain.wave_parameters import WaveParameters  # noqa: E402
from plugins.relief_generator.generators.wave_generator import (  # noqa: E402
    WaveGenerator,
)

# A `WaveGenerationError` a normalizáláshoz mintavételezett felület
# degenerált esetén (mintavételezett F_max == F_min) dobódik. Ez érvényes
# `WaveParameters`-ből közvetlenül nem provokálható ki, mivel a
# `WaveParameters` validációja `amplitude > 0`-t megkövetel, ami
# biztosítja, hogy a domináns (i=0) komponens amplitúdója sosem nulla,
# tehát a mintavételezett felület sosem lehet konstans. Emiatt ehhez a
# kivételhez itt szándékosan nincs teszt — a védőháló jelenleg tisztán
# elméleti (l. WAVE_FUNCTION_MODEL.md 23. szakasz).


def _grid_1d(resolution: int) -> list[float]:
    step = 1.0 / (resolution - 1)
    return [i * step for i in range(resolution)]


def test_generate_is_deterministic_across_repeated_calls() -> None:
    parameters = WaveParameters(
        wavelength=0.25,
        amplitude=1.0,
        direction=35.0,
        direction_spread=40.0,
        irregularity=0.6,
        complexity=0.7,
    )
    generator = WaveGenerator()

    first = generator.generate(parameters)
    second = generator.generate(parameters)

    sample_points = [(0.0, 0.0), (0.2, 0.9), (0.5, 0.5), (0.9, 0.2), (1.0, 1.0)]
    for x, y in sample_points:
        assert first.query(x, y) == second.query(x, y)


def test_generate_values_stay_within_unit_interval_and_reach_bounds() -> None:
    # direction=0° ⇒ a vetítés d(x,y) = x·cos(0) + y·sin(0) = x, azaz a
    # felület y-tól független. complexity=0.0 ⇒ n=1 (egyetlen komponens),
    # irregularity=0.0 ⇒ nincs jitter, tehát a nyers felület pontosan
    # F(x,y) = amplitude·sin(2π/wavelength·x). A wavelength=4.0 választás
    # mellett a sin argumentuma x=0-nál 0, x=1-nél π/2 — ezen a
    # tartományon a sin monoton növekvő, tehát a mintavételezett globális
    # minimum pontosan x=0-nál (F=0), a maximum pontosan x=1-nél
    # (F=amplitude) adódik, mindkettő eleme a 65x65-ös belső
    # normalizálási rácsnak és a lenti 21 pontos teszt-rácsnak is. Emiatt
    # a normalizált H(0,y)=0.0 és H(1,y)=1.0 egzaktul (lebegőpontos
    # tűréssel) várható, nem csak közelítőleg.
    parameters = WaveParameters(
        wavelength=4.0,
        amplitude=2.0,
        direction=0.0,
        direction_spread=0.0,
        irregularity=0.0,
        complexity=0.0,
    )
    height_field = WaveGenerator().generate(parameters)

    grid = _grid_1d(21)
    values = [height_field.query(x, y) for x in grid for y in grid]

    assert all(0.0 <= value <= 1.0 for value in values)
    assert min(values) == pytest.approx(0.0, abs=1e-9)
    assert max(values) == pytest.approx(1.0, abs=1e-9)


def test_generate_matches_analytic_single_component_formula() -> None:
    # complexity=0.0 ⇒ n=1, irregularity=0.0 ⇒ nincs jitter, ezért a
    # nyers felület pontosan az egykomponensű
    # A·sin(2π/λ·(x·cosθ+y·sinθ)+φ) alakot ölti, φ=0-val és θ=direction-nel.
    wavelength = 4.0
    amplitude = 2.0
    direction_deg = 0.0
    parameters = WaveParameters(
        wavelength=wavelength,
        amplitude=amplitude,
        direction=direction_deg,
        direction_spread=0.0,
        irregularity=0.0,
        complexity=0.0,
    )
    height_field = WaveGenerator().generate(parameters)

    x, y = 0.5, 0.3
    direction_rad = math.radians(direction_deg)
    projection = x * math.cos(direction_rad) + y * math.sin(direction_rad)
    raw = amplitude * math.sin(2.0 * math.pi / wavelength * projection)

    # A mintavételezett globális minimum/maximum (l. az előző teszt
    # kommentárja) pontosan 0.0, illetve `amplitude`, ezért a normalizált
    # érték pontosan `raw / amplitude`.
    expected = raw / amplitude

    assert height_field.query(x, y) == pytest.approx(expected, abs=1e-9)


# --- WaveParameters.function (ROADMAP Phase 10.2) ---


def test_generate_uses_function_field_for_automatic_components() -> None:
    # A `test_generate_matches_analytic_single_component_formula` már
    # implicit igazolja, hogy `function` explicit megadása nélkül (tehát
    # alapértelmezett `"Sinusoidal"` mellett) a generált `HeightField` a
    # 10.2 előtti, Sinusoidal-lal hardkódolt eredménnyel bitre azonos
    # (analitikus Sinusoidal-formulával egyezik). Ez a teszt azt igazolja,
    # hogy egy eltérő `function` ténylegesen más eredményt ad ugyanazon a
    # mintaponton.
    sinusoidal = WaveGenerator().generate(WaveParameters(**_BASE_KWARGS))
    triangle = WaveGenerator().generate(
        WaveParameters(**_BASE_KWARGS, function="Triangle")
    )

    x, y = 0.5, 0.3
    assert triangle.query(x, y) != pytest.approx(sinusoidal.query(x, y))


# --- WaveParameters.asymmetry_strength (ROADMAP Phase 12.2) ---


def test_generate_with_asymmetry_strength_differs_but_stays_in_unit_interval() -> None:
    parameters = WaveParameters(
        wavelength=0.25,
        amplitude=1.0,
        direction=35.0,
        direction_spread=40.0,
        irregularity=0.6,
        complexity=0.7,
    )
    without_asymmetry = WaveGenerator().generate(parameters)
    with_asymmetry = WaveGenerator().generate(
        WaveParameters(
            wavelength=0.25,
            amplitude=1.0,
            direction=35.0,
            direction_spread=40.0,
            irregularity=0.6,
            complexity=0.7,
            asymmetry_strength=0.8,
        )
    )

    sample_points = [(0.0, 0.0), (0.2, 0.9), (0.5, 0.5), (0.9, 0.2), (1.0, 1.0)]
    differs_somewhere = any(
        with_asymmetry.query(x, y) != pytest.approx(without_asymmetry.query(x, y))
        for x, y in sample_points
    )
    assert differs_somewhere
    for x, y in sample_points:
        assert 0.0 <= with_asymmetry.query(x, y) <= 1.0


# --- WaveParameters.envelope/distortion/sources tényleges bekötése (9.7.c) ---

_BASE_KWARGS = {
    "wavelength": 4.0,
    "amplitude": 2.0,
    "direction": 0.0,
    "direction_spread": 0.0,
    "irregularity": 0.0,
    "complexity": 0.0,
}


def test_generate_applies_shared_envelope_to_automatic_components() -> None:
    from plugins.relief_generator.domain.amplitude_envelope import (
        LinearFalloff,
        RadialAmplitudeEnvelope,
    )

    envelope = RadialAmplitudeEnvelope(
        center_x=0.0, center_y=0.0, radius=0.3, falloff=LinearFalloff()
    )
    without_envelope = WaveGenerator().generate(WaveParameters(**_BASE_KWARGS))
    with_envelope = WaveGenerator().generate(
        WaveParameters(**_BASE_KWARGS, envelope=envelope)
    )

    x, y = 0.9, 0.9
    assert with_envelope.query(x, y) != pytest.approx(without_envelope.query(x, y))


def test_generate_applies_shared_distortion_to_automatic_components() -> None:
    from plugins.relief_generator.domain.procedural_distortion import SwirlDistortion

    distortion = SwirlDistortion(center_x=0.0, center_y=0.0, radius=5.0, strength=1.5)
    without_distortion = WaveGenerator().generate(WaveParameters(**_BASE_KWARGS))
    with_distortion = WaveGenerator().generate(
        WaveParameters(**_BASE_KWARGS, distortion=distortion)
    )

    x, y = 0.5, 0.3
    assert with_distortion.query(x, y) != pytest.approx(without_distortion.query(x, y))


def test_generate_appends_explicit_sources_after_automatic_components() -> None:
    from plugins.relief_generator.domain.multiple_wave_sources import WaveSourceSpec

    source = WaveSourceSpec(
        source_type="Radial",
        amplitude=5.0,
        wavelength=0.2,
        phase=0.0,
        source_x=0.5,
        source_y=0.5,
    )
    without_source = WaveGenerator().generate(WaveParameters(**_BASE_KWARGS))
    with_source = WaveGenerator().generate(
        WaveParameters(**_BASE_KWARGS, sources=(source,))
    )

    x, y = 0.5, 0.5
    assert with_source.query(x, y) != pytest.approx(without_source.query(x, y))


def test_generate_is_deterministic_with_envelope_distortion_and_sources() -> None:
    from plugins.relief_generator.domain.amplitude_envelope import (
        LinearFalloff,
        RadialAmplitudeEnvelope,
    )
    from plugins.relief_generator.domain.multiple_wave_sources import WaveSourceSpec
    from plugins.relief_generator.domain.procedural_distortion import SwirlDistortion

    parameters = WaveParameters(
        wavelength=0.25,
        amplitude=1.0,
        direction=35.0,
        direction_spread=40.0,
        irregularity=0.6,
        complexity=0.7,
        envelope=RadialAmplitudeEnvelope(
            center_x=0.5, center_y=0.5, radius=0.6, falloff=LinearFalloff()
        ),
        distortion=SwirlDistortion(
            center_x=0.5, center_y=0.5, radius=0.4, strength=0.8
        ),
        sources=(
            WaveSourceSpec(
                source_type="Radial",
                amplitude=0.5,
                wavelength=0.3,
                phase=0.1,
                source_x=0.2,
                source_y=0.8,
            ),
        ),
    )
    generator = WaveGenerator()

    first = generator.generate(parameters)
    second = generator.generate(parameters)

    sample_points = [(0.0, 0.0), (0.2, 0.9), (0.5, 0.5), (0.9, 0.2), (1.0, 1.0)]
    for x, y in sample_points:
        assert first.query(x, y) == second.query(x, y)


# --- megosztott envelope/distortion és include_automatic (2026-08-21-i kiegészítés) ---


def test_generate_with_include_automatic_false_and_no_sources_raises() -> None:
    from plugins.relief_generator.exceptions import WaveSetValueError

    parameters = WaveParameters(**_BASE_KWARGS, include_automatic=False)

    with pytest.raises(WaveSetValueError):
        WaveGenerator().generate(parameters)


def test_generate_with_include_automatic_false_uses_only_explicit_sources() -> None:
    from plugins.relief_generator.domain.multiple_wave_sources import WaveSourceSpec

    source = WaveSourceSpec(
        source_type="Radial",
        amplitude=1.0,
        wavelength=0.2,
        phase=0.0,
        source_x=0.5,
        source_y=0.5,
    )
    parameters = WaveParameters(
        **_BASE_KWARGS, include_automatic=False, sources=(source,)
    )

    height_field = WaveGenerator().generate(parameters)

    assert 0.0 <= height_field.query(0.5, 0.5) <= 1.0


def test_generate_applies_shared_envelope_to_explicit_sources_too() -> None:
    from plugins.relief_generator.domain.amplitude_envelope import (
        LinearFalloff,
        RadialAmplitudeEnvelope,
    )
    from plugins.relief_generator.domain.multiple_wave_sources import WaveSourceSpec

    envelope = RadialAmplitudeEnvelope(
        center_x=0.0, center_y=0.0, radius=0.05, falloff=LinearFalloff()
    )
    source = WaveSourceSpec(
        source_type="Radial",
        amplitude=1.0,
        wavelength=0.1,
        phase=0.0,
        source_x=0.9,
        source_y=0.9,
    )
    without_envelope = WaveGenerator().generate(
        WaveParameters(**_BASE_KWARGS, include_automatic=False, sources=(source,))
    )
    with_envelope = WaveGenerator().generate(
        WaveParameters(
            **_BASE_KWARGS,
            include_automatic=False,
            sources=(source,),
            envelope=envelope,
        )
    )

    assert with_envelope.query(0.9, 0.9) != pytest.approx(
        without_envelope.query(0.9, 0.9)
    )
