"""Tesztek a `MeshValidator`-hoz.

Lásd: docs/plugins/relief_generator/MESH_GENERATION_MODEL.md 20., 28., 37.
szakasz (watertight mesh, hatókör-döntés a további validációkról),
docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 21. szakasz
(4. tétel: Mesh Generator).
"""

import sys
from pathlib import Path

import pytest

# A `plugins/` névtér PEP 420 namespace package (l. ADR-0016: nincs
# `plugins/__init__.py`, hogy az egyes pluginok később önálló csomagként
# leválaszthatók legyenek). A meglévő `tests/gui/` és `tests/project/`
# csomagok (saját `__init__.py`-jal) miatt a teljes tesztkészlet együttes
# futtatásakor a pytest a repo gyökér előtt a `tests/` könyvtárat is
# felveszi a `sys.path`-ra, ami egy azonos nevű, üres `tests/plugins/`
# namespace-szegmenst hoz létre — enélkül a `plugins.relief_generator`
# tévesen a tesztfa alá, nem a valódi forráscsomagba oldódna fel. Ezért a
# repo gyökeret explicit módon a `sys.path` elejére kell tenni, mielőtt a
# `plugins.relief_generator` névtér először importálásra kerül.
_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from plugins.relief_generator.domain.height_field import HeightField  # noqa: E402
from plugins.relief_generator.exceptions import MeshValidationError  # noqa: E402
from plugins.relief_generator.geometry.relief_geometry import (  # noqa: E402
    ReliefGeometry,
)
from plugins.relief_generator.mesh.generated_mesh import GeneratedMesh  # noqa: E402
from plugins.relief_generator.mesh.mesh_generator import MeshGenerator  # noqa: E402
from plugins.relief_generator.mesh.mesh_validator import MeshValidator  # noqa: E402


def _make_valid_mesh() -> GeneratedMesh:
    geometry = ReliefGeometry(
        width=10.0,
        height=7.0,
        base_thickness=2.0,
        relief_height=3.0,
        top_surface=HeightField(lambda x, y: 0.3 + 0.2 * x + 0.1 * y),
    )
    return MeshGenerator().generate(geometry, sampling_distance=2.0)


def test_valid_generated_mesh_does_not_raise() -> None:
    mesh = _make_valid_mesh()

    MeshValidator().validate(mesh)  # nem dob kivételt


def test_mesh_with_removed_triangle_raises_mesh_validation_error() -> None:
    # Egy érvényes (watertight) mesh háromszög-listájából egyetlen
    # háromszög eltávolítva: a törölt háromszög három éle a globális
    # él-számlálóban 2-ről 1-re csökken, ezért nyitott élt hagy maga
    # után — a `validate()`-nek ezt észlelnie kell.
    valid_mesh = _make_valid_mesh()
    broken_mesh = GeneratedMesh(
        vertices=valid_mesh.vertices,
        triangles=valid_mesh.triangles[:-1],
    )

    with pytest.raises(MeshValidationError):
        MeshValidator().validate(broken_mesh)
