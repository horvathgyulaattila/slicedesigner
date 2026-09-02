"""Tesztek az `interpret_image`-hez.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_INTERPRETATION.md.
"""

import json
import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

import pytest  # noqa: E402
from PIL import Image  # noqa: E402

from plugins.relief_generator.domain.image_interpretation import (  # noqa: E402
    interpret_image,
)
from plugins.relief_generator.domain.region import DepthBehavior  # noqa: E402
from plugins.relief_generator.exceptions import ImageInterpretationError  # noqa: E402


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


def test_single_region_covers_all_matching_pixels(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    _write_image(image_path, [[(139, 69, 19), (139, 69, 19)], [(139, 69, 19), (139, 69, 19)]])
    _write_assignment(
        assignment_path,
        {
            "regions": [
                {"color": "#8B4513", "contribution": 0.5, "depth_behavior": "raised", "parent": None}
            ]
        },
    )

    roots = interpret_image(str(image_path), str(assignment_path))

    assert len(roots) == 1
    assert roots[0].contribution == 0.5
    assert roots[0].depth_behavior == DepthBehavior.RAISED
    assert roots[0].children == ()
    assert roots[0].mask.member(0.0, 0.0) is True
    assert roots[0].mask.member(1.0, 1.0) is True


def test_hierarchy_via_parent_field(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    _write_image(
        image_path,
        [[(139, 69, 19), (255, 0, 0)]],
    )
    _write_assignment(
        assignment_path,
        {
            "regions": [
                {"color": "#8B4513", "contribution": 0.5, "depth_behavior": "raised", "parent": None},
                {"color": "#FF0000", "contribution": 0.2, "depth_behavior": "recessed", "parent": "#8B4513"},
            ]
        },
    )

    roots = interpret_image(str(image_path), str(assignment_path))

    assert len(roots) == 1
    assert len(roots[0].children) == 1
    assert roots[0].children[0].contribution == 0.2
    assert roots[0].children[0].depth_behavior == DepthBehavior.RECESSED


def test_disjoint_same_color_blobs_merge_into_one_region(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    # Két, egymással nem összefüggő piros folt.
    _write_image(
        image_path,
        [
            [(255, 0, 0), (255, 255, 255), (255, 0, 0)],
        ],
    )
    _write_assignment(
        assignment_path,
        {
            "background": "#FFFFFF",
            "regions": [
                {"color": "#FF0000", "contribution": 0.3, "depth_behavior": "raised", "parent": None}
            ],
        },
    )

    roots = interpret_image(str(image_path), str(assignment_path))

    assert len(roots) == 1
    assert roots[0].mask.member(0.0, 0.0) is True
    assert roots[0].mask.member(1.0, 0.0) is False
    assert roots[0].mask.member(2.0, 0.0) is True


def test_background_pixels_are_excluded(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    _write_image(image_path, [[(255, 0, 0), (255, 255, 255)]])
    _write_assignment(
        assignment_path,
        {
            "background": "#FFFFFF",
            "regions": [
                {"color": "#FF0000", "contribution": 0.3, "depth_behavior": "raised", "parent": None}
            ],
        },
    )

    roots = interpret_image(str(image_path), str(assignment_path))

    assert roots[0].mask.member(1.0, 0.0) is False


def test_color_tolerance_quantizes_nearby_shades(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    # (250, 5, 5) közel van a deklarált (255, 0, 0)-hoz.
    _write_image(image_path, [[(255, 0, 0), (250, 5, 5)]])
    _write_assignment(
        assignment_path,
        {
            "color_tolerance": 12.0,
            "regions": [
                {"color": "#FF0000", "contribution": 0.3, "depth_behavior": "raised", "parent": None}
            ],
        },
    )

    roots = interpret_image(str(image_path), str(assignment_path))

    assert roots[0].mask.member(0.0, 0.0) is True
    assert roots[0].mask.member(1.0, 0.0) is True


def test_unassigned_color_without_background_raises(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    _write_image(image_path, [[(255, 0, 0), (0, 255, 0)]])
    _write_assignment(
        assignment_path,
        {
            "regions": [
                {"color": "#FF0000", "contribution": 0.3, "depth_behavior": "raised", "parent": None}
            ]
        },
    )

    with pytest.raises(ImageInterpretationError, match="#00FF00"):
        interpret_image(str(image_path), str(assignment_path))


def test_duplicate_color_raises(tmp_path: Path) -> None:
    assignment_path = tmp_path / "assignment.json"
    _write_assignment(
        assignment_path,
        {
            "regions": [
                {"color": "#FF0000", "contribution": 0.1, "depth_behavior": "raised", "parent": None},
                {"color": "#FF0000", "contribution": 0.2, "depth_behavior": "recessed", "parent": None},
            ]
        },
    )

    with pytest.raises(ImageInterpretationError):
        interpret_image("unused.png", str(assignment_path))


def test_cycle_in_parent_chain_raises(tmp_path: Path) -> None:
    assignment_path = tmp_path / "assignment.json"
    _write_assignment(
        assignment_path,
        {
            "regions": [
                {"color": "#FF0000", "contribution": 0.1, "depth_behavior": "raised", "parent": "#00FF00"},
                {"color": "#00FF00", "contribution": 0.2, "depth_behavior": "raised", "parent": "#FF0000"},
            ]
        },
    )

    with pytest.raises(ImageInterpretationError):
        interpret_image("unused.png", str(assignment_path))


def test_empty_regions_list_raises(tmp_path: Path) -> None:
    assignment_path = tmp_path / "assignment.json"
    _write_assignment(assignment_path, {"regions": []})

    with pytest.raises(ImageInterpretationError):
        interpret_image("unused.png", str(assignment_path))


def test_negative_color_tolerance_raises(tmp_path: Path) -> None:
    assignment_path = tmp_path / "assignment.json"
    _write_assignment(
        assignment_path,
        {
            "color_tolerance": -1.0,
            "regions": [
                {"color": "#FF0000", "contribution": 0.1, "depth_behavior": "raised", "parent": None}
            ],
        },
    )

    with pytest.raises(ImageInterpretationError):
        interpret_image("unused.png", str(assignment_path))


def test_missing_parent_reference_raises(tmp_path: Path) -> None:
    assignment_path = tmp_path / "assignment.json"
    _write_assignment(
        assignment_path,
        {
            "regions": [
                {"color": "#FF0000", "contribution": 0.1, "depth_behavior": "raised", "parent": "#000000"}
            ]
        },
    )

    with pytest.raises(ImageInterpretationError):
        interpret_image("unused.png", str(assignment_path))
