"""Relief Generator Parameters — a MeshSource adapter forrás-specifikus
bemeneti paramétereinek gyűjtő típusa.

Lásd: docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 15. szakasz
(MeshSource adapter), docs/MESH_SOURCE.md 3., 6. szakasz.
"""

from dataclasses import dataclass

from plugins.relief_generator.domain.wave_parameters import WaveParameters


@dataclass(frozen=True)
class ReliefGeneratorParameters:
    """A teljes Relief Generator pipeline bemeneti paramétereinek gyűjtője.

    Tisztán szállító (carrier) típus, saját validáció nélkül — minden
    mezőt a downstream konstruktorok (`ReliefGeometry.__post_init__`) és
    hívások (`MeshGenerator.generate()`, `WaveParameters.__post_init__`)
    validálnak a tényleges felhasználáskor, elkerülve a validációs logika
    duplikálását.

    Attributes:
        width: a relief-test fizikai X-kiterjedése (ld. `ReliefGeometry`).
        height: a relief-test fizikai Y-kiterjedése (ld. `ReliefGeometry`).
        base_thickness: az alaptest vastagsága (ld. `ReliefGeometry`).
        relief_height: a relief-magasság (ld. `ReliefGeometry`).
        sampling_distance: a mesh mintavételi sűrűsége, fizikai
            egységben (ld. `MeshGenerator.generate`).
        wave: a Wave Generator bemeneti paraméterei.
    """

    width: float
    height: float
    base_thickness: float
    relief_height: float
    sampling_distance: float
    wave: WaveParameters
