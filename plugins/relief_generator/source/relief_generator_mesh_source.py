"""Relief Generator MeshSource adapter — a plugin belső generálási láncát
a SliceDesigner `Mesh` szerződéséhez illeszti.

Lásd: docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 15. szakasz,
docs/MESH_SOURCE.md.
"""

from plugins.relief_generator.generators.wave_generator import WaveGenerator
from plugins.relief_generator.geometry.relief_geometry import ReliefGeometry
from plugins.relief_generator.mesh.generated_mesh import GeneratedMesh
from plugins.relief_generator.mesh.mesh_generator import MeshGenerator
from plugins.relief_generator.source.relief_generator_parameters import (
    ReliefGeneratorParameters,
)
from slicedesigner.engines.mesh_import import BoundingBox, Mesh


class ReliefGeneratorMeshSource:
    """A parametrikus Relief Generator MeshSource-adaptere.

    A `get_mesh()` a teljes generálási láncot végigfuttatja:
    `WaveGenerator → HeightField → ReliefGeometry → MeshGenerator →
    GeneratedMesh`, majd a `GeneratedMesh`-t a SliceDesigner core `Mesh`
    típusára alakítja (`source_path=None`, mivel generált, nem
    fájlból importált modellről van szó — MESH_SOURCE.md 5. szakasz).

    A downstream kivételek (`WaveGenerationError`, `ReliefGeometryValueError`,
    `MeshGenerationError`, `MeshValidationError`, `HeightFieldValueError`,
    `WaveParametersValueError`) nem kerülnek újra-csomagolásra, változatlanul
    propagálnak — a MeshSource fail-fast szerződését (MESH_SOURCE.md 9.
    szakasz) ezek a már meglévő, saját kivételek teljesítik.
    """

    def __init__(self, parameters: ReliefGeneratorParameters) -> None:
        """Létrehozza az adaptert a source-specifikus paraméterekkel.

        Args:
            parameters: a teljes generálási lánc bemeneti paraméterei.
        """
        self._parameters = parameters

    def get_mesh(self) -> Mesh:
        """Legenerálja és a core `Mesh` szerződésére alakítja a reliefet.

        Returns:
            A generált relief SliceDesigner-kompatibilis `Mesh`
            reprezentációja — `source_path=None`, `is_valid=True`,
            `warnings=()` (a `MeshGenerator.generate()` már fail-fast
            validál, ezért egy sikeresen visszatért mesh definíció
            szerint érvényes).

        Raises:
            WaveGenerationError: l. `WaveGenerator.generate`.
            ReliefGeometryValueError: l. `ReliefGeometry.__post_init__`.
            HeightFieldValueError: l. `HeightField.query`.
            MeshGenerationError: l. `MeshGenerator.generate`.
            MeshValidationError: l. `MeshGenerator.generate`.
        """
        height_field = WaveGenerator().generate(self._parameters.wave)

        geometry = ReliefGeometry(
            width=self._parameters.width,
            height=self._parameters.height,
            base_thickness=self._parameters.base_thickness,
            relief_height=self._parameters.relief_height,
            top_surface=height_field,
        )

        generated_mesh = MeshGenerator().generate(
            geometry, sampling_distance=self._parameters.sampling_distance
        )

        return self._to_core_mesh(generated_mesh)

    def _to_core_mesh(self, generated_mesh: GeneratedMesh) -> Mesh:
        """A plugin-belső `GeneratedMesh`-t core `Mesh`-re alakítja."""
        bounding_box = self._compute_bounding_box(generated_mesh.vertices)
        return Mesh(
            vertices=generated_mesh.vertices,
            triangles=generated_mesh.triangles,
            source_path=None,
            bounding_box=bounding_box,
            is_valid=True,
            warnings=(),
        )

    def _compute_bounding_box(
        self, vertices: tuple[tuple[float, float, float], ...]
    ) -> BoundingBox:
        """A vertexek tengelyhez igazított befoglaló dobozát számítja."""
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        zs = [v[2] for v in vertices]
        return BoundingBox(
            min=(min(xs), min(ys), min(zs)),
            max=(max(xs), max(ys), max(zs)),
        )
