"""Tesztek a `RegionAssignmentDialog`-hoz.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_REGION_ASSIGNMENT_GUI.md,
ADR-0022.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_REPO_ROOT = str(Path(__file__).resolve().parents[4])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

import pytest  # noqa: E402
from PIL import Image  # noqa: E402
from pytestqt.qtbot import QtBot  # noqa: E402

from plugins.relief_generator.domain.region import DepthBehavior  # noqa: E402
from plugins.relief_generator.gui.region_assignment_dialog import (  # noqa: E402
    RegionAssignmentDialog,
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


def _make_two_region_image(path: Path) -> None:
    """Egy 4x2-es kép, két, egymástól nem összefüggő, tömör színfolttal
    (bal oldal barna, jobb oldal piros) — két külön flood-fillhez."""
    _write_image(
        path,
        [
            [(139, 69, 19), (139, 69, 19), (255, 0, 0), (255, 0, 0)],
            [(139, 69, 19), (139, 69, 19), (255, 0, 0), (255, 0, 0)],
        ],
    )


def _make_dialog(
    qtbot: QtBot, tmp_path: Path, *, existing_assignment_path: str | None = None
) -> RegionAssignmentDialog:
    image_path = tmp_path / "image.png"
    _make_two_region_image(image_path)
    dialog = RegionAssignmentDialog(
        image_path=str(image_path),
        existing_assignment_path=existing_assignment_path,
    )
    qtbot.addWidget(dialog)
    return dialog


def _wait_for_flood_fill(qtbot: QtBot, dialog: RegionAssignmentDialog) -> None:
    """A háttérszálas `_FloodFillWorker` befejezésének szinkron
    megvárása — a core `_wait_for_interactive_render`-mintáját követi
    (`test_preview_panel.py`): a worker-referencia nullázódását várja."""
    qtbot.waitUntil(lambda: dialog._active_worker is None, timeout=5000)


def test_click_on_unassigned_pixel_creates_new_tree_item(
    qtbot: QtBot, tmp_path: Path
) -> None:
    dialog = _make_dialog(qtbot, tmp_path)
    assert dialog._tree.topLevelItemCount() == 0

    dialog._canvas.region_clicked.emit(0, 0)
    _wait_for_flood_fill(qtbot, dialog)

    assert dialog._tree.topLevelItemCount() == 1
    assert (0, 0) in dialog._regions
    assert dialog._selected_seed == (0, 0)


def test_click_on_already_assigned_pixel_only_selects_no_new_worker(
    qtbot: QtBot, tmp_path: Path
) -> None:
    dialog = _make_dialog(qtbot, tmp_path)
    dialog._canvas.region_clicked.emit(0, 0)
    _wait_for_flood_fill(qtbot, dialog)
    assert len(dialog._regions) == 1

    # Egy másik, ugyanahhoz a folthoz tartozó pixelre kattintás — nem
    # indít új flood-fillt (a worker-referencia szinkron NEM változik),
    # csak kiválaszt.
    dialog._canvas.region_clicked.emit(1, 1)

    assert dialog._active_worker is None
    assert len(dialog._regions) == 1
    assert dialog._selected_seed == (0, 0)


def test_delete_keeps_children_reparented_to_root(qtbot: QtBot, tmp_path: Path) -> None:
    dialog = _make_dialog(qtbot, tmp_path)
    dialog._canvas.region_clicked.emit(0, 0)
    _wait_for_flood_fill(qtbot, dialog)
    dialog._canvas.region_clicked.emit(2, 0)
    _wait_for_flood_fill(qtbot, dialog)
    assert set(dialog._regions) == {(0, 0), (2, 0)}

    # (2, 0) a (0, 0) gyermeke.
    dialog._regions[(2, 0)].parent_seed = (0, 0)
    dialog._rebuild_tree()

    dialog._select_region((0, 0))
    dialog._on_delete_clicked()

    assert (0, 0) not in dialog._regions
    assert (2, 0) in dialog._regions
    assert dialog._regions[(2, 0)].parent_seed is None


def test_accept_rejects_rootless_inherit_region(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dialog = _make_dialog(qtbot, tmp_path)
    dialog._canvas.region_clicked.emit(0, 0)
    _wait_for_flood_fill(qtbot, dialog)
    dialog._regions[(0, 0)].depth_behavior = DepthBehavior.INHERIT

    warnings: list[object] = []
    monkeypatch.setattr(
        "plugins.relief_generator.gui.region_assignment_dialog.QMessageBox.warning",
        lambda *args, **kwargs: warnings.append(args),
    )

    dialog._on_accept()

    assert len(warnings) == 1
    assert dialog.result_path is None


def test_accept_with_valid_state_writes_tempfile_with_blob_strategy(
    qtbot: QtBot, tmp_path: Path
) -> None:
    dialog = _make_dialog(qtbot, tmp_path)
    dialog._canvas.region_clicked.emit(0, 0)
    _wait_for_flood_fill(qtbot, dialog)
    dialog._regions[(0, 0)].contribution = 0.5
    dialog._regions[(0, 0)].depth_behavior = DepthBehavior.RAISED
    dialog._regions[(0, 0)].color_tolerance = 3.0

    dialog._on_accept()

    assert dialog.result_path is not None
    with open(dialog.result_path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["strategy"] == "blob"
    assert len(data["regions"]) == 1
    region = data["regions"][0]
    assert region["seed_pixel"] == [0, 0]
    assert region["contribution"] == 0.5
    assert region["depth_behavior"] == "raised"
    assert region["color_tolerance"] == 3.0
    assert region["parent"] is None


def test_existing_assignment_path_restores_regions_on_open(
    qtbot: QtBot, tmp_path: Path
) -> None:
    assignment_path = tmp_path / "assignment.json"
    assignment_path.write_text(
        json.dumps(
            {
                "strategy": "blob",
                "regions": [
                    {
                        "seed_pixel": [0, 0],
                        "color_tolerance": 0.0,
                        "contribution": 0.7,
                        "depth_behavior": "recessed",
                        "parent": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    dialog = _make_dialog(
        qtbot, tmp_path, existing_assignment_path=str(assignment_path)
    )

    assert (0, 0) in dialog._regions
    region = dialog._regions[(0, 0)]
    assert region.contribution == 0.7
    assert region.depth_behavior == DepthBehavior.RECESSED
    assert dialog._tree.topLevelItemCount() == 1


def test_existing_assignment_path_with_color_strategy_starts_empty(
    qtbot: QtBot, tmp_path: Path
) -> None:
    assignment_path = tmp_path / "assignment.json"
    assignment_path.write_text(
        json.dumps(
            {
                "regions": [
                    {
                        "color": "#8B4513",
                        "contribution": 0.5,
                        "depth_behavior": "raised",
                        "parent": None,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    dialog = _make_dialog(
        qtbot, tmp_path, existing_assignment_path=str(assignment_path)
    )

    assert dialog._regions == {}


def test_tree_hierarchy_change_syncs_parent_seed(qtbot: QtBot, tmp_path: Path) -> None:
    """A fa (`_RegionTreeWidget`) tényleges alakja az egyetlen
    igazságforrás a szülő-kapcsolatokra — a jelen teszt a fa
    programozott átrendezésével (a valós húzás Qt-belső mechanizmusa
    helyett) igazolja a szinkronizációt."""
    dialog = _make_dialog(qtbot, tmp_path)
    dialog._canvas.region_clicked.emit(0, 0)
    _wait_for_flood_fill(qtbot, dialog)
    dialog._canvas.region_clicked.emit(2, 0)
    _wait_for_flood_fill(qtbot, dialog)
    assert dialog._regions[(2, 0)].parent_seed is None

    # (0, 0) volt az elsőként létrehozott (tehát elsőként beszúrt)
    # gyökér-elem, (2, 0) a második — mindkettő eredetileg gyökér.
    root_item = dialog._tree.topLevelItem(0)
    other_item = dialog._tree.topLevelItem(1)
    dialog._tree.takeTopLevelItem(dialog._tree.indexOfTopLevelItem(other_item))
    root_item.addChild(other_item)

    dialog._tree.hierarchy_changed.emit()

    assert dialog._regions[(2, 0)].parent_seed == (0, 0)
    assert dialog._regions[(0, 0)].parent_seed is None
