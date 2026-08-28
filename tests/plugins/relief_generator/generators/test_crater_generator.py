"""Tesztek a `CraterGenerator`-hoz és a `CraterHeightFieldSource`-hoz.

Lásd: docs/plugins/relief_generator/CRATER_RELIEF_GENERATOR.md, ROADMAP
Phase 11.2, tests/plugins/relief_generator/generators/test_wave_generator.py
(sys.path-minta).
"""

import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

import pytest  # noqa: E402

from plugins.relief_generator.domain.crater_parameters import (  # noqa: E402
    CraterParameters,
)
from plugins.relief_generator.domain.procedural_noise import (  # noqa: E402
    VoronoiNoiseField,
)
from plugins.relief_generator.generators.crater_generator import (  # noqa: E402
    CraterGenerator,
    CraterHeightFieldSource,
)


def test_generate_values_stay_within_unit_interval() -> None:
    parameters = CraterParameters(scale=0.2, seed=0, radius=0.4, power=3.0)
    height_field = CraterGenerator().generate(parameters)

    grid = [i / 10.0 for i in range(11)]
    values = [height_field.query(x, y) for x in grid for y in grid]

    assert all(0.0 <= value <= 1.0 for value in values)


def test_generate_is_deterministic_across_repeated_calls() -> None:
    parameters = CraterParameters(scale=0.15, seed=3, radius=0.4, power=2.5)
    generator = CraterGenerator()

    first = generator.generate(parameters)
    second = generator.generate(parameters)

    sample_points = [(0.0, 0.0), (0.2, 0.9), (0.5, 0.5), (0.9, 0.2), (1.0, 1.0)]
    for x, y in sample_points:
        assert first.query(x, y) == second.query(x, y)


def test_crater_center_reaches_near_zero_floor() -> None:
    # A legközelebbi magpont közelében a kráter alja h≈0.
    parameters = CraterParameters(scale=0.2, seed=0, radius=0.4, power=3.0)
    crater = CraterGenerator().generate(parameters)

    grid = [i / 100.0 for i in range(101)]
    minimum = min(crater.query(x, y) for x in grid for y in grid)

    assert minimum < 0.01


def test_beyond_radius_returns_undisturbed_baseline() -> None:
    # Kis radius mellett kell léteznie olyan pontnak, ami messze esik
    # minden magponttól — ott a felszín érintetlen (h=1.0).
    parameters = CraterParameters(scale=0.5, seed=0, radius=0.05, power=3.0)
    noise = VoronoiNoiseField(scale=0.5, seed=0)
    crater = CraterGenerator().generate(parameters)

    grid = [i / 20.0 for i in range(21)]
    far_points = [(x, y) for x in grid for y in grid if noise.sample(x, y) >= 0.05]

    assert far_points
    for x, y in far_points:
        assert crater.query(x, y) == 1.0


def test_higher_power_flattens_crater_floor() -> None:
    # Egy magasabb power a radius-on belül mindenütt kisebb vagy egyenlő
    # értéket ad, mint egy alacsonyabb power ugyanazon a ponton — a
    # kráterfenék ellaposodását igazolja.
    scale, seed, radius = 0.2, 0, 0.4
    low_power = CraterGenerator().generate(
        CraterParameters(scale=scale, seed=seed, radius=radius, power=1.5)
    )
    high_power = CraterGenerator().generate(
        CraterParameters(scale=scale, seed=seed, radius=radius, power=5.0)
    )

    grid = [i / 20.0 for i in range(1, 20)]
    for x in grid:
        for y in grid:
            assert high_power.query(x, y) <= low_power.query(x, y) + 1e-9


def test_different_seeds_produce_different_fields() -> None:
    a = CraterGenerator().generate(
        CraterParameters(scale=0.2, seed=0, radius=0.4, power=3.0)
    )
    b = CraterGenerator().generate(
        CraterParameters(scale=0.2, seed=1, radius=0.4, power=3.0)
    )

    assert a.query(0.5, 0.5) != b.query(0.5, 0.5)


def test_height_field_source_delegates_to_generator() -> None:
    parameters = CraterParameters(scale=0.2, seed=0, radius=0.4, power=3.0)
    source = CraterHeightFieldSource(parameters)

    height_field = source.build_height_field()
    expected = CraterGenerator().generate(parameters)

    sample_points = [(0.0, 0.0), (0.3, 0.7), (1.0, 1.0)]
    for x, y in sample_points:
        assert height_field.query(x, y) == expected.query(x, y)


