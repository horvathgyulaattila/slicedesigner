"""Tesztek a `VoronoiGenerator`-hoz és a `VoronoiHeightFieldSource`-hoz.

Lásd: docs/plugins/relief_generator/VORONOI_RELIEF_GENERATOR.md, ROADMAP
Phase 11.1, tests/plugins/relief_generator/generators/test_wave_generator.py
(sys.path-minta).
"""

import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from plugins.relief_generator.domain.voronoi_parameters import (  # noqa: E402
    VoronoiParameters,
)
from plugins.relief_generator.generators.voronoi_generator import (  # noqa: E402
    VoronoiGenerator,
    VoronoiHeightFieldSource,
)


def test_generate_values_stay_within_unit_interval() -> None:
    parameters = VoronoiParameters(scale=0.2, seed=0)
    height_field = VoronoiGenerator().generate(parameters)

    grid = [i / 10.0 for i in range(11)]
    values = [height_field.query(x, y) for x in grid for y in grid]

    assert all(0.0 <= value <= 1.0 for value in values)


def test_generate_is_deterministic_across_repeated_calls() -> None:
    parameters = VoronoiParameters(scale=0.15, seed=3)
    generator = VoronoiGenerator()

    first = generator.generate(parameters)
    second = generator.generate(parameters)

    sample_points = [(0.0, 0.0), (0.2, 0.9), (0.5, 0.5), (0.9, 0.2), (1.0, 1.0)]
    for x, y in sample_points:
        assert first.query(x, y) == second.query(x, y)


def test_different_seeds_produce_different_fields() -> None:
    a = VoronoiGenerator().generate(VoronoiParameters(scale=0.2, seed=0))
    b = VoronoiGenerator().generate(VoronoiParameters(scale=0.2, seed=1))

    assert a.query(0.5, 0.5) != b.query(0.5, 0.5)


def test_height_field_source_delegates_to_generator() -> None:
    parameters = VoronoiParameters(scale=0.2, seed=0)
    source = VoronoiHeightFieldSource(parameters)

    height_field = source.build_height_field()
    expected = VoronoiGenerator().generate(parameters)

    sample_points = [(0.0, 0.0), (0.3, 0.7), (1.0, 1.0)]
    for x, y in sample_points:
        assert height_field.query(x, y) == expected.query(x, y)
