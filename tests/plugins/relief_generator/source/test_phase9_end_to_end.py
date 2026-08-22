"""Phase 9 (Wave Extension) end-to-end integrációs teszt.

Igazolja, hogy egy kevert Phase 9-konfiguráció (automatikus Directional
komponensek + explicit Radial és Directional forrás + Radial envelope +
Swirl distortion — mind a hat Phase 9 domain-építőelem legalább egyszer
szerepel) a teljes downstream SliceDesigner pipeline-on (WaveGenerator →
HeightField → ReliefGeometry → MeshGenerator → Mesh → MeshSource →
Slice Engine) hiba nélkül, érvényes eredménnyel végigfut.

Lásd: docs/plugins/relief_generator/WAVE_EXTENSION_IMPLEMENTATION_PLAN.md
6. szakasz, ROADMAP Phase 9.7.e.
"""

import sys
from pathlib import Path

# A `plugins/` névtér PEP 420 namespace package (l. ADR-0016). L. a
# `test_relief_generator_mesh_source.py` azonos mintáját.
_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from plugins.relief_generator.domain.amplitude_envelope import (  # noqa: E402
    LinearFalloff,
    RadialAmplitudeEnvelope,
)
from plugins.relief_generator.domain.multiple_wave_sources import (  # noqa: E402
    WaveSourceSpec,
)
from plugins.relief_generator.domain.procedural_distortion import (  # noqa: E402
    SwirlDistortion,
)
from plugins.relief_generator.domain.wave_parameters import WaveParameters  # noqa: E402
from plugins.relief_generator.source.relief_generator_mesh_source import (  # noqa: E402
    ReliefGeneratorMeshSource,
)
from plugins.relief_generator.source.relief_generator_parameters import (  # noqa: E402
    ReliefGeneratorParameters,
)
from slicedesigner.engines.slice_engine import (  # noqa: E402
    SliceAxis,
    create_slice_set,
)


def _make_mixed_phase9_parameters() -> ReliefGeneratorParameters:
    """Kevert Phase 9-konfiguráció: automatikus Directional komponensek
    + explicit Radial és Directional forrás + Radial envelope + Swirl
    distortion — mind a hat domain-építőelem legalább egyszer szerepel.
    """
    wave = WaveParameters(
        wavelength=0.25,
        amplitude=1.0,
        direction=35.0,
        direction_spread=40.0,
        irregularity=0.6,
        complexity=0.7,
        envelope=RadialAmplitudeEnvelope(
            center_x=0.5, center_y=0.5, radius=0.6, falloff=LinearFalloff()
        ),
        distortion=SwirlDistortion(
            center_x=0.5, center_y=0.5, radius=0.4, strength=0.8
        ),
        sources=(
            WaveSourceSpec(
                source_type="Radial",
                amplitude=0.3,
                wavelength=0.2,
                phase=0.0,
                weight=0.5,
                source_x=0.2,
                source_y=0.8,
            ),
            WaveSourceSpec(
                source_type="Directional",
                amplitude=0.2,
                wavelength=0.3,
                phase=0.5,
                weight=-0.3,
                direction=90.0,
            ),
        ),
    )
    return ReliefGeneratorParameters(
        width=20.0,
        height=15.0,
        base_thickness=2.0,
        relief_height=3.0,
        sampling_distance=1.0,
        wave=wave,
    )


def test_mixed_phase9_configuration_produces_valid_core_mesh() -> None:
    parameters = _make_mixed_phase9_parameters()

    mesh = ReliefGeneratorMeshSource(parameters).get_mesh()

    assert mesh.source_path is None
    assert mesh.is_valid is True
    assert mesh.warnings == ()
    assert len(mesh.vertices) > 0
    assert len(mesh.triangles) > 0


def test_mixed_phase9_configuration_mesh_bounding_box_matches_vertices() -> None:
    parameters = _make_mixed_phase9_parameters()

    mesh = ReliefGeneratorMeshSource(parameters).get_mesh()

    xs = [v[0] for v in mesh.vertices]
    ys = [v[1] for v in mesh.vertices]
    zs = [v[2] for v in mesh.vertices]
    assert mesh.bounding_box.min == (min(xs), min(ys), min(zs))
    assert mesh.bounding_box.max == (max(xs), max(ys), max(zs))


def test_mixed_phase9_configuration_mesh_is_sliceable_by_slice_engine() -> None:
    parameters = _make_mixed_phase9_parameters()
    mesh = ReliefGeneratorMeshSource(parameters).get_mesh()

    # A slice_thickness_mm-et a tényleges Z-kiterjedésből vezetjük le
    # (pontosan 5 egyenlő szeletre osztva), hogy a create_slice_set()
    # skálázási tűrése (alapértelmezetten 2%) semmilyen körülmények
    # között ne akadályozza a szeletelést, függetlenül attól, hogy a
    # kevert Phase 9-felület ténylegesen milyen Z-tartományt fed le
    # (a normalizált magasság a mesh-mintavételezési rácson nem
    # feltétlenül éri el pontosan a [0,1] széleket, szemben a
    # WaveGenerator belső 65x65-ös normalizálási rácsával).
    z_min, z_max = mesh.bounding_box.min[2], mesh.bounding_box.max[2]
    slice_thickness_mm = (z_max - z_min) / 5.0

    slice_set = create_slice_set(
        mesh,
        slice_thickness_mm=slice_thickness_mm,
        slice_axis=SliceAxis.Z,
        gap_mm=0.0,
    )

    assert slice_set.slice_count > 0
    assert len(slice_set.slices) == slice_set.slice_count
    for slice_ in slice_set.slices:
        assert len(slice_.contours) > 0


def test_mixed_phase9_configuration_is_deterministic() -> None:
    parameters = _make_mixed_phase9_parameters()

    first = ReliefGeneratorMeshSource(parameters).get_mesh()
    second = ReliefGeneratorMeshSource(parameters).get_mesh()

    assert first.vertices == second.vertices
    assert first.triangles == second.triangles
