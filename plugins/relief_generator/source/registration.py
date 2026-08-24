"""Relief Generator MeshSource entry point regisztráció (ADR-0017).

A `slicedesigner.mesh_sources` entry point csoport ezen modul
`build_mesh_source_descriptor` függvényére mutat (l.
`plugins/relief_generator/pyproject.toml`). A core ezt hívja meg
discovery-kor — a visszaadott `MeshSourceDescriptor` teljesen
domain-semleges a core szempontjából (ADR-0017): a core sosem szembesül
a "Wave", "relief" stb. fogalmakkal, kizárólag `ParameterSpec`-ekkel.

A Phase 9.7.d óta a `_PARAMETERS` a Phase 9 (Wave Extension) `envelope`/
`distortion`/`sources` képességeit is GUI-konfigurálhatóvá teszi, egy
lapos, típusválasztó-enumes reprezentáción keresztül — l.
docs/plugins/relief_generator/WAVE_EXTENSION_IMPLEMENTATION_PLAN.md,
ROADMAP Phase 9.7.d.
"""

from __future__ import annotations

from typing import Any

from plugins.relief_generator.domain.amplitude_envelope import (
    GaussianFalloff,
    LinearFalloff,
    NoiseAmplitudeEnvelope,
    RadialAmplitudeEnvelope,
    SmoothFalloff,
)
from plugins.relief_generator.domain.multiple_wave_sources import WaveSourceSpec
from plugins.relief_generator.domain.procedural_distortion import (
    NoiseDistortion,
    SwirlDistortion,
)
from plugins.relief_generator.domain.procedural_noise import (
    GradientNoiseField,
    VoronoiNoiseField,
)
from plugins.relief_generator.domain.wave import AmplitudeEnvelope, Distortion
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
        group="Automatikus hullám",
    ),
    ParameterSpec(
        name="amplitude",
        label="Amplitúdó",
        type="float",
        default=0.5,
        minimum=0.0001,
        group="Automatikus hullám",
    ),
    ParameterSpec(
        name="direction",
        label="Irány",
        type="float",
        default=0.0,
        minimum=0.0,
        maximum=360.0,
        unit="°",
        group="Automatikus hullám",
    ),
    ParameterSpec(
        name="direction_spread",
        label="Irányszórás",
        type="float",
        default=30.0,
        minimum=0.0,
        maximum=180.0,
        unit="°",
        group="Automatikus hullám",
    ),
    ParameterSpec(
        name="irregularity",
        label="Szabálytalanság",
        type="float",
        default=0.3,
        minimum=0.0,
        maximum=1.0,
        group="Automatikus hullám",
    ),
    ParameterSpec(
        name="complexity",
        label="Komplexitás",
        type="float",
        default=0.5,
        minimum=0.0,
        maximum=1.0,
        group="Automatikus hullám",
    ),
    ParameterSpec(
        name="function",
        label="Hullámalak",
        type="enum",
        default="Sinusoidal",
        choices=("Sinusoidal", "Triangle", "Sawtooth", "Square"),
        group="Automatikus hullám",
    ),
    ParameterSpec(
        name="envelope_type",
        label="Envelope típusa",
        type="enum",
        default="None",
        choices=("None", "Radial", "Noise"),
        group="Envelope",
    ),
    ParameterSpec(
        name="envelope_center_x",
        label="Envelope center X",
        type="float",
        default=0.5,
        group="Envelope",
    ),
    ParameterSpec(
        name="envelope_center_y",
        label="Envelope center Y",
        type="float",
        default=0.5,
        group="Envelope",
    ),
    ParameterSpec(
        name="envelope_radius",
        label="Envelope sugár",
        type="float",
        default=0.3,
        minimum=0.0001,
        group="Envelope",
    ),
    ParameterSpec(
        name="envelope_falloff",
        label="Envelope lecsengés",
        type="enum",
        default="Linear",
        choices=("Linear", "Smooth", "Gaussian"),
        group="Envelope",
    ),
    ParameterSpec(
        name="envelope_sharpness",
        label="Envelope élesség (Gaussian)",
        type="float",
        default=1.0,
        minimum=0.0001,
        group="Envelope",
    ),
    ParameterSpec(
        name="envelope_noise_type",
        label="Envelope zaj típusa",
        type="enum",
        default="Gradient",
        choices=("Gradient", "Voronoi"),
        group="Envelope",
    ),
    ParameterSpec(
        name="envelope_noise_scale",
        label="Envelope zaj skála",
        type="float",
        default=0.3,
        minimum=0.0001,
        group="Envelope",
    ),
    ParameterSpec(
        name="envelope_noise_seed",
        label="Envelope zaj seed",
        type="int",
        default=0,
        group="Envelope",
    ),
    ParameterSpec(
        name="envelope_noise_octaves",
        label="Envelope zaj oktávok",
        type="int",
        default=1,
        minimum=1,
        group="Envelope",
    ),
    ParameterSpec(
        name="envelope_noise_persistence",
        label="Envelope zaj persistence",
        type="float",
        default=0.5,
        minimum=0.0001,
        group="Envelope",
    ),
    ParameterSpec(
        name="envelope_noise_lacunarity",
        label="Envelope zaj lacunarity",
        type="float",
        default=2.0,
        minimum=0.0001,
        group="Envelope",
    ),
    ParameterSpec(
        name="distortion_type",
        label="Torzítás típusa",
        type="enum",
        default="None",
        choices=("None", "Swirl", "Noise"),
        group="Torzítás",
    ),
    ParameterSpec(
        name="distortion_center_x",
        label="Torzítás center X",
        type="float",
        default=0.5,
        group="Torzítás",
    ),
    ParameterSpec(
        name="distortion_center_y",
        label="Torzítás center Y",
        type="float",
        default=0.5,
        group="Torzítás",
    ),
    ParameterSpec(
        name="distortion_radius",
        label="Torzítás sugár",
        type="float",
        default=0.3,
        minimum=0.0001,
        group="Torzítás",
    ),
    ParameterSpec(
        name="distortion_strength",
        label="Torzítás mértéke",
        type="float",
        default=1.0,
        group="Torzítás",
    ),
    ParameterSpec(
        name="distortion_noise_scale",
        label="Torzítás zaj skála",
        type="float",
        default=0.3,
        minimum=0.0001,
        group="Torzítás",
    ),
    ParameterSpec(
        name="distortion_noise_seed",
        label="Torzítás zaj seed",
        type="int",
        default=0,
        group="Torzítás",
    ),
    ParameterSpec(
        name="distortion_noise_octaves",
        label="Torzítás zaj oktávok",
        type="int",
        default=1,
        minimum=1,
        group="Torzítás",
    ),
    ParameterSpec(
        name="distortion_noise_persistence",
        label="Torzítás zaj persistence",
        type="float",
        default=0.5,
        minimum=0.0001,
        group="Torzítás",
    ),
    ParameterSpec(
        name="distortion_noise_lacunarity",
        label="Torzítás zaj lacunarity",
        type="float",
        default=2.0,
        minimum=0.0001,
        group="Torzítás",
    ),
    ParameterSpec(
        name="distortion_noise_strength",
        label="Torzítás zaj mértéke",
        type="float",
        default=0.1,
        group="Torzítás",
    ),
    ParameterSpec(
        name="sources",
        label="Explicit hullámforrások",
        type="list",
        default=[],
        item_schema=(
            ParameterSpec(
                name="source_type",
                label="Típus",
                type="enum",
                default="Directional",
                choices=("Directional", "Radial"),
            ),
            ParameterSpec(
                name="amplitude",
                label="Amplitúdó",
                type="float",
                default=0.3,
                minimum=0.0001,
            ),
            ParameterSpec(
                name="wavelength",
                label="Hullámhossz",
                type="float",
                default=0.2,
                minimum=0.0001,
            ),
            ParameterSpec(name="phase", label="Fázis", type="float", default=0.0),
            ParameterSpec(name="weight", label="Súly", type="float", default=1.0),
            ParameterSpec(
                name="function",
                label="Hullámalak",
                type="enum",
                default="Sinusoidal",
                choices=("Sinusoidal", "Triangle", "Sawtooth", "Square"),
            ),
            ParameterSpec(
                name="irregularity",
                label="Szabálytalanság",
                type="float",
                default=0.0,
                minimum=0.0,
                maximum=1.0,
            ),
            ParameterSpec(
                name="complexity",
                label="Komplexitás",
                type="float",
                default=0.0,
                minimum=0.0,
                maximum=1.0,
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
            ParameterSpec(name="source_x", label="Forrás X", type="float", default=0.5),
            ParameterSpec(name="source_y", label="Forrás Y", type="float", default=0.5),
        ),
    ),
    ParameterSpec(
        name="include_automatic",
        label="Automatikus hullám",
        type="enum",
        default="Igen",
        choices=("Igen", "Nem"),
        group="Automatikus hullám",
    ),
)


