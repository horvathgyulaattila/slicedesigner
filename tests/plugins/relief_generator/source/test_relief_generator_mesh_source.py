"""Tesztek a `ReliefGeneratorMeshSource`-hoz.

Lásd: docs/plugins/relief_generator/IMPLEMENTATION_PLAN.md 15. szakasz
(MeshSource adapter), docs/MESH_SOURCE.md.
"""

import sys
from pathlib import Path

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

import pytest  # noqa: E402

from plugins.relief_generator.domain.wave_parameters import (  # noqa: E402
    WaveParameters,
)
from plugins.relief_generator.exceptions import (  # noqa: E402
    MeshGenerationError,
    ReliefGeometryValueError,
)
from plugins.relief_generator.generators.wave_generator import (  # noqa: E402
    WaveHeightFieldSource,
)
from plugins.relief_generator.source.relief_generator_mesh_source import (  # noqa: E402
    ReliefGeneratorMeshSource,
)
from plugins.relief_generator.source.relief_generator_parameters import (  # noqa: E402
    ReliefGeneratorParameters,
)


def _make_parameters(
    width: float = 10.0,
    height: float = 7.0,
    base_thickness: float = 2.0,
    relief_height: float = 3.0,
    sampling_distance: float = 2.0,
) -> ReliefGeneratorParameters:
    wave = WaveParameters(
        wavelength=0.25,
        amplitude=1.0,
        direction=35.0,
        direction_spread=40.0,
        irregularity=0.6,
        complexity=0.7,
    )
    return ReliefGeneratorParameters(
        width=width,
        height=height,
        base_thickness=base_thickness,
        relief_height=relief_height,
        sampling_distance=sampling_distance,
        height_field_source=WaveHeightFieldSource(wave),
    )


def test_get_mesh_returns_valid_core_mesh() -> None:
    parameters = _make_parameters()

    mesh = ReliefGeneratorMeshSource(parameters).get_mesh()

    assert mesh.source_path is None
    assert mesh.is_valid is True
    assert mesh.warnings == ()
    assert len(mesh.vertices) > 0
    assert len(mesh.triangles) > 0


def test_get_mesh_bounding_box_matches_actual_vertex_extents() -> None:
    parameters = _make_parameters()

    mesh = ReliefGeneratorMeshSource(parameters).get_mesh()

    xs = [v[0] for v in mesh.vertices]
    ys = [v[1] for v in mesh.vertices]
    zs = [v[2] for v in mesh.vertices]
    assert mesh.bounding_box.min == (min(xs), min(ys), min(zs))
    assert mesh.bounding_box.max == (max(xs), max(ys), max(zs))


def test_get_mesh_is_deterministic_across_repeated_calls() -> None:
    parameters = _make_parameters()
    source = ReliefGeneratorMeshSource(parameters)

    first = source.get_mesh()
    second = source.get_mesh()

    assert first.vertices == second.vertices
    assert first.triangles == second.triangles


def test_get_mesh_propagates_relief_geometry_value_error_for_zero_width() -> None:
    parameters = _make_parameters(width=0.0)

    with pytest.raises(ReliefGeometryValueError):
        ReliefGeneratorMeshSource(parameters).get_mesh()


def test_get_mesh_propagates_mesh_generation_error_for_zero_sampling() -> None:
    parameters = _make_parameters(sampling_distance=0.0)

    with pytest.raises(MeshGenerationError):
        ReliefGeneratorMeshSource(parameters).get_mesh()
