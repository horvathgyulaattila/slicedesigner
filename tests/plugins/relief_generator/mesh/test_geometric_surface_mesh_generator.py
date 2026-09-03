"""Tesztek a `GeometricSurfaceMeshGenerator`-hez.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_RAW_MESH.md.
"""

import math
import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

import pytest  # noqa: E402

from plugins.relief_generator.domain.geometric_surface import (  # noqa: E402
    GeometricSurface,
)
from plugins.relief_generator.exceptions import (  # noqa: E402
    GeometricSurfaceMeshGenerationError,
)
from plugins.relief_generator.mesh.geometric_surface_mesh_generator import (  # noqa: E402
    GeometricSurfaceMeshGenerator,
)


def _make_surface(raw_relief, **overrides):
    defaults = dict(
        width=50.0,
        height=50.0,
        base_thickness=3.0,
        relief_height_raised=6.0,
        relief_height_recessed=1.5,
    )
    defaults.update(overrides)
    return GeometricSurface(raw_relief=raw_relief, **defaults)


def test_valid_generation_produces_expected_vertex_and_triangle_counts() -> None:
    surface = _make_surface(lambda x, y: 0.0, width=20.0, height=20.0)
    mesh = GeometricSurfaceMeshGenerator().generate(surface, sampling_distance=5.0)

    nx = math.ceil(20.0 / 5.0)
    ny = math.ceil(20.0 / 5.0)
    expected_vertices = 2 * nx * ny
    expected_triangles = 4 * (nx - 1) * (ny - 1) + 4 * (nx - 1) + 4 * (ny - 1)

    assert len(mesh.vertices) == expected_vertices
    assert len(mesh.triangles) == expected_triangles


def test_bottom_vertices_are_all_at_zero() -> None:
    surface = _make_surface(lambda x, y: 0.3, width=20.0, height=20.0)
    mesh = GeometricSurfaceMeshGenerator().generate(surface, sampling_distance=5.0)

    half = len(mesh.vertices) // 2
    bottom_vertices = mesh.vertices[half:]

    assert all(z == 0.0 for _, _, z in bottom_vertices)


def test_flat_zero_relief_yields_uniform_base_thickness_without_division() -> None:
    surface = _make_surface(
        lambda x, y: 0.0, base_thickness=3.0, width=20.0, height=20.0
    )
    mesh = GeometricSurfaceMeshGenerator().generate(surface, sampling_distance=5.0)

    half = len(mesh.vertices) // 2
    top_vertices = mesh.vertices[:half]

    assert all(z == 3.0 for _, _, z in top_vertices)


def test_uniform_positive_relief_scales_to_relief_height_raised() -> None:
    surface = _make_surface(
        lambda x, y: 0.4,
        base_thickness=3.0,
        relief_height_raised=6.0,
        width=20.0,
        height=20.0,
    )
    mesh = GeometricSurfaceMeshGenerator().generate(surface, sampling_distance=5.0)

    half = len(mesh.vertices) // 2
    top_vertices = mesh.vertices[:half]
    expected_z = 3.0 + (0.4 / 0.4) * 6.0

    assert all(z == pytest.approx(expected_z) for _, _, z in top_vertices)


def test_negative_relief_scales_with_relief_height_recessed() -> None:
    def raw_relief(x: float, y: float) -> float:
        return -0.4 if x < 0.5 else 0.0

    surface = _make_surface(
        raw_relief,
        base_thickness=3.0,
        relief_height_recessed=1.5,
        width=20.0,
        height=20.0,
    )
    mesh = GeometricSurfaceMeshGenerator().generate(surface, sampling_distance=5.0)

    half = len(mesh.vertices) // 2
    top_zs = [z for _, _, z in mesh.vertices[:half]]
    expected_recessed_z = 3.0 - (-0.4 / -0.4) * 1.5

    assert min(top_zs) == pytest.approx(expected_recessed_z)
    assert max(top_zs) == pytest.approx(3.0)


def test_sampling_distance_not_positive_raises() -> None:
    surface = _make_surface(lambda x, y: 0.0)

    with pytest.raises(GeometricSurfaceMeshGenerationError):
        GeometricSurfaceMeshGenerator().generate(surface, sampling_distance=0.0)


def test_nx_below_minimum_raises() -> None:
    surface = _make_surface(lambda x, y: 0.0, width=10.0, height=100.0)

    with pytest.raises(GeometricSurfaceMeshGenerationError):
        GeometricSurfaceMeshGenerator().generate(surface, sampling_distance=50.0)


def test_ny_below_minimum_raises() -> None:
    surface = _make_surface(lambda x, y: 0.0, width=100.0, height=10.0)

    with pytest.raises(GeometricSurfaceMeshGenerationError):
        GeometricSurfaceMeshGenerator().generate(surface, sampling_distance=50.0)


def test_max_sample_count_exceeded_raises() -> None:
    surface = _make_surface(lambda x, y: 0.0, width=100_000.0, height=100_000.0)

    with pytest.raises(GeometricSurfaceMeshGenerationError):
        GeometricSurfaceMeshGenerator().generate(surface, sampling_distance=0.01)


def test_generated_mesh_is_watertight_via_internal_validation() -> None:
    surface = _make_surface(
        lambda x, y: 0.2 if 0.3 < x < 0.7 else 0.0, width=30.0, height=20.0
    )

    # A generate() belsőleg MeshValidator-t hív; ha nem watertight, itt
    # MeshValidationError-t dobna. A sikeres visszatérés maga a bizonyíték.
    mesh = GeometricSurfaceMeshGenerator().generate(surface, sampling_distance=3.0)

    assert len(mesh.vertices) > 0
    assert len(mesh.triangles) > 0
