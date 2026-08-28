"""Tesztek a `CraterParameters`-hez.

Lásd: docs/plugins/relief_generator/CRATER_RELIEF_GENERATOR.md, ROADMAP
Phase 11.2.
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
from plugins.relief_generator.exceptions import (  # noqa: E402
    CraterParametersValueError,
)


def test_valid_parameters_are_accepted() -> None:
    parameters = CraterParameters(
        scale=0.2, seed=0, radius=0.4, power=3.0, octaves=3, lacunarity=2.0
    )

    assert parameters.scale == 0.2
    assert parameters.seed == 0
    assert parameters.radius == 0.4
    assert parameters.power == 3.0
    assert parameters.octaves == 3
    assert parameters.lacunarity == 2.0


def test_octaves_and_lacunarity_default_to_single_layer() -> None:
    parameters = CraterParameters(scale=0.2, seed=0, radius=0.4, power=3.0)

    assert parameters.octaves == 1
    assert parameters.lacunarity == 2.0


@pytest.mark.parametrize("scale", [0.0, -1.0])
def test_non_positive_scale_raises(scale: float) -> None:
    with pytest.raises(CraterParametersValueError):
        CraterParameters(scale=scale, seed=0, radius=0.4, power=3.0)


@pytest.mark.parametrize("radius", [0.0, -1.0, 1.5])
def test_out_of_range_radius_raises(radius: float) -> None:
    with pytest.raises(CraterParametersValueError):
        CraterParameters(scale=0.2, seed=0, radius=radius, power=3.0)


def test_radius_equal_to_one_is_accepted() -> None:
    # A felső határ (1.0) még érvényes — ez a korábbi, cellahatárig érő
    # viselkedésnek felel meg, csak nem ez az alapérték.
    parameters = CraterParameters(scale=0.2, seed=0, radius=1.0, power=3.0)

    assert parameters.radius == 1.0


@pytest.mark.parametrize("power", [0.0, -1.0])
def test_non_positive_power_raises(power: float) -> None:
    with pytest.raises(CraterParametersValueError):
        CraterParameters(scale=0.2, seed=0, radius=0.4, power=power)


@pytest.mark.parametrize("octaves", [0, -1])
def test_non_positive_octaves_raises(octaves: int) -> None:
    with pytest.raises(CraterParametersValueError):
        CraterParameters(scale=0.2, seed=0, radius=0.4, power=3.0, octaves=octaves)


@pytest.mark.parametrize("lacunarity", [1.0, 0.5, -2.0])
def test_lacunarity_not_greater_than_one_raises(lacunarity: float) -> None:
    with pytest.raises(CraterParametersValueError):
        CraterParameters(
            scale=0.2, seed=0, radius=0.4, power=3.0, lacunarity=lacunarity
        )


def test_negative_seed_is_accepted() -> None:
    # A seed bármely egész érték lehet, a VoronoiNoiseField-hez hasonlóan
    # (docs/plugins/relief_generator/PROCEDURAL_NOISE.md) — nincs korlát.
    parameters = CraterParameters(scale=0.2, seed=-5, radius=0.4, power=3.0)

    assert parameters.seed == -5
