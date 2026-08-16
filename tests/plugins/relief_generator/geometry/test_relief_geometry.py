"""Tesztek a `ReliefGeometry`-hez.

Lásd: docs/plugins/relief_generator/RELIEF_GEOMETRY_MODEL.md 4., 8–10., 14.,
23. szakasz, docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 21. szakasz
(3. tétel: ReliefGeometry).
"""

import sys
from pathlib import Path
from typing import TypedDict

import pytest

_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from plugins.relief_generator.domain.height_field import HeightField  # noqa: E402
from plugins.relief_generator.exceptions import (  # noqa: E402
    HeightFieldValueError,
    ReliefGeometryValueError,
)
from plugins.relief_generator.geometry.relief_geometry import (  # noqa: E402
    ReliefGeometry,
)

_CONSTANT_HALF = HeightField(lambda x, y: 0.5)
_CONSTANT_ZERO = HeightField(lambda x, y: 0.0)
_CONSTANT_ONE = HeightField(lambda x, y: 1.0)


class _ValidKwargs(TypedDict):
    """A `ReliefGeometry` érvényes konstruktor-kwargs-ainak típusa.

    Kizárólag a teszt `**_VALID_KWARGS` szétbontásának mypy --strict
    alatti tipizálhatóságát szolgálja (heterogén float/HeightField
    mezőkkel egy sima dict `dict[str, object]`-re szélesedne).
    """

    width: float
    height: float
    base_thickness: float
    relief_height: float
    top_surface: HeightField


_VALID_KWARGS: _ValidKwargs = {
    "width": 100.0,
    "height": 50.0,
    "base_thickness": 2.0,
    "relief_height": 10.0,
    "top_surface": _CONSTANT_HALF,
}


def test_valid_parameters_are_created_successfully() -> None:
    geometry = ReliefGeometry(**_VALID_KWARGS)

    assert geometry.width == 100.0
    assert geometry.height == 50.0
    assert geometry.base_thickness == 2.0
    assert geometry.relief_height == 10.0
    assert geometry.top_surface is _CONSTANT_HALF


@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("width", 0.0),
        ("width", -1.0),
        ("height", 0.0),
        ("height", -1.0),
        ("base_thickness", -0.001),
        ("relief_height", -0.001),
    ],
)
def test_out_of_range_field_raises(field: str, invalid_value: float) -> None:
    kwargs = _VALID_KWARGS.copy()
    kwargs[field] = invalid_value  # type: ignore[literal-required]

    with pytest.raises(ReliefGeometryValueError):
        ReliefGeometry(**kwargs)


@pytest.mark.parametrize("field", ["base_thickness", "relief_height"])
def test_zero_is_valid_inclusive_lower_bound(field: str) -> None:
    kwargs = _VALID_KWARGS.copy()
    kwargs[field] = 0.0  # type: ignore[literal-required]

    geometry = ReliefGeometry(**kwargs)

    assert getattr(geometry, field) == 0.0


def test_bottom_z_is_zero() -> None:
    assert ReliefGeometry.BOTTOM_Z == 0.0


def test_top_z_computes_formula_with_constant_height_field() -> None:
    geometry = ReliefGeometry(**_VALID_KWARGS)

    assert geometry.top_z(0.3, 0.7) == pytest.approx(2.0 + 0.5 * 10.0)


def test_top_z_at_minimum_height_field_equals_base_thickness() -> None:
    kwargs = _VALID_KWARGS.copy()
    kwargs["top_surface"] = _CONSTANT_ZERO
    geometry = ReliefGeometry(**kwargs)

    assert geometry.top_z(0.5, 0.5) == pytest.approx(geometry.base_thickness)


def test_top_z_at_maximum_height_field_equals_base_plus_relief_height() -> None:
    kwargs = _VALID_KWARGS.copy()
    kwargs["top_surface"] = _CONSTANT_ONE
    geometry = ReliefGeometry(**kwargs)

    assert geometry.top_z(0.5, 0.5) == pytest.approx(
        geometry.base_thickness + geometry.relief_height
    )


@pytest.mark.parametrize("x, y", [(-0.1, 0.5), (1.1, 0.5), (0.5, -0.1), (0.5, 1.1)])
def test_top_z_out_of_range_coordinates_propagate_height_field_error(
    x: float, y: float
) -> None:
    geometry = ReliefGeometry(**_VALID_KWARGS)

    with pytest.raises(HeightFieldValueError):
        geometry.top_z(x, y)


def test_base_thickness_and_relief_height_both_zero_raises() -> None:
    with pytest.raises(ReliefGeometryValueError):
        ReliefGeometry(
            width=100.0,
            height=50.0,
            base_thickness=0.0,
            relief_height=0.0,
            top_surface=_CONSTANT_HALF,
        )