def _build_envelope(values: dict[str, Any]) -> AmplitudeEnvelope | None:
    """A `values` dict envelope-mezőiből épít `AmplitudeEnvelope`-ot.

    Args:
        values: a generikus form kitöltött értékei (legalább az
            `envelope_type` és — ha az nem `"None"` — a típusnak
            megfelelő `envelope_*` kulcsokat tartalmaznia kell).

    Returns:
        `None`, ha `values["envelope_type"] == "None"`; egy
        `RadialAmplitudeEnvelope`, ha `"Radial"`, a választott
        `envelope_falloff`-nak megfelelő `Falloff`-fal; egy
        `NoiseAmplitudeEnvelope`, ha `"Noise"`, a választott
        `envelope_noise_type`-nak megfelelő `GradientNoiseField`/
        `VoronoiNoiseField`-del (ROADMAP Phase 10.5).
    """
    if values["envelope_type"] == "None":
        return None
    if values["envelope_type"] == "Noise":
        noise: GradientNoiseField | VoronoiNoiseField
        if values["envelope_noise_type"] == "Gradient":
            noise = GradientNoiseField(
                scale=values["envelope_noise_scale"],
                seed=values["envelope_noise_seed"],
                octaves=values["envelope_noise_octaves"],
                persistence=values["envelope_noise_persistence"],
                lacunarity=values["envelope_noise_lacunarity"],
            )
            return NoiseAmplitudeEnvelope(noise=noise, input_min=-1.0, input_max=1.0)
        noise = VoronoiNoiseField(
            scale=values["envelope_noise_scale"],
            seed=values["envelope_noise_seed"],
        )
        return NoiseAmplitudeEnvelope(noise=noise)
    falloff: LinearFalloff | SmoothFalloff | GaussianFalloff
    if values["envelope_falloff"] == "Linear":
        falloff = LinearFalloff()
    elif values["envelope_falloff"] == "Smooth":
        falloff = SmoothFalloff()
    else:
        falloff = GaussianFalloff(sharpness=values["envelope_sharpness"])
    return RadialAmplitudeEnvelope(
        center_x=values["envelope_center_x"],
        center_y=values["envelope_center_y"],
        radius=values["envelope_radius"],
        falloff=falloff,
    )


