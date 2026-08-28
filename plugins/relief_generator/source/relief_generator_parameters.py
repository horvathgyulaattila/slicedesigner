"""Relief Generator Parameters — a MeshSource adapter forrás-specifikus
bemeneti paramétereinek gyűjtő típusa.

Lásd: docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 15. szakasz
(MeshSource adapter), docs/MESH_SOURCE.md 3., 6. szakasz.
"""

from dataclasses import dataclass
from typing import Protocol

from plugins.relief_generator.domain.height_field import HeightField


class HeightFieldSource(Protocol):
    """A `ReliefGeneratorParameters` felszín-forrása — a konkrét generátor
    (Wave, Voronoi, ...) kiválasztásától független, egymetódusú szerződés
    (ROADMAP Phase 11.1). Minden megvalósítás a `generators/` rétegben él
    (pl. `WaveHeightFieldSource`, `VoronoiHeightFieldSource`), a saját
    paraméter-dataclass-át és a hozzá tartozó generátor-osztályt fogja
    össze — a `ReliefGeneratorMeshSource` sosem szembesül konkrét
    generátor-típussal.
    """

    def build_height_field(self) -> HeightField:
        """Előállítja a felszínt leíró, normalizált `HeightField`-et.

        Returns:
            A konkrét generátor kimenete, a `HeightField` szerződésének
            megfelelően (WAVE_FUNCTION_MODEL.md 18–20. szakasz,
            generátor-független kontraktus).
        """
        ...


@dataclass(frozen=True)
class ReliefGeneratorParameters:
    """A teljes Relief Generator pipeline bemeneti paramétereinek gyűjtője.

    Tisztán szállító (carrier) típus, saját validáció nélkül — minden
    mezőt a downstream konstruktorok (`ReliefGeometry.__post_init__`) és
    hívások (`MeshGenerator.generate()`, a `height_field_source` mögötti
    konkrét paraméter-dataclass `__post_init__`-je) validálnak a
    tényleges felhasználáskor, elkerülve a validációs logika duplikálását.

    Attributes:
        width: a relief-test fizikai X-kiterjedése (ld. `ReliefGeometry`).
        height: a relief-test fizikai Y-kiterjedése (ld. `ReliefGeometry`).
        base_thickness: az alaptest vastagsága (ld. `ReliefGeometry`).
        relief_height: a relief-magasság (ld. `ReliefGeometry`).
        sampling_distance: a mesh mintavételi sűrűsége, fizikai
            egységben (ld. `MeshGenerator.generate`).
        height_field_source: a felszínt előállító, konkrét generátor-
            típustól független forrás (ROADMAP Phase 11.1 — korábban
            `wave: WaveParameters` volt, l. `HeightFieldSource`).
    """

    width: float
    height: float
    base_thickness: float
    relief_height: float
    sampling_distance: float
    height_field_source: HeightFieldSource
