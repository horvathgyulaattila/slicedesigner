"""RegionAssignmentDialog — interaktív GUI a blob-alapú
régió-hozzárendeléshez.

Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_REGION_ASSIGNMENT_GUI.md,
ADR-0022.

FONTOS: ez a modul szándékosan NEM importál `slicedesigner.gui.*`
core-internal modult (l. ADR-0022 "Döntés" 5. pontja, ADR-0015/0016
egyirányú függőségi szabály) — a zoom/pan-technikát (`_NestingGraphicsView`
mintája, `preview_panel.py`) és a háttérszálas mintát
(`_PreviewComputeWorker` mintája) ÖNÁLLÓ, plugin-belső kódként tükrözi,
nem osztott importként.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass

from PIL import Image
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QColor, QDropEvent, QImage, QMouseEvent, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plugins.relief_generator.domain.image_interpretation_blob import (
    flood_fill_region,
)
from plugins.relief_generator.domain.region import DepthBehavior

# Zoom-korlátok és -lépésköz — a core `_NestingGraphicsView`
# (`preview_panel.py`) mintájának plugin-belüli, önálló megismétlése.
_ZOOM_MIN = 0.2
_ZOOM_MAX = 10.0
_ZOOM_STEP_FACTOR = 1.15

_TOLERANCE_SLIDER_MAX = 200  # a csúszka 0..200 egészet enged, 1.0 lépésközzel
_SEED_KEY_ROLE = Qt.ItemDataRole.UserRole

_OVERLAY_COLOR = QColor(255, 165, 0, 110)  # félig átlátszó narancs — minden aktív folt


@dataclass
class _PendingRegion:
    """Egy, a dialógusban még csak memóriában létező blob-hozzárendelési
    bejegyzés — a végleges JSON séma
    (`IMAGE_RELIEF_BLOB_INTERPRETATION.md` 2. szakasz) közvetlen,
    GUI-oldali tükre, kiegészítve a már kiszámított `mask`-kal (hogy a
    mentéskor ne kelljen a flood-fillt újra lefuttatni)."""

    seed_pixel: tuple[int, int]
    color_tolerance: float
    mask: frozenset[tuple[int, int]]
    contribution: float = 0.0
    depth_behavior: DepthBehavior = DepthBehavior.RAISED
    parent_seed: tuple[int, int] | None = None


class _RegionCanvasView(QGraphicsView):
    """Zoom/pan-képes `QGraphicsView` a kép-vászonhoz — a core
    `_NestingGraphicsView` egérgörgős nagyítás-technikáját tükrözi,
    önálló, plugin-belső implementációként (l. a modul docstringjét).
    A kattintva-húzva mozgatás (pan) a Qt beépített `ScrollHandDrag`
    módjával működik.

    Bal kattintás esetén a `region_clicked(x, y)` szignált emittálja, a
    kép-pixel-koordinátarendszerben (nem scene-transzformált
    koordinátában) számított egész `(x, y)` párral — feltételezve, hogy
    a megjelenített `QGraphicsPixmapItem` a scene origójánál, 1:1
    léptékben (1 scene-egység = 1 kép-pixel) van elhelyezve.
    """

    region_clicked = Signal(int, int)

    def __init__(
        self,
        scene: QGraphicsScene,
        image_width: int,
        image_height: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(scene, parent)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._zoom_factor = 1.0
        self._image_width = image_width
        self._image_height = image_height

    def wheelEvent(self, event: QWheelEvent) -> None:
        angle_delta = event.angleDelta().y()
        if angle_delta == 0:
            return
        step_factor = _ZOOM_STEP_FACTOR if angle_delta > 0 else 1 / _ZOOM_STEP_FACTOR
        new_zoom_factor = self._zoom_factor * step_factor
        if not (_ZOOM_MIN <= new_zoom_factor <= _ZOOM_MAX):
            return
        self._zoom_factor = new_zoom_factor
        self.scale(step_factor, step_factor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            x, y = int(scene_pos.x()), int(scene_pos.y())
            if 0 <= x < self._image_width and 0 <= y < self._image_height:
                self.region_clicked.emit(x, y)
        super().mousePressEvent(event)


class _RegionTreeWidget(QTreeWidget):
    """`QTreeWidget`-alosztály, kizárólag a húzással történő
    újraszülőzés (`InternalMove`) utáni szinkronizáció megbízható
    elkapásához — a `dropEvent()` felülírása megbízhatóbb, mint a
    `model().rowsMoved` szignálra hagyatkozni (nem garantált, hogy az
    pontosan egyszer, a húzás VÉGLEGES fa-alakját tükrözve sül el)."""

    hierarchy_changed = Signal()

    def dropEvent(self, event: QDropEvent) -> None:
        super().dropEvent(event)
        self.hierarchy_changed.emit()


class _FloodFillWorker(QThread):
    """Egyetlen `flood_fill_region()` hívást végez háttérszálon — a core
    `_PreviewComputeWorker` mintáját (`QThread`-alosztály, `run()`-
    felülírással, `succeeded`/`failed` jelzéssel) tükrözi, önálló,
    plugin-belső implementációként (l. a modul docstringjét)."""

    succeeded = Signal(object)  # frozenset[tuple[int, int]]
    failed = Signal(Exception)

    def __init__(
        self,
        pixels: object,
        width: int,
        height: int,
        seed_pixel: tuple[int, int],
        color_tolerance: float,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._pixels = pixels
        self._width = width
        self._height = height
        self._seed_pixel = seed_pixel
        self._color_tolerance = color_tolerance

    def run(self) -> None:
        try:
            mask = flood_fill_region(
                self._pixels,
                self._width,
                self._height,
                self._seed_pixel,
                self._color_tolerance,
            )
        except Exception as exc:  # noqa: BLE001 — a hívóhoz kell eljutnia
            self.failed.emit(exc)
            return
        self.succeeded.emit(mask)


class RegionAssignmentDialog(QDialog):
    """Interaktív dialógus a blob-alapú régió-hozzárendeléshez.

    Lásd: docs/plugins/relief_generator/IMAGE_RELIEF_REGION_ASSIGNMENT_GUI.md
    a teljes interakciós szerződésért.

    Attributes:
        result_path: sikeres "Kész" után a megírt ideiglenes
            hozzárendelési fájl útvonala; addig `None`.
    """

    def __init__(
        self,
        image_path: str,
        existing_assignment_path: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Régiók hozzárendelése")
        self.result_path: str | None = None

        self._image_path = image_path
        with Image.open(image_path) as image:
            rgb_image = image.convert("RGB")
            self._image_width, self._image_height = rgb_image.size
            self._pixels = rgb_image.load()

        self._regions: dict[tuple[int, int], _PendingRegion] = {}
        self._selected_seed: tuple[int, int] | None = None
        self._active_worker: _FloodFillWorker | None = None

        self._build_ui()
        self._load_existing_state(existing_assignment_path)

    # --- Felépítés ---

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        scene = QGraphicsScene(self)
        pixmap = QPixmap(self._image_path)
        scene.addItem(QGraphicsPixmapItem(pixmap))
        self._overlay_item = QGraphicsPixmapItem()
        scene.addItem(self._overlay_item)
        self._canvas = _RegionCanvasView(
            scene, self._image_width, self._image_height, self
        )
        self._canvas.region_clicked.connect(self._on_region_clicked)
        content_layout.addWidget(self._canvas, stretch=2)

        side_layout = QVBoxLayout()
        content_layout.addLayout(side_layout, stretch=1)

        side_layout.addWidget(QLabel("Tolerancia:"))
        self._tolerance_slider = QSlider(Qt.Orientation.Horizontal)
        self._tolerance_slider.setRange(0, _TOLERANCE_SLIDER_MAX)
        self._tolerance_slider.setValue(0)
        self._tolerance_value_label = QLabel("0.0")
        self._tolerance_slider.valueChanged.connect(
            lambda v: self._tolerance_value_label.setText(f"{float(v):.1f}")
        )
        side_layout.addWidget(self._tolerance_slider)
        side_layout.addWidget(self._tolerance_value_label)

        self._tree = _RegionTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self._tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        self._tree.hierarchy_changed.connect(self._on_tree_hierarchy_changed)
        side_layout.addWidget(self._tree, stretch=1)

        editor_group = QGroupBox("Kijelölt régió szerkesztése")
        editor_form = QFormLayout(editor_group)
        self._contribution_spin = QDoubleSpinBox()
        self._contribution_spin.setMinimum(0.0)
        self._contribution_spin.setMaximum(1_000_000.0)
        self._contribution_spin.setDecimals(4)
        self._contribution_spin.valueChanged.connect(self._on_editor_field_changed)
        editor_form.addRow("Contribution:", self._contribution_spin)

        self._depth_behavior_combo = QComboBox()
        for behavior in DepthBehavior:
            self._depth_behavior_combo.addItem(behavior.value, behavior)
        self._depth_behavior_combo.currentIndexChanged.connect(
            self._on_editor_field_changed
        )
        editor_form.addRow("DepthBehavior:", self._depth_behavior_combo)

        self._editor_tolerance_spin = QDoubleSpinBox()
        self._editor_tolerance_spin.setMinimum(0.0)
        self._editor_tolerance_spin.setMaximum(float(_TOLERANCE_SLIDER_MAX))
        self._editor_tolerance_spin.setDecimals(1)
        editor_form.addRow("Tolerancia (ennél):", self._editor_tolerance_spin)

        buttons_layout = QHBoxLayout()
        self._recompute_button = QPushButton("Újraszámol")
        self._recompute_button.clicked.connect(self._on_recompute_clicked)
        self._delete_button = QPushButton("Törlés")
        self._delete_button.clicked.connect(self._on_delete_clicked)
        buttons_layout.addWidget(self._recompute_button)
        buttons_layout.addWidget(self._delete_button)
        editor_form.addRow(buttons_layout)

        side_layout.addWidget(editor_group)
        self._set_editor_enabled(False)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        assert ok_button is not None
        ok_button.setText("Kész")
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        assert cancel_button is not None
        cancel_button.setText("Mégse")
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _set_editor_enabled(self, enabled: bool) -> None:
        self._contribution_spin.setEnabled(enabled)
        self._depth_behavior_combo.setEnabled(enabled)
        self._editor_tolerance_spin.setEnabled(enabled)
        self._recompute_button.setEnabled(enabled)
        self._delete_button.setEnabled(enabled)

    def _load_existing_state(self, existing_assignment_path: str | None) -> None:
        """L. IMAGE_RELIEF_REGION_ASSIGNMENT_GUI.md 5. szakasz — csendben
        üresen indul, ha a fájl hiányzik/olvashatatlan/nem blob-stratégiás."""
        if not existing_assignment_path:
            return
        try:
            with open(existing_assignment_path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return
        if data.get("strategy") != "blob":
            return
        for entry in data.get("regions", []):
            seed = tuple(entry["seed_pixel"])
            tolerance = entry.get("color_tolerance", 0.0)
            mask = flood_fill_region(
                self._pixels, self._image_width, self._image_height, seed, tolerance
            )
            parent_raw = entry.get("parent")
            self._regions[seed] = _PendingRegion(
                seed_pixel=seed,
                color_tolerance=tolerance,
                mask=mask,
                contribution=entry.get("contribution", 0.0),
                depth_behavior=DepthBehavior(entry.get("depth_behavior", "raised")),
                parent_seed=tuple(parent_raw) if parent_raw is not None else None,
            )
        self._rebuild_tree()
        self._rebuild_overlay()

    # --- Kattintás-feldolgozás ---

    def _on_region_clicked(self, x: int, y: int) -> None:
        seed = (x, y)
        for region in self._regions.values():
            if seed in region.mask:
                self._select_region(region.seed_pixel)
                return
        tolerance = float(self._tolerance_slider.value())
        self._start_flood_fill(seed, tolerance, is_new=True)

    def _start_flood_fill(
        self, seed: tuple[int, int], tolerance: float, *, is_new: bool
    ) -> None:
        worker = _FloodFillWorker(
            self._pixels, self._image_width, self._image_height, seed, tolerance, self
        )
        worker.succeeded.connect(
            lambda mask: self._on_flood_fill_succeeded(seed, tolerance, mask, is_new)
        )
        worker.failed.connect(self._on_flood_fill_failed)
        worker.finished.connect(worker.deleteLater)
        self._active_worker = worker
        worker.start()

    def _on_flood_fill_succeeded(
        self,
        seed: tuple[int, int],
        tolerance: float,
        mask: frozenset[tuple[int, int]],
        is_new: bool,
    ) -> None:
        self._active_worker = None
        if is_new:
            self._regions[seed] = _PendingRegion(
                seed_pixel=seed, color_tolerance=tolerance, mask=mask
            )
        else:
            region = self._regions[seed]
            region.mask = mask
            region.color_tolerance = tolerance
        self._rebuild_tree()
        self._rebuild_overlay()
        self._select_region(seed)

    def _on_flood_fill_failed(self, error: Exception) -> None:
        self._active_worker = None
        QMessageBox.warning(self, "Régiók hozzárendelése", str(error))

    # --- Fa és kijelölés ---

    def _rebuild_tree(self) -> None:
        self._tree.blockSignals(True)
        self._tree.clear()
        items: dict[tuple[int, int], QTreeWidgetItem] = {}
        for seed in self._regions:
            item = QTreeWidgetItem([f"({seed[0]}, {seed[1]})"])
            item.setData(0, _SEED_KEY_ROLE, seed)
            items[seed] = item
        for seed, region in self._regions.items():
            item = items[seed]
            if region.parent_seed is not None and region.parent_seed in items:
                items[region.parent_seed].addChild(item)
            else:
                self._tree.addTopLevelItem(item)
        self._tree.expandAll()
        self._tree.blockSignals(False)

    def _on_tree_selection_changed(self) -> None:
        selected = self._tree.selectedItems()
        if not selected:
            self._selected_seed = None
            self._set_editor_enabled(False)
            return
        seed = selected[0].data(0, _SEED_KEY_ROLE)
        self._select_region(seed, update_tree_selection=False)

    def _select_region(
        self, seed: tuple[int, int], *, update_tree_selection: bool = True
    ) -> None:
        self._selected_seed = seed
        region = self._regions[seed]
        self._contribution_spin.blockSignals(True)
        self._contribution_spin.setValue(region.contribution)
        self._contribution_spin.blockSignals(False)
        index = self._depth_behavior_combo.findData(region.depth_behavior)
        self._depth_behavior_combo.blockSignals(True)
        self._depth_behavior_combo.setCurrentIndex(max(index, 0))
        self._depth_behavior_combo.blockSignals(False)
        self._editor_tolerance_spin.setValue(region.color_tolerance)
        self._set_editor_enabled(True)
        if update_tree_selection:
            self._select_tree_item_for_seed(seed)

    def _select_tree_item_for_seed(self, seed: tuple[int, int]) -> None:
        iterator_stack: list[QTreeWidgetItem] = []
        for i in range(self._tree.topLevelItemCount()):
            top_item = self._tree.topLevelItem(i)
            assert top_item is not None
            iterator_stack.append(top_item)
        while iterator_stack:
            item = iterator_stack.pop()
            if item.data(0, _SEED_KEY_ROLE) == seed:
                self._tree.setCurrentItem(item)
                return
            for i in range(item.childCount()):
                child = item.child(i)
                assert child is not None
                iterator_stack.append(child)

    def _on_tree_hierarchy_changed(self) -> None:
        """A `_RegionTreeWidget` `InternalMove` húzása utáni szinkronizáció
        — a fa TÉNYLEGES, aktuális alakja szerint állítja be minden
        `_PendingRegion.parent_seed`-jét (l.
        IMAGE_RELIEF_REGION_ASSIGNMENT_GUI.md 3.3 szakasz — a fa az
        egyetlen igazságforrás)."""
        for i in range(self._tree.topLevelItemCount()):
            top_item = self._tree.topLevelItem(i)
            assert top_item is not None
            self._sync_parent_from_tree(top_item, None)

    def _sync_parent_from_tree(
        self, item: QTreeWidgetItem, parent_seed: tuple[int, int] | None
    ) -> None:
        seed = item.data(0, _SEED_KEY_ROLE)
        self._regions[seed].parent_seed = parent_seed
        for i in range(item.childCount()):
            self._sync_parent_from_tree(item.child(i), seed)

    # --- Szerkesztő-panel ---

    def _on_editor_field_changed(self) -> None:
        if self._selected_seed is None:
            return
        region = self._regions[self._selected_seed]
        region.contribution = self._contribution_spin.value()
        region.depth_behavior = self._depth_behavior_combo.currentData()

    def _on_recompute_clicked(self) -> None:
        if self._selected_seed is None:
            return
        tolerance = self._editor_tolerance_spin.value()
        self._start_flood_fill(self._selected_seed, tolerance, is_new=False)

    def _on_delete_clicked(self) -> None:
        """L. IMAGE_RELIEF_REGION_ASSIGNMENT_GUI.md 3.4 szakasz — a
        gyermekek a gyökérbe kerülnek, nem törlődnek."""
        if self._selected_seed is None:
            return
        deleted_seed = self._selected_seed
        for region in self._regions.values():
            if region.parent_seed == deleted_seed:
                region.parent_seed = None
        del self._regions[deleted_seed]
        self._selected_seed = None
        self._set_editor_enabled(False)
        self._rebuild_tree()
        self._rebuild_overlay()

    # --- Overlay ---

    def _rebuild_overlay(self) -> None:
        image = QImage(
            self._image_width, self._image_height, QImage.Format.Format_ARGB32
        )
        image.fill(Qt.GlobalColor.transparent)
        for region in self._regions.values():
            for x, y in region.mask:
                image.setPixelColor(x, y, _OVERLAY_COLOR)
        self._overlay_item.setPixmap(QPixmap.fromImage(image))

    # --- Mentés ---

    def _on_accept(self) -> None:
        invalid = [
            region
            for region in self._regions.values()
            if region.parent_seed is None
            and region.depth_behavior is DepthBehavior.INHERIT
        ]
        if invalid:
            QMessageBox.warning(
                self,
                "Régiók hozzárendelése",
                "Szülő nélküli régió nem lehet 'Inherit' — jelöld ki és "
                "válassz másik DepthBehavior-t.",
            )
            return

        payload = {
            "strategy": "blob",
            "regions": [
                {
                    "seed_pixel": list(region.seed_pixel),
                    "color_tolerance": region.color_tolerance,
                    "contribution": region.contribution,
                    "depth_behavior": region.depth_behavior.value,
                    "parent": (
                        list(region.parent_seed)
                        if region.parent_seed is not None
                        else None
                    ),
                }
                for region in self._regions.values()
            ],
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(payload, f)
            self.result_path = f.name
        self.accept()
