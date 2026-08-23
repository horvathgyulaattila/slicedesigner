"""Tesztek a determinisztikus, több léptékű komponens-előállítási
szabály közös építőelemeihez (ROADMAP Phase 10.3).

Lásd: docs/plugins/relief_generator/WAVE_FUNCTION_MODEL.md 22. szakasz,
plugins/relief_generator/domain/deterministic_components.py.
"""

import sys
from pathlib import Path

import pytest

# A `plugins/` névtér PEP 420 namespace package (l. ADR-0016). L. a
# `test_multiple_wave_sources.py` azonos mintáját.
_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from plugins.relief_generator.domain.deterministic_components import (  # noqa: E402
    MAX_COMPONENTS,
    MIN_COMPONENTS,
    component_count,
    rho,
)


def test_component_count_at_zero_complexity_is_minimum() -> None:
    assert component_count(0.0) == MIN_COMPONENTS


def test_component_count_at_full_complexity_is_maximum() -> None:
    assert component_count(1.0) == MAX_COMPONENTS


@pytest.mark.parametrize("complexity", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_component_count_stays_within_bounds(complexity: float) -> None:
    count = component_count(complexity)

    assert MIN_COMPONENTS <= count <= MAX_COMPONENTS


@pytest.mark.parametrize(
    ("index", "salt"),
    [(0, 0), (0, 1), (0, 2), (1, 0), (4, 2), (10, 5)],
)
def test_rho_stays_within_unit_range(index: int, salt: int) -> None:
    value = rho(index, salt)

    assert -1.0 <= value <= 1.0


def test_rho_is_deterministic() -> None:
    assert rho(3, 1) == rho(3, 1)


def test_rho_differs_across_index_and_salt() -> None:
    # Nem szigorú matematikai garancia, csak annak igazolása, hogy a
    # függvény ténylegesen az index/salt-tól függ, nem konstans.
    values = {rho(i, s) for i in range(5) for s in range(3)}

    assert len(values) > 1
