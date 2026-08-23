"""Tesztek a WaveSourceSpec-hez és a WaveSet-összefűzéshez
(ROADMAP Phase 9.4).

Lásd: docs/plugins/relief_generator/MULTIPLE_WAVE_SOURCES.md.
"""

import math
import sys
from pathlib import Path

import pytest

# A `plugins/` névtér PEP 420 namespace package (l. ADR-0016). L. a
# `test_wave.py`/`test_radial_wave_source.py` azonos mintáját.
_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from plugins.relief_generator.domain.deterministic_components import (  # noqa: E402
    LACUNARITY,
    PERSISTENCE,
    component_count,
)
from plugins.relief_generator.domain.multiple_wave_sources import (  # noqa: E402
    WaveSourceSpec,
    build_combined_wave_set,
    build_waves,
)
from plugins.relief_generator.domain.radial_wave_source import (  # noqa: E402
    RadialPropagation,
)
from plugins.relief_generator.domain.wave import (  # noqa: E402
    DirectionalPropagation,
    Sinusoidal,
    Square,
    UniformEnvelope,
    Wave,
    WaveSet,
)
from plugins.relief_generator.exceptions import WaveSourceSpecValueError  # noqa: E402


def test_directional_spec_is_created_successfully() -> None:
    spec = WaveSourceSpec(
        source_type="Directional",
        amplitude=1.0,
        wavelength=0.5,
        phase=0.2,
        direction=45.0,
    )

    assert spec.direction == 45.0
    assert spec.source_x is None
    assert spec.source_y is None
    assert spec.weight == 1.0
    assert spec.function == "Sinusoidal"


def test_radial_spec_is_created_successfully() -> None:
    spec = WaveSourceSpec(
        source_type="Radial",
        amplitude=1.0,
        wavelength=0.5,
        phase=0.2,
        source_x=0.3,
        source_y=0.7,
    )

    assert spec.source_x == 0.3
    assert spec.source_y == 0.7
    assert spec.direction is None


@pytest.mark.parametrize("amplitude", [0.0, -1.0])
def test_non_positive_amplitude_raises(amplitude: float) -> None:
    with pytest.raises(WaveSourceSpecValueError):
        WaveSourceSpec(
            source_type="Directional",
            amplitude=amplitude,
            wavelength=1.0,
            phase=0.0,
            direction=0.0,
        )


@pytest.mark.parametrize("wavelength", [0.0, -1.0])
def test_non_positive_wavelength_raises(wavelength: float) -> None:
    with pytest.raises(WaveSourceSpecValueError):
        WaveSourceSpec(
            source_type="Directional",
            amplitude=1.0,
            wavelength=wavelength,
            phase=0.0,
            direction=0.0,
        )


def test_directional_without_direction_raises() -> None:
    with pytest.raises(WaveSourceSpecValueError):
        WaveSourceSpec(
            source_type="Directional", amplitude=1.0, wavelength=1.0, phase=0.0
        )


def test_directional_with_radial_fields_raises() -> None:
    with pytest.raises(WaveSourceSpecValueError):
        WaveSourceSpec(
            source_type="Directional",
            amplitude=1.0,
            wavelength=1.0,
            phase=0.0,
            direction=0.0,
            source_x=1.0,
        )


def test_radial_without_source_coordinates_raises() -> None:
    with pytest.raises(WaveSourceSpecValueError):
        WaveSourceSpec(source_type="Radial", amplitude=1.0, wavelength=1.0, phase=0.0)


def test_radial_with_direction_raises() -> None:
    with pytest.raises(WaveSourceSpecValueError):
        WaveSourceSpec(
            source_type="Radial",
            amplitude=1.0,
            wavelength=1.0,
            phase=0.0,
            source_x=0.0,
            source_y=0.0,
            direction=10.0,
        )


def test_build_wave_directional_uses_directional_propagation() -> None:
    spec = WaveSourceSpec(
        source_type="Directional",
        amplitude=2.0,
        wavelength=0.4,
        phase=0.1,
        weight=0.5,
        direction=90.0,
    )

    wave = build_waves(spec)[0]

    assert isinstance(wave.function, Sinusoidal)
    assert isinstance(wave.envelope, UniformEnvelope)
    assert isinstance(wave.propagation, DirectionalPropagation)
    assert wave.propagation.direction_rad == pytest.approx(math.radians(90.0))
    assert wave.amplitude == 2.0
    assert wave.wavelength == 0.4
    assert wave.phase == 0.1
    assert wave.weight == 0.5


