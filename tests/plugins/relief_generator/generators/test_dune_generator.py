"""Tesztek a `DuneGenerator`-hoz és a `DuneHeightFieldSource`-hoz.

Lásd: docs/plugins/relief_generator/DUNE_RELIEF_GENERATOR.md, ROADMAP
Phase 11.3, tests/plugins/relief_generator/generators/test_wave_generator.py
(sys.path-minta).
"""

import math
import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

import pytest  # noqa: E402

from plugins.relief_generator.domain.dune_parameters import (  # noqa: E402
    DuneParameters,
)
from plugins.relief_generator.domain.procedural_noise import (  # noqa: E402
    GradientNoiseField,
)
from plugins.relief_generator.generators.dune_generator import (  # noqa: E402
    DuneGenerator,
    DuneHeightFieldSource,
)

_EPS = 0.001
_RIDGE_HEIGHT = 0.9


def _ridge_profile(u: float, dune_spacing: float, asymmetry: float) -> float:
    t = (u / dune_spacing) % 1.0
    if t < 1.0 - asymmetry:
        local = t / (1.0 - asymmetry)
        return 0.5 - 0.5 * math.cos(math.pi * local)
    local = (t - (1.0 - asymmetry)) / asymmetry
    return 0.5 + 0.5 * math.cos(math.pi * local)


def _manual_expected(
    x: float,
    y: float,
    segment_noise: GradientNoiseField,
    warp_noise: GradientNoiseField,
    dune_spacing: float,
    asymmetry: float,
    ripple_wavelength: float,
    ripple_amplitude: float,
    warp_strength: float,
    direction: float,
    slope_sensitivity: float,
) -> float:
    theta = math.radians(direction)
    cos_t, sin_t = math.cos(theta), math.sin(theta)

    def base_height(px: float, py: float) -> float:
        u = px * cos_t + py * sin_t
        ridge = _ridge_profile(u, dune_spacing, asymmetry)
        segment = 0.5 + 0.5 * segment_noise.sample(px, py)
        return 0.5 + _RIDGE_HEIGHT * (ridge - 0.5) * segment

    base = base_height(x, y)
    forward = base_height(x + _EPS * cos_t, y + _EPS * sin_t)
    backward = base_height(x - _EPS * cos_t, y - _EPS * sin_t)
    slope = (forward - backward) / (2.0 * _EPS)
    wind_exposure = min(max(slope * slope_sensitivity, 0.0), 1.0)

    phase = x * cos_t + y * sin_t + warp_strength * warp_noise.sample(x, y)
    ripple = math.sin(2.0 * math.pi / ripple_wavelength * phase)

    return min(max(base + ripple_amplitude * wind_exposure * ripple, 0.0), 1.0)


def test_generate_values_stay_within_unit_interval() -> None:
    parameters = DuneParameters(
        dune_spacing=0.3,
        asymmetry=0.25,
        segment_scale=0.5,
        ripple_wavelength=0.03,
        ripple_amplitude=0.08,
        warp_scale=0.15,
        warp_strength=0.02,
        direction=30.0,
        slope_sensitivity=3.0,
        seed=0,
    )
    height_field = DuneGenerator().generate(parameters)

    grid = [i / 20.0 for i in range(21)]
    values = [height_field.query(x, y) for x in grid for y in grid]

    assert all(0.0 <= value <= 1.0 for value in values)


def test_generate_is_deterministic_across_repeated_calls() -> None:
    parameters = DuneParameters(
        dune_spacing=0.25,
        asymmetry=0.3,
        segment_scale=0.4,
        ripple_wavelength=0.04,
        ripple_amplitude=0.1,
        warp_scale=0.2,
        warp_strength=0.03,
        direction=60.0,
        slope_sensitivity=2.0,
        seed=3,
    )
    generator = DuneGenerator()

    first = generator.generate(parameters)
    second = generator.generate(parameters)

    sample_points = [(0.0, 0.0), (0.2, 0.9), (0.5, 0.5), (0.9, 0.2), (1.0, 1.0)]
    for x, y in sample_points:
        assert first.query(x, y) == second.query(x, y)


def test_matches_manual_formula() -> None:
    # A kimenetnek pontosan meg kell egyeznie a teljes képlettel: a
    # szélirány menti, aszimmetrikus, szegmentált gerinc-profil, plusz
    # a szélirányra merőleges, lejtő-kitettséggel tompított hullámfodor,
    # [0,1]-re vágva.
    dune_spacing, asymmetry, segment_scale = 0.3, 0.25, 0.5
    ripple_wavelength, ripple_amplitude = 0.03, 0.08
    warp_scale, warp_strength = 0.15, 0.02
    direction, slope_sensitivity, seed = 40.0, 3.0, 0
    parameters = DuneParameters(
        dune_spacing=dune_spacing,
        asymmetry=asymmetry,
        segment_scale=segment_scale,
        ripple_wavelength=ripple_wavelength,
        ripple_amplitude=ripple_amplitude,
        warp_scale=warp_scale,
        warp_strength=warp_strength,
        direction=direction,
        slope_sensitivity=slope_sensitivity,
        seed=seed,
    )
    dune = DuneGenerator().generate(parameters)

    segment_noise = GradientNoiseField(scale=segment_scale, seed=seed)
    warp_noise = GradientNoiseField(scale=warp_scale, seed=seed + 1)

    grid = [i / 10.0 for i in range(11)]
    for x in grid:
        for y in grid:
            expected = _manual_expected(
                x,
                y,
                segment_noise,
                warp_noise,
                dune_spacing,
                asymmetry,
                ripple_wavelength,
                ripple_amplitude,
                warp_strength,
                direction,
                slope_sensitivity,
            )
            assert dune.query(x, y) == pytest.approx(expected, abs=1e-9)


