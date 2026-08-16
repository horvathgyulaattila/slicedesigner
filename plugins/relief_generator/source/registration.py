"""Relief Generator MeshSource entry point regisztráció (ADR-0017).

A `slicedesigner.mesh_sources` entry point csoport ezen modul
`build_mesh_source_descriptor` függvényére mutat (l.
`plugins/relief_generator/pyproject.toml`). A core ezt hívja meg
discovery-kor — a visszaadott `MeshSourceDescriptor` teljesen
domain-semleges a core szempontjából (ADR-0017): a core sosem szembesül
a "Wave", "relief" stb. fogalmakkal, kizárólag `ParameterSpec`-ekkel.
"""

from __future__ import annotations

from typing import Any

from plugins.relief_generator.domain.wave_parameters import WaveParameters
from plugins.relief_generator.source.relief_generator_mesh_source import (
    ReliefGeneratorMeshSource,
)
from plugins.relief_generator.source.relief_generator_parameters import (
    ReliefGeneratorParameters,
)
from slicedesigner.project.mesh_source_registry import (
    MeshSourceDescriptor,
    ParameterSpec,
)

_PARAMETERS: tuple[ParameterSpec, ...] = (
    ParameterSpec(
        name="width",
        label="Szélesség",
        type="float",
        default=100.0,
        minimum=0.0001,
        unit="mm",
    ),
    ParameterSpec(
        name="height",
        label="Magasság",
        type="float",
        default=100.0,
        minimum=0.0001,
        unit="mm",
    ),
    ParameterSpec(
        name="base_thickness",
        label="Alap vastagsága",
        type="float",
        default=2.0,
        minimum=0.0,
        unit="mm",
    ),
    ParameterSpec(
        name="relief_height",
        label="Relief magassága",
        type="float",
        default=10.0,
        minimum=0.0,
        unit="mm",
    ),
    ParameterSpec(
        name="sampling_distance",
        label="Mintavételi távolság",
        type="float",
        default=1.0,
        minimum=0.01,
        unit="mm",
    ),
    ParameterSpec(
        name="wavelength",
        label="Hullámhossz",
        type="float",
        default=0.3,
        minimum=0.0001,
    ),
    ParameterSpec(
        name="amplitude",
        label="Amplitúdó",
        type="float",
        default=0.5,
        minimum=0.0001,
    ),
    ParameterSpec(
        name="direction",
        label="Irány",
        type="float",
        default=0.0,
        minimum=0.0,
        maximum=360.0,
        unit="°",
    ),
    ParameterSpec(
        name="direction_spread",
        label="Irányszórás",
        type="float",
        default=30.0,
        minimum=0.0,
        maximum=180.0,
        unit="°",
    ),
    ParameterSpec(
        name="irregularity",
        label="Szabálytalanság",
        type="float",
        default=0.3,
        minimum=0.0,
        maximum=1.0,
    ),
    ParameterSpec(
        name="complexity",
        label="Komplexitás",
        type="float",
        default=0.5,
        minimum=0.0,
        maximum=1.0,
    ),
)


def _build(values: dict[str, Any]) -> ReliefGeneratorMeshSource:
    """A generikus `values` dict-ből `ReliefGeneratorMeshSource`-t épít."""
    wave = WaveParameters(
        wavelength=values["wavelength"],
        amplitude=values["amplitude"],
        direction=values["direction"],
        direction_spread=values["direction_spread"],
        irregularity=values["irregularity"],
        complexity=values["complexity"],
    )
    parameters = ReliefGeneratorParameters(
        width=values["width"],
        height=values["height"],
        base_thickness=values["base_thickness"],
        relief_height=values["relief_height"],
        sampling_distance=values["sampling_distance"],
        wave=wave,
    )
    return ReliefGeneratorMeshSource(parameters)


def build_mesh_source_descriptor() -> MeshSourceDescriptor:
    """Az entry point által hívott factory — l. `pyproject.toml`."""
    return MeshSourceDescriptor(
        display_name="Relief Generator (Wave)",
        parameters=_PARAMETERS,
        build=_build,
    )
