"""Közös kivétel-hierarchia a Relief Generator pluginhoz.

A hierarchia szándékosan független a SliceDesigner core
`slicedesigner.engines.exceptions.SliceDesignerError` hierarchiájától — a
plugin nem importálhat core-internal modult (ADR-0015, ADR-0016).
"""


class ReliefGeneratorError(Exception):
    """A Relief Generator plugin összes kivételének közös bázisosztálya."""


class HeightFieldValueError(ReliefGeneratorError):
    """Érvénytelen bemeneti vagy kimeneti érték a `HeightField` lekérdezésekor.

    Akkor dobódik, ha a `HeightField.query` hívása során a bemeneti `x`
    vagy `y` koordináta, vagy a becsomagolt magasságfüggvény visszatérési
    értéke kívül esik a `[0.0, 1.0]` zárt intervallumon.
    """


class WaveParametersValueError(ReliefGeneratorError):
    """Érvénytelen `WaveParameters` mezőérték.

    Akkor dobódik, ha a `WaveParameters` létrehozásakor bármelyik mező
    kívül esik a dokumentált érvényességi tartományán (l.
    `WaveParameters` osztály docstringje).
    """


class WaveValueError(ReliefGeneratorError):
    """Érvénytelen `Wave` mezőérték.

    Akkor dobódik, ha a `Wave` létrehozásakor az `amplitude` vagy a
    `wavelength` nem szigorúan pozitív (l. `Wave` osztály docstringje,
    docs/plugins/relief_generator/WAVE_DOMAIN_MODEL.md 5.1–5.2 szakasz).
    """


class WaveSetValueError(ReliefGeneratorError):
    """Érvénytelen `WaveSet` állapot.

    Akkor dobódik, ha a `WaveSet` létrehozásakor a `waves` gyűjtemény
    üres (l. `WaveSet` osztály docstringje,
    docs/plugins/relief_generator/WAVE_DOMAIN_MODEL.md 9.1 szakasz).
    """


class RadialAmplitudeEnvelopeValueError(ReliefGeneratorError):
    """Érvénytelen `RadialAmplitudeEnvelope` mezőérték.

    Akkor dobódik, ha a `RadialAmplitudeEnvelope` létrehozásakor a
    `radius` nem szigorúan pozitív (l. `RadialAmplitudeEnvelope` osztály
    docstringje, docs/plugins/relief_generator/AMPLITUDE_ENVELOPE.md 2.
    szakasz).
    """


class GaussianFalloffValueError(ReliefGeneratorError):
    """Érvénytelen `GaussianFalloff` mezőérték.

    Akkor dobódik, ha a `GaussianFalloff` létrehozásakor a `sharpness`
    nem szigorúan pozitív (l. `GaussianFalloff` osztály docstringje,
    docs/plugins/relief_generator/AMPLITUDE_ENVELOPE.md 7., 9. szakasz).
    """


class NoiseAmplitudeEnvelopeValueError(ReliefGeneratorError):
    """Érvénytelen `NoiseAmplitudeEnvelope` mezőérték.

    Akkor dobódik, ha a `NoiseAmplitudeEnvelope` létrehozásakor az
    `input_max` nem szigorúan nagyobb, mint az `input_min` (l.
    `NoiseAmplitudeEnvelope` osztály docstringje,
    docs/plugins/relief_generator/AMPLITUDE_ENVELOPE.md 11. szakasz).
    """


class WaveSourceSpecValueError(ReliefGeneratorError):
    """Érvénytelen `WaveSourceSpec` mezőérték.

    Akkor dobódik, ha a `WaveSourceSpec` létrehozásakor az `amplitude`
    vagy a `wavelength` nem szigorúan pozitív, vagy a típus-specifikus
    mezők (`direction`, illetve `source_x`/`source_y`) nem a
    `source_type`-nak megfelelően vannak kitöltve (l. `WaveSourceSpec`
    osztály docstringje,
    docs/plugins/relief_generator/MULTIPLE_WAVE_SOURCES.md 4. szakasz).
    """


