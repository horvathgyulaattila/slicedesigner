"""Tesztek az `ImageReliefGeneratorMeshSource`-hoz.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_ORCHESTRATION.md,
docs/MESH_SOURCE.md.
"""

import json
import sys
from pathlib import Path

# L. `test_relief_generator_mesh_source.py` docstringje: a `plugins/`
# névtér PEP 420 namespace package, a repo gyökeret explicit a `sys.path`
# elejére kell tenni, mielőtt a `plugins.relief_generator` névtér először
# importálásra kerül.
_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

import pytest  # noqa: E402
from PIL import Image  # noqa: E402

from plugins.relief_generator.exceptions import (  # noqa: E402
    GeometricSurfaceValueError,
    ImageInterpretationError,
)
from plugins.relief_generator.source.image_relief_generator_mesh_source import (  # noqa: E402
    ImageReliefGeneratorMeshSource,
)
from plugins.relief_generator.source.image_relief_generator_parameters import (  # noqa: E402
    ImageReliefGeneratorParameters,
)


def _write_image(path: Path, pixels: list[list[tuple[int, int, int]]]) -> None:
    """`pixels[y][x]` alakú RGB-rácsból PNG-fájlt ír."""
    height = len(pixels)
    width = len(pixels[0])
    image = Image.new("RGB", (width, height))
    for y in range(height):
        for x in range(width):
            image.putpixel((x, y), pixels[y][x])
    image.save(path)


