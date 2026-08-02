"""Mesh Import engine — STL betöltés, validálás, Mesh domain objektum előállítása.

Lásd: docs/specifications/MESH_IMPORT_SPEC.md.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal

import trimesh

from slicedesigner.engines.exceptions import InvalidMeshError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BoundingBox:
    """A Mesh tengelyhez igazított befoglaló doboza, mm-ben."""

    min: tuple[float, float, float]
    max: tuple[float, float, float]


class MeshWarningKind(Enum):
    """A Mesh Import által jelezhető, nem blokkoló figyelmeztetés-típusok."""

    NON_MANIFOLD = "non_manifold"
    UNIT_PLAUSIBILITY = "unit_plausibility"


@dataclass(frozen=True)
class MeshWarning:
    """Egyetlen, nem blokkoló figyelmeztetés a Mesh betöltése során."""

    kind: MeshWarningKind
    message: str


@dataclass(frozen=True)
class Mesh:
    """A Mesh Import engine kimenete: betöltött és validált háromszögháló.

    Lásd: MESH_IMPORT_SPEC.md 4. szakasz.
    """

    vertices: tuple[tuple[float, float, float], ...]
    triangles: tuple[tuple[int, int, int], ...]
    source_path: str
    bounding_box: BoundingBox
    is_valid: bool
    warnings: tuple[MeshWarning, ...]


def import_mesh(
    file_path: str,
    origin_alignment: Literal["none"] = "none",
    min_plausible_size_mm: float = 1.0,
    max_plausible_size_mm: float = 3000.0,
) -> Mesh:
    """STL fájl betöltése, geometriai és egység-plauzibilitási validálással.

    Args:
        file_path: A betöltendő STL fájl elérési útja (ASCII vagy bináris,
            automatikus felismeréssel).
        origin_alignment: Origókezelés betöltéskor. Jelenleg kizárólag
            ``"none"`` érvényes érték (a forrásfájl koordinátái
            változatlanok maradnak) — MESH_IMPORT_SPEC.md 5. szakasz.
        min_plausible_size_mm: A bounding box legkisebb elfogadott mérete
            (mm) az egység-plauzibilitási figyelmeztetéshez.
        max_plausible_size_mm: A bounding box legnagyobb elfogadott mérete
            (mm) az egység-plauzibilitási figyelmeztetéshez.

    Returns:
        A betöltött és validált Mesh objektum.

    Raises:
        InvalidMeshError: ha a fájl nem található vagy nem olvasható, ha a
            tartalma sem ASCII, sem bináris STL szerkezetként nem
            ismerhető fel, vagy ha a betöltött geometria üres/nulla méretű.
    """
    path = Path(file_path)
    if not path.is_file():
        raise InvalidMeshError(
            f"A megadott STL fájl nem található vagy nem olvasható: {file_path}"
        )

    try:
        loaded_mesh = trimesh.load_mesh(str(path), file_type="stl")
    except Exception as exc:
        raise InvalidMeshError(
            "A fájl tartalma sem ASCII, sem bináris STL szerkezetként nem "
            f"ismerhető fel: {file_path}"
        ) from exc

    vertex_count = loaded_mesh.vertices.shape[0]
    face_count = loaded_mesh.faces.shape[0]
    if vertex_count == 0 or face_count == 0:
        raise InvalidMeshError(f"A betöltött geometria üres: {file_path}")

    bounds = loaded_mesh.bounds
    size = bounds[1] - bounds[0]
    if float(size.max()) <= 0.0:
        raise InvalidMeshError(f"A betöltött geometria nulla méretű: {file_path}")

    bounding_box = BoundingBox(
        min=(float(bounds[0][0]), float(bounds[0][1]), float(bounds[0][2])),
        max=(float(bounds[1][0]), float(bounds[1][1]), float(bounds[1][2])),
    )

    warnings: list[MeshWarning] = []

    if not loaded_mesh.is_watertight:
        warnings.append(
            MeshWarning(
                kind=MeshWarningKind.NON_MANIFOLD,
                message="A geometria nem manifold / nem vízzáró.",
            )
        )

    size_below_min = bool((size < min_plausible_size_mm).any())
    size_above_max = bool((size > max_plausible_size_mm).any())
    if size_below_min or size_above_max:
        warnings.append(
            MeshWarning(
                kind=MeshWarningKind.UNIT_PLAUSIBILITY,
                message=(
                    "A modell mérete a bounding box alapján valószínűtlen "
                    f"(elfogadott tartomány: {min_plausible_size_mm}-"
                    f"{max_plausible_size_mm} mm)."
                ),
            )
        )

    for warning in warnings:
        logger.warning("%s: %s", warning.kind.value, warning.message)

    # origin_alignment jelenleg nem módosítja a koordinátákat
    # (MESH_IMPORT_SPEC.md 6. szakasz, 6. lépés).

    return Mesh(
        vertices=tuple(
            (float(vertex[0]), float(vertex[1]), float(vertex[2]))
            for vertex in loaded_mesh.vertices
        ),
        triangles=tuple(
            (int(face[0]), int(face[1]), int(face[2])) for face in loaded_mesh.faces
        ),
        source_path=str(file_path),
        bounding_box=bounding_box,
        is_valid=not warnings,
        warnings=tuple(warnings),
    )