class SwirlDistortionValueError(ReliefGeneratorError):
    """Érvénytelen `SwirlDistortion` mezőérték.

    Akkor dobódik, ha a `SwirlDistortion` létrehozásakor a `radius` nem
    szigorúan pozitív (l. `SwirlDistortion` osztály docstringje,
    docs/plugins/relief_generator/PROCEDURAL_DISTORTION.md 3. szakasz).
    """


class ProceduralNoiseValueError(ReliefGeneratorError):
    """Érvénytelen `GradientNoiseField`/`VoronoiNoiseField` mezőérték.

    Akkor dobódik, ha a `scale` nem szigorúan pozitív, vagy (kizárólag
    `GradientNoiseField` esetén) az `octaves` 1-nél kisebb (l.
    docs/plugins/relief_generator/PROCEDURAL_NOISE.md).
    """


class WaveGenerationError(ReliefGeneratorError):
    """A Wave Generator nem tud érvényes Height Fieldet előállítani.

    Akkor dobódik, ha a `WaveGenerator.generate` a normalizáláshoz
    mintavételezett felület alapján degenerált esetet észlel (a
    mintavételezett maximum és minimum megegyezik, ezért a normalizálás
    nullával osztana). Elméletileg nem fordulhat elő érvényes
    `WaveParameters` mellett, mivel az `amplitude > 0` validáció ezt
    kizárja — fail-fast védőháló.
    """


class ReliefGeometryValueError(ReliefGeneratorError):
    """Érvénytelen `ReliefGeometry` mezőérték.

    Akkor dobódik, ha a `ReliefGeometry` létrehozásakor a `width` vagy
    `height` nem szigorúan pozitív, vagy a `base_thickness`/`relief_height`
    negatív (l. `ReliefGeometry` osztály docstringje).
    """


class MeshGenerationError(ReliefGeneratorError):
    """Érvénytelen sampling-paraméter vagy túl nagy mintapontszám.

    Akkor dobódik, ha a `MeshGenerator.generate` hívásakor a
    `sampling_distance` nem szigorúan pozitív, az ebből számított `Nx`
    vagy `Ny` mintaszám 2-nél kisebb, vagy a `Nx * Ny` szorzat meghaladja
    a `MAX_SAMPLE_COUNT` korlátot.
    """


class MeshValidationError(ReliefGeneratorError):
    """A generált mesh nem watertight.

    Akkor dobódik, ha a `MeshValidator.validate` során legalább egy
    (rendezetlen) él nem pontosan két háromszögben szerepel a mesh-ben.
    """


class VoronoiParametersValueError(ReliefGeneratorError):
    """Érvénytelen `VoronoiParameters` mezőérték.

    Akkor dobódik, ha a `VoronoiParameters` létrehozásakor a `scale` nem
    szigorúan pozitív (l. `VoronoiParameters` osztály docstringje,
    docs/plugins/relief_generator/VORONOI_RELIEF_GENERATOR.md,
    ROADMAP Phase 11.1).
    """


class CraterParametersValueError(ReliefGeneratorError):
    """Érvénytelen `CraterParameters` mezőérték.

    Akkor dobódik, ha a `CraterParameters` létrehozásakor a `scale` vagy
    a `power` nem szigorúan pozitív, a `radius` nem esik a `(0, 1]`
    tartományba, az `octaves` 1-nél kisebb, vagy a `lacunarity` nem
    szigorúan nagyobb 1.0-nál (l. `CraterParameters` osztály
    docstringje, docs/plugins/relief_generator/CRATER_RELIEF_GENERATOR.md,
    ROADMAP Phase 11.2).
    """


class DuneParametersValueError(ReliefGeneratorError):
    """Érvénytelen `DuneParameters` mezőérték.

    Akkor dobódik, ha a `DuneParameters` létrehozásakor a `base_scale`,
    a `ripple_wavelength`, a `ripple_amplitude` vagy a `warp_scale` nem
    szigorúan pozitív (l. `DuneParameters` osztály docstringje,
    docs/plugins/relief_generator/DUNE_RELIEF_GENERATOR.md,
    ROADMAP Phase 11.3).
    """


