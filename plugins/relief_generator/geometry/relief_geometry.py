"""Relief Geometry — a Height Fieldet fizikai relief-testté alakítja.

Lásd: docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 21. szakasz
(3. tétel: ReliefGeometry),
docs/plugins/relief_generator/RELIEF_GEOMETRY_MODEL.md 4., 8–10., 14., 23.
szakasz, docs/plugins/relief_generator/MESH_GENERATION_MODEL.md 29. szakasz.
"""

from dataclasses import dataclass
from typing import ClassVar

from plugins.relief_generator.domain.height_field import HeightField
from plugins.relief_generator.exceptions import ReliefGeometryValueError


@dataclass(frozen=True)
class ReliefGeometry:
    """Fizikai méretekkel rendelkező relief-test domainmodellje.

    A `ReliefGeometry` a `HeightField`-et (normalizált, `[0,1]x[0,1]`
    koordinátatéren értelmezett magasságfüggvényt) fizikai méretekkel —
    XY kiterjedéssel, alapvastagsággal és relief-magassággal — egészíti
    ki. Nem CAD-solid és nem mesh: a tényleges mintavételezés és
    rácsképzés a Mesh Generator (későbbi lépés) feladata.

    A test alsó felülete a koordinátarendszer `Z = 0` síkjában fekszik
    (`BOTTOM_Z`, l. RELIEF_GEOMETRY_MODEL.md 9., 23. szakasz). A felső
    felület magasságát a `top_z` metódus adja meg, a
    `base_thickness + H(x,y) * relief_height` képlet szerint
    (RELIEF_GEOMETRY_MODEL.md 8–9., 14. szakasz).

    Az összes mező kötelező (nincs alapérték), a létrehozott példány
    immutábilis (`frozen=True`). A mezők érvényességét a `__post_init__`
    fail-fast ellenőrzi.

    Attributes:
        width: a test fizikai X-kiterjedése. Szigorúan pozitív.
        height: a test fizikai Y-kiterjedése. Szigorúan pozitív.
        base_thickness: az alaptest vastagsága (az alap felső síkjának
            `Z`-koordinátája). Nem lehet negatív, a `0.0` érvényes.
        relief_height: a felső relief-felület maximális, az alaphoz
            viszonyított magassága. Nem lehet negatív, a `0.0` érvényes.
        top_surface: a relief felső felületét leíró, normalizált
            `HeightField`.
    """

    width: float
    height: float
    base_thickness: float
    relief_height: float
    top_surface: HeightField

    BOTTOM_Z: ClassVar[float] = 0.0
    """A test alsó síkjának `Z`-koordinátája — invariáns, nem konfigurálható."""

    def __post_init__(self) -> None:
        """Fail-fast validálja az összes mezőt a dokumentált tartományok szerint.

        Raises:
            ReliefGeometryValueError: ha a `width` vagy `height` nem
                szigorúan pozitív, vagy a `base_thickness`/`relief_height`
                negatív.
        """
        if not self.width > 0.0:
            raise ReliefGeometryValueError(
                "A width-nek szigorúan pozitívnak kell lennie, "
                f"kapott érték: {self.width}"
            )
        if not self.height > 0.0:
            raise ReliefGeometryValueError(
                "A height-nak szigorúan pozitívnak kell lennie, "
                f"kapott érték: {self.height}"
            )
        if not self.base_thickness >= 0.0:
            raise ReliefGeometryValueError(
                "A base_thickness-nek nem-negatívnak kell lennie, "
                f"kapott érték: {self.base_thickness}"
            )
        if not self.relief_height >= 0.0:
            raise ReliefGeometryValueError(
                "A relief_height-nak nem-negatívnak kell lennie, "
                f"kapott érték: {self.relief_height}"
            )

    def top_z(self, x: float, y: float) -> float:
        """Kiszámítja a relief felső felületének `Z`-koordinátáját egy ponton.

        Args:
            x: normalizált X-koordináta, a `[0.0, 1.0]` zárt
                intervallumból (a `top_surface` HeightField-del
                konzisztensen). A fizikai `X = x * width` leképezés nem
                ennek a metódusnak a feladata.
            y: normalizált Y-koordináta, a `[0.0, 1.0]` zárt
                intervallumból (a `top_surface` HeightField-del
                konzisztensen). A fizikai `Y = y * height` leképezés nem
                ennek a metódusnak a feladata.

        Returns:
            A `base_thickness + top_surface.query(x, y) * relief_height`
            képlettel számított `Z`-koordináta.

        Raises:
            HeightFieldValueError: ha `x` vagy `y` kívül esik a
                `[0.0, 1.0]` zárt intervallumon — a `top_surface.query`
                hívásából propagálva.
        """
        return self.base_thickness + self.top_surface.query(x, y) * self.relief_height
