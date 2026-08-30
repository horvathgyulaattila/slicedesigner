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

_VALID_KWARGS = dict(
    direction=40.0,
    seed=0,
    coarse_scale=0.2,
    ridge_spacing=0.9,
    ridge_length=3.0,
    asymmetry_strength=-0.012,
    fine_scale=0.11,
    fine_octaves=2,
    fine_persistence=0.5,
    fine_lacunarity=2.0,
    detail_weight=0.15,
    ripple_wavelength_front=0.035,
    ripple_amplitude_front=0.055,
    ripple_wavelength_back=0.025,
    ripple_amplitude_back=0.06,
    ripple_warp_scale=0.04,
    ripple_warp_strength=0.015,
    blend_low=-6.0,
    blend_high=6.0,
    patch_dune_scale=0.2,
    patch_dune_low=-0.5,
    patch_dune_high=0.5,
    patch_within_scale=0.16,
)


def _with(**overrides: object) -> DuneParameters:
    kwargs = dict(_VALID_KWARGS)
    kwargs.update(overrides)
    return DuneParameters(**kwargs)  # type: ignore[arg-type]


def _smoothstep01(t: float) -> float:
    clipped = min(max(t, 0.0), 1.0)
    return clipped * clipped * (3.0 - 2.0 * clipped)


def _manual_expected(x: float, y: float, parameters: DuneParameters) -> float:
    seed = parameters.seed
    coarse = GradientNoiseField(scale=parameters.coarse_scale, seed=seed)
    fine = GradientNoiseField(
        scale=parameters.fine_scale,
        seed=seed + 1,
        octaves=parameters.fine_octaves,
        persistence=parameters.fine_persistence,
        lacunarity=parameters.fine_lacunarity,
    )
    warp_front = GradientNoiseField(scale=parameters.ripple_warp_scale, seed=seed + 2)
    warp_back = GradientNoiseField(scale=parameters.ripple_warp_scale, seed=seed + 3)
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

    theta = math.radians(parameters.direction)
    cos_t, sin_t = math.cos(theta), math.sin(theta)

    def base_height(px: float, py: float) -> float:
        u = px * cos_t + py * sin_t
        v = -px * sin_t + py * cos_t
        uu = u * parameters.ridge_spacing
        vv = v / parameters.ridge_length
        if parameters.asymmetry_strength != 0.0:
            slope = (
                coarse.sample(uu + _EPS, vv) - coarse.sample(uu - _EPS, vv)
            ) / (2.0 * _EPS)
            uu = uu - parameters.asymmetry_strength * slope
        base = coarse.sample(uu, vv)
        detail = fine.sample(u * parameters.ridge_spacing, v / parameters.ridge_length)
        return base + parameters.detail_weight * detail

    base = base_height(x, y)
    forward = base_height(x + _EPS * cos_t, y + _EPS * sin_t)
    backward = base_height(x - _EPS * cos_t, y - _EPS * sin_t)
    slope = (forward - backward) / (2.0 * _EPS)
    blend = _smoothstep01(
        (slope - parameters.blend_low) / (parameters.blend_high - parameters.blend_low)
    )

    u = x * cos_t + y * sin_t
    v = -x * sin_t + y * cos_t
    uu_patch = u * parameters.ridge_spacing
    vv_patch = v / parameters.ridge_length

    dune_front = _smoothstep01(
        (patch_dune_front.sample(uu_patch, vv_patch) - parameters.patch_dune_low)
        / (parameters.patch_dune_high - parameters.patch_dune_low)
    )
    dune_back = _smoothstep01(
        (patch_dune_back.sample(uu_patch, vv_patch) - parameters.patch_dune_low)
        / (parameters.patch_dune_high - parameters.patch_dune_low)
    )
    within_front = 0.5 + 0.5 * patch_within_front.sample(x, y)
    within_back = 0.5 + 0.5 * patch_within_back.sample(x, y)
    patch_front = dune_front * within_front
    patch_back = dune_back * within_back

    phase_front = v + parameters.ripple_warp_strength * warp_front.sample(x, y)
    phase_back = u + parameters.ripple_warp_strength * warp_back.sample(x, y)
    ripple_front = math.sin(
        2.0 * math.pi / parameters.ripple_wavelength_front * phase_front
    )
    ripple_back = math.sin(
        2.0 * math.pi / parameters.ripple_wavelength_back * phase_back
    )

    raw = (
        base
        + blend * parameters.ripple_amplitude_front * patch_front * ripple_front
        + (1.0 - blend) * parameters.ripple_amplitude_back * patch_back * ripple_back
    )
    return min(max(0.5 + 0.5 * raw, 0.0), 1.0)


