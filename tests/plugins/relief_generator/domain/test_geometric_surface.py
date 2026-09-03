"""Tesztek a `GeometricSurface`-hez.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_GEOMETRIC_SURFACE.md.
"""

import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

import pytest  # noqa: E402

from plugins.relief_generator.domain.geometric_surface import (  # noqa: E402
    GeometricSurface,
)
from plugins.relief_generator.exceptions import (  # noqa: E402
    GeometricSurfaceValueError,
)


def _constant_relief(value: float):
    def relief(x: float, y: float) -> float:
        return value

    return relief


def test_valid_parameters_are_created_successfully() -> None:
    surface = GeometricSurface(
        width=100.0,
        height=50.0,
        base_thickness=2.0,
        relief_height_raised=5.0,
        relief_height_recessed=1.0,
        raw_relief=_constant_relief(0.0),
    )

    assert surface.width == 100.0
    assert surface.height == 50.0
    assert surface.base_thickness == 2.0
    assert surface.relief_height_raised == 5.0
    assert surface.relief_height_recessed == 1.0


def test_relief_height_recessed_equal_to_base_thickness_raises() -> None:
    with pytest.raises(GeometricSurfaceValueError):
        GeometricSurface(
            width=100.0,
            height=50.0,
            base_thickness=2.0,
            relief_height_raised=5.0,
            relief_height_recessed=2.0,
            raw_relief=_constant_relief(0.0),
        )


def test_relief_height_recessed_exceeding_base_thickness_raises() -> None:
    with pytest.raises(GeometricSurfaceValueError):
        GeometricSurface(
            width=100.0,
            height=50.0,
            base_thickness=2.0,
            relief_height_raised=5.0,
            relief_height_recessed=3.0,
            raw_relief=_constant_relief(0.0),
        )


def test_relief_height_recessed_strictly_less_than_base_thickness_is_valid() -> None:
    surface = GeometricSurface(
        width=100.0,
        height=50.0,
        base_thickness=2.0,
        relief_height_raised=5.0,
        relief_height_recessed=1.999,
        raw_relief=_constant_relief(0.0),
    )

    assert surface.relief_height_recessed == 1.999


def test_physical_z_at_raw_value_zero_returns_base_thickness() -> None:
    surface = GeometricSurface(
        width=100.0,
        height=50.0,
        base_thickness=2.0,
        relief_height_raised=5.0,
        relief_height_recessed=1.0,
        raw_relief=_constant_relief(0.0),
    )

    assert surface.physical_z(0.0, v_min=-0.5, v_max=0.8) == 2.0


def test_physical_z_positive_raw_value_scales_with_relief_height_raised() -> None:
    surface = GeometricSurface(
        width=100.0,
        height=50.0,
        base_thickness=2.0,
        relief_height_raised=5.0,
        relief_height_recessed=1.0,
        raw_relief=_constant_relief(0.0),
    )

    assert surface.physical_z(0.4, v_min=-0.5, v_max=0.8) == pytest.approx(
        2.0 + (0.4 / 0.8) * 5.0
    )


def test_physical_z_negative_raw_value_scales_with_relief_height_recessed() -> None:
    surface = GeometricSurface(
        width=100.0,
        height=50.0,
        base_thickness=2.0,
        relief_height_raised=5.0,
        relief_height_recessed=1.0,
        raw_relief=_constant_relief(0.0),
    )

    assert surface.physical_z(-0.25, v_min=-0.5, v_max=0.8) == pytest.approx(
        2.0 - (-0.25 / -0.5) * 1.0
    )


def test_negative_width_does_not_raise_documenting_intentional_scope() -> None:
    surface = GeometricSurface(
        width=-10.0,
        height=50.0,
        base_thickness=2.0,
        relief_height_raised=5.0,
        relief_height_recessed=1.0,
        raw_relief=_constant_relief(0.0),
    )

    assert surface.width == -10.0