def _build_distortion(values: dict[str, Any]) -> Distortion | None:
    """A `values` dict distortion-mezőiből épít `Distortion`-t.

    Args:
        values: a generikus form kitöltött értékei (legalább a
            `distortion_type` és — ha az nem `"None"` — a típusnak
            megfelelő `distortion_*` kulcsokat tartalmaznia kell).

    Returns:
        `None`, ha `values["distortion_type"] == "None"`; egy
        `SwirlDistortion`, ha `"Swirl"`; egy `NoiseDistortion`, ha
        `"Noise"` (ROADMAP Phase 10.6), két, egymástól dekorrelált
        (`seed`/`seed+1`) `GradientNoiseField`-del.
    """
    if values["distortion_type"] == "None":
        return None
    if values["distortion_type"] == "Noise":
        noise_x = GradientNoiseField(
            scale=values["distortion_noise_scale"],
            seed=values["distortion_noise_seed"],
            octaves=values["distortion_noise_octaves"],
            persistence=values["distortion_noise_persistence"],
            lacunarity=values["distortion_noise_lacunarity"],
        )
        noise_y = GradientNoiseField(
            scale=values["distortion_noise_scale"],
            seed=values["distortion_noise_seed"] + 1,
            octaves=values["distortion_noise_octaves"],
            persistence=values["distortion_noise_persistence"],
            lacunarity=values["distortion_noise_lacunarity"],
        )
        return NoiseDistortion(
            noise_x=noise_x,
            noise_y=noise_y,
            strength=values["distortion_noise_strength"],
        )
    return SwirlDistortion(
        center_x=values["distortion_center_x"],
        center_y=values["distortion_center_y"],
        radius=values["distortion_radius"],
        strength=values["distortion_strength"],
    )


def _build_sources(source_values: list[dict[str, Any]]) -> tuple[WaveSourceSpec, ...]:
    """A `sources` lista-mező elemeiből épít `WaveSourceSpec`-tuple-t.

    Soronként a `source_type` alapján kizárólag a releváns mezőket adja
    át a `WaveSourceSpec`-nek (Directional esetén `direction`-t, Radial
    esetén `source_x`/`source_y`-t) — a `WaveSourceSpec` kölcsönösen
    kizárja a típus-specifikus mezőket (MULTIPLE_WAVE_SOURCES.md 4.
    szakasz).

    Args:
        source_values: a `sources` lista-mező soronkénti `values()`-ei
            (mindegyik az `item_schema` kulcsait tartalmazza).

    Returns:
        A megfelelő `WaveSourceSpec`-ekből álló tuple, a bemeneti sorrend
        megőrzésével.
    """
    sources: list[WaveSourceSpec] = []
    for item in source_values:
        if item["source_type"] == "Directional":
            sources.append(
                WaveSourceSpec(
                    source_type="Directional",
                    amplitude=item["amplitude"],
                    wavelength=item["wavelength"],
                    phase=item["phase"],
                    weight=item["weight"],
                    function=item["function"],
                    irregularity=item["irregularity"],
                    complexity=item["complexity"],
                    direction=item["direction"],
                )
            )
        else:
            sources.append(
                WaveSourceSpec(
                    source_type="Radial",
                    amplitude=item["amplitude"],
                    wavelength=item["wavelength"],
                    phase=item["phase"],
                    weight=item["weight"],
                    function=item["function"],
                    irregularity=item["irregularity"],
                    complexity=item["complexity"],
                    source_x=item["source_x"],
                    source_y=item["source_y"],
                )
            )
    return tuple(sources)


def _build(values: dict[str, Any]) -> ReliefGeneratorMeshSource:
    """A generikus `values` dict-ből `ReliefGeneratorMeshSource`-t épít."""
    wave = WaveParameters(
        wavelength=values["wavelength"],
        amplitude=values["amplitude"],
        direction=values["direction"],
        direction_spread=values["direction_spread"],
        irregularity=values["irregularity"],
        complexity=values["complexity"],
        function=values["function"],
        envelope=_build_envelope(values),
        distortion=_build_distortion(values),
        sources=_build_sources(values["sources"]),
        include_automatic=values["include_automatic"] == "Igen",
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