def test_generate_values_stay_within_unit_interval() -> None:
    parameters = _with()
    height_field = DuneGenerator().generate(parameters)

    grid = [i / 20.0 for i in range(21)]
    values = [height_field.query(x, y) for x in grid for y in grid]

    assert all(0.0 <= value <= 1.0 for value in values)


def test_generate_is_deterministic_across_repeated_calls() -> None:
    parameters = _with(direction=60.0, seed=3)
    generator = DuneGenerator()

    first = generator.generate(parameters)
    second = generator.generate(parameters)

    sample_points = [(0.0, 0.0), (0.2, 0.9), (0.5, 0.5), (0.9, 0.2), (1.0, 1.0)]
    for x, y in sample_points:
        assert first.query(x, y) == second.query(x, y)


def test_matches_manual_formula() -> None:
    # A kimenetnek pontosan meg kell egyeznie a teljes képlettel: a
    # kétrétegű, anizotróp domb-alap, plusz az elülső/hátsó,
    # kétszintű foltossággal modulált hullámfodor, [0,1]-re vágva.
    parameters = _with()
    dune = DuneGenerator().generate(parameters)

    grid = [i / 10.0 for i in range(11)]
    for x in grid:
        for y in grid:
            expected = _manual_expected(x, y, parameters)
            assert dune.query(x, y) == pytest.approx(expected, abs=1e-9)


def test_different_seeds_produce_different_fields() -> None:
    a = DuneGenerator().generate(_with(seed=0))
    b = DuneGenerator().generate(_with(seed=1))

    assert a.query(0.5, 0.5) != b.query(0.5, 0.5)


def test_height_field_source_delegates_to_generator() -> None:
    parameters = _with()
    source = DuneHeightFieldSource(parameters)

    height_field = source.build_height_field()
    expected = DuneGenerator().generate(parameters)

    sample_points = [(0.0, 0.0), (0.3, 0.7), (1.0, 1.0)]
    for x, y in sample_points:
        assert height_field.query(x, y) == expected.query(x, y)


def test_higher_ripple_amplitude_front_increases_value_range() -> None:
    small = DuneGenerator().generate(_with(ripple_amplitude_front=0.01))
    large = DuneGenerator().generate(_with(ripple_amplitude_front=0.3))

    grid = [i / 30.0 for i in range(31)]
    small_values = [small.query(x, y) for x in grid for y in grid]
    large_values = [large.query(x, y) for x in grid for y in grid]

    assert (max(large_values) - min(large_values)) > (
        max(small_values) - min(small_values)
    )


def test_zero_detail_weight_removes_fine_layer_contribution() -> None:
    # detail_weight=0 esetén a finomréteg (fine_scale) semmilyen
    # módosítást nem okozhat a kimeneten — ez igazolja, hogy a
    # detail_weight ténylegesen kikapcsolja a finomréteg hozzájárulását.
    a = DuneGenerator().generate(_with(detail_weight=0.0, fine_scale=0.11))
    b = DuneGenerator().generate(_with(detail_weight=0.0, fine_scale=0.4))

    grid = [i / 15.0 for i in range(16)]
    for x in grid:
        for y in grid:
            assert a.query(x, y) == pytest.approx(b.query(x, y), abs=1e-12)


def test_zero_asymmetry_strength_leaves_coordinate_unwarped() -> None:
    symmetric = _with(asymmetry_strength=0.0)
    asymmetric = _with(asymmetry_strength=-0.012)

    a = DuneGenerator().generate(symmetric)
    b = DuneGenerator().generate(asymmetric)

    grid = [i / 15.0 for i in range(16)]
    values_a = [a.query(x, y) for x in grid for y in grid]
    values_b = [b.query(x, y) for x in grid for y in grid]

    assert values_a != values_b