class WoodGrainParametersValueError(ReliefGeneratorError):
    """Érvénytelen `WoodGrainParameters` mezőérték.

    Akkor dobódik, ha a `WoodGrainParameters` létrehozásakor bármelyik
    mező kívül esik a dokumentált érvényességi tartományán (l.
    `WoodGrainParameters` osztály docstringje,
    docs/plugins/relief_generator/WOOD_GRAIN_RELIEF_GENERATOR.md,
    ROADMAP Phase 11.4).
    """


class RegionValueError(ReliefGeneratorError):
    """Érvénytelen `Region` mezőérték.

    Akkor dobódik, ha a `Region` létrehozásakor a `contribution` negatív
    (l. `Region` osztály docstringje,
    docs/plugins/relief_generator/IMAGE_RELIEF_REGION_MODEL.md 4. szakasz).
    """


class ImageInterpretationError(ReliefGeneratorError):
    """Érvénytelen hozzárendelési fájl, olvashatatlan kép, vagy nem
    hozzárendelt szín a képen.

    Akkor dobódik, ha a `interpret_image` hívása során a hozzárendelési
    JSON érvénytelen (üres `regions`, duplikált szín, negatív
    `color_tolerance`, hiányzó vagy köröket tartalmazó `parent`-
    hivatkozás), a kép/fájl nem olvasható be, vagy a képen olyan
    pixel található, amely sem egy deklarált régiószínhez, sem a
    háttérhez nem rendelhető a toleranciával (l.
    docs/plugins/relief_generator/IMAGE_RELIEF_INTERPRETATION.md 4.
    szakasz).
    """


class RegionResolutionError(ReliefGeneratorError):
    """A Region Resolver kontraktussértést észlelt.

    Akkor dobódik, ha a `resolve_regions` hívása során egy top-level
    Region `DepthBehavior`-ja `Inherit` (l.
    docs/plugins/relief_generator/IMAGE_RELIEF_REGION_RESOLUTION.md 4.
    szakasz).
    """


class EffectProcessingConflictError(ReliefGeneratorError):
    """Nem-rokon, ellentétes irányú EffectSpec-ütközés, egyértelmű
    feloldás nélkül.

    Akkor dobódik, ha a `combine` hívása során egy adott ponton
    legalább egy pozitív és legalább egy negatív `elevation`-ű,
    egymással nem rokon EffectSpec aktív, és egyikük sem rendelkezik
    egyértelmű, a többiek között maximális `TieBreakPriority`-val (l.
    docs/plugins/relief_generator/IMAGE_RELIEF_EFFECT_PROCESSING.md
    5–6. szakasz).
    """


class GeometricSurfaceValueError(ReliefGeneratorError):
    """Érvénytelen `GeometricSurface` mezőérték.

    Akkor dobódik, ha a `GeometricSurface` létrehozásakor a
    `base_thickness - relief_height_recessed` különbség nem szigorúan
    pozitív (l. `GeometricSurface` osztály docstringje,
    docs/plugins/relief_generator/IMAGE_RELIEF_GEOMETRIC_SURFACE.md 6.
    szakasz).
    """


class GeometricSurfaceMeshGenerationError(ReliefGeneratorError):
    """Érvénytelen sampling-paraméter vagy túl nagy mintapontszám a
    `GeometricSurfaceMeshGenerator` hívásakor.

    Akkor dobódik, ha a `GeometricSurfaceMeshGenerator.generate` hívásakor
    a `sampling_distance` nem szigorúan pozitív, az ebből számított `Nx`
    vagy `Ny` mintaszám 2-nél kisebb, vagy a `Nx * Ny` szorzat meghaladja
    a modul saját `MAX_SAMPLE_COUNT` korlátját. Önálló a meglévő
    `MeshGenerationError`-tól — l.
    docs/adr/0020-image-relief-raw-mesh-sampling-and-generator-independence.md
    ("Döntés" 2. pont).
    """