def test_build_wave_radial_uses_radial_propagation() -> None:
    spec = WaveSourceSpec(
        source_type="Radial",
        amplitude=1.0,
        wavelength=0.3,
        phase=0.0,
        source_x=1.5,
        source_y=-2.5,
    )

    wave = build_waves(spec)[0]

    assert isinstance(wave.propagation, RadialPropagation)
    assert wave.propagation.source_x == 1.5
    assert wave.propagation.source_y == -2.5


def test_build_wave_uses_spec_function() -> None:
    spec = WaveSourceSpec(
        source_type="Directional",
        amplitude=1.0,
        wavelength=0.4,
        phase=0.0,
        direction=0.0,
        function="Square",
    )

    wave = build_waves(spec)[0]

    assert isinstance(wave.function, Square)


def _directional_wave(**overrides: object) -> Wave:
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


def test_combined_wave_set_orders_automatic_before_explicit() -> None:
    automatic = (_directional_wave(amplitude=1.0), _directional_wave(amplitude=2.0))
    spec = WaveSourceSpec(
        source_type="Radial",
        amplitude=3.0,
        wavelength=0.5,
        phase=0.0,
        source_x=0.0,
        source_y=0.0,
    )

    combined = build_combined_wave_set(automatic, (spec,))

    assert len(combined.waves) == 3
    assert combined.waves[0] is automatic[0]
    assert combined.waves[1] is automatic[1]
    assert combined.waves[2].amplitude == 3.0
    assert isinstance(combined.waves[2].propagation, RadialPropagation)


def test_empty_explicit_list_matches_phase8_9_1_behavior() -> None:
    # MULTIPLE_WAVE_SOURCES.md 8. szakasz: üres explicit forráslista
    # esetén a viselkedés pontosan megegyezik a Phase 8/9.1
    # viselkedésével -- azaz a kombinált WaveSet a tisztán automatikus
    # WaveSet-tel egyezik meg minden mintaponton.
    automatic = (_directional_wave(amplitude=1.0), _directional_wave(amplitude=0.5))

    combined = build_combined_wave_set(automatic, ())
    automatic_only = WaveSet(waves=automatic)

    for x, y in [(0.0, 0.0), (0.3, 0.6), (1.0, -1.0)]:
        assert combined.evaluate_raw(x, y) == pytest.approx(
            automatic_only.evaluate_raw(x, y)
        )


def test_two_radial_sources_with_identical_center_are_valid() -> None:
    # MULTIPLE_WAVE_SOURCES.md 6. szakasz: két azonos centerű Radial
    # forrás érvényes konfiguráció, egyszerűen összeadódnak.
    spec_a = WaveSourceSpec(
        source_type="Radial",
        amplitude=1.0,
        wavelength=0.5,
        phase=0.0,
        source_x=2.0,
        source_y=3.0,
    )
    spec_b = WaveSourceSpec(
        source_type="Radial",
        amplitude=2.0,
        wavelength=0.5,
        phase=0.0,
        source_x=2.0,
        source_y=3.0,
    )

    combined = build_combined_wave_set((), (spec_a, spec_b))

    assert len(combined.waves) == 2
    wave_a, wave_b = build_waves(spec_a)[0], build_waves(spec_b)[0]
    x, y = 2.5, 3.1
    expected = wave_a.evaluate(x, y) + wave_b.evaluate(x, y)
    assert combined.evaluate_raw(x, y) == pytest.approx(expected)


# --- megosztott envelope/distortion (2026-08-21-i kiegészítés) ---


def test_build_wave_defaults_to_uniform_envelope_and_no_distortion() -> None:
    spec = WaveSourceSpec(
        source_type="Directional",
        amplitude=1.0,
        wavelength=0.3,
        phase=0.0,
        direction=0.0,
    )

    wave = build_waves(spec)[0]

    assert isinstance(wave.envelope, UniformEnvelope)
    assert wave.distortion is None


def test_build_wave_uses_provided_envelope_and_distortion() -> None:
    from plugins.relief_generator.domain.amplitude_envelope import (
        LinearFalloff,
        RadialAmplitudeEnvelope,
    )
    from plugins.relief_generator.domain.procedural_distortion import SwirlDistortion

    spec = WaveSourceSpec(
        source_type="Radial",
        amplitude=1.0,
        wavelength=0.3,
        phase=0.0,
        source_x=0.4,
        source_y=0.6,
    )
    envelope = RadialAmplitudeEnvelope(
        center_x=0.5, center_y=0.5, radius=0.4, falloff=LinearFalloff()
    )
    distortion = SwirlDistortion(center_x=0.5, center_y=0.5, radius=0.3, strength=1.2)

    wave = build_waves(spec, envelope=envelope, distortion=distortion)[0]

    assert wave.envelope is envelope
    assert wave.distortion is distortion


