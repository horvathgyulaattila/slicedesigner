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


def test_valid_parameters_are_accepted() -> None:
    parameters = DuneParameters(
        dune_spacing=0.3,
        asymmetry=0.25,
        segment_scale=0.5,
        ripple_wavelength=0.03,
        ripple_amplitude=0.08,
        warp_scale=0.15,
        warp_strength=0.02,
        direction=45.0,
        slope_sensitivity=3.0,
        seed=0,
    )

    assert parameters.dune_spacing == 0.3
    assert parameters.asymmetry == 0.25
    assert parameters.segment_scale == 0.5
    assert parameters.ripple_wavelength == 0.03
    assert parameters.ripple_amplitude == 0.08
    assert parameters.warp_scale == 0.15
    assert parameters.warp_strength == 0.02
    assert parameters.direction == 45.0
    assert parameters.slope_sensitivity == 3.0
    assert parameters.seed == 0


@pytest.mark.parametrize("dune_spacing", [0.0, -1.0])
def test_non_positive_dune_spacing_raises(dune_spacing: float) -> None:
    with pytest.raises(DuneParametersValueError):
        DuneParameters(
            dune_spacing=dune_spacing,
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


@pytest.mark.parametrize("asymmetry", [0.0, 1.0, -0.1, 1.1])
def test_out_of_range_asymmetry_raises(asymmetry: float) -> None:
    with pytest.raises(DuneParametersValueError):
        DuneParameters(
            dune_spacing=0.3,
            asymmetry=asymmetry,
            segment_scale=0.5,
            ripple_wavelength=0.03,
            ripple_amplitude=0.08,
            warp_scale=0.15,
            warp_strength=0.02,
            direction=0.0,
            slope_sensitivity=3.0,
            seed=0,
        )


@pytest.mark.parametrize("segment_scale", [0.0, -1.0])
def test_non_positive_segment_scale_raises(segment_scale: float) -> None:
    with pytest.raises(DuneParametersValueError):
        DuneParameters(
            dune_spacing=0.3,
            asymmetry=0.25,
            segment_scale=segment_scale,
            ripple_wavelength=0.03,
            ripple_amplitude=0.08,
            warp_scale=0.15,
            warp_strength=0.02,
            direction=0.0,
            slope_sensitivity=3.0,
            seed=0,
        )


@pytest.mark.parametrize("ripple_wavelength", [0.0, -1.0])
def test_non_positive_ripple_wavelength_raises(ripple_wavelength: float) -> None:
    with pytest.raises(DuneParametersValueError):
        DuneParameters(
            dune_spacing=0.3,
            asymmetry=0.25,
            segment_scale=0.5,
            ripple_wavelength=ripple_wavelength,
            ripple_amplitude=0.08,
            warp_scale=0.15,
            warp_strength=0.02,
            direction=0.0,
            slope_sensitivity=3.0,
            seed=0,
        )


@pytest.mark.parametrize("ripple_amplitude", [0.0, -1.0])
def test_non_positive_ripple_amplitude_raises(ripple_amplitude: float) -> None:
    with pytest.raises(DuneParametersValueError):
        DuneParameters(
            dune_spacing=0.3,
            asymmetry=0.25,
            segment_scale=0.5,
            ripple_wavelength=0.03,
            ripple_amplitude=ripple_amplitude,
            warp_scale=0.15,
            warp_strength=0.02,
            direction=0.0,
            slope_sensitivity=3.0,
            seed=0,
        )


@pytest.mark.parametrize("warp_scale", [0.0, -1.0])
def test_non_positive_warp_scale_raises(warp_scale: float) -> None:
    with pytest.raises(DuneParametersValueError):
        DuneParameters(
            dune_spacing=0.3,
            asymmetry=0.25,
            segment_scale=0.5,
            ripple_wavelength=0.03,
            ripple_amplitude=0.08,
            warp_scale=warp_scale,
            warp_strength=0.02,
            direction=0.0,
            slope_sensitivity=3.0,
            seed=0,
        )


def test_negative_warp_strength_is_accepted() -> None:
    parameters = DuneParameters(
        dune_spacing=0.3,
        asymmetry=0.25,
        segment_scale=0.5,
        ripple_wavelength=0.03,
        ripple_amplitude=0.08,
        warp_scale=0.15,
        warp_strength=-0.5,
        direction=0.0,
        slope_sensitivity=3.0,
        seed=0,
    )

    assert parameters.warp_strength == -0.5


@pytest.mark.parametrize("direction", [-45.0, 0.0, 361.0, 720.0])
def test_any_direction_is_accepted(direction: float) -> None:
    parameters = DuneParameters(
        dune_spacing=0.3,
        asymmetry=0.25,
        segment_scale=0.5,
        ripple_wavelength=0.03,
        ripple_amplitude=0.08,
        warp_scale=0.15,
        warp_strength=0.02,
        direction=direction,
        slope_sensitivity=3.0,
        seed=0,
    )

    assert parameters.direction == direction


@pytest.mark.parametrize("slope_sensitivity", [-1.0, 0.0])
def test_non_positive_slope_sensitivity_is_accepted(slope_sensitivity: float) -> None:
    parameters = DuneParameters(
        dune_spacing=0.3,
        asymmetry=0.25,
        segment_scale=0.5,
        ripple_wavelength=0.03,
        ripple_amplitude=0.08,
        warp_scale=0.15,
        warp_strength=0.02,
        direction=0.0,
        slope_sensitivity=slope_sensitivity,
        seed=0,
    )

    assert parameters.slope_sensitivity == slope_sensitivity


def test_negative_seed_is_accepted() -> None:
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
        seed=-5,
    )

    assert parameters.seed == -5
