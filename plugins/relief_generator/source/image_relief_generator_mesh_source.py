"""Image Relief Generator MeshSource adapter — a plugin Image Relief
Generator generálási láncát a SliceDesigner Mesh szerződéséhez illeszti.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_ORCHESTRATION.md,
docs/MESH_SOURCE.md.
"""

from __future__ import annotations

from PIL import Image

from plugins.relief_generator.domain.effect_processing import combine
from plugins.relief_generator.domain.geometric_surface import GeometricSurface
from plugins.relief_generator.domain.image_interpretation import interpret_image
from plugins.relief_generator.domain.region_resolution import resolve_regions
from plugins.relief_generator.mesh.generated_mesh import GeneratedMesh
from plugins.relief_generator.mesh.geometric_surface_mesh_generator import (
    GeometricSurfaceMeshGenerator,
)
from plugins.relief_generator.source.image_relief_generator_parameters import (
    ImageReliefGeneratorParameters,
)
from slicedesigner.engines.mesh_import import BoundingBox, Mesh


class ImageReliefGeneratorMeshSource:
    """Az Image Relief Generator MeshSource-adaptere.

    A `get_mesh()` a teljes láncot végigfuttatja: `interpret_image() →
    Region-erdő → resolve_regions() → EffectSpec[] → (a `raw_relief`
    closure-ön, a normalizált → kép abszolút pixel-koordináta
    leképezésen keresztül) → GeometricSurface →
    GeometricSurfaceMeshGenerator → GeneratedMesh`, majd a
    `GeneratedMesh`-t a SliceDesigner core `Mesh` típusára alakítja
    (`source_path=None`, a `ReliefGeneratorMeshSource` precedense
    szerint — generált, nem fájlból importált modell).

    A `raw_relief` closure normalizált `(x_norm, y_norm) ∈ [0,1]²`
    bemenetet vár, és a kép abszolút, diszkrét pixel-rácsának
    határpontjaihoz képezi le: `px = x_norm · (image_width − 1)`,
    `py = y_norm · (image_height − 1)` — a leképezés folytonos marad,
    nem kerekít/csonkol pixelre; az egész-pixel értelmezés a
    `Mask`-backend (`PixelSetMask.member`) belső döntése (l. `ADR-0020`
    kiegészítés).

    Az `interpret_image()` szerződése nem módosul; a kép méretét ez az
    osztály önállóan olvassa be egy második `Image.open()` hívással —
    ez azt is jelenti, hogy érvénytelen/üres `image_path` vagy
    `assignment_path` esetén az `interpret_image()` hívása már elsőként,
    fail-fast elbukik a saját `ImageInterpretationError`-jával, külön,
    e osztályhoz tartozó validáció nélkül.

    A downstream kivételek (`ImageInterpretationError`,
    `RegionResolutionError`, `EffectProcessingConflictError`,
    `GeometricSurfaceValueError`, `GeometricSurfaceMeshGenerationError`,
    `MeshValidationError`) nem kerülnek újracsomagolásra, változatlanul
    propagálnak.
    """

    def __init__(self, parameters: ImageReliefGeneratorParameters) -> None:
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
            `warnings=()`.

        Raises:
            ImageInterpretationError: l. `interpret_image`.
            RegionResolutionError: l. `resolve_regions`.
            EffectProcessingConflictError: l. `combine`.
            GeometricSurfaceValueError: l. `GeometricSurface.__post_init__`.
            GeometricSurfaceMeshGenerationError, MeshValidationError:
                l. `GeometricSurfaceMeshGenerator.generate`.
        """
        params = self._parameters

        region_tree = interpret_image(params.image_path, params.assignment_path)
        effect_specs = resolve_regions(region_tree)

        with Image.open(params.image_path) as image:
            image_width, image_height = image.size

        def raw_relief(x_norm: float, y_norm: float) -> float:
            px = x_norm * (image_width - 1)
            py = y_norm * (image_height - 1)
            return combine(effect_specs, px, py)

        surface = GeometricSurface(
            width=params.width,
            height=params.height,
            base_thickness=params.base_thickness,
            relief_height_raised=params.relief_height_raised,
            relief_height_recessed=params.relief_height_recessed,
            raw_relief=raw_relief,
        )

        generated_mesh = GeometricSurfaceMeshGenerator().generate(
            surface, params.sampling_distance
        )

        return self._to_core_mesh(generated_mesh)

    def _to_core_mesh(self, generated_mesh: GeneratedMesh) -> Mesh:
        """A plugin-belső `GeneratedMesh`-t core `Mesh`-re alakítja —
        a `ReliefGeneratorMeshSource._to_core_mesh` mintájának szó
        szerinti átvétele."""
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
        """A vertexek tengelyhez igazított befoglaló dobozát számítja —
        a `ReliefGeneratorMeshSource._compute_bounding_box` mintájának
        szó szerinti átvétele."""
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        zs = [v[2] for v in vertices]
        return BoundingBox(
            min=(min(xs), min(ys), min(zs)),
            max=(max(xs), max(ys), max(zs)),
        )
