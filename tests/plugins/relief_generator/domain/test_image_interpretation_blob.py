"""Tesztek az `interpret_image_blob`-hoz.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_BLOB_INTERPRETATION.md,
ADR-0021.
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

from plugins.relief_generator.domain.image_interpretation_blob import (  # noqa: E402
    flood_fill_region,
    interpret_image_blob,
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


def test_simple_flood_fill_covers_connected_region(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    _write_image(
        image_path,
        [
            [(139, 69, 19), (139, 69, 19), (255, 255, 255)],
            [(139, 69, 19), (139, 69, 19), (255, 255, 255)],
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

    roots = interpret_image_blob(str(image_path), str(assignment_path))

    assert len(roots) == 1
    assert roots[0].contribution == 0.5
    assert roots[0].depth_behavior == DepthBehavior.RAISED
    assert roots[0].children == ()
    assert roots[0].mask.member(0.0, 0.0) is True
    assert roots[0].mask.member(1.0, 1.0) is True
    assert roots[0].mask.member(2.0, 0.0) is False


def test_diagonally_touching_same_color_blobs_are_separate_regions(
    tmp_path: Path,
) -> None:
    """A 4-szomszédság döntés közvetlen igazolása: két, csak átlósan
    érintkező, azonos színű folt a blob-stratégiánál KÜLÖN régió marad —
    szemben a színenkénti stratégia (13.2) egyesítő viselkedésével."""
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    _write_image(
        image_path,
        [
            [(255, 0, 0), (255, 255, 255)],
            [(255, 255, 255), (255, 0, 0)],
        ],
    )
    _write_assignment(
        assignment_path,
        {
            "strategy": "blob",
            "regions": [
                {
                    "seed_pixel": [0, 0],
                    "contribution": 0.3,
                    "depth_behavior": "raised",
                    "parent": None,
                },
                {
                    "seed_pixel": [1, 1],
                    "contribution": 0.4,
                    "depth_behavior": "recessed",
                    "parent": None,
                },
            ],
        },
    )

    roots = interpret_image_blob(str(image_path), str(assignment_path))

    assert len(roots) == 2
    first, second = roots
    assert first.mask.member(0.0, 0.0) is True
    assert first.mask.member(1.0, 1.0) is False
    assert second.mask.member(1.0, 1.0) is True
    assert second.mask.member(0.0, 0.0) is False


def test_per_blob_color_tolerance(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    # (250, 5, 5) közel van a (255, 0, 0)-hoz; (100, 0, 0) messze van.
    _write_image(
        image_path,
        [[(255, 0, 0), (250, 5, 5), (100, 0, 0)]],
    )
    _write_assignment(
        assignment_path,
        {
            "strategy": "blob",
            "regions": [
                {
                    "seed_pixel": [0, 0],
                    "color_tolerance": 12.0,
                    "contribution": 0.3,
                    "depth_behavior": "raised",
                    "parent": None,
                }
            ],
        },
    )

    roots = interpret_image_blob(str(image_path), str(assignment_path))

    assert roots[0].mask.member(0.0, 0.0) is True
    assert roots[0].mask.member(1.0, 0.0) is True
    assert roots[0].mask.member(2.0, 0.0) is False


def test_hierarchy_via_parent_field(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    _write_image(image_path, [[(139, 69, 19), (255, 0, 0)]])
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
                },
                {
                    "seed_pixel": [1, 0],
                    "contribution": 0.2,
                    "depth_behavior": "recessed",
                    "parent": [0, 0],
                },
            ],
        },
    )

    roots = interpret_image_blob(str(image_path), str(assignment_path))

    assert len(roots) == 1
    assert len(roots[0].children) == 1
    assert roots[0].children[0].contribution == 0.2
    assert roots[0].children[0].depth_behavior == DepthBehavior.RECESSED


def test_no_background_field_uncovered_pixels_simply_unassigned(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    _write_image(image_path, [[(255, 0, 0), (255, 255, 255)]])
    _write_assignment(
        assignment_path,
        {
            "strategy": "blob",
            "regions": [
                {
                    "seed_pixel": [0, 0],
                    "contribution": 0.3,
                    "depth_behavior": "raised",
                    "parent": None,
                }
            ],
        },
    )

    roots = interpret_image_blob(str(image_path), str(assignment_path))

    assert roots[0].mask.member(1.0, 0.0) is False


def test_seed_pixel_out_of_bounds_raises(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    _write_image(image_path, [[(255, 0, 0)]])
    _write_assignment(
        assignment_path,
        {
            "strategy": "blob",
            "regions": [
                {
                    "seed_pixel": [5, 5],
                    "contribution": 0.3,
                    "depth_behavior": "raised",
                    "parent": None,
                }
            ],
        },
    )

    with pytest.raises(ImageInterpretationError):
        interpret_image_blob(str(image_path), str(assignment_path))


def test_duplicate_seed_pixel_raises(tmp_path: Path) -> None:
    assignment_path = tmp_path / "assignment.json"
    _write_assignment(
        assignment_path,
        {
            "strategy": "blob",
            "regions": [
                {
                    "seed_pixel": [0, 0],
                    "contribution": 0.1,
                    "depth_behavior": "raised",
                    "parent": None,
                },
                {
                    "seed_pixel": [0, 0],
                    "contribution": 0.2,
                    "depth_behavior": "recessed",
                    "parent": None,
                },
            ],
        },
    )

    with pytest.raises(ImageInterpretationError):
        interpret_image_blob("unused.png", str(assignment_path))


def test_negative_color_tolerance_raises(tmp_path: Path) -> None:
    assignment_path = tmp_path / "assignment.json"
    _write_assignment(
        assignment_path,
        {
            "strategy": "blob",
            "regions": [
                {
                    "seed_pixel": [0, 0],
                    "color_tolerance": -1.0,
                    "contribution": 0.1,
                    "depth_behavior": "raised",
                    "parent": None,
                }
            ],
        },
    )

    with pytest.raises(ImageInterpretationError):
        interpret_image_blob("unused.png", str(assignment_path))


def test_unresolvable_parent_reference_raises(tmp_path: Path) -> None:
    assignment_path = tmp_path / "assignment.json"
    _write_assignment(
        assignment_path,
        {
            "strategy": "blob",
            "regions": [
                {
                    "seed_pixel": [0, 0],
                    "contribution": 0.1,
                    "depth_behavior": "raised",
                    "parent": [9, 9],
                }
            ],
        },
    )

    with pytest.raises(ImageInterpretationError):
        interpret_image_blob("unused.png", str(assignment_path))


def test_circular_parent_chain_raises(tmp_path: Path) -> None:
    assignment_path = tmp_path / "assignment.json"
    _write_assignment(
        assignment_path,
        {
            "strategy": "blob",
            "regions": [
                {
                    "seed_pixel": [0, 0],
                    "contribution": 0.1,
                    "depth_behavior": "raised",
                    "parent": [1, 0],
                },
                {
                    "seed_pixel": [1, 0],
                    "contribution": 0.2,
                    "depth_behavior": "raised",
                    "parent": [0, 0],
                },
            ],
        },
    )

    with pytest.raises(ImageInterpretationError):
        interpret_image_blob("unused.png", str(assignment_path))


def test_flood_fill_region_is_publicly_importable_and_usable_standalone(
    tmp_path: Path,
) -> None:
    """`flood_fill_region()` (13.9, 2. rész — `RegionAssignmentDialog`)
    közvetlenül, `interpret_image_blob()` nélkül is hívható, egyetlen
    seed-pixelre — l. ADR-0022 "Következmények"."""
    image_path = tmp_path / "image.png"
    _write_image(
        image_path,
        [
            [(139, 69, 19), (139, 69, 19), (255, 255, 255)],
            [(139, 69, 19), (139, 69, 19), (255, 255, 255)],
        ],
    )
    with Image.open(image_path) as image:
        rgb_image = image.convert("RGB")
        width, height = rgb_image.size
        pixels = rgb_image.load()

        mask = flood_fill_region(pixels, width, height, (0, 0), 0.0)

    assert mask == frozenset({(0, 0), (1, 0), (0, 1), (1, 1)})
