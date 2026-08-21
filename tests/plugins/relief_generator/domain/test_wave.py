"""Tesztek a komponensalapú `Wave`/`WaveSet` modellhez (ROADMAP Phase 9.1).

Lásd: docs/plugins/relief_generator/WAVE_DOMAIN_MODEL.md.
"""

import math
import sys
from pathlib import Path

import pytest

# A `plugins/` névtér PEP 420 namespace package (l. ADR-0016). L. a
# `test_wave_parameters.py`/`test_height_field.py` azonos mintáját.
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
from plugins.relief_generator.exceptions import (  # noqa: E402
    WaveSetValueError,
    WaveValueError,
)


def test_sinusoidal_matches_formula() -> None:
    function = Sinusoidal()

    result = function.evaluate(phase_position=0.3, wavelength=2.0, phase=0.5)

    expected = math.sin(2.0 * math.pi / 2.0 * 0.3 + 0.5)
    assert result == pytest.approx(expected)


def test_directional_propagation_matches_formula() -> None:
    direction_rad = math.radians(30.0)
    propagation = DirectionalPropagation(direction_rad=direction_rad)

    result = propagation.phase_position(x=0.4, y=0.7)

    expected = 0.4 * math.cos(direction_rad) + 0.7 * math.sin(direction_rad)
    assert result == pytest.approx(expected)


def test_uniform_envelope_is_always_one() -> None:
    envelope = UniformEnvelope()

    assert envelope.amplitude_factor(0.0, 0.0) == 1.0
    assert envelope.amplitude_factor(0.5, 0.9) == 1.0
    assert envelope.amplitude_factor(-3.0, 100.0) == 1.0


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


def test_wave_default_weight_is_one() -> None:
    wave = _make_wave()

    assert wave.weight == 1.0


@pytest.mark.parametrize("amplitude", [0.0, -1.0])
def test_wave_non_positive_amplitude_raises(amplitude: float) -> None:
    with pytest.raises(WaveValueError):
        _make_wave(amplitude=amplitude)


@pytest.mark.parametrize("wavelength", [0.0, -1.0])
def test_wave_non_positive_wavelength_raises(wavelength: float) -> None:
    with pytest.raises(WaveValueError):
        _make_wave(wavelength=wavelength)


def test_wave_evaluate_matches_analytic_formula() -> None:
    direction_rad = math.radians(15.0)
    wave = _make_wave(
        amplitude=2.0,
        wavelength=0.5,
        phase=0.2,
        propagation=DirectionalPropagation(direction_rad=direction_rad),
        weight=1.0,
    )

    x, y = 0.3, 0.6
    result = wave.evaluate(x, y)

    projection = x * math.cos(direction_rad) + y * math.sin(direction_rad)
    expected = 2.0 * math.sin(2.0 * math.pi / 0.5 * projection + 0.2)
    assert result == pytest.approx(expected)


def test_wave_evaluate_applies_weight() -> None:
    positive = _make_wave(weight=1.0)
    negative = _make_wave(weight=-1.0)
    zero = _make_wave(weight=0.0)

    x, y = 0.25, 0.75
    assert negative.evaluate(x, y) == pytest.approx(-positive.evaluate(x, y))
    assert zero.evaluate(x, y) == 0.0


def test_waveset_empty_raises() -> None:
    with pytest.raises(WaveSetValueError):
        WaveSet(waves=())


def test_waveset_evaluate_raw_sums_components_in_order() -> None:
    wave_a = _make_wave(amplitude=1.0, wavelength=1.0, phase=0.0)
    wave_b = _make_wave(amplitude=2.0, wavelength=0.5, phase=0.3, weight=-1.0)
    wave_set = WaveSet(waves=(wave_a, wave_b))

    x, y = 0.4, 0.1
    result = wave_set.evaluate_raw(x, y)

    expected = wave_a.evaluate(x, y) + wave_b.evaluate(x, y)
    assert result == pytest.approx(expected)


def test_waveset_evaluate_raw_is_deterministic() -> None:
    wave_set = WaveSet(waves=(_make_wave(), _make_wave(weight=0.5)))

    first = wave_set.evaluate_raw(0.33, 0.77)
    second = wave_set.evaluate_raw(0.33, 0.77)

    assert first == second
