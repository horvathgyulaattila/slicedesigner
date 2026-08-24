"""Tesztek a SwirlDistortion-höz (ROADMAP Phase 9.6).

Lásd: docs/plugins/relief_generator/PROCEDURAL_DISTORTION.md.
"""

import math
import sys
from pathlib import Path

import pytest

# A `plugins/` névtér PEP 420 namespace package (l. ADR-0016). L. a
# `test_wave.py`/`test_amplitude_envelope.py` azonos mintáját.
_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from plugins.relief_generator.domain.procedural_distortion import (  # noqa: E402
    NoiseDistortion,
    SwirlDistortion,
)
from plugins.relief_generator.domain.procedural_noise import (  # noqa: E402
    GradientNoiseField,
)
from plugins.relief_generator.domain.wave import (  # noqa: E402
    DirectionalPropagation,
    Sinusoidal,
    UniformEnvelope,
    Wave,
)
from plugins.relief_generator.exceptions import SwirlDistortionValueError  # noqa: E402


def test_swirl_distortion_matches_formula() -> None:
    distortion = SwirlDistortion(center_x=1.0, center_y=2.0, radius=3.0, strength=0.8)

    x, y = 4.0, 5.0
    warped_x, warped_y = distortion.warp(x, y)

    d = math.hypot(x - 1.0, y - 2.0)
    angle = 0.8 * math.exp(-((d / 3.0) ** 2))
    dx, dy = x - 1.0, y - 2.0
    expected_x = 1.0 + dx * math.cos(angle) - dy * math.sin(angle)
    expected_y = 2.0 + dx * math.sin(angle) + dy * math.cos(angle)
    assert warped_x == pytest.approx(expected_x)
    assert warped_y == pytest.approx(expected_y)


def test_swirl_distortion_at_center_is_identity() -> None:
    distortion = SwirlDistortion(center_x=0.5, center_y=0.5, radius=1.0, strength=2.0)

    warped_x, warped_y = distortion.warp(0.5, 0.5)

    assert warped_x == pytest.approx(0.5)
    assert warped_y == pytest.approx(0.5)


def test_swirl_distortion_zero_strength_is_identity_everywhere() -> None:
    distortion = SwirlDistortion(center_x=0.0, center_y=0.0, radius=1.0, strength=0.0)

    for x, y in [(0.3, 0.7), (-2.0, 5.0), (10.0, -10.0)]:
        warped_x, warped_y = distortion.warp(x, y)
        assert warped_x == pytest.approx(x)
        assert warped_y == pytest.approx(y)


def test_swirl_distortion_far_beyond_radius_still_rotates_slightly() -> None:
    # A radius referencia-skála, nem hard cutoff -- Gaussian-jellegű
    # lecsengés, d > radius esetén is alpha != 0 véges d-re.
    distortion = SwirlDistortion(center_x=0.0, center_y=0.0, radius=1.0, strength=1.0)

    warped_x, warped_y = distortion.warp(2.0, 0.0)

    assert (warped_x, warped_y) != pytest.approx((2.0, 0.0))


@pytest.mark.parametrize("radius", [0.0, -1.0])
def test_swirl_distortion_non_positive_radius_raises(radius: float) -> None:
    with pytest.raises(SwirlDistortionValueError):
        SwirlDistortion(center_x=0.0, center_y=0.0, radius=radius, strength=1.0)


def test_swirl_distortion_negative_strength_rotates_opposite_direction() -> None:
    positive = SwirlDistortion(center_x=0.0, center_y=0.0, radius=1.0, strength=0.5)
    negative = SwirlDistortion(center_x=0.0, center_y=0.0, radius=1.0, strength=-0.5)

    x, y = 2.0, 0.0
    pos_x, pos_y = positive.warp(x, y)
    neg_x, neg_y = negative.warp(x, y)

    # Ellentétes irányú elforgatás -> a Y-eltolás előjele fordított.
    assert pos_y == pytest.approx(-neg_y)


