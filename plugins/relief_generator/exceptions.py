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
