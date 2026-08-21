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
