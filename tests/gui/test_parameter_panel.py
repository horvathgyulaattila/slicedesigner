"""`ParameterPanel` tesztjei: 8 fülre tagolt, lapozható kártyás
elrendezés (ROADMAP Phase 7 7.4 tétele, prompt 2.2 szakasz).

A widget-ATTRIBÚTUMOK létezését/típusát ellenőrző korábbi asszerciók
(`config_builder`/`config_loader`-nek megfelelően) a `test_config_builder.py`/
`test_config_loader.py`-ban maradnak — ez a fájl kizárólag az ÚJ,
fülsávos konténer-struktúrát fedi le."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QScrollArea, QTabWidget  # noqa: E402
from pytestqt.qtbot import QtBot  # noqa: E402

from slicedesigner.gui.parameter_panel import ParameterPanel  # noqa: E402

_EXPECTED_TAB_TITLES = (
    "Mesh Import",
    "Slicing",
    "Dowel",
    "Gap",
    "Backplate",
    "Numbering",
    "Nesting",
    "Export",
)


def _make_panel(qtbot: QtBot) -> ParameterPanel:
    panel = ParameterPanel()
    qtbot.addWidget(panel)
    # `isVisible()` a teljes ős-láncot figyeli — egy sosem megjelenített
    # top-level widget minden leszármazottja láthatatlannak számít,
    # függetlenül a saját `setVisible()`-állapotától; a láthatósági
    # tesztekhez ezért szükséges a tényleges megjelenítés.
    panel.show()
    return panel


def test_parameter_panel_is_a_tab_widget(qtbot: QtBot) -> None:
    panel = _make_panel(qtbot)
    assert isinstance(panel, QTabWidget)


def test_parameter_panel_has_eight_tabs_in_order(qtbot: QtBot) -> None:
    panel = _make_panel(qtbot)

    assert panel.count() == 8
    titles = tuple(panel.tabText(index) for index in range(panel.count()))
    assert titles == _EXPECTED_TAB_TITLES


def test_every_tab_content_is_wrapped_in_its_own_scroll_area(qtbot: QtBot) -> None:
    panel = _make_panel(qtbot)

    for index in range(panel.count()):
        assert isinstance(panel.widget(index), QScrollArea)


def test_dowel_group_visibility_toggles_within_its_own_tab(qtbot: QtBot) -> None:
    panel = _make_panel(qtbot)
    panel.setCurrentIndex(_EXPECTED_TAB_TITLES.index("Dowel"))

    assert not panel.dowel_group.isVisible()
    panel.use_dowels_checkbox.setChecked(True)
    assert panel.dowel_group.isVisible()
    panel.use_dowels_checkbox.setChecked(False)
    assert not panel.dowel_group.isVisible()


def test_gap_group_visibility_toggles_within_its_own_tab(qtbot: QtBot) -> None:
    panel = _make_panel(qtbot)
    panel.setCurrentIndex(_EXPECTED_TAB_TITLES.index("Gap"))

    assert not panel.gap_group.isVisible()
    panel.use_spacers_checkbox.setChecked(True)
    assert panel.gap_group.isVisible()


def test_backplate_group_visibility_toggles_within_its_own_tab(qtbot: QtBot) -> None:
    panel = _make_panel(qtbot)
    panel.setCurrentIndex(_EXPECTED_TAB_TITLES.index("Backplate"))

    assert not panel.backplate_group.isVisible()
    panel.use_backplate_checkbox.setChecked(True)
    assert panel.backplate_group.isVisible()


def test_export_tab_is_initially_empty(qtbot: QtBot) -> None:
    panel = _make_panel(qtbot)
    export_scroll_area = panel.widget(_EXPECTED_TAB_TITLES.index("Export"))
    assert isinstance(export_scroll_area, QScrollArea)
    export_content = export_scroll_area.widget()
    assert export_content is not None

    # Csak a záró `addStretch()` van benne, tényleges widget nélkül,
    # amíg a `MainWindow` be nem illeszti a `RunPanel` export-beállítás
    # konténerét.
    assert export_content.layout().count() == 1


def test_set_export_tab_content_inserts_widget(qtbot: QtBot) -> None:
    from PySide6.QtWidgets import QLabel

    panel = _make_panel(qtbot)
    export_widget = QLabel("DXF Export beállítások")

    panel.set_export_tab_content(export_widget)

    export_scroll_area = panel.widget(_EXPECTED_TAB_TITLES.index("Export"))
    export_content = export_scroll_area.widget()
    assert export_content.layout().itemAt(0).widget() is export_widget


def test_origin_alignment_combo_has_none_and_min_corner(qtbot: QtBot) -> None:
    panel = _make_panel(qtbot)

    items = [
        panel.origin_alignment_combo.itemData(index)
        for index in range(panel.origin_alignment_combo.count())
    ]
    assert items == ["none", "min_corner"]


def test_mesh_file_selected_signal_still_emits(qtbot: QtBot) -> None:
    """A `mesh_file_selected` signal (a `MainWindow` automatikus
    3D-előnézetéhez, ADR-független widget-viselkedés) a fülsávos
    átalakítás után is változatlanul emittálódik."""
    panel = _make_panel(qtbot)
    received: list[str] = []
    panel.mesh_file_selected.connect(received.append)

    panel.mesh_file_selected.emit("C:/models/example.stl")

    assert received == ["C:/models/example.stl"]
