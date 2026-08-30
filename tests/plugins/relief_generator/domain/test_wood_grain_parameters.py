"""Tesztek a `WoodGrainParameters`-hez.

Lásd: docs/plugins/relief_generator/WOOD_GRAIN_RELIEF_GENERATOR.md,
ROADMAP Phase 11.4.
"""

import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

import pytest  # noqa: E402

from plugins.relief_generator.domain.wood_grain_parameters import (  # noqa: E402
    WoodGrainParameters,
)
from plugins.relief_generator.exceptions import (  # noqa: E402
    WoodGrainParametersValueError,
)

_VALID_KWARGS = dict(
    direction=90.0,
    seed=0,
    board_width=0.42,
    ring_spacing=0.09,
    ring_octaves=4,
    ring_persistence=0.55,
    ring_lacunarity=2.3,
    elongation_min=5.0,
    elongation_max=50.0,
    warp_scale=0.35,
    warp_strength=0.02,
    knot_count_max=3,
    knot_size_min=0.006,
    knot_size_max=0.06,
    knot_ghost_probability=0.3,
    ring_contrast=0.6,
)


def _with(**overrides: object) -> WoodGrainParameters:
    kwargs = dict(_VALID_KWARGS)
    kwargs.update(overrides)
    return WoodGrainParameters(**kwargs)  # type: ignore[arg-type]


def test_valid_parameters_are_accepted() -> None:
    parameters = _with()

    for name, value in _VALID_KWARGS.items():
        assert getattr(parameters, name) == value


def test_any_direction_and_seed_are_accepted() -> None:
    parameters = _with(direction=-720.0, seed=-5)

    assert parameters.direction == -720.0
    assert parameters.seed == -5


def test_any_warp_strength_is_accepted() -> None:
    parameters = _with(warp_strength=-1.0)

    assert parameters.warp_strength == -1.0


@pytest.mark.parametrize("board_width", [0.0, -1.0])
def test_non_positive_board_width_raises(board_width: float) -> None:
    with pytest.raises(WoodGrainParametersValueError):
        _with(board_width=board_width)


@pytest.mark.parametrize("ring_spacing", [0.0, -1.0])
def test_non_positive_ring_spacing_raises(ring_spacing: float) -> None:
    with pytest.raises(WoodGrainParametersValueError):
        _with(ring_spacing=ring_spacing)


@pytest.mark.parametrize("ring_octaves", [0, -1])
def test_ring_octaves_below_one_raises(ring_octaves: int) -> None:
    with pytest.raises(WoodGrainParametersValueError):
        _with(ring_octaves=ring_octaves)


@pytest.mark.parametrize("ring_persistence", [0.0, -1.0])
def test_non_positive_ring_persistence_raises(ring_persistence: float) -> None:
    with pytest.raises(WoodGrainParametersValueError):
        _with(ring_persistence=ring_persistence)


@pytest.mark.parametrize("ring_lacunarity", [1.0, 0.5])
def test_ring_lacunarity_not_above_one_raises(ring_lacunarity: float) -> None:
    with pytest.raises(WoodGrainParametersValueError):
        _with(ring_lacunarity=ring_lacunarity)


@pytest.mark.parametrize("elongation_min", [0.0, -1.0])
def test_non_positive_elongation_min_raises(elongation_min: float) -> None:
    with pytest.raises(WoodGrainParametersValueError):
        _with(elongation_min=elongation_min)


@pytest.mark.parametrize(
    ("elongation_min", "elongation_max"), [(5.0, 5.0), (5.0, 4.0)]
)
def test_elongation_max_not_above_elongation_min_raises(
    elongation_min: float, elongation_max: float
) -> None:
    with pytest.raises(WoodGrainParametersValueError):
        _with(elongation_min=elongation_min, elongation_max=elongation_max)


@pytest.mark.parametrize("warp_scale", [0.0, -1.0])
def test_non_positive_warp_scale_raises(warp_scale: float) -> None:
    with pytest.raises(WoodGrainParametersValueError):
        _with(warp_scale=warp_scale)


@pytest.mark.parametrize("knot_count_max", [-1, -5])
def test_negative_knot_count_max_raises(knot_count_max: int) -> None:
    with pytest.raises(WoodGrainParametersValueError):
        _with(knot_count_max=knot_count_max)


def test_zero_knot_count_max_is_accepted() -> None:
    parameters = _with(knot_count_max=0)

    assert parameters.knot_count_max == 0


@pytest.mark.parametrize("knot_size_min", [0.0, -1.0])
def test_non_positive_knot_size_min_raises(knot_size_min: float) -> None:
    with pytest.raises(WoodGrainParametersValueError):
        _with(knot_size_min=knot_size_min)


@pytest.mark.parametrize(
    ("knot_size_min", "knot_size_max"), [(0.06, 0.06), (0.06, 0.05)]
)
def test_knot_size_max_not_above_knot_size_min_raises(
    knot_size_min: float, knot_size_max: float
) -> None:
    with pytest.raises(WoodGrainParametersValueError):
        _with(knot_size_min=knot_size_min, knot_size_max=knot_size_max)


@pytest.mark.parametrize("knot_ghost_probability", [-0.1, 1.1])
def test_knot_ghost_probability_out_of_range_raises(
    knot_ghost_probability: float,
) -> None:
    with pytest.raises(WoodGrainParametersValueError):
        _with(knot_ghost_probability=knot_ghost_probability)


@pytest.mark.parametrize("knot_ghost_probability", [0.0, 1.0])
def test_knot_ghost_probability_boundary_is_accepted(
    knot_ghost_probability: float,
) -> None:
    parameters = _with(knot_ghost_probability=knot_ghost_probability)

    assert parameters.knot_ghost_probability == knot_ghost_probability


@pytest.mark.parametrize("ring_contrast", [-0.1, -1.0])
def test_negative_ring_contrast_raises(ring_contrast: float) -> None:
    with pytest.raises(WoodGrainParametersValueError):
        _with(ring_contrast=ring_contrast)


def test_zero_ring_contrast_is_accepted() -> None:
    parameters = _with(ring_contrast=0.0)

    assert parameters.ring_contrast == 0.0