def test_ridge_profile_is_steeper_on_leeward_side() -> None:
    # Az aszimmetrikus gerinc-profil hátsó (szélárnyékos) szakasza
    # rövidebb távolság alatt fut le, mint amennyi a lankás (szél
    # felőli) szakasz felfutásához kell — ez igazolja a kért
    # aszimmetriát (lankás elöl, meredek hátul).
    dune_spacing, asymmetry = 0.3, 0.25
    windward_span = dune_spacing * (1.0 - asymmetry)
    leeward_span = dune_spacing * asymmetry

    assert leeward_span < windward_span

    crest = _ridge_profile(windward_span - 1e-9, dune_spacing, asymmetry)
    valley = _ridge_profile(dune_spacing - 1e-9, dune_spacing, asymmetry)
    assert crest == pytest.approx(1.0, abs=1e-3)
    assert valley == pytest.approx(0.0, abs=1e-3)


def test_zero_slope_sensitivity_removes_ripple_everywhere() -> None:
    dune_spacing, asymmetry, segment_scale, seed = 0.3, 0.25, 0.5, 0
    parameters = DuneParameters(
        dune_spacing=dune_spacing,
        asymmetry=asymmetry,
        segment_scale=segment_scale,
        ripple_wavelength=0.03,
        ripple_amplitude=0.08,
        warp_scale=0.15,
        warp_strength=0.02,
        direction=30.0,
        slope_sensitivity=0.0,
        seed=seed,
    )
    dune = DuneGenerator().generate(parameters)
    segment_noise = GradientNoiseField(scale=segment_scale, seed=seed)

    theta = math.radians(30.0)
    cos_t, sin_t = math.cos(theta), math.sin(theta)

    grid = [i / 10.0 for i in range(11)]
    for x in grid:
        for y in grid:
            u = x * cos_t + y * sin_t
            ridge = _ridge_profile(u, dune_spacing, asymmetry)
            segment = 0.5 + 0.5 * segment_noise.sample(x, y)
            expected_base = 0.5 + _RIDGE_HEIGHT * (ridge - 0.5) * segment
            assert dune.query(x, y) == pytest.approx(expected_base, abs=1e-9)


def test_different_seeds_produce_different_fields() -> None:
    a = DuneGenerator().generate(
        DuneParameters(
            dune_spacing=0.3,
            asymmetry=0.25,
            segment_scale=0.5,
            ripple_wavelength=0.03,
            ripple_amplitude=0.08,
            warp_scale=0.15,
            warp_strength=0.02,
            direction=0.0,
            slope_sensitivity=3.0,
            seed=0,
        )
    )
    b = DuneGenerator().generate(
        DuneParameters(
            dune_spacing=0.3,
            asymmetry=0.25,
            segment_scale=0.5,
            ripple_wavelength=0.03,
            ripple_amplitude=0.08,
            warp_scale=0.15,
            warp_strength=0.02,
            direction=0.0,
            slope_sensitivity=3.0,
            seed=1,
        )
    )

    assert a.query(0.5, 0.5) != b.query(0.5, 0.5)


def test_height_field_source_delegates_to_generator() -> None:
    parameters = DuneParameters(
        dune_spacing=0.3,
        asymmetry=0.25,
        segment_scale=0.5,
        ripple_wavelength=0.03,
        ripple_amplitude=0.08,
        warp_scale=0.15,
        warp_strength=0.02,
        direction=0.0,
        slope_sensitivity=3.0,
        seed=0,
    )
    source = DuneHeightFieldSource(parameters)

    height_field = source.build_height_field()
    expected = DuneGenerator().generate(parameters)

    sample_points = [(0.0, 0.0), (0.3, 0.7), (1.0, 1.0)]
    for x, y in sample_points:
        assert height_field.query(x, y) == expected.query(x, y)


def test_higher_ripple_amplitude_increases_value_range() -> None:
    small = DuneGenerator().generate(
        DuneParameters(
            dune_spacing=0.3,
            asymmetry=0.25,
            segment_scale=0.5,
            ripple_wavelength=0.03,
            ripple_amplitude=0.02,
            warp_scale=0.15,
            warp_strength=0.02,
            direction=0.0,
            slope_sensitivity=3.0,
            seed=0,
        )
    )
    large = DuneGenerator().generate(
        DuneParameters(
            dune_spacing=0.3,
            asymmetry=0.25,
            segment_scale=0.5,
            ripple_wavelength=0.03,
            ripple_amplitude=0.15,
            warp_scale=0.15,
            warp_strength=0.02,
            direction=0.0,
            slope_sensitivity=3.0,
            seed=0,
        )
    )

    grid = [i / 30.0 for i in range(31)]
    small_values = [small.query(x, y) for x in grid for y in grid]
    large_values = [large.query(x, y) for x in grid for y in grid]

    assert (max(large_values) - min(large_values)) > (
        max(small_values) - min(small_values)
    )
