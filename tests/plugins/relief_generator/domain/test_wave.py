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
    AsymmetricPhase,
    DirectionalPropagation,
    Sawtooth,
    Sinusoidal,
    Square,
    Triangle,
    UniformEnvelope,
    Wave,
    WaveSet,
    build_wave_function,
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


def test_triangle_matches_formula() -> None:
    function = Triangle()

    result = function.evaluate(phase_position=0.3, wavelength=2.0, phase=0.5)

    theta = 2.0 * math.pi / 2.0 * 0.3 + 0.5
    expected = (2.0 / math.pi) * math.asin(math.sin(theta))
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "phase_position", [-3.0, -1.0, -0.2, 0.0, 0.2, 0.5, 1.0, 2.7, 10.0]
)
def test_triangle_stays_within_unit_range(phase_position: float) -> None:
    function = Triangle()

    result = function.evaluate(phase_position=phase_position, wavelength=1.3, phase=0.1)

    assert -1.0 <= result <= 1.0


def test_sawtooth_matches_formula() -> None:
    function = Sawtooth()

    result = function.evaluate(phase_position=0.3, wavelength=2.0, phase=0.5)

    theta = 2.0 * math.pi / 2.0 * 0.3 + 0.5
    t = theta / (2.0 * math.pi)
    expected = 2.0 * (t - math.floor(t + 0.5))
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "phase_position", [-3.0, -1.0, -0.2, 0.0, 0.2, 0.5, 1.0, 2.7, 10.0]
)
def test_sawtooth_stays_within_unit_range(phase_position: float) -> None:
    function = Sawtooth()

    result = function.evaluate(phase_position=phase_position, wavelength=1.3, phase=0.1)

    assert -1.0 <= result <= 1.0


def test_square_matches_formula() -> None:
    function = Square()

    result = function.evaluate(phase_position=0.3, wavelength=2.0, phase=0.5)

    theta = 2.0 * math.pi / 2.0 * 0.3 + 0.5
    t = (theta / (2.0 * math.pi)) % 1.0
    expected = 1.0 if t < 0.5 else -1.0
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "phase_position", [-3.0, -1.0, -0.2, 0.0, 0.2, 0.5, 1.0, 2.7, 10.0]
)
def test_square_stays_within_unit_range(phase_position: float) -> None:
    function = Square()

    result = function.evaluate(phase_position=phase_position, wavelength=1.3, phase=0.1)

    assert result in (-1.0, 1.0)


@pytest.mark.parametrize(
    ("name", "expected_type"),
    [
        ("Sinusoidal", Sinusoidal),
        ("Triangle", Triangle),
        ("Sawtooth", Sawtooth),
        ("Square", Square),
    ],
)
def test_build_wave_function_returns_matching_type(
    name: str, expected_type: type
) -> None:
    function = build_wave_function(name)  # type: ignore[arg-type]

    assert isinstance(function, expected_type)


def test_asymmetric_phase_matches_formula() -> None:
    inner = Sinusoidal()
    function = AsymmetricPhase(inner=inner, asymmetry_strength=0.4)

    phase_position, wavelength, phase = 0.3, 2.0, 0.5
    result = function.evaluate(phase_position, wavelength, phase)

    theta = 2.0 * math.pi / wavelength * phase_position + phase
    distorted_position = phase_position + (
        wavelength / (2.0 * math.pi) * 0.4 * math.sin(theta)
    )
    expected = inner.evaluate(distorted_position, wavelength, phase)
    assert result == pytest.approx(expected)


def test_asymmetric_phase_zero_strength_matches_inner_directly() -> None:
    inner = Triangle()
    function = AsymmetricPhase(inner=inner, asymmetry_strength=0.0)

    phase_position, wavelength, phase = 0.6, 1.5, 0.2
    result = function.evaluate(phase_position, wavelength, phase)

    assert result == pytest.approx(inner.evaluate(phase_position, wavelength, phase))


@pytest.mark.parametrize("asymmetry_strength", [-3.5, -1.5, 1.5, 5.0])
def test_asymmetric_phase_with_large_strength_stays_finite_and_deterministic(
    asymmetry_strength: float,
) -> None:
    # |k| >= 1 esetén a P -> P' leképezés nem monoton (WAVE_DOMAIN_MODEL.md
    # 6.4 szakasz), de ettől a kimenetnek még mindig végesnek és
    # determinisztikusnak kell maradnia — nincs semmilyen korlátozott
    # tartomány, amibe esnie kellene.
    function = AsymmetricPhase(
        inner=Sinusoidal(), asymmetry_strength=asymmetry_strength
    )

    first = function.evaluate(0.3, 1.0, 0.0)
    second = function.evaluate(0.3, 1.0, 0.0)

    assert math.isfinite(first)
    assert first == second


def test_build_wave_function_with_zero_asymmetry_matches_unwrapped_call() -> None:
    wrapped = build_wave_function("Sinusoidal", 0.0)
    unwrapped = build_wave_function("Sinusoidal")

    assert isinstance(wrapped, Sinusoidal)
    assert type(wrapped) is type(unwrapped)
    for phase_position in (-1.0, 0.0, 0.3, 1.7):
        assert wrapped.evaluate(phase_position, 1.0, 0.0) == pytest.approx(
            unwrapped.evaluate(phase_position, 1.0, 0.0)
        )


@pytest.mark.parametrize(
    ("name", "expected_inner_type"),
    [
        ("Sinusoidal", Sinusoidal),
        ("Triangle", Triangle),
        ("Sawtooth", Sawtooth),
        ("Square", Square),
    ],
)
def test_build_wave_function_with_nonzero_asymmetry_wraps_in_asymmetric_phase(
    name: str, expected_inner_type: type
) -> None:
    function = build_wave_function(name, 0.7)  # type: ignore[arg-type]

    assert isinstance(function, AsymmetricPhase)
    assert isinstance(function.inner, expected_inner_type)
    assert function.asymmetry_strength == 0.7


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


def test_wave_distortion_defaults_to_none() -> None:
    wave = _make_wave()

    assert wave.distortion is None


class _TrackingEnvelope:
    """Teszt-envelope, amely rögzíti a legutóbbi hívás koordinátáit."""

    def __init__(self) -> None:
        self.last_call: tuple[float, float] | None = None

    def amplitude_factor(self, x: float, y: float) -> float:
        self.last_call = (x, y)
        return 1.0


def test_wave_distortion_warps_propagation_input_but_not_envelope() -> None:
    # Egy egyszerű, nem-identitás teszt-Distortion: eltolja a
    # koordinátákat egy fix vektorral. Ez megváltoztatja a
    # PropagationModel bemenetét, de nem az AmplitudeEnvelope-ét
    # (PROCEDURAL_DISTORTION.md 2.1 szakasz képlete).
    class _ShiftDistortion:
        def warp(self, x: float, y: float) -> tuple[float, float]:
            return (x + 0.37, y)

    tracking_envelope = _TrackingEnvelope()
    wave = _make_wave(
        propagation=DirectionalPropagation(direction_rad=0.0),
        envelope=tracking_envelope,
        distortion=_ShiftDistortion(),
    )

    x, y = 0.2, 0.5
    distorted_result = wave.evaluate(x, y)
    undistorted_wave = _make_wave(
        propagation=DirectionalPropagation(direction_rad=0.0),
        envelope=tracking_envelope,
    )
    undistorted_result = undistorted_wave.evaluate(x, y)

    assert distorted_result != pytest.approx(undistorted_result)
    assert tracking_envelope.last_call == (x, y)
