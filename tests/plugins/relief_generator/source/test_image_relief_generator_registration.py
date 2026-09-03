"""Tesztek az Image Relief Generator MeshSource entry point
regisztrációjához (ADR-0017).

Lásd: `plugins/relief_generator/source/image_relief_generator_registration.py`,
`plugins/relief_generator/pyproject.toml`.
"""

import json
import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from PIL import Image  # noqa: E402

from plugins.relief_generator.source.image_relief_generator_mesh_source import (  # noqa: E402
    ImageReliefGeneratorMeshSource,
)
from plugins.relief_generator.source.image_relief_generator_registration import (  # noqa: E402
    build_mesh_source_descriptor,
)

_EXPECTED_PARAMETER_NAMES = (
    "image_path",
    "assignment_path",
    "width",
    "height",
    "base_thickness",
    "relief_height_raised",
    "relief_height_recessed",
    "sampling_distance",
)

_EXPECTED_PARAMETER_TYPES = {
    "image_path": "file",
    "assignment_path": "file",
    "width": "float",
    "height": "float",
    "base_thickness": "float",
    "relief_height_raised": "float",
    "relief_height_recessed": "float",
    "sampling_distance": "float",
}


def _write_image(path: Path, pixels: list[list[tuple[int, int, int]]]) -> None:
    height = len(pixels)
    width = len(pixels[0])
    image = Image.new("RGB", (width, height))
    for y in range(height):
        for x in range(width):
            image.putpixel((x, y), pixels[y][x])
    image.save(path)


def _write_assignment(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def test_build_mesh_source_descriptor_has_expected_display_name() -> None:
    descriptor = build_mesh_source_descriptor()

    assert descriptor.display_name == "Image Relief Generator"


def test_build_mesh_source_descriptor_has_expected_parameters() -> None:
    descriptor = build_mesh_source_descriptor()

    assert len(descriptor.parameters) == len(_EXPECTED_PARAMETER_NAMES)
    assert tuple(spec.name for spec in descriptor.parameters) == (
        _EXPECTED_PARAMETER_NAMES
    )
    types = {spec.name: spec.type for spec in descriptor.parameters}
    assert types == _EXPECTED_PARAMETER_TYPES


def test_descriptor_build_get_mesh_runs_end_to_end(tmp_path: Path) -> None:
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
    descriptor = build_mesh_source_descriptor()
    values = {
        "image_path": str(image_path),
        "assignment_path": str(assignment_path),
        "width": 10.0,
        "height": 10.0,
        "base_thickness": 3.0,
        "relief_height_raised": 2.0,
        "relief_height_recessed": 1.0,
        "sampling_distance": 2.0,
    }

    mesh_source = descriptor.build(values)

    assert isinstance(mesh_source, ImageReliefGeneratorMeshSource)

    mesh = mesh_source.get_mesh()

    assert mesh.is_valid is True
    assert mesh.source_path is None
