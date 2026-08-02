"""Tesztek a Mesh Import engine-hez (MESH_IMPORT_SPEC.md)."""

from pathlib import Path

import pytest
import trimesh

from slicedesigner.engines.exceptions import InvalidMeshError
from slicedesigner.engines.mesh_import import MeshWarningKind, import_mesh


def _export_stl(
    tmp_path: Path, mesh: trimesh.Trimesh, filename: str = "mesh.stl"
) -> str:
    """Egy trimesh.Trimesh objektum kiírása ideiglenes STL fájlba; visszaadja
    az útvonalat."""
    path = tmp_path / filename
    mesh.export(str(path), file_type="stl")
    return str(path)


def test_import_mesh_valid_box_no_warnings(tmp_path: Path) -> None:
    box = trimesh.creation.box(extents=(10.0, 20.0, 30.0))
    stl_path = _export_stl(tmp_path, box)

    mesh = import_mesh(stl_path)

    assert mesh.is_valid is True
    assert mesh.warnings == ()
    assert mesh.source_path == stl_path
    assert len(mesh.vertices) > 0
    assert len(mesh.triangles) > 0
    assert mesh.bounding_box.min == pytest.approx((-5.0, -10.0, -15.0))
    assert mesh.bounding_box.max == pytest.approx((5.0, 10.0, 15.0))


def test_import_mesh_missing_file_raises(tmp_path: Path) -> None:
    missing_path = str(tmp_path / "nincs_ilyen.stl")

    with pytest.raises(InvalidMeshError):
        import_mesh(missing_path)


def test_import_mesh_unrecognized_content_raises(tmp_path: Path) -> None:
    garbage_path = tmp_path / "nem_stl.stl"
    garbage_path.write_bytes(b"ez nem STL tartalom, csak sima szoveg" * 10)

    with pytest.raises(InvalidMeshError):
        import_mesh(str(garbage_path))


def test_import_mesh_empty_geometry_raises(tmp_path: Path) -> None:
    empty_stl_path = tmp_path / "ures.stl"
    empty_stl_path.write_text("solid empty\nendsolid empty\n")

    with pytest.raises(InvalidMeshError):
        import_mesh(str(empty_stl_path))


def test_import_mesh_non_watertight_warns(tmp_path: Path) -> None:
    box = trimesh.creation.box(extents=(10.0, 10.0, 10.0))
    box.faces = box.faces[:-1]  # egy lap eltávolítása -> nem vízzáró geometria
    stl_path = _export_stl(tmp_path, box, "non_watertight.stl")

    mesh = import_mesh(stl_path)

    assert mesh.is_valid is False
    assert any(w.kind is MeshWarningKind.NON_MANIFOLD for w in mesh.warnings)


def test_import_mesh_implausible_size_warns(tmp_path: Path) -> None:
    tiny_box = trimesh.creation.box(extents=(0.1, 0.1, 0.1))
    stl_path = _export_stl(tmp_path, tiny_box, "tiny.stl")

    mesh = import_mesh(
        stl_path, min_plausible_size_mm=1.0, max_plausible_size_mm=3000.0
    )

    assert mesh.is_valid is False
    assert any(w.kind is MeshWarningKind.UNIT_PLAUSIBILITY for w in mesh.warnings)


def test_import_mesh_default_origin_alignment_is_none(tmp_path: Path) -> None:
    box = trimesh.creation.box(extents=(10.0, 10.0, 10.0))
    stl_path = _export_stl(tmp_path, box)

    mesh = import_mesh(stl_path, origin_alignment="none")

    # origin_alignment="none" esetén a koordináták változatlanok maradnak
    # (MESH_IMPORT_SPEC.md 5-6. szakasz).
    assert mesh.bounding_box.min == pytest.approx((-5.0, -5.0, -5.0))
    assert mesh.bounding_box.max == pytest.approx((5.0, 5.0, 5.0))
