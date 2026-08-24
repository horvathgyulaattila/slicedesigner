"""Tesztek a Relief Generator MeshSource entry point regisztrációjához
(ADR-0017).

Lásd: `plugins/relief_generator/source/registration.py`,
`plugins/relief_generator/pyproject.toml`.
"""

import pytest

from plugins.relief_generator.domain.amplitude_envelope import (
    GaussianFalloff,
    NoiseAmplitudeEnvelope,
    RadialAmplitudeEnvelope,
)
from plugins.relief_generator.domain.procedural_distortion import (
    NoiseDistortion,
    SwirlDistortion,
)
from plugins.relief_generator.domain.procedural_noise import GradientNoiseField
from plugins.relief_generator.source.registration import (
    _build_distortion,
    _build_envelope,
    _build_sources,
    build_mesh_source_descriptor,
)
from plugins.relief_generator.source.relief_generator_mesh_source import (
    ReliefGeneratorMeshSource,
)

_EXPECTED_PARAMETER_NAMES = (
    "width",
    "height",
    "base_thickness",
    "relief_height",
    "sampling_distance",
    "wavelength",
    "amplitude",
    "direction",
    "direction_spread",
    "irregularity",
    "complexity",
    "function",
    "envelope_type",
    "envelope_center_x",
    "envelope_center_y",
    "envelope_radius",
    "envelope_falloff",
    "envelope_sharpness",
    "envelope_noise_type",
    "envelope_noise_scale",
    "envelope_noise_seed",
    "envelope_noise_octaves",
    "envelope_noise_persistence",
    "envelope_noise_lacunarity",
    "distortion_type",
    "distortion_center_x",
    "distortion_center_y",
    "distortion_radius",
    "distortion_strength",
    "distortion_noise_scale",
    "distortion_noise_seed",
    "distortion_noise_octaves",
    "distortion_noise_persistence",
    "distortion_noise_lacunarity",
    "distortion_noise_strength",
    "sources",
    "include_automatic",
)


def test_build_mesh_source_descriptor_has_expected_display_name() -> None:
    descriptor = build_mesh_source_descriptor()

    assert descriptor.display_name == "Relief Generator (Wave)"


def test_build_mesh_source_descriptor_has_expected_parameters() -> None:
    descriptor = build_mesh_source_descriptor()

    assert len(descriptor.parameters) == len(_EXPECTED_PARAMETER_NAMES)
    assert tuple(spec.name for spec in descriptor.parameters) == (
        _EXPECTED_PARAMETER_NAMES
    )


# --- mezőcsoportosítás (`group`, ADR-0017 kiegészítés, 2026-08-23) ---

_EXPECTED_PARAMETER_GROUPS = {
    "width": None,
    "height": None,
    "base_thickness": None,
    "relief_height": None,
    "sampling_distance": None,
    "wavelength": "Automatikus hullám",
    "amplitude": "Automatikus hullám",
    "direction": "Automatikus hullám",
    "direction_spread": "Automatikus hullám",
    "irregularity": "Automatikus hullám",
    "complexity": "Automatikus hullám",
    "function": "Automatikus hullám",
    "envelope_type": "Envelope",
    "envelope_center_x": "Envelope",
    "envelope_center_y": "Envelope",
    "envelope_radius": "Envelope",
    "envelope_falloff": "Envelope",
    "envelope_sharpness": "Envelope",
    "envelope_noise_type": "Envelope",
    "envelope_noise_scale": "Envelope",
    "envelope_noise_seed": "Envelope",
    "envelope_noise_octaves": "Envelope",
    "envelope_noise_persistence": "Envelope",
    "envelope_noise_lacunarity": "Envelope",
    "distortion_type": "Torzítás",
    "distortion_center_x": "Torzítás",
    "distortion_center_y": "Torzítás",
    "distortion_radius": "Torzítás",
    "distortion_strength": "Torzítás",
    "distortion_noise_scale": "Torzítás",
    "distortion_noise_seed": "Torzítás",
    "distortion_noise_octaves": "Torzítás",
    "distortion_noise_persistence": "Torzítás",
    "distortion_noise_lacunarity": "Torzítás",
    "distortion_noise_strength": "Torzítás",
    "sources": None,
    "include_automatic": "Automatikus hullám",
}


