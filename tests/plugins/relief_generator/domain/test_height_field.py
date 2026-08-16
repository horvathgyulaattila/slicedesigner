"""Tesztek a `HeightField`-hez.

Lásd: docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 19. szakasz
("Height Field" tétel: értéktartomány, koordinátakezelés, determinisztikus
lekérdezés).
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
from plugins.relief_generator.exceptions import HeightFieldValueError  # noqa: E402


def test_query_valid_interior_point_returns_expected_value() -> None:
    height_field = HeightField(lambda x, y: (x + y) / 2)

    assert height_field.query(0.4, 0.6) == pytest.approx(0.5)


@pytest.mark.parametrize("x", [0.0, 1.0])
@pytest.mark.parametrize("y", [0.0, 1.0])
def test_query_coordinate_bounds_are_inclusive(x: float, y: float) -> None:
    height_field = HeightField(lambda x, y: 0.5)

    assert height_field.query(x, y) == pytest.approx(0.5)


@pytest.mark.parametrize(
    "x, y",
    [
        (-0.001, 0.5),
        (1.001, 0.5),
        (0.5, -0.001),
        (0.5, 1.001),
    ],
)
def test_query_out_of_range_coordinates_raise(x: float, y: float) -> None:
    height_field = HeightField(lambda x, y: 0.5)

    with pytest.raises(HeightFieldValueError):
        height_field.query(x, y)


def test_query_height_function_returning_below_zero_raises() -> None:
    height_field = HeightField(lambda x, y: -0.1)

    with pytest.raises(HeightFieldValueError):
        height_field.query(0.5, 0.5)


def test_query_height_function_returning_above_one_raises() -> None:
    height_field = HeightField(lambda x, y: 1.1)

    with pytest.raises(HeightFieldValueError):
        height_field.query(0.5, 0.5)


def test_query_is_deterministic_for_repeated_calls_on_same_point() -> None:
    height_field = HeightField(lambda x, y: x * 0.3 + y * 0.7)

    first = height_field.query(0.25, 0.75)
    second = height_field.query(0.25, 0.75)

    assert first == second
