"""Geometric Surface Mesh Generator — a `GeometricSurface` szabályos
rácsos mesh-sé alakítása.

Önálló implementáció, nem osztja meg a triangulációs/vertex-indexelési
logikát a meglévő `MeshGenerator`-ral (l. ADR-0020, "Döntés" 2. pont).
A vertex-indexelés és a trianguláció ennek ellenére a MESH_GENERATION_MODEL.md
36. szakaszában rögzített sémát követi, mert az a séma geometria-független
(watertight, kifelé mutató normálú rácsos mesh bármely Z-forrásra).

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_RAW_MESH.md.
"""

from __future__ import annotations

import math

from plugins.relief_generator.domain.geometric_surface import GeometricSurface
from plugins.relief_generator.exceptions import GeometricSurfaceMeshGenerationError
from plugins.relief_generator.mesh.generated_mesh import GeneratedMesh
from plugins.relief_generator.mesh.mesh_validator import MeshValidator

MAX_SAMPLE_COUNT = 2_000_000
"""A megengedett legnagyobb `Nx * Ny` mintapontszám. Önálló érték, nem
importálva a meglévő `MeshGenerator` moduljából (l. ADR-0020) — azonos
számérték, tudatosan duplikálva a teljes függetlenség megtartásáért."""


def _top_index(i: int, j: int, nx: int) -> int:
    """A `(i, j)` rácspont top-felületi vertexindexe (MESH_GENERATION_MODEL.md §36)."""
    return j * nx + i


def _bottom_index(i: int, j: int, nx: int, ny: int) -> int:
    """A `(i, j)` rácspont bottom-felületi vertexindexe (MESH_GENERATION_MODEL.md
    §36)."""
    return nx * ny + j * nx + i


