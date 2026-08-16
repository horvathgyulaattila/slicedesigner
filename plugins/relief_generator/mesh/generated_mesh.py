"""GeneratedMesh — a Mesh Generator plugin-belső kimeneti típusa.

Lásd: docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 21. szakasz
(4. tétel: Mesh Generator),
docs/plugins/relief_generator/MESH_GENERATION_MODEL.md.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedMesh:
    """A Mesh Generator plugin-belső, validáció nélküli kimeneti típusa.

    Tisztán generátor-kimenet, nem felhasználói bemenet — emiatt (a
    `ReliefGeometry`-vel ellentétben) nincs `__post_init__` validációja.
    A `GeneratedMesh` **nem** azonos a SliceDesigner core `Mesh` típusával
    (`slicedesigner.engines.mesh_import.Mesh`): azzá a MeshSource adapter
    (5. lépés) alakítja majd, ez a réteg nem függ és nem is importálhat a
    `src/slicedesigner/` alól.

    Attributes:
        vertices: a mesh csúcspontjainak `(X, Y, Z)` fizikai (nem
            normalizált) koordinátái, a csúcsindex szerinti sorrendben.
        triangles: a mesh háromszögei; egyenként a három csúcs `vertices`-be
            mutató indexét tartalmazó hármas, a kifelé mutató normált
            eredményező, MESH_GENERATION_MODEL.md 36. szakasz szerinti
            bejárási sorrendben.
    """

    vertices: tuple[tuple[float, float, float], ...]
    triangles: tuple[tuple[int, int, int], ...]
