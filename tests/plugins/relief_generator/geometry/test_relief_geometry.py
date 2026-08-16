"""Tesztek a `ReliefGeometry`-hez.

Lásd: docs/plugins/relief_generator/RELIEF_GEOMETRY_MODEL.md 4., 8–10., 14.,
23. szakasz, docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 21. szakasz
(3. tétel: ReliefGeometry).
"""

import sys
from pathlib import Path

import pytest

# A `plugins/` névtér PEP 420 namespace package (l. ADR-0016: nincs
# `plugins/__init__.py`, hogy az egyes pluginok később önálló csomagként
# leválaszthatók legyenek). A meglévő `tests/gui/` és `tests/project/`
# csomagok (saját `__init__.py`-jal) miatt a teljes tesztkészlet együttes
# futtatásakor a pytest a repo gyökér előtt a `tests/` könyvtárat is
# felveszi a `sys.path`-ra, ami egy azonos nevű, üres `tests/plugins/`
# namespace-szegmenst hoz létre — enélkül a `plugins.relief_generator`
# tévesen a tesztfa alá, nem a valódi forráscsomagba oldódna fel. Ezért a
# repo gyökeret explicit módon a `sys.path` elejére kell tenni, mielőtt a
# `plugins.relief_generator` névtér először importálásra kerül.
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

_VALID_KWARGS = {
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
    kwargs = dict(_VALID_KWARGS)
    kwargs[field] = invalid_value

    with pytest.raises(ReliefGeometryValueError):
        ReliefGeometry(**kwargs)


@pytest.mark.parametrize("field", ["base_thickness", "relief_height"])
def test_zero_is_valid_inclusive_lower_bound(field: str) -> None:
    kwargs = dict(_VALID_KWARGS)
    kwargs[field] = 0.0

    geometry = ReliefGeometry(**kwargs)

    assert getattr(geometry, field) == 0.0


def test_bottom_z_is_zero() -> None:
    assert ReliefGeometry.BOTTOM_Z == 0.0


def test_top_z_computes_formula_with_constant_height_field() -> None:
    geometry = ReliefGeometry(**_VALID_KWARGS)

    assert geometry.top_z(0.3, 0.7) == pytest.approx(2.0 + 0.5 * 10.0)


def test_top_z_at_minimum_height_field_equals_base_thickness() -> None:
    kwargs = dict(_VALID_KWARGS)
    kwargs["top_surface"] = _CONSTANT_ZERO
    geometry = ReliefGeometry(**kwargs)

    assert geometry.top_z(0.5, 0.5) == pytest.approx(geometry.base_thickness)


def test_top_z_at_maximum_height_field_equals_base_plus_relief_height() -> None:
    kwargs = dict(_VALID_KWARGS)
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
