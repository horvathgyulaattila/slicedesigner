"""Tesztek a GradientNoiseField/VoronoiNoiseField-hez (ROADMAP Phase 10.4).

Lásd: docs/plugins/relief_generator/PROCEDURAL_NOISE.md.
"""

import sys
from pathlib import Path

import pytest

# A `plugins/` névtér PEP 420 namespace package (l. ADR-0016). L. a
# `test_wave.py`/`test_procedural_distortion.py` azonos mintáját.
_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from plugins.relief_generator.domain.procedural_noise import (  # noqa: E402
    GradientNoiseField,
    VoronoiNoiseField,
)
from plugins.relief_generator.exceptions import ProceduralNoiseValueError  # noqa: E402

_SAMPLE_POINTS = [
    (0.0, 0.0),
    (0.3, 0.7),
    (1.5, -2.5),
    (-4.2, 3.1),
    (10.0, 10.0),
    (-1.0, -1.0),
    (0.01, 99.9),
]


class TestGradientNoiseField:
    @pytest.mark.parametrize("scale", [0.0, -1.0])
    def test_non_positive_scale_raises(self, scale: float) -> None:
        with pytest.raises(ProceduralNoiseValueError):
            GradientNoiseField(scale=scale)

    @pytest.mark.parametrize("octaves", [0, -1])
    def test_octaves_below_one_raises(self, octaves: int) -> None:
        with pytest.raises(ProceduralNoiseValueError):
            GradientNoiseField(scale=1.0, octaves=octaves)

    @pytest.mark.parametrize("scale", [0.5, 1.0, 3.7])
    @pytest.mark.parametrize("seed", [0, 1, 42])
    def test_sample_within_bounds(self, scale: float, seed: int) -> None:
        field = GradientNoiseField(scale=scale, seed=seed)
        for x, y in _SAMPLE_POINTS:
            value = field.sample(x, y)
            assert -1.0 <= value <= 1.0

    def test_sample_is_deterministic(self) -> None:
        field = GradientNoiseField(scale=2.0, seed=7)
        for x, y in _SAMPLE_POINTS:
            assert field.sample(x, y) == field.sample(x, y)

    def test_different_seed_gives_different_pattern(self) -> None:
        field_a = GradientNoiseField(scale=1.5, seed=1)
        field_b = GradientNoiseField(scale=1.5, seed=2)

        values_a = [field_a.sample(x, y) for x, y in _SAMPLE_POINTS]
        values_b = [field_b.sample(x, y) for x, y in _SAMPLE_POINTS]

        assert values_a != values_b

    def test_octaves_change_result(self) -> None:
        single = GradientNoiseField(scale=1.0, seed=3, octaves=1)
        multi = GradientNoiseField(scale=1.0, seed=3, octaves=3)

        assert single.sample(0.37, 0.61) != pytest.approx(multi.sample(0.37, 0.61))

    @pytest.mark.parametrize("scale", [1.0, 2.5])
    def test_sample_at_grid_point_is_near_zero(self, scale: float) -> None:
        # Rácsponton a saroktól a ponthoz mutató vektor nulla, tehát a
        # skaláris szorzat is nulla -- elméletileg 0.0-hoz közeli érték.
        field = GradientNoiseField(scale=scale, seed=5)
        value = field.sample(0.0, 0.0)
        assert value == pytest.approx(0.0, abs=1e-9)

        value_at_other_grid_point = field.sample(3 * scale, -2 * scale)
        assert value_at_other_grid_point == pytest.approx(0.0, abs=1e-9)


class TestVoronoiNoiseField:
    @pytest.mark.parametrize("scale", [0.0, -1.0])
    def test_non_positive_scale_raises(self, scale: float) -> None:
        with pytest.raises(ProceduralNoiseValueError):
            VoronoiNoiseField(scale=scale)

    @pytest.mark.parametrize("scale", [0.5, 1.0, 3.7])
    @pytest.mark.parametrize("seed", [0, 1, 42])
    def test_sample_within_bounds(self, scale: float, seed: int) -> None:
        field = VoronoiNoiseField(scale=scale, seed=seed)
        for x, y in _SAMPLE_POINTS:
            value = field.sample(x, y)
            assert 0.0 <= value <= 1.0

    def test_sample_is_deterministic(self) -> None:
        field = VoronoiNoiseField(scale=2.0, seed=7)
        for x, y in _SAMPLE_POINTS:
            assert field.sample(x, y) == field.sample(x, y)

    def test_different_seed_gives_different_pattern(self) -> None:
        field_a = VoronoiNoiseField(scale=1.5, seed=1)
        field_b = VoronoiNoiseField(scale=1.5, seed=2)

        values_a = [field_a.sample(x, y) for x, y in _SAMPLE_POINTS]
        values_b = [field_b.sample(x, y) for x, y in _SAMPLE_POINTS]

        assert values_a != values_b
