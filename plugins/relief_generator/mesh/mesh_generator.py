"""Mesh Generator — a `ReliefGeometry` szabályos rácsos mesh-é alakítása.

A vertex-indexelés és a trianguláció szó szerinti forrása:
docs/plugins/relief_generator/MESH_GENERATION_MODEL.md 36. szakasz
(l. még 37. szakasz: hibakontraktus).
"""

import math

from plugins.relief_generator.exceptions import MeshGenerationError
from plugins.relief_generator.geometry.relief_geometry import ReliefGeometry
from plugins.relief_generator.mesh.generated_mesh import GeneratedMesh
from plugins.relief_generator.mesh.mesh_validator import MeshValidator

MAX_SAMPLE_COUNT = 2_000_000
"""A megengedett legnagyobb `Nx * Ny` mintapontszám (MESH_GENERATION_MODEL.md
37. szakasz). Ennél nagyobb rácsot igénylő bemenet `MeshGenerationError`-t
vált ki, a tényleges vertex-generálási ciklus megkezdése előtt."""


def _top_index(i: int, j: int, nx: int) -> int:
    """A `(i, j)` rácspont top-felületi vertexindexe (§36)."""
    return j * nx + i


def _bottom_index(i: int, j: int, nx: int, ny: int) -> int:
    """A `(i, j)` rácspont bottom-felületi vertexindexe (§36)."""
    return nx * ny + j * nx + i