def test_swirl_distortion_satisfies_distortion_contract_with_wave() -> None:
    # Integrációs jellegű mini-teszt: a SwirlDistortion valódi
    # Distortion-ként használható egy Wave-ben, a wave.py-ban ebben a
    # lépésben bevezetett `distortion` mezőn keresztül.
    distortion = SwirlDistortion(center_x=0.0, center_y=0.0, radius=1.0, strength=1.5)
    wave = Wave(
        amplitude=1.0,
        wavelength=1.0,
        phase=0.0,
        function=Sinusoidal(),
        propagation=DirectionalPropagation(direction_rad=0.0),
        envelope=UniformEnvelope(),
        distortion=distortion,
    )
    wave_without_distortion = Wave(
        amplitude=1.0,
        wavelength=1.0,
        phase=0.0,
        function=Sinusoidal(),
        propagation=DirectionalPropagation(direction_rad=0.0),
        envelope=UniformEnvelope(),
    )

    # A center-ben a Distortion identitás, tehát a Wave hozzájárulása
    # megegyezik a Distortion nélküli esettel.
    assert wave.evaluate(0.0, 0.0) == pytest.approx(
        wave_without_distortion.evaluate(0.0, 0.0)
    )

    # Máshol a torzítás megváltoztathatja az eredményt.
    off_center = wave.evaluate(0.5, 0.3)
    off_center_without = wave_without_distortion.evaluate(0.5, 0.3)
    assert off_center != pytest.approx(off_center_without)


# --- NoiseDistortion (ROADMAP Phase 10.6) ---


class _StubNoiseSource:
    """Rögzített `sample()`-visszatérésű stub `NoiseSource` teszthez."""

    def __init__(self, value: float) -> None:
        self._value = value

    def sample(self, x: float, y: float) -> float:
        return self._value


def test_noise_distortion_matches_formula_with_stub_sources() -> None:
    distortion = NoiseDistortion(
        noise_x=_StubNoiseSource(0.4), noise_y=_StubNoiseSource(-0.7), strength=2.0
    )

    warped_x, warped_y = distortion.warp(3.0, 5.0)

    assert warped_x == pytest.approx(3.0 + 2.0 * 0.4)
    assert warped_y == pytest.approx(5.0 + 2.0 * (-0.7))


def test_noise_distortion_zero_strength_is_identity() -> None:
    distortion = NoiseDistortion(
        noise_x=_StubNoiseSource(0.9), noise_y=_StubNoiseSource(-0.3), strength=0.0
    )

    for x, y in [(0.3, 0.7), (-2.0, 5.0), (10.0, -10.0)]:
        warped_x, warped_y = distortion.warp(x, y)
        assert warped_x == pytest.approx(x)
        assert warped_y == pytest.approx(y)


def test_noise_distortion_gradient_fields_deterministic_and_decorrelated() -> None:
    noise_x = GradientNoiseField(scale=0.3, seed=0)
    noise_y = GradientNoiseField(scale=0.3, seed=1)
    distortion = NoiseDistortion(noise_x=noise_x, noise_y=noise_y, strength=0.5)

    warped_first = distortion.warp(0.4, 0.6)
    warped_second = distortion.warp(0.4, 0.6)

    assert warped_first == warped_second

    dx = warped_first[0] - 0.4
    dy = warped_first[1] - 0.6
    assert dx != pytest.approx(dy)


def test_noise_distortion_satisfies_distortion_contract_with_wave() -> None:
    noise_x = GradientNoiseField(scale=0.3, seed=0)
    noise_y = GradientNoiseField(scale=0.3, seed=1)
    distortion = NoiseDistortion(noise_x=noise_x, noise_y=noise_y, strength=0.5)
    wave = Wave(
        amplitude=1.0,
        wavelength=1.0,
        phase=0.0,
        function=Sinusoidal(),
        propagation=DirectionalPropagation(direction_rad=0.0),
        envelope=UniformEnvelope(),
        distortion=distortion,
    )
    wave_without_distortion = Wave(
        amplitude=1.0,
        wavelength=1.0,
        phase=0.0,
        function=Sinusoidal(),
        propagation=DirectionalPropagation(direction_rad=0.0),
        envelope=UniformEnvelope(),
    )

    with_distortion = wave.evaluate(0.5, 0.3)
    without_distortion = wave_without_distortion.evaluate(0.5, 0.3)
    assert with_distortion != pytest.approx(without_distortion)
