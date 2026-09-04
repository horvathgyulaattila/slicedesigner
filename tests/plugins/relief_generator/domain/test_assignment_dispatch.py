"""Tesztek az `interpret_assignment`-hez.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_BLOB_INTERPRETATION.md
4. szakasz, ADR-0021.
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

from plugins.relief_generator.domain.assignment_dispatch import (  # noqa: E402
    interpret_assignment,
)
from plugins.relief_generator.domain.image_interpretation import (  # noqa: E402
    interpret_image,
)
from plugins.relief_generator.domain.image_interpretation_blob import (  # noqa: E402
    interpret_image_blob,
)
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


def test_missing_strategy_dispatches_to_color_strategy(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    _write_image(image_path, [[(139, 69, 19), (139, 69, 19)]])
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

    dispatched = interpret_assignment(str(image_path), str(assignment_path))
    direct = interpret_image(str(image_path), str(assignment_path))

    assert len(dispatched) == len(direct) == 1
    assert dispatched[0].contribution == direct[0].contribution
    assert dispatched[0].depth_behavior == direct[0].depth_behavior
    assert dispatched[0].mask.member(0.0, 0.0) == direct[0].mask.member(0.0, 0.0)


def test_explicit_color_strategy_dispatches_to_color_strategy(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    _write_image(image_path, [[(139, 69, 19), (139, 69, 19)]])
    _write_assignment(
        assignment_path,
        {
            "strategy": "color",
            "regions": [
                {
                    "color": "#8B4513",
                    "contribution": 0.5,
                    "depth_behavior": "raised",
                    "parent": None,
                }
            ],
        },
    )

    roots = interpret_assignment(str(image_path), str(assignment_path))

    assert len(roots) == 1
    assert roots[0].mask.member(0.0, 0.0) is True


def test_blob_strategy_dispatches_to_blob_strategy(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    assignment_path = tmp_path / "assignment.json"
    _write_image(image_path, [[(139, 69, 19), (139, 69, 19)]])
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

    dispatched = interpret_assignment(str(image_path), str(assignment_path))
    direct = interpret_image_blob(str(image_path), str(assignment_path))

    assert len(dispatched) == len(direct) == 1
    assert dispatched[0].contribution == direct[0].contribution
    assert dispatched[0].mask.member(0.0, 0.0) == direct[0].mask.member(0.0, 0.0)
    assert dispatched[0].mask.member(1.0, 0.0) == direct[0].mask.member(1.0, 0.0)


def test_unknown_strategy_raises(tmp_path: Path) -> None:
    assignment_path = tmp_path / "assignment.json"
    _write_assignment(assignment_path, {"strategy": "nonexistent", "regions": []})

    with pytest.raises(ImageInterpretationError):
        interpret_assignment("unused.png", str(assignment_path))
