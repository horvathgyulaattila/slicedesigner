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

A ROADMAP Phase 11.1 óta a `_PARAMETERS` egy `generator_type` enum-mal
(`"Wave"`/`"Voronoi"`) választja ki a tényleges generátort — a
Wave-specifikus mezők (11 db, a `visible_when` mechanizmuson keresztül,
ROADMAP Phase 11.0) csak `generator_type=="Wave"` esetén látszanak a
GUI-n, a Voronoi-specifikusak (`voronoi_scale`/`voronoi_seed`) csak
`generator_type=="Voronoi"` esetén.

A ROADMAP Phase 11.2 óta a `generator_type` egy harmadik választással,
`"Crater"`-rel bővült — a Holdkráter-specifikus mezők
(`crater_scale`/`crater_seed`/`crater_power`) csak
`generator_type=="Crater"` esetén látszanak a GUI-n; a meglévő Wave/
Voronoi mezők retrofit nélkül, változatlanul működnek tovább (a
`visible_when` egyenlőség-vizsgálat, nem felsorolás).

A ROADMAP Phase 11.3 ötödik (végleges) tervezete a Dűne-specifikus
mezőket 10-ről 23-ra bővítette, három alcsoportba rendezve ("Dűne —
alap" / "Dűne — fodor" / "Dűne — foltosság") — l.
docs/plugins/relief_generator/DUNE_RELIEF_GENERATOR.md.

A ROADMAP Phase 11.4 a `generator_type`-ot egy ötödik választással,
`"WoodGrain"`-nel bővítette — a Faerezet-specifikus mezők (16 db, két
alcsoportba rendezve: "Faerezet — alap" / "Faerezet — csomók") csak
`generator_type=="WoodGrain"` esetén látszanak a GUI-n; a meglévő
Wave/Voronoi/Crater/Dune mezők semmilyen módosítást nem igényeltek.
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
from plugins.relief_generator.domain.crater_parameters import CraterParameters
from plugins.relief_generator.domain.dune_parameters import DuneParameters
from plugins.relief_generator.domain.multiple_wave_sources import WaveSourceSpec
from plugins.relief_generator.domain.procedural_distortion import (
    NoiseDistortion,
    SwirlDistortion,
)
from plugins.relief_generator.domain.procedural_noise import (
    GradientNoiseField,
    VoronoiNoiseField,
)
from plugins.relief_generator.domain.voronoi_parameters import VoronoiParameters
from plugins.relief_generator.domain.wave import AmplitudeEnvelope, Distortion
from plugins.relief_generator.domain.wave_parameters import WaveParameters
from plugins.relief_generator.domain.wood_grain_parameters import (
    WoodGrainParameters,
)
from plugins.relief_generator.generators.crater_generator import (
    CraterHeightFieldSource,
)
from plugins.relief_generator.generators.dune_generator import DuneHeightFieldSource
from plugins.relief_generator.generators.voronoi_generator import (
    VoronoiHeightFieldSource,
)
from plugins.relief_generator.generators.wave_generator import WaveHeightFieldSource
from plugins.relief_generator.generators.wood_grain_generator import (
    WoodGrainHeightFieldSource,
)
from plugins.relief_generator.source.relief_generator_mesh_source import (
    ReliefGeneratorMeshSource,
)
from plugins.relief_generator.source.relief_generator_parameters import (
    HeightFieldSource,
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
        name="generator_type",
        label="Generátor",
        type="enum",
        default="Wave",
        choices=("Wave", "Voronoi", "Crater", "Dune", "WoodGrain"),
    ),
    ParameterSpec(
        name="wavelength",
        label="Hullámhossz",
        type="float",
        default=0.3,
        minimum=0.0001,
        group="Automatikus hullám",
        visible_when=("generator_type", "Wave"),
    ),
    ParameterSpec(
        name="amplitude",
        label="Amplitúdó",
        type="float",
        default=0.5,
        minimum=0.0001,
        group="Automatikus hullám",
        visible_when=("generator_type", "Wave"),
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
        visible_when=("generator_type", "Wave"),
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
        visible_when=("generator_type", "Wave"),
    ),
    ParameterSpec(
        name="irregularity",
        label="Szabálytalanság",
        type="float",
        default=0.3,
        minimum=0.0,
        maximum=1.0,
        group="Automatikus hullám",
        visible_when=("generator_type", "Wave"),
    ),
    ParameterSpec(
        name="complexity",
        label="Komplexitás",
        type="float",
        default=0.5,
        minimum=0.0,
        maximum=1.0,
        group="Automatikus hullám",
        visible_when=("generator_type", "Wave"),
    ),
    ParameterSpec(
        name="function",
        label="Hullámalak",
        type="enum",
        default="Sinusoidal",
        choices=("Sinusoidal", "Triangle", "Sawtooth", "Square"),
        group="Automatikus hullám",
        visible_when=("generator_type", "Wave"),
    ),
    ParameterSpec(
        name="envelope_type",
        label="Envelope típusa",
        type="enum",
        default="None",
        choices=("None", "Radial", "Noise"),
        group="Envelope",
        visible_when=("generator_type", "Wave"),
    ),
    ParameterSpec(
        name="envelope_center_x",
        label="Envelope center X",
        type="float",
        default=0.5,
        group="Envelope",
        visible_when=("envelope_type", "Radial"),
    ),
    ParameterSpec(
        name="envelope_center_y",
        label="Envelope center Y",
        type="float",
        default=0.5,
        group="Envelope",
        visible_when=("envelope_type", "Radial"),
    ),
    ParameterSpec(
        name="envelope_radius",
        label="Envelope sugár",
        type="float",
        default=0.3,
        minimum=0.0001,
        group="Envelope",
        visible_when=("envelope_type", "Radial"),
    ),
    ParameterSpec(
        name="envelope_falloff",
        label="Envelope lecsengés",
        type="enum",
        default="Linear",
        choices=("Linear", "Smooth", "Gaussian"),
        group="Envelope",
        visible_when=("envelope_type", "Radial"),
    ),
    ParameterSpec(
        name="envelope_sharpness",
        label="Envelope élesség (Gaussian)",
        type="float",
        default=1.0,
        minimum=0.0001,
        group="Envelope",
        visible_when=("envelope_falloff", "Gaussian"),
    ),
    ParameterSpec(
        name="envelope_noise_type",
        label="Envelope zaj típusa",
        type="enum",
        default="Gradient",
        choices=("Gradient", "Voronoi"),
        group="Envelope",
        visible_when=("envelope_type", "Noise"),
    ),
    ParameterSpec(
        name="envelope_noise_scale",
        label="Envelope zaj skála",
        type="float",
        default=0.3,
        minimum=0.0001,
        group="Envelope",
        visible_when=("envelope_type", "Noise"),
    ),
    ParameterSpec(
        name="envelope_noise_seed",
        label="Envelope zaj seed",
        type="int",
        default=0,
        group="Envelope",
        visible_when=("envelope_type", "Noise"),
    ),
    ParameterSpec(
        name="envelope_noise_octaves",
        label="Envelope zaj oktávok",
        type="int",
        default=1,
        minimum=1,
        group="Envelope",
        visible_when=("envelope_noise_type", "Gradient"),
    ),
    ParameterSpec(
        name="envelope_noise_persistence",
        label="Envelope zaj persistence",
        type="float",
        default=0.5,
        minimum=0.0001,
        group="Envelope",
        visible_when=("envelope_noise_type", "Gradient"),
    ),
    ParameterSpec(
        name="envelope_noise_lacunarity",
        label="Envelope zaj lacunarity",
        type="float",
        default=2.0,
        minimum=0.0001,
        group="Envelope",
        visible_when=("envelope_noise_type", "Gradient"),
    ),
    ParameterSpec(
        name="distortion_type",
        label="Torzítás típusa",
        type="enum",
        default="None",
        choices=("None", "Swirl", "Noise"),
        group="Torzítás",
        visible_when=("generator_type", "Wave"),
    ),
    ParameterSpec(
        name="distortion_center_x",
        label="Torzítás center X",
        type="float",
        default=0.5,
        group="Torzítás",
        visible_when=("distortion_type", "Swirl"),
    ),
    ParameterSpec(
        name="distortion_center_y",
        label="Torzítás center Y",
        type="float",
        default=0.5,
        group="Torzítás",
        visible_when=("distortion_type", "Swirl"),
    ),
    ParameterSpec(
        name="distortion_radius",
        label="Torzítás sugár",
        type="float",
        default=0.3,
        minimum=0.0001,
        group="Torzítás",
        visible_when=("distortion_type", "Swirl"),
    ),
    ParameterSpec(
        name="distortion_strength",
        label="Torzítás mértéke",
        type="float",
        default=1.0,
        group="Torzítás",
        visible_when=("distortion_type", "Swirl"),
    ),
    ParameterSpec(
        name="distortion_noise_scale",
        label="Torzítás zaj skála",
        type="float",
        default=0.3,
        minimum=0.0001,
        group="Torzítás",
        visible_when=("distortion_type", "Noise"),
    ),
    ParameterSpec(
        name="distortion_noise_seed",
        label="Torzítás zaj seed",
        type="int",
        default=0,
        group="Torzítás",
        visible_when=("distortion_type", "Noise"),
    ),
    ParameterSpec(
        name="distortion_noise_octaves",
        label="Torzítás zaj oktávok",
        type="int",
        default=1,
        minimum=1,
        group="Torzítás",
        visible_when=("distortion_type", "Noise"),
    ),
    ParameterSpec(
        name="distortion_noise_persistence",
        label="Torzítás zaj persistence",
        type="float",
        default=0.5,
        minimum=0.0001,
        group="Torzítás",
        visible_when=("distortion_type", "Noise"),
    ),
    ParameterSpec(
        name="distortion_noise_lacunarity",
        label="Torzítás zaj lacunarity",
        type="float",
        default=2.0,
        minimum=0.0001,
        group="Torzítás",
        visible_when=("distortion_type", "Noise"),
    ),
    ParameterSpec(
        name="distortion_noise_strength",
        label="Torzítás zaj mértéke",
        type="float",
        default=0.1,
        group="Torzítás",
        visible_when=("distortion_type", "Noise"),
    ),
    ParameterSpec(
        name="sources",
        label="Explicit hullámforrások",
        type="list",
        default=[],
        visible_when=("generator_type", "Wave"),
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
                visible_when=("source_type", "Directional"),
            ),
            ParameterSpec(
                name="source_x",
                label="Forrás X",
                type="float",
                default=0.5,
                visible_when=("source_type", "Radial"),
            ),
            ParameterSpec(
                name="source_y",
                label="Forrás Y",
                type="float",
                default=0.5,
                visible_when=("source_type", "Radial"),
            ),
        ),
    ),
    ParameterSpec(
        name="include_automatic",
        label="Automatikus hullám",
        type="enum",
        default="Igen",
        choices=("Igen", "Nem"),
        group="Automatikus hullám",
        visible_when=("generator_type", "Wave"),
    ),
    ParameterSpec(
        name="voronoi_scale",
        label="Voronoi skála",
        type="float",
        default=0.2,
        minimum=0.0001,
        group="Voronoi",
        visible_when=("generator_type", "Voronoi"),
    ),
    ParameterSpec(
        name="voronoi_seed",
        label="Voronoi seed",
        type="int",
        default=0,
        group="Voronoi",
        visible_when=("generator_type", "Voronoi"),
    ),
    ParameterSpec(
        name="crater_scale",
        label="Kráter skála",
        type="float",
        default=0.2,
        minimum=0.0001,
        group="Holdkráter",
        visible_when=("generator_type", "Crater"),
    ),
    ParameterSpec(
        name="crater_seed",
        label="Kráter seed",
        type="int",
        default=0,
        group="Holdkráter",
        visible_when=("generator_type", "Crater"),
    ),
    ParameterSpec(
        name="crater_radius",
        label="Kráter sugár",
        type="float",
        default=0.4,
        minimum=0.0001,
        maximum=1.0,
        group="Holdkráter",
        visible_when=("generator_type", "Crater"),
    ),
    ParameterSpec(
        name="crater_power",
        label="Kráter élesség",
        type="float",
        default=3.0,
        minimum=0.0001,
        group="Holdkráter",
        visible_when=("generator_type", "Crater"),
    ),
    ParameterSpec(
        name="crater_octaves",
        label="Kráter rétegek",
        type="int",
        default=3,
        minimum=1,
        group="Holdkráter",
        visible_when=("generator_type", "Crater"),
    ),
    ParameterSpec(
        name="crater_lacunarity",
        label="Kráter lacunarity",
        type="float",
        default=2.0,
        minimum=1.0001,
        group="Holdkráter",
        visible_when=("generator_type", "Crater"),
    ),
    ParameterSpec(
        name="dune_direction",
        label="Szélirány",
        type="float",
        default=0.0,
        minimum=0.0,
        maximum=360.0,
        unit="°",
        group="Dűne — alap",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_seed",
        label="Dűne seed",
        type="int",
        default=0,
        group="Dűne — alap",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_coarse_scale",
        label="Domb-alap skála (durva réteg)",
        type="float",
        default=0.2,
        minimum=0.0001,
        group="Dűne — alap",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_ridge_spacing",
        label="Gerincsűrűség szélirányban",
        type="float",
        default=0.9,
        minimum=0.0001,
        group="Dűne — alap",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_ridge_length",
        label="Gerincmegnyúlás keresztirányban",
        type="float",
        default=3.0,
        minimum=0.0001,
        group="Dűne — alap",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_asymmetry_strength",
        label="Aszimmetria erőssége",
        type="float",
        default=-0.012,
        group="Dűne — alap",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_fine_scale",
        label="Finomréteg skála",
        type="float",
        default=0.11,
        minimum=0.0001,
        group="Dűne — alap",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_fine_octaves",
        label="Finomréteg oktávok",
        type="int",
        default=2,
        minimum=1,
        group="Dűne — alap",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_fine_persistence",
        label="Finomréteg persistence",
        type="float",
        default=0.5,
        minimum=0.0001,
        group="Dűne — alap",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_fine_lacunarity",
        label="Finomréteg lacunarity",
        type="float",
        default=2.0,
        minimum=1.0001,
        group="Dűne — alap",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_detail_weight",
        label="Finomréteg súlya",
        type="float",
        default=0.15,
        minimum=0.0,
        group="Dűne — alap",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_ripple_wavelength_front",
        label="Elülső fodor hullámhossza",
        type="float",
        default=0.035,
        minimum=0.0001,
        group="Dűne — fodor",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_ripple_amplitude_front",
        label="Elülső fodor mértéke",
        type="float",
        default=0.055,
        minimum=0.0,
        group="Dűne — fodor",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_ripple_wavelength_back",
        label="Hátsó fodor hullámhossza",
        type="float",
        default=0.025,
        minimum=0.0001,
        group="Dűne — fodor",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_ripple_amplitude_back",
        label="Hátsó fodor mértéke",
        type="float",
        default=0.06,
        minimum=0.0,
        group="Dűne — fodor",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_ripple_warp_scale",
        label="Fodor kanyargás skála",
        type="float",
        default=0.04,
        minimum=0.0001,
        group="Dűne — fodor",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_ripple_warp_strength",
        label="Fodor kanyargás mértéke",
        type="float",
        default=0.015,
        group="Dűne — fodor",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_blend_low",
        label="Elülső/hátsó átmenet alsó küszöb",
        type="float",
        default=-6.0,
        group="Dűne — fodor",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_blend_high",
        label="Elülső/hátsó átmenet felső küszöb",
        type="float",
        default=6.0,
        group="Dűne — fodor",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_patch_dune_scale",
        label="Domb-szintű foltosság skála",
        type="float",
        default=0.2,
        minimum=0.0001,
        group="Dűne — foltosság",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_patch_dune_low",
        label="Domb-szintű foltosság alsó küszöb",
        type="float",
        default=-0.5,
        group="Dűne — foltosság",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_patch_dune_high",
        label="Domb-szintű foltosság felső küszöb",
        type="float",
        default=0.5,
        group="Dűne — foltosság",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="dune_patch_within_scale",
        label="Dombon-belüli foltosság skála",
        type="float",
        default=0.16,
        minimum=0.0001,
        group="Dűne — foltosság",
        visible_when=("generator_type", "Dune"),
    ),
    ParameterSpec(
        name="wood_direction",
        label="Szálirány",
        type="float",
        default=90.0,
        minimum=0.0,
        maximum=360.0,
        unit="°",
        group="Faerezet — alap",
        visible_when=("generator_type", "WoodGrain"),
    ),
    ParameterSpec(
        name="wood_seed",
        label="Faerezet seed",
        type="int",
        default=0,
        group="Faerezet — alap",
        visible_when=("generator_type", "WoodGrain"),
    ),
    ParameterSpec(
        name="wood_board_width",
        label="Deszkaszélesség",
        type="float",
        default=0.42,
        minimum=0.0001,
        group="Faerezet — alap",
        visible_when=("generator_type", "WoodGrain"),
    ),
    ParameterSpec(
        name="wood_ring_spacing",
        label="Gyűrűtávolság",
        type="float",
        default=0.09,
        minimum=0.0001,
        group="Faerezet — alap",
        visible_when=("generator_type", "WoodGrain"),
    ),
    ParameterSpec(
        name="wood_ring_octaves",
        label="Gyűrű oktávok",
        type="int",
        default=4,
        minimum=1,
        group="Faerezet — alap",
        visible_when=("generator_type", "WoodGrain"),
    ),
    ParameterSpec(
        name="wood_ring_persistence",
        label="Gyűrű persistence",
        type="float",
        default=0.55,
        minimum=0.0001,
        group="Faerezet — alap",
        visible_when=("generator_type", "WoodGrain"),
    ),
    ParameterSpec(
        name="wood_ring_lacunarity",
        label="Gyűrű lacunarity",
        type="float",
        default=2.3,
        minimum=1.0001,
        group="Faerezet — alap",
        visible_when=("generator_type", "WoodGrain"),
    ),
    ParameterSpec(
        name="wood_elongation_min",
        label="Flóderosság — minimum",
        type="float",
        default=5.0,
        minimum=0.0001,
        group="Faerezet — alap",
        visible_when=("generator_type", "WoodGrain"),
    ),
    ParameterSpec(
        name="wood_elongation_max",
        label="Flóderosság — maximum",
        type="float",
        default=50.0,
        minimum=0.0001,
        group="Faerezet — alap",
        visible_when=("generator_type", "WoodGrain"),
    ),
    ParameterSpec(
        name="wood_warp_scale",
        label="Bél-vonal hullámzás skála",
        type="float",
        default=0.35,
        minimum=0.0001,
        group="Faerezet — alap",
        visible_when=("generator_type", "WoodGrain"),
    ),
    ParameterSpec(
        name="wood_warp_strength",
        label="Bél-vonal hullámzás mértéke",
        type="float",
        default=0.02,
        group="Faerezet — alap",
        visible_when=("generator_type", "WoodGrain"),
    ),
    ParameterSpec(
        name="wood_ring_contrast",
        label="Kontraszt",
        type="float",
        default=0.6,
        minimum=0.0,
        group="Faerezet — alap",
        visible_when=("generator_type", "WoodGrain"),
    ),
    ParameterSpec(
        name="wood_knot_count_max",
        label="Csomók max. száma deszkánként",
        type="int",
        default=3,
        minimum=0,
        group="Faerezet — csomók",
        visible_when=("generator_type", "WoodGrain"),
    ),
    ParameterSpec(
        name="wood_knot_size_min",
        label="Csomóméret — minimum",
        type="float",
        default=0.006,
        minimum=0.0001,
        group="Faerezet — csomók",
        visible_when=("generator_type", "WoodGrain"),
    ),
    ParameterSpec(
        name="wood_knot_size_max",
        label="Csomóméret — maximum",
        type="float",
        default=0.06,
        minimum=0.0001,
        group="Faerezet — csomók",
        visible_when=("generator_type", "WoodGrain"),
    ),
    ParameterSpec(
        name="wood_knot_ghost_probability",
        label="Szellem-csomó valószínűség",
        type="float",
        default=0.3,
        minimum=0.0,
        maximum=1.0,
        group="Faerezet — csomók",
        visible_when=("generator_type", "WoodGrain"),
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
    height_field_source: HeightFieldSource
    if values["generator_type"] == "Voronoi":
        height_field_source = VoronoiHeightFieldSource(
            VoronoiParameters(
                scale=values["voronoi_scale"],
                seed=values["voronoi_seed"],
            )
        )
    elif values["generator_type"] == "Crater":
        height_field_source = CraterHeightFieldSource(
            CraterParameters(
                scale=values["crater_scale"],
                seed=values["crater_seed"],
                radius=values["crater_radius"],
                power=values["crater_power"],
                octaves=values["crater_octaves"],
                lacunarity=values["crater_lacunarity"],
            )
        )
    elif values["generator_type"] == "Dune":
        height_field_source = DuneHeightFieldSource(
            DuneParameters(
                direction=values["dune_direction"],
                seed=values["dune_seed"],
                coarse_scale=values["dune_coarse_scale"],
                ridge_spacing=values["dune_ridge_spacing"],
                ridge_length=values["dune_ridge_length"],
                asymmetry_strength=values["dune_asymmetry_strength"],
                fine_scale=values["dune_fine_scale"],
                fine_octaves=values["dune_fine_octaves"],
                fine_persistence=values["dune_fine_persistence"],
                fine_lacunarity=values["dune_fine_lacunarity"],
                detail_weight=values["dune_detail_weight"],
                ripple_wavelength_front=values["dune_ripple_wavelength_front"],
                ripple_amplitude_front=values["dune_ripple_amplitude_front"],
                ripple_wavelength_back=values["dune_ripple_wavelength_back"],
                ripple_amplitude_back=values["dune_ripple_amplitude_back"],
                ripple_warp_scale=values["dune_ripple_warp_scale"],
                ripple_warp_strength=values["dune_ripple_warp_strength"],
                blend_low=values["dune_blend_low"],
                blend_high=values["dune_blend_high"],
                patch_dune_scale=values["dune_patch_dune_scale"],
                patch_dune_low=values["dune_patch_dune_low"],
                patch_dune_high=values["dune_patch_dune_high"],
                patch_within_scale=values["dune_patch_within_scale"],
            )
        )
    elif values["generator_type"] == "WoodGrain":
        height_field_source = WoodGrainHeightFieldSource(
            WoodGrainParameters(
                direction=values["wood_direction"],
                seed=values["wood_seed"],
                board_width=values["wood_board_width"],
                ring_spacing=values["wood_ring_spacing"],
                ring_octaves=values["wood_ring_octaves"],
                ring_persistence=values["wood_ring_persistence"],
                ring_lacunarity=values["wood_ring_lacunarity"],
                elongation_min=values["wood_elongation_min"],
                elongation_max=values["wood_elongation_max"],
                warp_scale=values["wood_warp_scale"],
                warp_strength=values["wood_warp_strength"],
                knot_count_max=values["wood_knot_count_max"],
                knot_size_min=values["wood_knot_size_min"],
                knot_size_max=values["wood_knot_size_max"],
                knot_ghost_probability=values["wood_knot_ghost_probability"],
                ring_contrast=values["wood_ring_contrast"],
            )
        )
    else:
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
        height_field_source = WaveHeightFieldSource(wave)
    parameters = ReliefGeneratorParameters(
        width=values["width"],
        height=values["height"],
        base_thickness=values["base_thickness"],
        relief_height=values["relief_height"],
        sampling_distance=values["sampling_distance"],
        height_field_source=height_field_source,
    )
    return ReliefGeneratorMeshSource(parameters)


def build_mesh_source_descriptor() -> MeshSourceDescriptor:
    """Az entry point által hívott factory — l. `pyproject.toml`."""
    return MeshSourceDescriptor(
        display_name="Relief Generator",
        parameters=_PARAMETERS,
        build=_build,
    )