def test_single_octave_matches_manual_single_layer_computation() -> None:
    # octaves=1 (alapérték) esetén pontosan az eredeti, egyrétegű
    # képlettel kell megegyeznie — visszamenőleges kompatibilitás.
    scale, seed, radius, power = 0.2, 0, 0.4, 3.0
    parameters = CraterParameters(scale=scale, seed=seed, radius=radius, power=power)
    crater = CraterGenerator().generate(parameters)
    noise = VoronoiNoiseField(scale=scale, seed=seed)

    sample_points = [(0.1, 0.1), (0.4, 0.6), (0.9, 0.9)]
    for x, y in sample_points:
        d = noise.sample(x, y)
        expected = 1.0 if d >= radius else (d / radius) ** power
        assert crater.query(x, y) == pytest.approx(expected)


def test_multiple_octaves_take_minimum_across_layers() -> None:
    # Több réteggel a kimenetnek pontosan a rétegenkénti (radius-ra
    # vágott, power-re emelt, majd a réteg saját mélység-szorzójával
    # tompított) értékek minimumával kell megegyeznie — a mélység-
    # szorzó is lacunarity-vel zsugorodik rétegenként, ugyanúgy, mint
    # a rácsméret.
    scale, seed, radius, power, lacunarity = 0.3, 0, 0.4, 3.0, 2.0
    parameters = CraterParameters(
        scale=scale,
        seed=seed,
        radius=radius,
        power=power,
        octaves=2,
        lacunarity=lacunarity,
    )
    crater = CraterGenerator().generate(parameters)

    noise0 = VoronoiNoiseField(scale=scale, seed=seed)
    noise1 = VoronoiNoiseField(scale=scale / lacunarity, seed=seed + 1)

    def layer_value(
        noise: VoronoiNoiseField, x: float, y: float, depth: float
    ) -> float:
        d = noise.sample(x, y)
        if d >= radius:
            return 1.0
        # `float(...)`: l. `crater_generator.py` azonos indoklású
        # megjegyzése — a `float ** float` a typeshedben `Any`-t ad
        # vissza, viselkedést nem változtat.
        shape = float((d / radius) ** power)
        return 1.0 - (1.0 - shape) * depth

    grid = [i / 10.0 for i in range(11)]
    for x in grid:
        for y in grid:
            expected = min(
                layer_value(noise0, x, y, 1.0),
                layer_value(noise1, x, y, 1.0 / lacunarity),
            )
            assert crater.query(x, y) == pytest.approx(expected)


def test_more_octaves_never_raises_the_height() -> None:
    # Több réteg csak mélyítheti (vagy változatlanul hagyhatja) a
    # felszínt egy adott ponton, sosem emelheti — a min-kombinálás
    # közvetlen következménye. Ez modellezi azt, hogy egy kisebb,
    # finomabb rétegből származó kráter "átütheti" egy nagyobb, durvább
    # réteg krátere alját.
    base = CraterGenerator().generate(
        CraterParameters(scale=0.2, seed=0, radius=0.4, power=3.0, octaves=1)
    )
    layered = CraterGenerator().generate(
        CraterParameters(
            scale=0.2, seed=0, radius=0.4, power=3.0, octaves=4, lacunarity=2.0
        )
    )

    grid = [i / 15.0 for i in range(16)]
    for x in grid:
        for y in grid:
            assert layered.query(x, y) <= base.query(x, y) + 1e-9


def test_finer_layer_crater_does_not_reach_full_depth_on_its_own() -> None:
    # Olyan pont keresése, ahol a finomabb (1. index, seed+1) réteg
    # nagyon mély (közel a saját magpontjához), de a durvább (0. index)
    # réteg nem ad ott mély értéket. Ekkor a kombinált eredménynek a
    # finomabb réteg saját, mérettel arányosan tompított mélységéhez
    # kell közelítenie — ami SOSEM éri el a 0-t, ellentétben azzal a
    # korábbi viselkedéssel, ahol minden réteg egyformán mélyre mehetett.
    scale, seed, radius, power, lacunarity = 0.3, 0, 0.4, 3.0, 2.0
    noise0 = VoronoiNoiseField(scale=scale, seed=seed)
    noise1 = VoronoiNoiseField(scale=scale / lacunarity, seed=seed + 1)

    grid = [i / 100.0 for i in range(101)]
    candidates = [
        (x, y)
        for x in grid
        for y in grid
        if noise1.sample(x, y) < 0.02 and noise0.sample(x, y) >= radius * 0.9
    ]
    assert candidates  # legyen legalább egy ilyen pont a rácson

    parameters = CraterParameters(
        scale=scale,
        seed=seed,
        radius=radius,
        power=power,
        octaves=2,
        lacunarity=lacunarity,
    )
    crater = CraterGenerator().generate(parameters)
    x, y = candidates[0]

    # A finom réteg elméleti padlója: 1 - 1/lacunarity = 0.5 (a power
    # hatása elhanyagolható, mivel d1 ≈ 0 → normalized ≈ 0 → shape ≈ 0).
    assert crater.query(x, y) > 0.4
    assert crater.query(x, y) < 1.0
