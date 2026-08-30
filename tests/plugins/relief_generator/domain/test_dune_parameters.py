"""Tesztek a `DuneParameters`-hez.

Lásd: docs/plugins/relief_generator/DUNE_RELIEF_GENERATOR.md, ROADMAP
Phase 11.3.
"""

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
from plugins.relief_generator.exceptions import (  # noqa: E402
    DuneParametersValueError,
)

_VALID_KWARGS = dict(
    direction=0.0,
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


def test_valid_parameters_are_accepted() -> None:
    parameters = _with()

    for name, value in _VALID_KWARGS.items():
        assert getattr(parameters, name) == value


def test_any_direction_and_seed_are_accepted() -> None:
    parameters = _with(direction=-720.0, seed=-5)

    assert parameters.direction == -720.0
    assert parameters.seed == -5


def test_any_asymmetry_strength_is_accepted() -> None:
    parameters = _with(asymmetry_strength=0.0)

    assert parameters.asymmetry_strength == 0.0


def test_any_ripple_warp_strength_is_accepted() -> None:
    parameters = _with(ripple_warp_strength=-1.0)

    assert parameters.ripple_warp_strength == -1.0


@pytest.mark.parametrize("coarse_scale", [0.0, -1.0])
def test_non_positive_coarse_scale_raises(coarse_scale: float) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(coarse_scale=coarse_scale)


@pytest.mark.parametrize("ridge_spacing", [0.0, -1.0])
def test_non_positive_ridge_spacing_raises(ridge_spacing: float) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(ridge_spacing=ridge_spacing)


@pytest.mark.parametrize("ridge_length", [0.0, -1.0])
def test_non_positive_ridge_length_raises(ridge_length: float) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(ridge_length=ridge_length)


@pytest.mark.parametrize("fine_scale", [0.0, -1.0])
def test_non_positive_fine_scale_raises(fine_scale: float) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(fine_scale=fine_scale)


@pytest.mark.parametrize("fine_octaves", [0, -1])
def test_fine_octaves_below_one_raises(fine_octaves: int) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(fine_octaves=fine_octaves)


@pytest.mark.parametrize("fine_persistence", [0.0, -1.0])
def test_non_positive_fine_persistence_raises(fine_persistence: float) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(fine_persistence=fine_persistence)


@pytest.mark.parametrize("fine_lacunarity", [1.0, 0.5])
def test_fine_lacunarity_not_above_one_raises(fine_lacunarity: float) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(fine_lacunarity=fine_lacunarity)


@pytest.mark.parametrize("detail_weight", [-0.1, -1.0])
def test_negative_detail_weight_raises(detail_weight: float) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(detail_weight=detail_weight)


def test_zero_detail_weight_is_accepted() -> None:
    parameters = _with(detail_weight=0.0)

    assert parameters.detail_weight == 0.0


@pytest.mark.parametrize("ripple_wavelength_front", [0.0, -1.0])
def test_non_positive_ripple_wavelength_front_raises(
    ripple_wavelength_front: float,
) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(ripple_wavelength_front=ripple_wavelength_front)


@pytest.mark.parametrize("ripple_amplitude_front", [-0.1, -1.0])
def test_negative_ripple_amplitude_front_raises(ripple_amplitude_front: float) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(ripple_amplitude_front=ripple_amplitude_front)


def test_zero_ripple_amplitude_front_is_accepted() -> None:
    parameters = _with(ripple_amplitude_front=0.0)

    assert parameters.ripple_amplitude_front == 0.0


@pytest.mark.parametrize("ripple_wavelength_back", [0.0, -1.0])
def test_non_positive_ripple_wavelength_back_raises(
    ripple_wavelength_back: float,
) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(ripple_wavelength_back=ripple_wavelength_back)


@pytest.mark.parametrize("ripple_amplitude_back", [-0.1, -1.0])
def test_negative_ripple_amplitude_back_raises(ripple_amplitude_back: float) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(ripple_amplitude_back=ripple_amplitude_back)


def test_zero_ripple_amplitude_back_is_accepted() -> None:
    parameters = _with(ripple_amplitude_back=0.0)

    assert parameters.ripple_amplitude_back == 0.0


@pytest.mark.parametrize("ripple_warp_scale", [0.0, -1.0])
def test_non_positive_ripple_warp_scale_raises(ripple_warp_scale: float) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(ripple_warp_scale=ripple_warp_scale)


@pytest.mark.parametrize(
    ("blend_low", "blend_high"), [(6.0, 6.0), (6.0, -6.0)]
)
def test_blend_low_not_below_blend_high_raises(
    blend_low: float, blend_high: float
) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(blend_low=blend_low, blend_high=blend_high)


@pytest.mark.parametrize("patch_dune_scale", [0.0, -1.0])
def test_non_positive_patch_dune_scale_raises(patch_dune_scale: float) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(patch_dune_scale=patch_dune_scale)


@pytest.mark.parametrize(
    ("patch_dune_low", "patch_dune_high"), [(0.5, 0.5), (0.5, -0.5)]
)
def test_patch_dune_low_not_below_patch_dune_high_raises(
    patch_dune_low: float, patch_dune_high: float
) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(patch_dune_low=patch_dune_low, patch_dune_high=patch_dune_high)


@pytest.mark.parametrize("patch_within_scale", [0.0, -1.0])
def test_non_positive_patch_within_scale_raises(patch_within_scale: float) -> None:
    with pytest.raises(DuneParametersValueError):
        _with(patch_within_scale=patch_within_scale)
