"""Mesh Validator — a generált mesh watertight-tulajdonságának ellenőrzése.

Lásd: docs/plugins/relief_generator/MESH_GENERATION_MODEL.md 20., 28., 37.
szakasz, docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 21. szakasz
(4. tétel: Mesh Generator).
"""

from collections import Counter

from plugins.relief_generator.exceptions import MeshValidationError
from plugins.relief_generator.mesh.generated_mesh import GeneratedMesh


class MeshValidator:
    """Kizárólag a mesh watertight-tulajdonságát ellenőrzi.

    A MESH_GENERATION_MODEL.md §28 által felsorolt további
    Validator-ellenőrzések (degenerált face-ek, self-intersection) nem
    részei ennek az implementációnak — l. §21–22, §37: az első
    implementációban normál működés mellett nem várt esetek, tudatos
    hatókör-döntés, nem hiányosság.
    """

    def validate(self, mesh: GeneratedMesh) -> None:
        """Ellenőrzi, hogy a mesh minden (rendezetlen) éle pontosan két
        háromszögben szerepel-e.

        Minden háromszög három élét összegyűjti (a csúcsindex-párt
        rendezetlenként kezelve), majd ellenőrzi, hogy a teljes mesh-ben
        minden él pontosan kétszer fordul-e elő.

        Args:
            mesh: az ellenőrizendő `GeneratedMesh`.

        Raises:
            MeshValidationError: ha legalább egy él nem pontosan két
                háromszögben szerepel.
        """
        edge_counts: Counter[tuple[int, int]] = Counter()
        for a, b, c in mesh.triangles:
            for u, v in ((a, b), (b, c), (c, a)):
                edge = (u, v) if u < v else (v, u)
                edge_counts[edge] += 1

        bad_edges = [edge for edge, count in edge_counts.items() if count != 2]
        if bad_edges:
            example_edge = bad_edges[0]
            raise MeshValidationError(
                f"A mesh nem watertight: {len(bad_edges)} él nem pontosan "
                f"két háromszögben szerepel (pl. {example_edge}: "
                f"{edge_counts[example_edge]}x)."
            )