class MeshGenerator:
    """A `ReliefGeometry`-t szabályos rácson mintavételezett, watertight mesh-é
    alakítja.

    A vertex-indexelés és a trianguláció a MESH_GENERATION_MODEL.md 36.
    szakaszában rögzített, numerikusan verifikált (kereszttermék-alapú
    normálellenőrzéssel és él-paritás alapú watertight-ellenőrzéssel
    tesztelt) sémát szó szerint követi — attól nem szabad eltérni.
    """

    def generate(
        self, geometry: ReliefGeometry, sampling_distance: float
    ) -> GeneratedMesh:
        """Legenerálja a `geometry` reliefjének validált mesh-reprezentációját.

        Args:
            geometry: a mintavételezendő relief-test.
            sampling_distance: a kívánt mintavételezési sűrűség, fizikai
                egységben — szigorúan pozitívnak kell lennie.

        Returns:
            A MESH_GENERATION_MODEL.md 36. szakasza szerint felépített,
            watertight `GeneratedMesh`.

        Raises:
            MeshGenerationError: ha `sampling_distance` nem szigorúan
                pozitív, ha az ebből számított `Nx` vagy `Ny` mintaszám
                2-nél kisebb, vagy ha `Nx * Ny` meghaladja a
                `MAX_SAMPLE_COUNT` korlátot — mindegyik ellenőrzés a
                tényleges vertex-generálás megkezdése előtt fut le.
            MeshValidationError: ha a felépített mesh mégsem watertight.
                Helyes konstrukció mellett ez elméletileg nem fordulhat
                elő — fail-fast védőháló (MESH_GENERATION_MODEL.md 37.).
        """
        if not sampling_distance > 0.0:
            raise MeshGenerationError(
                "A sampling_distance-nek szigorúan pozitívnak kell lennie, "
                f"kapott érték: {sampling_distance}"
            )

        nx = math.ceil(geometry.width / sampling_distance)
        if nx < 2:
            raise MeshGenerationError(
                "A width és sampling_distance alapján számított Nx "
                f"mintaszámnak legalább 2-nek kell lennie, kapott érték: {nx}"
            )

        ny = math.ceil(geometry.height / sampling_distance)
        if ny < 2:
            raise MeshGenerationError(
                "A height és sampling_distance alapján számított Ny "
                f"mintaszámnak legalább 2-nek kell lennie, kapott érték: {ny}"
            )

        if nx * ny > MAX_SAMPLE_COUNT:
            raise MeshGenerationError(
                f"A kért rács ({nx}x{ny} = {nx * ny} mintapont) meghaladja "
                f"a MAX_SAMPLE_COUNT = {MAX_SAMPLE_COUNT} korlátot."
            )

        vertices = self._build_vertices(geometry, nx, ny)
        triangles = self._build_triangles(nx, ny)
        mesh = GeneratedMesh(vertices=tuple(vertices), triangles=tuple(triangles))

        MeshValidator().validate(mesh)

        return mesh

    def _build_vertices(
        self, geometry: ReliefGeometry, nx: int, ny: int
    ) -> list[tuple[float, float, float]]:
        """Legenerálja a top és bottom felület vertexeit `top_index`/`bottom_index`
        szerint.

        A normalizált `x_norm`/`y_norm` koordinátákat közvetlenül
        `i / (Nx - 1)` és `j / (Ny - 1)` alakban számítja — NEM a fizikai
        `X_i / width` úton —, hogy a rács-határokon (`i = Nx-1`, `j = Ny-1`)
        lebegőpontos kerekítés miatt se csúszhasson `1.0` fölé, ami a
        `HeightField.query()` `[0.0, 1.0]` zárt intervallum-ellenőrzését
        hamisan megbuktatná.
        """
        vertices: list[tuple[float, float, float]] = [(0.0, 0.0, 0.0)] * (2 * nx * ny)
        for j in range(ny):
            y_norm = j / (ny - 1)
            y = y_norm * geometry.height
            for i in range(nx):
                x_norm = i / (nx - 1)
                x = x_norm * geometry.width
                z_top = geometry.top_z(x_norm, y_norm)
                vertices[_top_index(i, j, nx)] = (x, y, z_top)
                vertices[_bottom_index(i, j, nx, ny)] = (
                    x,
                    y,
                    ReliefGeometry.BOTTOM_Z,
                )
        return vertices

    def _build_triangles(self, nx: int, ny: int) -> list[tuple[int, int, int]]:
        """Felépíti mind a hat logikai felület háromszögeit, §36 szerint."""
        triangles: list[tuple[int, int, int]] = []
        triangles.extend(self._top_surface_triangles(nx, ny))
        triangles.extend(self._bottom_surface_triangles(nx, ny))
        triangles.extend(self._side_wall_triangles(nx, ny))
        return triangles

    def _top_surface_triangles(self, nx: int, ny: int) -> list[tuple[int, int, int]]:
        """Top Surface trianguláció (§36, "Top Surface")."""
        triangles: list[tuple[int, int, int]] = []
        for j in range(ny - 1):
            for i in range(nx - 1):
                v00 = _top_index(i, j, nx)
                v10 = _top_index(i + 1, j, nx)
                v01 = _top_index(i, j + 1, nx)
                v11 = _top_index(i + 1, j + 1, nx)
                triangles.append((v00, v10, v11))
                triangles.append((v00, v11, v01))
        return triangles

    def _bottom_surface_triangles(self, nx: int, ny: int) -> list[tuple[int, int, int]]:
        """Bottom Surface trianguláció (§36, "Bottom Surface")."""
        triangles: list[tuple[int, int, int]] = []
        for j in range(ny - 1):
            for i in range(nx - 1):
                v00 = _bottom_index(i, j, nx, ny)
                v10 = _bottom_index(i + 1, j, nx, ny)
                v01 = _bottom_index(i, j + 1, nx, ny)
                v11 = _bottom_index(i + 1, j + 1, nx, ny)
                triangles.append((v00, v11, v10))
                triangles.append((v00, v01, v11))
        return triangles

    def _side_wall_triangles(self, nx: int, ny: int) -> list[tuple[int, int, int]]:
        """Oldalfalak trianguláció (§36, "Oldalfalak")."""
        triangles: list[tuple[int, int, int]] = []

        # X- fal (i=0)
        for j in range(ny - 1):
            ta = _top_index(0, j, nx)
            tb = _top_index(0, j + 1, nx)
            ba = _bottom_index(0, j, nx, ny)
            bb = _bottom_index(0, j + 1, nx, ny)
            triangles.append((ba, ta, bb))
            triangles.append((bb, ta, tb))

        # X+ fal (i=Nx-1)
        for j in range(ny - 1):
            ta = _top_index(nx - 1, j, nx)
            tb = _top_index(nx - 1, j + 1, nx)
            ba = _bottom_index(nx - 1, j, nx, ny)
            bb = _bottom_index(nx - 1, j + 1, nx, ny)
            triangles.append((ba, bb, ta))
            triangles.append((bb, tb, ta))

        # Y- fal (j=0)
        for i in range(nx - 1):
            ta = _top_index(i, 0, nx)
            tb = _top_index(i + 1, 0, nx)
            ba = _bottom_index(i, 0, nx, ny)
            bb = _bottom_index(i + 1, 0, nx, ny)
            triangles.append((ba, bb, ta))
            triangles.append((bb, tb, ta))

        # Y+ fal (j=Ny-1)
        for i in range(nx - 1):
            ta = _top_index(i, ny - 1, nx)
            tb = _top_index(i + 1, ny - 1, nx)
            ba = _bottom_index(i, ny - 1, nx, ny)
            bb = _bottom_index(i + 1, ny - 1, nx, ny)
            triangles.append((ba, ta, bb))
            triangles.append((bb, ta, tb))

        return triangles
