"""Tesztek a RadialAmplitudeEnvelope-hoz és a Falloff-modellekhez
(ROADMAP Phase 9.2).

Lásd: docs/plugins/relief_generator/AMPLITUDE_ENVELOPE.md.
"""

import math
import sys
from pathlib import Path

import pytest

# A `plugins/` névtér PEP 420 namespace package (l. ADR-0016). L. a
# `test_wave.py` azonos mintáját.
_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from plugins.relief_generator.domain.amplitude_envelope import (  # noqa: E402
    GaussianFalloff,
    LinearFalloff,
    RadialAmplitudeEnvelope,
    SmoothFalloff,
)
from plugins.relief_generator.domain.wave import (  # noqa: E402
    DirectionalPropagation,
    Sinusoidal,
    Wave,
)
from plugins.relief_generator.exceptions import (  # noqa: E402
    GaussianFalloffValueError,
    RadialAmplitudeEnvelopeValueError,
)


def test_linear_falloff_matches_formula() -> None:
    falloff = LinearFalloff()

    assert falloff.factor(d=0.0, radius=2.0) == pytest.approx(1.0)
    assert falloff.factor(d=1.0, radius=2.0) == pytest.approx(0.5)
    assert falloff.factor(d=2.0, radius=2.0) == pytest.approx(0.0)


def test_linear_falloff_is_zero_beyond_radius() -> None:
    falloff = LinearFalloff()

    assert falloff.factor(d=3.0, radius=2.0) == 0.0
    assert falloff.factor(d=100.0, radius=2.0) == 0.0


def test_smooth_falloff_matches_formula() -> None:
    falloff = SmoothFalloff()

    t = 0.5
    expected = 1.0 - (3.0 * t**2 - 2.0 * t**3)
    assert falloff.factor(d=1.0, radius=2.0) == pytest.approx(expected)
    assert falloff.factor(d=0.0, radius=2.0) == pytest.approx(1.0)
    assert falloff.factor(d=2.0, radius=2.0) == pytest.approx(0.0)


def test_smooth_falloff_is_zero_beyond_radius() -> None:
    falloff = SmoothFalloff()

    assert falloff.factor(d=3.0, radius=2.0) == 0.0


def test_gaussian_falloff_matches_formula() -> None:
    falloff = GaussianFalloff(sharpness=1.5)

    d, radius = 1.0, 2.0
    t = d / radius
    expected = math.exp(-1.5 * t**2)
    assert falloff.factor(d, radius) == pytest.approx(expected)


def test_gaussian_falloff_is_positive_beyond_radius_no_clamp() -> None:
    falloff = GaussianFalloff(sharpness=1.0)

    result = falloff.factor(d=10.0, radius=2.0)

    assert result > 0.0


def test_gaussian_falloff_at_center_is_one() -> None:
    falloff = GaussianFalloff(sharpness=3.0)

    assert falloff.factor(d=0.0, radius=2.0) == pytest.approx(1.0)


def test_gaussian_falloff_small_sharpness_approaches_uniform() -> None:
    falloff = GaussianFalloff(sharpness=1e-6)

    result = falloff.factor(d=5.0, radius=1.0)

    assert result == pytest.approx(1.0, abs=1e-4)


@pytest.mark.parametrize("sharpness", [0.0, -1.0])
def test_gaussian_falloff_non_positive_sharpness_raises(sharpness: float) -> None:
    with pytest.raises(GaussianFalloffValueError):
        GaussianFalloff(sharpness=sharpness)


def test_radial_envelope_amplitude_factor_uses_distance_and_falloff() -> None:
    envelope = RadialAmplitudeEnvelope(
        center_x=1.0, center_y=1.0, radius=2.0, falloff=LinearFalloff()
    )

    # d = sqrt((3-1)^2 + (1-1)^2) = 2.0 -> pontosan a radius szélén, M=0
    assert envelope.amplitude_factor(3.0, 1.0) == pytest.approx(0.0)
    # a centerben M=1
    assert envelope.amplitude_factor(1.0, 1.0) == pytest.approx(1.0)


def test_radial_envelope_center_is_independent_of_origin() -> None:
    envelope = RadialAmplitudeEnvelope(
        center_x=-5.0, center_y=10.0, radius=1.0, falloff=SmoothFalloff()
    )

    assert envelope.amplitude_factor(-5.0, 10.0) == pytest.approx(1.0)


@pytest.mark.parametrize("radius", [0.0, -1.0])
def test_radial_envelope_non_positive_radius_raises(radius: float) -> None:
    with pytest.raises(RadialAmplitudeEnvelopeValueError):
        RadialAmplitudeEnvelope(
            center_x=0.0, center_y=0.0, radius=radius, falloff=LinearFalloff()
        )


def test_radial_envelope_satisfies_amplitude_envelope_contract_with_wave() -> None:
    # Integrációs jellegű mini-teszt: a RadialAmplitudeEnvelope valódi
    # AmplitudeEnvelope-ként használható egy Wave-ben (l. domain/wave.py),
    # a wave.py módosítása nélkül (structural typing, Protocol).
    envelope = RadialAmplitudeEnvelope(
        center_x=0.0, center_y=0.0, radius=1.0, falloff=LinearFalloff()
    )
    wave = Wave(
        amplitude=1.0,
        wavelength=1.0,
        phase=0.0,
        function=Sinusoidal(),
        propagation=DirectionalPropagation(direction_rad=0.0),
        envelope=envelope,
    )

    # d=2.0 > radius=1.0 -> Linear falloff nulla -> a teljes Wave hozzájárulás nulla
    assert wave.evaluate(2.0, 0.0) == pytest.approx(0.0)