def test_parameters_have_expected_group_assignment() -> None:
    descriptor = build_mesh_source_descriptor()

    groups = {spec.name: spec.group for spec in descriptor.parameters}

    assert groups == _EXPECTED_PARAMETER_GROUPS


def test_sources_item_schema_fields_have_no_group() -> None:
    descriptor = build_mesh_source_descriptor()

    sources_spec = next(s for s in descriptor.parameters if s.name == "sources")

    assert all(item.group is None for item in sources_spec.item_schema)


def test_function_parameter_has_expected_choices() -> None:
    descriptor = build_mesh_source_descriptor()

    spec = next(s for s in descriptor.parameters if s.name == "function")

    assert spec.default == "Sinusoidal"
    assert spec.choices == ("Sinusoidal", "Triangle", "Sawtooth", "Square")


def test_sources_item_schema_has_function_field_without_group() -> None:
    descriptor = build_mesh_source_descriptor()

    sources_spec = next(s for s in descriptor.parameters if s.name == "sources")
    function_spec = next(s for s in sources_spec.item_schema if s.name == "function")

    assert function_spec.group is None
    assert function_spec.default == "Sinusoidal"
    assert function_spec.choices == ("Sinusoidal", "Triangle", "Sawtooth", "Square")


def test_sources_item_schema_has_irregularity_and_complexity_fields() -> None:
    descriptor = build_mesh_source_descriptor()

    sources_spec = next(s for s in descriptor.parameters if s.name == "sources")
    item_names = {item.name: item for item in sources_spec.item_schema}

    for name in ("irregularity", "complexity"):
        item = item_names[name]
        assert item.group is None
        assert item.default == 0.0
        assert item.minimum == 0.0
        assert item.maximum == 1.0


def test_build_with_default_values_returns_working_mesh_source() -> None:
    descriptor = build_mesh_source_descriptor()
    values = {spec.name: spec.default for spec in descriptor.parameters}

    mesh_source = descriptor.build(values)

    assert isinstance(mesh_source, ReliefGeneratorMeshSource)
    mesh = mesh_source.get_mesh()
    assert mesh.is_valid is True
    assert len(mesh.vertices) > 0
    assert len(mesh.triangles) > 0


# --- envelope/distortion/sources bekötése (9.7.d) ---


def test_build_envelope_returns_none_when_type_is_none() -> None:
    assert _build_envelope({"envelope_type": "None"}) is None


def test_build_envelope_returns_radial_amplitude_envelope() -> None:
    values = {
        "envelope_type": "Radial",
        "envelope_center_x": 0.2,
        "envelope_center_y": 0.6,
        "envelope_radius": 0.4,
        "envelope_falloff": "Linear",
        "envelope_sharpness": 1.0,
    }

    envelope = _build_envelope(values)

    assert isinstance(envelope, RadialAmplitudeEnvelope)
    assert envelope.center_x == 0.2
    assert envelope.center_y == 0.6
    assert envelope.radius == 0.4


def test_build_envelope_gaussian_falloff_uses_sharpness() -> None:
    values = {
        "envelope_type": "Radial",
        "envelope_center_x": 0.5,
        "envelope_center_y": 0.5,
        "envelope_radius": 0.3,
        "envelope_falloff": "Gaussian",
        "envelope_sharpness": 2.5,
    }

    envelope = _build_envelope(values)

    assert isinstance(envelope, RadialAmplitudeEnvelope)
    assert isinstance(envelope.falloff, GaussianFalloff)
    assert envelope.falloff.sharpness == 2.5


def test_build_envelope_noise_gradient_uses_symmetric_input_range() -> None:
    values = {
        "envelope_type": "Noise",
        "envelope_noise_type": "Gradient",
        "envelope_noise_scale": 0.3,
        "envelope_noise_seed": 0,
        "envelope_noise_octaves": 1,
        "envelope_noise_persistence": 0.5,
        "envelope_noise_lacunarity": 2.0,
    }

    envelope = _build_envelope(values)

    assert isinstance(envelope, NoiseAmplitudeEnvelope)
    assert envelope.input_min == -1.0
    assert envelope.input_max == 1.0


