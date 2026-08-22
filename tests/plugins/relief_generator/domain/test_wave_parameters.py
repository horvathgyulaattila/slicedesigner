"""Tesztek a `WaveParameters`-hez.

Lásd: docs/plugins/relief_generator/WAVE_FUNCTION_MODEL.md 4–9. szakasz,
docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 21. szakasz
(2. tétel: Wave Generator).
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

from plugins.relief_generator.domain.amplitude_envelope import (  # noqa: E402
    LinearFalloff,
    RadialAmplitudeEnvelope,
)
from plugins.relief_generator.domain.multiple_wave_sources import (  # noqa: E402
    WaveSourceSpec,
)
from plugins.relief_generator.domain.procedural_distortion import (  # noqa: E402
    SwirlDistortion,
)
from plugins.relief_generator.domain.wave_parameters import WaveParameters  # noqa: E402
from plugins.relief_generator.exceptions import WaveParametersValueError  # noqa: E402

_VALID_KWARGS = {
    "wavelength": 0.3,
    "amplitude": 1.0,
    "direction": 45.0,
    "direction_spread": 20.0,
    "irregularity": 0.5,
    "complexity": 0.5,
}


def test_valid_parameters_are_created_successfully() -> None:
    parameters = WaveParameters(**_VALID_KWARGS)

    assert parameters.wavelength == 0.3
    assert parameters.amplitude == 1.0
    assert parameters.direction == 45.0
    assert parameters.direction_spread == 20.0
    assert parameters.irregularity == 0.5
    assert parameters.complexity == 0.5


@pytest.mark.parametrize(
    "field, boundary_value",
    [
        ("direction", 0.0),
        ("direction", 360.0),
        ("direction_spread", 0.0),
        ("direction_spread", 180.0),
        ("irregularity", 0.0),
        ("irregularity", 1.0),
        ("complexity", 0.0),
        ("complexity", 1.0),
    ],
)
def test_inclusive_boundary_values_are_valid(field: str, boundary_value: float) -> None:
    kwargs = dict(_VALID_KWARGS)
    kwargs[field] = boundary_value

    parameters = WaveParameters(**kwargs)

    assert getattr(parameters, field) == boundary_value


@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("wavelength", 0.0),
        ("wavelength", -1.0),
        ("amplitude", 0.0),
        ("amplitude", -1.0),
        ("direction", -0.001),
        ("direction", 360.001),
        ("direction_spread", -0.001),
        ("direction_spread", 180.001),
        ("irregularity", -0.001),
        ("irregularity", 1.001),
        ("complexity", -0.001),
        ("complexity", 1.001),
    ],
)
def test_out_of_range_field_raises(field: str, invalid_value: float) -> None:
    kwargs = dict(_VALID_KWARGS)
    kwargs[field] = invalid_value

    with pytest.raises(WaveParametersValueError):
        WaveParameters(**kwargs)


def test_envelope_defaults_to_none() -> None:
    parameters = WaveParameters(**_VALID_KWARGS)

    assert parameters.envelope is None


def test_distortion_defaults_to_none() -> None:
    parameters = WaveParameters(**_VALID_KWARGS)

    assert parameters.distortion is None


def test_sources_defaults_to_empty_tuple() -> None:
    parameters = WaveParameters(**_VALID_KWARGS)

    assert parameters.sources == ()


def test_envelope_accepts_radial_amplitude_envelope() -> None:
    envelope = RadialAmplitudeEnvelope(
        center_x=0.5, center_y=0.5, radius=0.5, falloff=LinearFalloff()
    )

    parameters = WaveParameters(
        wavelength=0.3,
        amplitude=1.0,
        direction=45.0,
        direction_spread=20.0,
        irregularity=0.5,
        complexity=0.5,
        envelope=envelope,
    )

    assert parameters.envelope is envelope


def test_distortion_accepts_swirl_distortion() -> None:
    distortion = SwirlDistortion(center_x=0.5, center_y=0.5, radius=0.3, strength=1.0)

    parameters = WaveParameters(
        wavelength=0.3,
        amplitude=1.0,
        direction=45.0,
        direction_spread=20.0,
        irregularity=0.5,
        complexity=0.5,
        distortion=distortion,
    )

    assert parameters.distortion is distortion


def test_sources_accepts_wave_source_spec_tuple() -> None:
    sources = (
        WaveSourceSpec(
            source_type="Radial",
            amplitude=1.0,
            wavelength=0.4,
            phase=0.0,
            source_x=0.5,
            source_y=0.5,
        ),
    )

    parameters = WaveParameters(
        wavelength=0.3,
        amplitude=1.0,
        direction=45.0,
        direction_spread=20.0,
        irregularity=0.5,
        complexity=0.5,
        sources=sources,
    )

    assert parameters.sources == sources
