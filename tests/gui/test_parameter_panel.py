"""`ParameterPanel` tesztjei: 8 fülre tagolt, lapozható kártyás
elrendezés (ROADMAP Phase 7 7.4 tétele, prompt 2.2 szakasz).

A widget-ATTRIBÚTUMOK létezését/típusát ellenőrző korábbi asszerciók
(`config_builder`/`config_loader`-nek megfelelően) a `test_config_builder.py`/
`test_config_loader.py`-ban maradnak — ez a fájl kizárólag az ÚJ,
fülsávos konténer-struktúrát fedi le."""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402  # noqa: E402
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
)
from pytestqt.qtbot import QtBot  # noqa: E402

from slicedesigner.gui.parameter_panel import (  # noqa: E402
    ParameterPanel,
    _GeneratorParameterForm,
)
from slicedesigner.project.mesh_source_registry import (  # noqa: E402
    MeshSourceDescriptor,
    ParameterSpec,
)

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


# --- MeshSource plugin "Forrás" választó és generikus form (ADR-0017) ---


def _make_stub_descriptor(display_name: str = "Stub Generator") -> MeshSourceDescriptor:
    return MeshSourceDescriptor(
        display_name=display_name,
        parameters=(
            ParameterSpec(
                name="width",
                label="Szélesség",
                type="float",
                default=2.0,
                minimum=0.0,
                maximum=100.0,
                unit="mm",
            ),
            ParameterSpec(
                name="count", label="Darabszám", type="int", default=3, maximum=10
            ),
            ParameterSpec(name="name", label="Név", type="str", default="wave"),
            ParameterSpec(
                name="mode",
                label="Mód",
                type="enum",
                default="b",
                choices=("a", "b", "c"),
            ),
        ),
        build=MagicMock(),
    )