def test_build_envelope_noise_voronoi_uses_default_input_range() -> None:
    values = {
        "envelope_type": "Noise",
        "envelope_noise_type": "Voronoi",
        "envelope_noise_scale": 0.3,
        "envelope_noise_seed": 0,
        "envelope_noise_octaves": 1,
        "envelope_noise_persistence": 0.5,
        "envelope_noise_lacunarity": 2.0,
    }

    envelope = _build_envelope(values)

    assert isinstance(envelope, NoiseAmplitudeEnvelope)
    assert envelope.input_min == 0.0
    assert envelope.input_max == 1.0


def test_build_distortion_returns_none_when_type_is_none() -> None:
    assert _build_distortion({"distortion_type": "None"}) is None


def test_build_distortion_returns_swirl_distortion() -> None:
    values = {
        "distortion_type": "Swirl",
        "distortion_center_x": 0.4,
        "distortion_center_y": 0.6,
        "distortion_radius": 0.2,
        "distortion_strength": 1.8,
    }

    distortion = _build_distortion(values)

    assert isinstance(distortion, SwirlDistortion)
    assert distortion.strength == 1.8


def test_build_distortion_returns_noise_distortion_with_decorrelated_seeds() -> None:
    values = {
        "distortion_type": "Noise",
        "distortion_noise_scale": 0.3,
        "distortion_noise_seed": 5,
        "distortion_noise_octaves": 1,
        "distortion_noise_persistence": 0.5,
        "distortion_noise_lacunarity": 2.0,
        "distortion_noise_strength": 0.1,
    }

    distortion = _build_distortion(values)

    assert isinstance(distortion, NoiseDistortion)
    assert distortion.strength == 0.1
    assert isinstance(distortion.noise_x, GradientNoiseField)
    assert isinstance(distortion.noise_y, GradientNoiseField)
    assert distortion.noise_x.seed == 5
    assert distortion.noise_y.seed == 6
    assert distortion.noise_x.seed + 1 == distortion.noise_y.seed


def test_build_sources_returns_empty_tuple_for_empty_list() -> None:
    assert _build_sources([]) == ()


def test_build_sources_directional_omits_radial_fields() -> None:
    sources = _build_sources(
        [
            {
                "source_type": "Directional",
                "amplitude": 0.4,
                "wavelength": 0.2,
                "phase": 0.0,
                "weight": 1.0,
                "function": "Sinusoidal",
                "irregularity": 0.0,
                "complexity": 0.0,
                "direction": 90.0,
                "source_x": 0.3,
                "source_y": 0.7,
            }
        ]
    )

    assert len(sources) == 1
    assert sources[0].direction == 90.0
    assert sources[0].source_x is None
    assert sources[0].source_y is None


def test_build_sources_radial_omits_direction() -> None:
    sources = _build_sources(
        [
            {
                "source_type": "Radial",
                "amplitude": 0.4,
                "wavelength": 0.2,
                "phase": 0.0,
                "weight": 1.0,
                "function": "Sinusoidal",
                "irregularity": 0.0,
                "complexity": 0.0,
                "direction": 90.0,
                "source_x": 0.3,
                "source_y": 0.7,
            }
        ]
    )

    assert len(sources) == 1
    assert sources[0].source_x == 0.3
    assert sources[0].source_y == 0.7
    assert sources[0].direction is None


def test_build_sources_uses_function_field() -> None:
    sources = _build_sources(
        [
            {
                "source_type": "Directional",
                "amplitude": 0.4,
                "wavelength": 0.2,
                "phase": 0.0,
                "weight": 1.0,
                "function": "Square",
                "irregularity": 0.0,
                "complexity": 0.0,
                "direction": 90.0,
                "source_x": 0.3,
                "source_y": 0.7,
            }
        ]
    )

    assert len(sources) == 1
    assert sources[0].function == "Square"


