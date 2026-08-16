"""Height Field — generátor-független közös felületi reprezentáció.

Lásd: docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 9. és 19. szakasz,
docs/plugins/relief_generator/RELIEF_GEOMETRY_MODEL.md 6. szakasz,
docs/plugins/relief_generator/WAVE_FUNCTION_MODEL.md 12–13. szakasz.
"""

from typing import Callable

from plugins.relief_generator.exceptions import HeightFieldValueError

_COORDINATE_MIN = 0.0
_COORDINATE_MAX = 1.0
_HEIGHT_MIN = 0.0
_HEIGHT_MAX = 1.0


class HeightField:
    """Normalizált, determinisztikusan lekérdezhető magasságfüggvény.

    A `HeightField` egy már előállított, `[0,1]x[0,1]` normalizált
    koordinátatéren értelmezett, `[0,1]` értékkészletű magasságfüggvényt
    csomagol be. Nem tud semmit a mögötte álló matematikai modellről (pl.
    a Wave Generatorról) — kizárólag a közös, generátor-független
    felületi reprezentációt biztosítja a Surface Generator és a Geometry
    Layer között.

    A `HeightField` maga nem gyorsítótáraz és nem mintavételez: minden
    `query()` hívás közvetlenül a becsomagolt függvényt hívja meg. A
    determinizmus a becsomagolt függvény tulajdonsága, amit a
    `HeightField` nem kényszerít ki, csak feltételez és dokumentál.
    """

    def __init__(self, height_function: Callable[[float, float], float]) -> None:
        """Létrehoz egy `HeightField`-et egy már normalizált függvény köré.

        Args:
            height_function: normalizált `x, y` koordinátapárt (mindkettő
                a `[0.0, 1.0]` zárt intervallumból) `[0.0, 1.0]`
                magasságértékre képező, determinisztikus függvény. A
                determinizmust a hívó felelőssége biztosítani.
        """
        self._height_function = height_function

    def query(self, x: float, y: float) -> float:
        """Lekérdezi a magasságértéket egy normalizált koordinátán.

        Args:
            x: normalizált X-koordináta, a `[0.0, 1.0]` zárt
                intervallumból (a határértékek érvényesek).
            y: normalizált Y-koordináta, a `[0.0, 1.0]` zárt
                intervallumból (a határértékek érvényesek).

        Returns:
            A becsomagolt magasságfüggvény `(x, y)` pontban vett,
            `[0.0, 1.0]` intervallumba eső értéke.

        Raises:
            HeightFieldValueError: ha `x` vagy `y` kívül esik a
                `[0.0, 1.0]` zárt intervallumon, vagy ha a becsomagolt
                magasságfüggvény `[0.0, 1.0]` intervallumon kívüli
                értéket ad vissza (hibásan normalizált generátor elleni
                védőháló).
        """
        if not _COORDINATE_MIN <= x <= _COORDINATE_MAX:
            raise HeightFieldValueError(
                f"Az x koordinátának a [{_COORDINATE_MIN}, {_COORDINATE_MAX}] "
                f"zárt intervallumba kell esnie, kapott érték: {x}"
            )
        if not _COORDINATE_MIN <= y <= _COORDINATE_MAX:
            raise HeightFieldValueError(
                f"Az y koordinátának a [{_COORDINATE_MIN}, {_COORDINATE_MAX}] "
                f"zárt intervallumba kell esnie, kapott érték: {y}"
            )

        height = self._height_function(x, y)

        if not _HEIGHT_MIN <= height <= _HEIGHT_MAX:
            raise HeightFieldValueError(
                "A becsomagolt height_function visszatérési értékének a "
                f"[{_HEIGHT_MIN}, {_HEIGHT_MAX}] zárt intervallumba kell esnie, "
                f"kapott érték: {height} (x={x}, y={y})"
            )

        return height