def test_build_combined_wave_set_shares_envelope_with_sources() -> None:
    from plugins.relief_generator.domain.amplitude_envelope import (
        LinearFalloff,
        RadialAmplitudeEnvelope,
    )

    spec = WaveSourceSpec(
        source_type="Radial",
        amplitude=1.0,
        wavelength=0.3,
        phase=0.0,
        source_x=0.4,
        source_y=0.6,
    )
    envelope = RadialAmplitudeEnvelope(
        center_x=0.5, center_y=0.5, radius=0.4, falloff=LinearFalloff()
    )

    combined = build_combined_wave_set((), (spec,), envelope=envelope)

    assert combined.waves[0].envelope is envelope


# --- koncentrikus rétegzés: irregularity/complexity (ROADMAP Phase 10.3) ---


def test_irregularity_and_complexity_default_to_zero() -> None:
    spec = WaveSourceSpec(
        source_type="Directional",
        amplitude=1.0,
        wavelength=0.5,
        phase=0.2,
        direction=45.0,
    )

    assert spec.irregularity == 0.0
    assert spec.complexity == 0.0


@pytest.mark.parametrize("irregularity", [-0.1, 1.1])
def test_irregularity_out_of_range_raises(irregularity: float) -> None:
    with pytest.raises(WaveSourceSpecValueError):
        WaveSourceSpec(
            source_type="Directional",
            amplitude=1.0,
            wavelength=1.0,
            phase=0.0,
            direction=0.0,
            irregularity=irregularity,
        )


@pytest.mark.parametrize("complexity", [-0.1, 1.1])
def test_complexity_out_of_range_raises(complexity: float) -> None:
    with pytest.raises(WaveSourceSpecValueError):
        WaveSourceSpec(
            source_type="Directional",
            amplitude=1.0,
            wavelength=1.0,
            phase=0.0,
            direction=0.0,
            complexity=complexity,
        )


def test_build_waves_with_default_complexity_returns_single_layer() -> None:
    spec = WaveSourceSpec(
        source_type="Directional",
        amplitude=2.0,
        wavelength=0.4,
        phase=0.1,
        weight=0.5,
        direction=90.0,
    )

    waves = build_waves(spec)

    assert len(waves) == 1
    wave = waves[0]
    assert isinstance(wave.function, Sinusoidal)
    assert isinstance(wave.envelope, UniformEnvelope)
    assert isinstance(wave.propagation, DirectionalPropagation)
    assert wave.propagation.direction_rad == pytest.approx(math.radians(90.0))
    assert wave.amplitude == 2.0
    assert wave.wavelength == 0.4
    assert wave.phase == pytest.approx(0.1 % (2.0 * math.pi))
    assert wave.weight == 0.5


def test_build_waves_layer_count_matches_component_count() -> None:
    spec = WaveSourceSpec(
        source_type="Radial",
        amplitude=1.0,
        wavelength=0.5,
        phase=0.0,
        source_x=0.5,
        source_y=0.5,
        complexity=1.0,
    )

    waves = build_waves(spec)

    assert len(waves) == component_count(1.0)
    assert len(waves) > 1


def test_build_waves_layers_have_decreasing_amplitude_and_wavelength() -> None:
    spec = WaveSourceSpec(
        source_type="Radial",
        amplitude=1.0,
        wavelength=0.5,
        phase=0.0,
        source_x=0.5,
        source_y=0.5,
        complexity=1.0,
    )

    waves = build_waves(spec)

    for i, wave in enumerate(waves):
        assert wave.amplitude == pytest.approx(spec.amplitude * PERSISTENCE**i)
        assert wave.wavelength == pytest.approx(spec.wavelength / LACUNARITY**i)


def test_build_waves_layers_share_identical_propagation() -> None:
    spec = WaveSourceSpec(
        source_type="Directional",
        amplitude=1.0,
        wavelength=0.5,
        phase=0.0,
        direction=30.0,
        complexity=1.0,
        irregularity=1.0,
    )

    waves = build_waves(spec)

    assert len(waves) > 1
    first_propagation = waves[0].propagation
    for wave in waves[1:]:
        assert wave.propagation is first_propagation


def test_build_combined_wave_set_merges_all_layers_of_multi_layer_source() -> None:
    spec = WaveSourceSpec(
        source_type="Radial",
        amplitude=1.0,
        wavelength=0.5,
        phase=0.0,
        source_x=0.2,
        source_y=0.3,
        complexity=1.0,
    )

    combined = build_combined_wave_set((), (spec,))

    assert len(combined.waves) == component_count(1.0)