def test_build_sources_uses_irregularity_and_complexity_fields() -> None:
    sources = _build_sources(
        [
            {
                "source_type": "Directional",
                "amplitude": 0.4,
                "wavelength": 0.2,
                "phase": 0.0,
                "weight": 1.0,
                "function": "Sinusoidal",
                "irregularity": 0.6,
                "complexity": 0.8,
                "direction": 90.0,
                "source_x": 0.3,
                "source_y": 0.7,
            }
        ]
    )

    assert len(sources) == 1
    assert sources[0].irregularity == 0.6
    assert sources[0].complexity == 0.8


def test_build_with_full_phase9_configuration_returns_working_mesh_source() -> None:
    descriptor = build_mesh_source_descriptor()
    values = {spec.name: spec.default for spec in descriptor.parameters}
    values["envelope_type"] = "Radial"
    values["distortion_type"] = "Swirl"
    values["sources"] = [
        {
            "source_type": "Radial",
            "amplitude": 0.3,
            "wavelength": 0.15,
            "phase": 0.0,
            "weight": 1.0,
            "function": "Sinusoidal",
            "irregularity": 0.0,
            "complexity": 0.0,
            "direction": 0.0,
            "source_x": 0.2,
            "source_y": 0.8,
        }
    ]

    mesh_source = descriptor.build(values)
    mesh = mesh_source.get_mesh()

    assert mesh.is_valid is True
    assert len(mesh.vertices) > 0
    assert len(mesh.triangles) > 0


# --- Noise envelope end-to-end (ROADMAP Phase 10.5) ---


@pytest.mark.parametrize("noise_type", ["Gradient", "Voronoi"])
def test_build_with_noise_envelope_returns_working_mesh_source(noise_type: str) -> None:
    descriptor = build_mesh_source_descriptor()
    values = {spec.name: spec.default for spec in descriptor.parameters}
    values["envelope_type"] = "Noise"
    values["envelope_noise_type"] = noise_type

    mesh_source = descriptor.build(values)
    mesh = mesh_source.get_mesh()

    assert mesh.is_valid is True
    assert len(mesh.vertices) > 0
    assert len(mesh.triangles) > 0


# --- Noise distortion end-to-end (ROADMAP Phase 10.6) ---


def test_build_with_noise_distortion_returns_working_mesh_source() -> None:
    descriptor = build_mesh_source_descriptor()
    values = {spec.name: spec.default for spec in descriptor.parameters}
    values["distortion_type"] = "Noise"

    mesh_source = descriptor.build(values)
    mesh = mesh_source.get_mesh()

    assert mesh.is_valid is True
    assert len(mesh.vertices) > 0
    assert len(mesh.triangles) > 0


# --- include_automatic GUI-paraméter (2026-08-21-i kiegészítés) ---


def test_include_automatic_parameter_defaults_to_igen() -> None:
    descriptor = build_mesh_source_descriptor()

    spec = next(s for s in descriptor.parameters if s.name == "include_automatic")

    assert spec.default == "Igen"
    assert spec.choices == ("Igen", "Nem")


def test_build_with_include_automatic_nem_and_sources_returns_working_mesh_source() -> (
    None
):
    descriptor = build_mesh_source_descriptor()
    values = {spec.name: spec.default for spec in descriptor.parameters}
    values["include_automatic"] = "Nem"
    values["sources"] = [
        {
            "source_type": "Radial",
            "amplitude": 0.3,
            "wavelength": 0.15,
            "phase": 0.0,
            "weight": 1.0,
            "function": "Sinusoidal",
            "irregularity": 0.0,
            "complexity": 0.0,
            "direction": 0.0,
            "source_x": 0.5,
            "source_y": 0.5,
        }
    ]

    mesh_source = descriptor.build(values)
    mesh = mesh_source.get_mesh()

    assert mesh.is_valid is True
    assert len(mesh.vertices) > 0
    assert len(mesh.triangles) > 0


def test_build_with_include_automatic_nem_and_no_sources_raises() -> None:
    from plugins.relief_generator.exceptions import WaveSetValueError

    descriptor = build_mesh_source_descriptor()
    values = {spec.name: spec.default for spec in descriptor.parameters}
    values["include_automatic"] = "Nem"

    with pytest.raises(WaveSetValueError):
        descriptor.build(values).get_mesh()
