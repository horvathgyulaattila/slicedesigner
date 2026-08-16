"""Tesztek a `WaveGenerator`-hoz.

Lásd: docs/plugins/relief_generator/WAVE_FUNCTION_MODEL.md 22–23. szakasz
(determinisztikus komponens-előállítás, normalizálási mintavételezés),
docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 21. szakasz
(2. tétel: Wave Generator).
"""

import math
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

from plugins.relief_generator.domain.wave_parameters import WaveParameters  # noqa: E402
from plugins.relief_generator.generators.wave_generator import (  # noqa: E402
    WaveGenerator,
)

# A `WaveGenerationError` a normalizáláshoz mintavételezett felület
# degenerált esetén (mintavételezett F_max == F_min) dobódik. Ez érvényes
# `WaveParameters`-ből közvetlenül nem provokálható ki, mivel a
# `WaveParameters` validációja `amplitude > 0`-t megkövetel, ami
# biztosítja, hogy a domináns (i=0) komponens amplitúdója sosem nulla,
# tehát a mintavételezett felület sosem lehet konstans. Emiatt ehhez a
# kivételhez itt szándékosan nincs teszt — a védőháló jelenleg tisztán
# elméleti (l. WAVE_FUNCTION_MODEL.md 23. szakasz).


def _grid_1d(resolution: int) -> list[float]:
    step = 1.0 / (resolution - 1)
    return [i * step for i in range(resolution)]


def test_generate_is_deterministic_across_repeated_calls() -> None:
    parameters = WaveParameters(
        wavelength=0.25,
        amplitude=1.0,
        direction=35.0,
        direction_spread=40.0,
        irregularity=0.6,
        complexity=0.7,
    )
    generator = WaveGenerator()

    first = generator.generate(parameters)
    second = generator.generate(parameters)

    sample_points = [(0.0, 0.0), (0.2, 0.9), (0.5, 0.5), (0.9, 0.2), (1.0, 1.0)]
    for x, y in sample_points:
        assert first.query(x, y) == second.query(x, y)


def test_generate_values_stay_within_unit_interval_and_reach_bounds() -> None:
    # direction=0° ⇒ a vetítés d(x,y) = x·cos(0) + y·sin(0) = x, azaz a
    # felület y-tól független. complexity=0.0 ⇒ n=1 (egyetlen komponens),
    # irregularity=0.0 ⇒ nincs jitter, tehát a nyers felület pontosan
    # F(x,y) = amplitude·sin(2π/wavelength·x). A wavelength=4.0 választás
    # mellett a sin argumentuma x=0-nál 0, x=1-nél π/2 — ezen a
    # tartományon a sin monoton növekvő, tehát a mintavételezett globális
    # minimum pontosan x=0-nál (F=0), a maximum pontosan x=1-nél
    # (F=amplitude) adódik, mindkettő eleme a 65x65-ös belső
    # normalizálási rácsnak és a lenti 21 pontos teszt-rácsnak is. Emiatt
    # a normalizált H(0,y)=0.0 és H(1,y)=1.0 egzaktul (lebegőpontos
    # tűréssel) várható, nem csak közelítőleg.
    parameters = WaveParameters(
        wavelength=4.0,
        amplitude=2.0,
        direction=0.0,
        direction_spread=0.0,
        irregularity=0.0,
        complexity=0.0,
    )
    height_field = WaveGenerator().generate(parameters)

    grid = _grid_1d(21)
    values = [height_field.query(x, y) for x in grid for y in grid]

    assert all(0.0 <= value <= 1.0 for value in values)
    assert min(values) == pytest.approx(0.0, abs=1e-9)
    assert max(values) == pytest.approx(1.0, abs=1e-9)


def test_generate_matches_analytic_single_component_formula() -> None:
    # complexity=0.0 ⇒ n=1, irregularity=0.0 ⇒ nincs jitter, ezért a
    # nyers felület pontosan az egykomponensű
    # A·sin(2π/λ·(x·cosθ+y·sinθ)+φ) alakot ölti, φ=0-val és θ=direction-nel.
    wavelength = 4.0
    amplitude = 2.0
    direction_deg = 0.0
    parameters = WaveParameters(
        wavelength=wavelength,
        amplitude=amplitude,
        direction=direction_deg,
        direction_spread=0.0,
        irregularity=0.0,
        complexity=0.0,
    )
    height_field = WaveGenerator().generate(parameters)

    x, y = 0.5, 0.3
    direction_rad = math.radians(direction_deg)
    projection = x * math.cos(direction_rad) + y * math.sin(direction_rad)
    raw = amplitude * math.sin(2.0 * math.pi / wavelength * projection)

    # A mintavételezett globális minimum/maximum (l. az előző teszt
    # kommentárja) pontosan 0.0, illetve `amplitude`, ezért a normalizált
    # érték pontosan `raw / amplitude`.
    expected = raw / amplitude

    assert height_field.query(x, y) == pytest.approx(expected, abs=1e-9)
