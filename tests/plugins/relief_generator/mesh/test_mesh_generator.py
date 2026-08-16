"""Tesztek a `MeshGenerator`-hoz.

Lásd: docs/plugins/relief_generator/MESH_GENERATION_MODEL.md 33., 36–37.
szakasz (alapvető invariánsok, vertex-/trianguláció-séma, hibakontraktus),
docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 21. szakasz
(4. tétel: Mesh Generator).
"""

import sys
import time
from collections import Counter
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
from plugins.relief_generator.exceptions import MeshGenerationError  # noqa: E402
from plugins.relief_generator.geometry.relief_geometry import (  # noqa: E402
    ReliefGeometry,
)
from plugins.relief_generator.mesh.generated_mesh import GeneratedMesh  # noqa: E402
from plugins.relief_generator.mesh.mesh_generator import (  # noqa: E402
    MAX_SAMPLE_COUNT,
    MeshGenerator,
)

_Vec3 = tuple[float, float, float]

# A `width=10.0`, `height=7.0`, `sampling_distance=2.0` választás pontosan
# `Nx=ceil(10/2)=5`, `Ny=ceil(7/2)=4` rácsot ad — ez a legtöbb lenti teszt
# közös alapja.
_NX = 5
_NY = 4
_SAMPLING_DISTANCE = 2.0


def _make_geometry(
    width: float = 10.0,
    height: float = 7.0,
    base_thickness: float = 2.0,
    relief_height: float = 3.0,
) -> ReliefGeometry:
    # Enyhén lejtős (nem konstans) felület: a Top Surface normálja így
    # ténylegesen a kereszttermék-alapú számítást teszteli, nem csak a
    # triviális, konstans-magasságú esetet. A lejtés elég kicsi ahhoz,
    # hogy a normál Z-komponense mindig domináns, tehát kifelé (+Z)
    # mutasson — ezt a `test_all_six_surfaces_have_outward_normals` teszt
    # numerikusan igazolja.
    top_surface = HeightField(lambda x, y: 0.3 + 0.2 * x + 0.1 * y)
    return ReliefGeometry(
        width=width,
        height=height,
        base_thickness=base_thickness,
        relief_height=relief_height,
        top_surface=top_surface,
    )


def _sub(a: _Vec3, b: _Vec3) -> _Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a: _Vec3, b: _Vec3) -> _Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a: _Vec3, b: _Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _triangle_normal(mesh: GeneratedMesh, triangle: tuple[int, int, int]) -> _Vec3:
    p_a, p_b, p_c = (mesh.vertices[index] for index in triangle)
    return _cross(_sub(p_b, p_a), _sub(p_c, p_a))


def test_generate_produces_expected_vertex_and_triangle_counts() -> None:
    geometry = _make_geometry()

    mesh = MeshGenerator().generate(geometry, sampling_distance=_SAMPLING_DISTANCE)

    assert len(mesh.vertices) == 2 * _NX * _NY
    expected_triangle_count = 4 * (_NX - 1) * (_NY - 1) + 4 * (_NY - 1) + 4 * (_NX - 1)
    assert len(mesh.triangles) == expected_triangle_count


def test_all_six_surfaces_have_outward_normals() -> None:
    # A generálási ciklus sorrendje (MESH_GENERATION_MODEL.md 36. szakasz,
    # `MeshGenerator._build_triangles`): Top, Bottom, X-, X+, Y-, Y+ — a
    # teszt ezt a sorrendet és az egyes csoportok méretét a rács
    # méretéből (`_NX`, `_NY`) függetlenül vezeti le, nem a generátor
    # belső metódusait hívva.
    geometry = _make_geometry()
    mesh = MeshGenerator().generate(geometry, sampling_distance=_SAMPLING_DISTANCE)

    groups: list[tuple[str, int, _Vec3]] = [
        ("top", 2 * (_NX - 1) * (_NY - 1), (0.0, 0.0, 1.0)),
        ("bottom", 2 * (_NX - 1) * (_NY - 1), (0.0, 0.0, -1.0)),
        ("x-", 2 * (_NY - 1), (-1.0, 0.0, 0.0)),
        ("x+", 2 * (_NY - 1), (1.0, 0.0, 0.0)),
        ("y-", 2 * (_NX - 1), (0.0, -1.0, 0.0)),
        ("y+", 2 * (_NX - 1), (0.0, 1.0, 0.0)),
    ]

    offset = 0
    for name, count, expected_direction in groups:
        for triangle in mesh.triangles[offset : offset + count]:
            normal = _triangle_normal(mesh, triangle)
            assert _dot(normal, expected_direction) > 0.0, (
                f"{name} felület {triangle} háromszögének normálja ({normal}) "
                "nem mutat kifelé"
            )
        offset += count

    assert offset == len(mesh.triangles)