def _write_assignment(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def _make_parameters(
    tmp_path: Path,
    *,
    width: float = 10.0,
    height: float = 10.0,
    base_thickness: float = 3.0,
    relief_height_raised: float = 2.0,
    relief_height_recessed: float = 1.0,
    sampling_distance: float = 2.0,
    image_path: str | None = None,
    assignment_path: str | None = None,
) -> ImageReliefGeneratorParameters:
    if image_path is None:
        default_image_path = tmp_path / "image.png"
        _write_image(
            default_image_path,
            [
                [(139, 69, 19), (139, 69, 19)],
                [(139, 69, 19), (139, 69, 19)],
            ],
        )
        image_path = str(default_image_path)
    if assignment_path is None:
        default_assignment_path = tmp_path / "assignment.json"
        _write_assignment(
            default_assignment_path,
            {
                "regions": [
                    {
                        "color": "#8B4513",
                        "contribution": 0.5,
                        "depth_behavior": "raised",
                        "parent": None,
                    }
                ]
            },
        )
        assignment_path = str(default_assignment_path)
    return ImageReliefGeneratorParameters(
        image_path=image_path,
        assignment_path=assignment_path,
        width=width,
        height=height,
        base_thickness=base_thickness,
        relief_height_raised=relief_height_raised,
        relief_height_recessed=relief_height_recessed,
        sampling_distance=sampling_distance,
    )


def test_get_mesh_returns_valid_core_mesh(tmp_path: Path) -> None:
    parameters = _make_parameters(tmp_path)

    mesh = ImageReliefGeneratorMeshSource(parameters).get_mesh()

    assert mesh.source_path is None
    assert mesh.is_valid is True
    assert mesh.warnings == ()
    assert len(mesh.vertices) > 0
    assert len(mesh.triangles) > 0


def test_raw_relief_maps_normalized_corners_to_actual_pixel_corners(
    tmp_path: Path,
) -> None:
    """A `(0,0)`/`(1,1)` normalizált sarokpontok a kép tényleges
    sarok-pixeleihez rendelődnek — l. ADR-0020 kiegészítés.

    Egy 2×2-es képen a bal-felső pixel Raised (`+0.5`), a jobb-alsó
    Recessed (`-0.3`), a másik két pixel semleges — a `combine` a
    px-mapping alapján pontosan a megfelelő sarok-pixel elevation-jét
    kell hogy visszaadja a normalizált `(0,0)`/`(1,1)` mintapontokon.
    """
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    _write_image(
        image_path,
        [
            [(255, 0, 0), (255, 255, 255)],
            [(255, 255, 255), (0, 0, 255)],
        ],
    )
    _write_assignment(
        assignment_path,
        {
            "background": "#FFFFFF",
            "regions": [
                {
                    "color": "#FF0000",
                    "contribution": 0.5,
                    "depth_behavior": "raised",
                    "parent": None,
                },
                {
                    "color": "#0000FF",
                    "contribution": 0.3,
                    "depth_behavior": "recessed",
                    "parent": None,
                },
            ],
        },
    )
    parameters = _make_parameters(
        tmp_path,
        image_path=str(image_path),
        assignment_path=str(assignment_path),
        base_thickness=3.0,
        relief_height_raised=2.0,
        relief_height_recessed=1.0,
        sampling_distance=1.0,
    )

    mesh = ImageReliefGeneratorMeshSource(parameters).get_mesh()

    top_zs = [v[2] for v in mesh.vertices if v[2] != 0.0]
    # Raised sarok: base_thickness + relief_height_raised (v_max a saját
    # elevation-je, tehát a normalizálás 1.0-t ad).
    assert any(z == pytest.approx(3.0 + 2.0) for z in top_zs)
    # Recessed sarok: base_thickness - relief_height_recessed.
    assert any(z == pytest.approx(3.0 - 1.0) for z in top_zs)


def test_raw_relief_top_image_row_maps_to_upper_half_of_physical_y_range(
    tmp_path: Path,
) -> None:
    """A kép **felső** sora (py=0) a fizikai Y-tartomány **felső**
    (nagy-Y) felére képződik le, nem az aljára — l. ADR-0020
    "Kiegészítés (2026-09-04)" szakasza.

    Egy 2×2-es képen a felső sor (py=0) Raised, az alsó sor (py=1)
    semleges (háttér) — minden, `base_thickness`-nél magasabb Z-jű
    vertex fizikai Y-koordinátájának a teljes Y-tartomány felső felében
    kell lennie (`v[1] > height / 2`). A régi (hibás) `py = y_norm *
    (image_height - 1)` képlet mellett ez a teszt megbukna.
    """
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    _write_image(
        image_path,
        [
            [(255, 0, 0), (255, 0, 0)],
            [(255, 255, 255), (255, 255, 255)],
        ],
    )
    _write_assignment(
        assignment_path,
        {
            "background": "#FFFFFF",
            "regions": [
                {
                    "color": "#FF0000",
                    "contribution": 0.5,
                    "depth_behavior": "raised",
                    "parent": None,
                }
            ],
        },
    )
    height = 10.0
    parameters = _make_parameters(
        tmp_path,
        image_path=str(image_path),
        assignment_path=str(assignment_path),
        height=height,
        base_thickness=3.0,
        relief_height_raised=2.0,
        # A legkisebb megengedett mintaszám (`ny=2`, l.
        # `GeometricSurfaceMeshGenerator.generate`) — csak a két szélső
        # `y_norm ∈ {0, 1}` mintapont, elkerülve a `PixelSetMask`
        # egész-pixel-csonkolásából adódó, e teszttől független
        # rács-aliasing-ot egy 2 soros kép és sűrűbb mintavételezés
        # között.
        sampling_distance=height / 2,
    )

    mesh = ImageReliefGeneratorMeshSource(parameters).get_mesh()

    raised_vertices = [v for v in mesh.vertices if v[2] > 3.0]
    assert raised_vertices
    for vertex in raised_vertices:
        assert vertex[1] > height / 2


def test_two_calls_differing_only_in_sampling_distance_yield_different_meshes(
    tmp_path: Path,
) -> None:
    coarse = ImageReliefGeneratorMeshSource(
        _make_parameters(tmp_path, sampling_distance=5.0)
    ).get_mesh()
    fine = ImageReliefGeneratorMeshSource(
        _make_parameters(tmp_path, sampling_distance=1.0)
    ).get_mesh()

    assert len(coarse.vertices) != len(fine.vertices)


def test_two_calls_differing_only_in_a_physical_parameter_yield_different_meshes(
    tmp_path: Path,
) -> None:
    narrow = ImageReliefGeneratorMeshSource(
        _make_parameters(tmp_path, width=10.0)
    ).get_mesh()
    wide = ImageReliefGeneratorMeshSource(
        _make_parameters(tmp_path, width=20.0)
    ).get_mesh()

    assert narrow.bounding_box.max[0] != wide.bounding_box.max[0]


def test_get_mesh_raises_image_interpretation_error_for_empty_image_path(
    tmp_path: Path,
) -> None:
    parameters = _make_parameters(tmp_path, image_path="")

    with pytest.raises(ImageInterpretationError):
        ImageReliefGeneratorMeshSource(parameters).get_mesh()


def test_get_mesh_raises_image_interpretation_error_for_empty_assignment_path(
    tmp_path: Path,
) -> None:
    parameters = _make_parameters(tmp_path, assignment_path="")

    with pytest.raises(ImageInterpretationError):
        ImageReliefGeneratorMeshSource(parameters).get_mesh()


def test_get_mesh_propagates_geometric_surface_value_error(tmp_path: Path) -> None:
    parameters = _make_parameters(
        tmp_path, base_thickness=1.0, relief_height_recessed=2.0
    )

    with pytest.raises(GeometricSurfaceValueError):
        ImageReliefGeneratorMeshSource(parameters).get_mesh()


def test_get_mesh_with_blob_strategy_assignment_file(tmp_path: Path) -> None:
    """`get_mesh()` `interpret_assignment()`-en keresztül a blob-alapú
    (13.9, 1. rész) stratégiát is helyesen futtatja végig — l. ADR-0021."""
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    _write_image(
        image_path,
        [
            [(139, 69, 19), (139, 69, 19)],
            [(139, 69, 19), (139, 69, 19)],
        ],
    )
    _write_assignment(
        assignment_path,
        {
            "strategy": "blob",
            "regions": [
                {
                    "seed_pixel": [0, 0],
                    "contribution": 0.5,
                    "depth_behavior": "raised",
                    "parent": None,
                }
            ],
        },
    )
    parameters = _make_parameters(
        tmp_path, image_path=str(image_path), assignment_path=str(assignment_path)
    )

    mesh = ImageReliefGeneratorMeshSource(parameters).get_mesh()

    assert mesh.source_path is None
    assert mesh.is_valid is True
    assert mesh.warnings == ()
    assert len(mesh.vertices) > 0
    assert len(mesh.triangles) > 0
