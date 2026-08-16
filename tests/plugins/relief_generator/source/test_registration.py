"""Tesztek a Relief Generator MeshSource entry point regisztrációjához
(ADR-0017).

Lásd: `plugins/relief_generator/source/registration.py`,
`plugins/relief_generator/pyproject.toml`.
"""

from plugins.relief_generator.source.registration import (
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


def test_build_with_default_values_returns_working_mesh_source() -> None:
    descriptor = build_mesh_source_descriptor()
    values = {spec.name: spec.default for spec in descriptor.parameters}

    mesh_source = descriptor.build(values)

    assert isinstance(mesh_source, ReliefGeneratorMeshSource)
    mesh = mesh_source.get_mesh()
    assert mesh.is_valid is True
    assert len(mesh.vertices) > 0
    assert len(mesh.triangles) > 0