class GeometricSurfaceMeshGenerator:
    """A `GeometricSurface`-t szabályos rácson mintavételezett, watertight
    mesh-é alakítja.

    Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_RAW_MESH.md.

    A vertex-indexelés és a trianguláció a MESH_GENERATION_MODEL.md 36.
    szakaszában rögzített sémát követi, szó szerint, a meglévő
    `MeshGenerator`-tól függetlenül újraírva (ADR-0020).
    """

    def generate(
        self, surface: GeometricSurface, sampling_distance: float
    ) -> GeneratedMesh:
        """Legenerálja a `surface` reliefjének validált mesh-reprezentációját.

        Args:
            surface: a mintavételezendő `GeometricSurface`. A `raw_relief`
                mezőjét normalizált `[0,1] x [0,1]` tartományon hívja meg
                ez a metódus (ADR-0020) — a hívó felelőssége, hogy a
                `raw_relief` ezt a konvenciót kövesse.
            sampling_distance: a kívánt mintavételezési sűrűség, fizikai
                egységben — szigorúan pozitívnak kell lennie.

        Returns:
            A MESH_GENERATION_MODEL.md 36. szakasza szerint felépített,
            watertight `GeneratedMesh`.

        Raises:
            GeometricSurfaceMeshGenerationError: ha `sampling_distance`
                nem szigorúan pozitív, ha az ebből számított `Nx` vagy
                `Ny` mintaszám 2-nél kisebb, vagy ha `Nx * Ny` meghaladja
                a `MAX_SAMPLE_COUNT` korlátot — mindegyik ellenőrzés a
                tényleges mintavételezés megkezdése előtt fut le.
            MeshValidationError: ha a felépített mesh mégsem watertight.
                Helyes konstrukció mellett ez elméletileg nem fordulhat
                elő — fail-fast védőháló.
        """
        if not sampling_distance > 0.0:
            raise GeometricSurfaceMeshGenerationError(
                "A sampling_distance-nek szigorúan pozitívnak kell lennie, "
                f"kapott érték: {sampling_distance}"
            )

        nx = math.ceil(surface.width / sampling_distance)
        if nx < 2:
            raise GeometricSurfaceMeshGenerationError(
                "A width és sampling_distance alapján számított Nx "
                f"mintaszámnak legalább 2-nek kell lennie, kapott érték: {nx}"
            )

        ny = math.ceil(surface.height / sampling_distance)
        if ny < 2:
            raise GeometricSurfaceMeshGenerationError(
                "A height és sampling_distance alapján számított Ny "
                f"mintaszámnak legalább 2-nek kell lennie, kapott érték: {ny}"
            )

        if nx * ny > MAX_SAMPLE_COUNT:
            raise GeometricSurfaceMeshGenerationError(
                f"A kért rács ({nx}x{ny} = {nx * ny} mintapont) meghaladja "
                f"a MAX_SAMPLE_COUNT = {MAX_SAMPLE_COUNT} korlátot."
            )

        raw_cache, v_min, v_max = self._sample_raw_relief(surface, nx, ny)

        vertices = self._build_vertices(surface, nx, ny, raw_cache, v_min, v_max)
        triangles = self._build_triangles(nx, ny)
        mesh = GeneratedMesh(vertices=tuple(vertices), triangles=tuple(triangles))

        MeshValidator().validate(mesh)

        return mesh

    def _sample_raw_relief(
        self, surface: GeometricSurface, nx: int, ny: int
    ) -> tuple[list[list[float]], float, float]:
        """Egyetlen mintavételezési kör: kiértékeli a `raw_relief`-et minden
        rácsponton, pontosan egyszer, és levezeti a `v_min`/`v_max`
        határokat (IMAGE_RELIEF_RAW_MESH.md 5. szakasz).

        A rácspontokat normalizált `x_norm = i/(Nx-1)`, `y_norm = j/(Ny-1)`
        alakban számítja (nem a fizikai `X_i/width` úton), hogy a
        rács-határokon lebegőpontos kerekítés miatt se csúszhasson a
        `[0,1]` tartományon kívülre.

        Returns:
            `(raw_cache, v_min, v_max)` — `raw_cache[j][i]` a `(i,j)`
            rácsponton kiértékelt nyers `ReliefValue`; `v_min = min(0,
            min(cache))`, `v_max = max(0, max(cache))`.
        """
        raw_cache: list[list[float]] = [[0.0] * nx for _ in range(ny)]
        v_min = 0.0
        v_max = 0.0
        for j in range(ny):
            y_norm = j / (ny - 1)
            for i in range(nx):
                x_norm = i / (nx - 1)
                raw_value = surface.raw_relief(x_norm, y_norm)
                raw_cache[j][i] = raw_value
                if raw_value < v_min:
                    v_min = raw_value
                if raw_value > v_max:
                    v_max = raw_value
        return raw_cache, v_min, v_max

    def _build_vertices(
        self,
        surface: GeometricSurface,
        nx: int,
        ny: int,
        raw_cache: list[list[float]],
        v_min: float,
        v_max: float,
    ) -> list[tuple[float, float, float]]:
        """Legenerálja a top és bottom felület vertexeit `_top_index`/
        `_bottom_index` szerint. A top-felület `Z`-je a cache-elt nyers
        értékekből, a `surface.physical_z`-n keresztül; a bottom-felület
        `Z`-je mindig `0.0` (IMAGE_RELIEF_RAW_MESH.md 6. szakasz)."""
        vertices: list[tuple[float, float, float] | None] = [None] * (2 * nx * ny)
        for j in range(ny):
            y_norm = j / (ny - 1)
            physical_y = y_norm * surface.height
            for i in range(nx):
                x_norm = i / (nx - 1)
                physical_x = x_norm * surface.width
                z_top = surface.physical_z(raw_cache[j][i], v_min, v_max)
                vertices[_top_index(i, j, nx)] = (physical_x, physical_y, z_top)
                vertices[_bottom_index(i, j, nx, ny)] = (physical_x, physical_y, 0.0)
        return vertices  # type: ignore[return-value]

    def _build_triangles(self, nx: int, ny: int) -> list[tuple[int, int, int]]:
        """A top+bottom+4 oldalfal, watertight, kifelé mutató normálú
        triangulációja — a MESH_GENERATION_MODEL.md 36. szakaszában
        rögzített séma szó szerinti átvétele."""
        triangles: list[tuple[int, int, int]] = []

        for j in range(ny - 1):
            for i in range(nx - 1):
                v00 = _top_index(i, j, nx)
                v10 = _top_index(i + 1, j, nx)
                v01 = _top_index(i, j + 1, nx)
                v11 = _top_index(i + 1, j + 1, nx)
                triangles.append((v00, v10, v11))
                triangles.append((v00, v11, v01))

        for j in range(ny - 1):
            for i in range(nx - 1):
                v00 = _bottom_index(i, j, nx, ny)
                v10 = _bottom_index(i + 1, j, nx, ny)
                v01 = _bottom_index(i, j + 1, nx, ny)
                v11 = _bottom_index(i + 1, j + 1, nx, ny)
                triangles.append((v00, v11, v10))
                triangles.append((v00, v01, v11))

        for j in range(ny - 1):
            ta = _top_index(0, j, nx)
            tb = _top_index(0, j + 1, nx)
            ba = _bottom_index(0, j, nx, ny)
            bb = _bottom_index(0, j + 1, nx, ny)
            triangles.append((ba, ta, bb))
            triangles.append((bb, ta, tb))

        for j in range(ny - 1):
            ta = _top_index(nx - 1, j, nx)
            tb = _top_index(nx - 1, j + 1, nx)
            ba = _bottom_index(nx - 1, j, nx, ny)
            bb = _bottom_index(nx - 1, j + 1, nx, ny)
            triangles.append((ba, bb, ta))
            triangles.append((bb, tb, ta))

        for i in range(nx - 1):
            ta = _top_index(i, 0, nx)
            tb = _top_index(i + 1, 0, nx)
            ba = _bottom_index(i, 0, nx, ny)
            bb = _bottom_index(i + 1, 0, nx, ny)
            triangles.append((ba, bb, ta))
            triangles.append((bb, tb, ta))

        for i in range(nx - 1):
            ta = _top_index(i, ny - 1, nx)
            tb = _top_index(i + 1, ny - 1, nx)
            ba = _bottom_index(i, ny - 1, nx, ny)
            bb = _bottom_index(i + 1, ny - 1, nx, ny)
            triangles.append((ba, ta, bb))
            triangles.append((bb, ta, tb))

        return triangles
