"""Tesztek a `VoronoiParameters`-hez.

Lásd: docs/plugins/relief_generator/VORONOI_RELIEF_GENERATOR.md, ROADMAP
Phase 11.1.
"""

import pytest

from plugins.relief_generator.domain.voronoi_parameters import VoronoiParameters
from plugins.relief_generator.exceptions import VoronoiParametersValueError


def test_valid_parameters_are_accepted() -> None:
    parameters = VoronoiParameters(scale=0.2, seed=0)

    assert parameters.scale == 0.2
    assert parameters.seed == 0


@pytest.mark.parametrize("scale", [0.0, -1.0])
def test_non_positive_scale_raises(scale: float) -> None:
    with pytest.raises(VoronoiParametersValueError):
        VoronoiParameters(scale=scale, seed=0)


def test_negative_seed_is_accepted() -> None:
    # A seed bármely egész érték lehet, a VoronoiNoiseField-hez hasonlóan
    # (docs/plugins/relief_generator/PROCEDURAL_NOISE.md) — nincs korlát.
    parameters = VoronoiParameters(scale=0.2, seed=-5)

    assert parameters.seed == -5