def _make_panel_with_stub_descriptor(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> tuple[ParameterPanel, MeshSourceDescriptor]:
    descriptor = _make_stub_descriptor()
    monkeypatch.setattr(
        "slicedesigner.gui.parameter_panel.discover_mesh_sources",
        lambda: (descriptor,),
    )
    return _make_panel(qtbot), descriptor


def test_source_combo_offers_stl_and_installed_generator(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    panel, descriptor = _make_panel_with_stub_descriptor(qtbot, monkeypatch)

    assert panel.mesh_source_combo is not None
    assert panel.mesh_source_combo.count() == 2
    assert panel.mesh_source_combo.itemText(0) == "STL fájl"
    assert panel.mesh_source_combo.itemData(0) is None
    assert panel.mesh_source_combo.itemText(1) == descriptor.display_name
    assert panel.mesh_source_combo.itemData(1) is descriptor


def test_source_combo_absent_without_installed_plugins(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "slicedesigner.gui.parameter_panel.discover_mesh_sources", lambda: ()
    )

    panel = _make_panel(qtbot)

    assert panel.mesh_source_combo is None
    assert panel.generate_mesh_button is None
    assert panel.generated_mesh is None


def test_switching_source_toggles_container_visibility(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    panel, _ = _make_panel_with_stub_descriptor(qtbot, monkeypatch)
    combo = panel.mesh_source_combo
    assert combo is not None

    assert panel._stl_source_container.isVisible()
    assert not panel._generator_source_container.isVisible()  # type: ignore[union-attr]

    combo.setCurrentIndex(1)

    assert not panel._stl_source_container.isVisible()
    assert panel._generator_source_container.isVisible()  # type: ignore[union-attr]

    combo.setCurrentIndex(0)

    assert panel._stl_source_container.isVisible()
    assert not panel._generator_source_container.isVisible()  # type: ignore[union-attr]


def test_generator_parameter_form_builds_widgets_for_all_types(qtbot: QtBot) -> None:
    parameters = (
        ParameterSpec(
            name="width",
            label="Szélesség",
            type="float",
            default=2.5,
            minimum=0.0,
            maximum=100.0,
            unit="mm",
        ),
        ParameterSpec(
            name="count", label="Darabszám", type="int", default=3, maximum=10
        ),
        ParameterSpec(name="name", label="Név", type="str", default="wave"),
        ParameterSpec(
            name="mode", label="Mód", type="enum", default="b", choices=("a", "b", "c")
        ),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)

    assert isinstance(form._float_widgets["width"], QDoubleSpinBox)
    assert isinstance(form._int_widgets["count"], QSpinBox)
    assert isinstance(form._str_widgets["name"], QLineEdit)
    assert isinstance(form._enum_widgets["mode"], QComboBox)

    assert form.values() == {
        "width": pytest.approx(2.5),
        "count": 3,
        "name": "wave",
        "mode": "b",
    }


def test_generate_button_emits_requested_signal_with_descriptor_and_values(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    panel, descriptor = _make_panel_with_stub_descriptor(qtbot, monkeypatch)
    assert panel.mesh_source_combo is not None
    assert panel.generate_mesh_button is not None
    panel.mesh_source_combo.setCurrentIndex(1)

    received: list[tuple[Any, dict[str, Any]]] = []
    panel.generate_mesh_requested.connect(
        lambda desc, values: received.append((desc, values))
    )

    panel.generate_mesh_button.click()

    assert len(received) == 1
    emitted_descriptor, emitted_values = received[0]
    assert emitted_descriptor is descriptor
    assert emitted_values == {
        "width": pytest.approx(2.0),
        "count": 3,
        "name": "wave",
        "mode": "b",
    }


# --- "list" típusú ParameterSpec (ADR-0017 kiegészítés) ---


def _make_item_schema() -> tuple[ParameterSpec, ...]:
    return (
        ParameterSpec(name="x", label="X", type="float", default=0.0, unit="mm"),
        ParameterSpec(name="label", label="Címke", type="str", default=""),
    )


def test_list_widget_starts_with_no_rows(qtbot: QtBot) -> None:
    from slicedesigner.gui.parameter_panel import _ListParameterWidget

    widget = _ListParameterWidget(_make_item_schema())
    qtbot.addWidget(widget)

    assert widget.values() == []


def test_list_widget_add_row_creates_item_schema_widgets(qtbot: QtBot) -> None:
    from slicedesigner.gui.parameter_panel import _ListParameterWidget

    widget = _ListParameterWidget(_make_item_schema())
    qtbot.addWidget(widget)

    widget._add_row()

    assert widget.values() == [{"x": pytest.approx(0.0), "label": ""}]


def test_list_widget_add_two_rows_preserves_order(qtbot: QtBot) -> None:
    from slicedesigner.gui.parameter_panel import _ListParameterWidget

    widget = _ListParameterWidget(_make_item_schema())
    qtbot.addWidget(widget)

    widget._add_row()
    widget._rows[0]._float_widgets["x"].setValue(1.5)
    widget._add_row()
    widget._rows[1]._float_widgets["x"].setValue(2.5)

    assert widget.values() == [
        {"x": pytest.approx(1.5), "label": ""},
        {"x": pytest.approx(2.5), "label": ""},
    ]


def test_list_widget_remove_row(qtbot: QtBot) -> None:
    from slicedesigner.gui.parameter_panel import _ListParameterWidget

    widget = _ListParameterWidget(_make_item_schema())
    qtbot.addWidget(widget)
    widget._add_row()
    widget._rows[0]._float_widgets["x"].setValue(9.0)
    widget._add_row()
    widget._rows[1]._float_widgets["x"].setValue(1.0)

    first_row_container = widget._rows_layout.itemAt(0).widget()
    remove_button = first_row_container.findChildren(QPushButton)[-1]
    remove_button.click()

    assert widget.values() == [{"x": pytest.approx(1.0), "label": ""}]


def test_generator_parameter_form_handles_list_type(qtbot: QtBot) -> None:
    parameters = (
        ParameterSpec(
            name="sources",
            label="Források",
            type="list",
            default=[],
            item_schema=_make_item_schema(),
        ),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)

    assert form.values() == {"sources": []}

    from slicedesigner.gui.parameter_panel import _ListParameterWidget

    assert isinstance(form._list_widgets["sources"], _ListParameterWidget)
