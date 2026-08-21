"""Tesztek a weight szemantikára és a WaveSet súlyozott összegzésére
(ROADMAP Phase 9.5).

Lásd: docs/plugins/relief_generator/WAVE_WEIGHTING.md. A `weight`
alapmechanizmusa (Wave.weight mező, alapérték, evaluate() súlyozása) már
a 9.1 (Wave model extension) részeként implementálva és tesztelve lett
(l. test_wave.py) — ez a modul a WAVE_WEIGHTING.md-ben rögzített,
WaveSet-szintű összegzési szemantikát fedi le mélyebben: a weight=0
komponens érvényben marad a gyűjteményben, a negatív weight destruktív
interferenciát okozhat, és a weight a normalizálás előtt érvényesül
(strukturálisan: a WaveSet.evaluate_raw már a súlyozott összeget adja
vissza, a normalizálás ezen felül, külön lépésben történik a
WaveGenerator-ban).
"""

import sys
from pathlib import Path

import pytest

# A `plugins/` névtér PEP 420 namespace package (l. ADR-0016). L. a
# `test_wave.py` azonos mintáját.
_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from plugins.relief_generator.domain.wave import (  # noqa: E402
    DirectionalPropagation,
    Sinusoidal,
    UniformEnvelope,
    Wave,
    WaveSet,
)


def _make_wave(**overrides: object) -> Wave:
    kwargs: dict[str, object] = {
        "amplitude": 1.0,
        "wavelength": 1.0,
        "phase": 0.0,
        "function": Sinusoidal(),
        "propagation": DirectionalPropagation(direction_rad=0.0),
        "envelope": UniformEnvelope(),
    }
    kwargs.update(overrides)
    return Wave(**kwargs)  # type: ignore[arg-type]


def test_zero_weight_component_remains_in_waveset() -> None:
    silenced = _make_wave(weight=0.0)
    active = _make_wave(amplitude=2.0, weight=1.0)
    wave_set = WaveSet(waves=(silenced, active))

    assert len(wave_set.waves) == 2
    assert wave_set.waves[0] is silenced


def test_zero_weight_component_does_not_affect_sum() -> None:
    silenced = _make_wave(amplitude=5.0, wavelength=0.3, phase=1.2, weight=0.0)
    active = _make_wave(amplitude=2.0)
    with_silenced = WaveSet(waves=(silenced, active))
    without_silenced = WaveSet(waves=(active,))

    x, y = 0.4, 0.15
    assert with_silenced.evaluate_raw(x, y) == pytest.approx(
        without_silenced.evaluate_raw(x, y)
    )


def test_opposite_weight_causes_destructive_interference() -> None:
    positive = _make_wave(amplitude=1.5, wavelength=0.4, phase=0.7, weight=1.0)
    negative = _make_wave(amplitude=1.5, wavelength=0.4, phase=0.7, weight=-1.0)
    wave_set = WaveSet(waves=(positive, negative))

    for x, y in [(0.0, 0.0), (0.3, 0.6), (-1.0, 2.5)]:
        assert wave_set.evaluate_raw(x, y) == pytest.approx(0.0)


def test_mixed_weights_sum_linearly() -> None:
    wave_a = _make_wave(amplitude=1.0, wavelength=1.0, phase=0.0, weight=2.0)
    wave_b = _make_wave(amplitude=1.0, wavelength=0.5, phase=0.5, weight=-0.5)
    wave_c = _make_wave(amplitude=1.0, wavelength=2.0, phase=1.0, weight=0.0)
    wave_set = WaveSet(waves=(wave_a, wave_b, wave_c))

    x, y = 0.2, 0.9
    expected = wave_a.evaluate(x, y) + wave_b.evaluate(x, y) + wave_c.evaluate(x, y)
    assert wave_set.evaluate_raw(x, y) == pytest.approx(expected)


def test_weight_scales_raw_field_before_any_normalization() -> None:
    # A WaveSet.evaluate_raw() már a súlyozott összeget adja vissza --
    # a normalizálás (WaveGenerator felelőssége) ezen felül, külön
    # lépésben történik. Ez azt jelenti, hogy a weight megváltoztatása
    # megváltoztatja a nyers F(x,y) értéket, nem csupán egy utólagos
    # skálázást a normalizált eredményen.
    base = _make_wave(amplitude=1.0, wavelength=0.5, phase=0.3, weight=1.0)
    doubled = _make_wave(amplitude=1.0, wavelength=0.5, phase=0.3, weight=2.0)

    x, y = 0.35, 0.1
    base_raw = WaveSet(waves=(base,)).evaluate_raw(x, y)
    doubled_raw = WaveSet(waves=(doubled,)).evaluate_raw(x, y)

    assert doubled_raw == pytest.approx(2.0 * base_raw)