def test_generated_mesh_is_watertight_via_explicit_edge_parity_check() -> None:
    geometry = _make_geometry()
    mesh = MeshGenerator().generate(geometry, sampling_distance=_SAMPLING_DISTANCE)

    edge_counts: Counter[tuple[int, int]] = Counter()
    for a, b, c in mesh.triangles:
        for u, v in ((a, b), (b, c), (c, a)):
            edge = (u, v) if u < v else (v, u)
            edge_counts[edge] += 1

    assert edge_counts
    assert all(count == 2 for count in edge_counts.values())


def test_generate_is_deterministic_across_repeated_calls() -> None:
    geometry = _make_geometry()
    generator = MeshGenerator()

    first = generator.generate(geometry, sampling_distance=_SAMPLING_DISTANCE)
    second = generator.generate(geometry, sampling_distance=_SAMPLING_DISTANCE)

    assert first == second


def test_geometric_invariants_hold_for_all_vertices() -> None:
    geometry = _make_geometry()
    mesh = MeshGenerator().generate(geometry, sampling_distance=_SAMPLING_DISTANCE)

    top_vertex_count = _NX * _NY
    for index, (x, y, z) in enumerate(mesh.vertices):
        assert 0.0 <= x <= geometry.width
        assert 0.0 <= y <= geometry.height
        assert z >= 0.0
        if index < top_vertex_count:
            assert (
                geometry.base_thickness
                <= z
                <= geometry.base_thickness + geometry.relief_height
            )


def test_non_positive_sampling_distance_raises() -> None:
    geometry = _make_geometry()

    with pytest.raises(MeshGenerationError):
        MeshGenerator().generate(geometry, sampling_distance=0.0)


def test_negative_sampling_distance_raises() -> None:
    geometry = _make_geometry()

    with pytest.raises(MeshGenerationError):
        MeshGenerator().generate(geometry, sampling_distance=-1.0)


def test_nx_below_minimum_raises() -> None:
    # width=10.0, sampling_distance=20.0 ⇒ Nx = ceil(10/20) = 1 < 2.
    geometry = _make_geometry(width=10.0)

    with pytest.raises(MeshGenerationError):
        MeshGenerator().generate(geometry, sampling_distance=20.0)


def test_ny_below_minimum_raises() -> None:
    # width=10.0, height=5.0, sampling_distance=6.0 ⇒
    # Nx = ceil(10/6) = 2 (érvényes), Ny = ceil(5/6) = 1 < 2.
    geometry = _make_geometry(width=10.0, height=5.0)

    with pytest.raises(MeshGenerationError):
        MeshGenerator().generate(geometry, sampling_distance=6.0)


def test_sample_count_above_maximum_raises_fast() -> None:
    # width=height=100_000.0, sampling_distance=1.0 ⇒ Nx=Ny=100_000, azaz
    # Nx*Ny=10_000_000_000 >> MAX_SAMPLE_COUNT — mindkét egyedi mintaszám
    # önmagában érvényes (>=2), tehát csakis a szorzat-korlát ellenőrzése
    # dobhatja a hibát. A teszt fut idejét is méri: a validációnak a
    # tényleges vertex-generálási ciklus megkezdése ELŐTT kell lefutnia,
    # különben egy 10 milliárd elemű rács legenerálása percekig tartana.
    geometry = _make_geometry(width=100_000.0, height=100_000.0)
    assert 100_000 * 100_000 > MAX_SAMPLE_COUNT  # a választott bemenet valóban túllépi

    started = time.perf_counter()
    with pytest.raises(MeshGenerationError):
        MeshGenerator().generate(geometry, sampling_distance=1.0)
    elapsed = time.perf_counter() - started

    assert elapsed < 2.0
