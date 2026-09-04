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
    QFormLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
)
from pytestqt.qtbot import QtBot  # noqa: E402

from slicedesigner.gui.parameter_panel import (  # noqa: E402
    ParameterPanel,
    _CollapsibleSection,
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

    # A "Mesh Import" fül, ha van telepített MeshSource plugin (a
    # tesztkörnyezetben a relief_generator az), a "Generálás" gombot
    # footerként kapja — ekkor a fül tartalma egy közös konténer, a
    # `QScrollArea` ALATT, nem közvetlenül `QScrollArea` (ROADMAP
    # Phase 10.1). A többi fülnél a viselkedés változatlan.
    mesh_import_index = _EXPECTED_TAB_TITLES.index("Mesh Import")
    for index in range(panel.count()):
        if index == mesh_import_index and panel.generate_mesh_button is not None:
            container = panel.widget(index)
            assert not isinstance(container, QScrollArea)
            assert isinstance(container.layout().itemAt(0).widget(), QScrollArea)
            assert container.layout().itemAt(1).widget() is panel.generate_mesh_button
            continue
        assert isinstance(panel.widget(index), QScrollArea)


def test_mesh_import_tab_is_plain_scroll_area_without_installed_plugins(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`footer=None` esetén (nincs telepített MeshSource plugin) a "Mesh
    Import" fül viselkedése bitre azonos a footer bevezetése előttivel."""
    monkeypatch.setattr(
        "slicedesigner.gui.parameter_panel.discover_mesh_sources", lambda: ()
    )
    panel = _make_panel(qtbot)

    mesh_import_index = _EXPECTED_TAB_TITLES.index("Mesh Import")
    assert panel.generate_mesh_button is None
    assert isinstance(panel.widget(mesh_import_index), QScrollArea)


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


def test_mesh_import_tab_footer_is_direct_child_not_inside_scroll_area(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    panel, _ = _make_panel_with_stub_descriptor(qtbot, monkeypatch)

    mesh_import_index = _EXPECTED_TAB_TITLES.index("Mesh Import")
    tab_content = panel.widget(mesh_import_index)
    assert not isinstance(tab_content, QScrollArea)

    layout = tab_content.layout()
    assert layout.count() == 2
    scroll_area = layout.itemAt(0).widget()
    footer = layout.itemAt(1).widget()
    assert isinstance(scroll_area, QScrollArea)
    assert footer is panel.generate_mesh_button


def test_generate_mesh_button_is_not_inside_generator_source_container(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    panel, _ = _make_panel_with_stub_descriptor(qtbot, monkeypatch)

    assert panel.generate_mesh_button is not None
    assert panel._generator_source_container is not None
    assert (
        panel.generate_mesh_button
        not in panel._generator_source_container.findChildren(QPushButton)
    )


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


# --- mezőcsoportosítás (`group`, ADR-0017 kiegészítés, 2026-08-23) ---


def test_generator_parameter_form_groups_same_group_fields_into_one_section(
    qtbot: QtBot,
) -> None:
    parameters = (
        ParameterSpec(name="a", label="A", type="float", default=1.0, group="G"),
        ParameterSpec(name="b", label="B", type="float", default=2.0, group="G"),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)

    layout = form.layout()
    assert isinstance(layout, QFormLayout)
    assert layout.rowCount() == 1
    section = layout.itemAt(0, QFormLayout.ItemRole.SpanningRole).widget()
    assert isinstance(section, _CollapsibleSection)
    assert section.content_layout.rowCount() == 2


def test_generator_parameter_form_ungrouped_field_stays_in_main_layout(
    qtbot: QtBot,
) -> None:
    parameters = (
        ParameterSpec(name="a", label="A", type="float", default=1.0),
        ParameterSpec(name="b", label="B", type="float", default=2.0, group="G"),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)

    layout = form.layout()
    assert layout.rowCount() == 2
    assert layout.itemAt(0, QFormLayout.ItemRole.LabelRole) is not None
    section = layout.itemAt(1, QFormLayout.ItemRole.SpanningRole).widget()
    assert isinstance(section, _CollapsibleSection)


def test_generator_parameter_form_non_adjacent_same_group_fields_share_one_section(
    qtbot: QtBot,
) -> None:
    parameters = (
        ParameterSpec(name="a", label="A", type="float", default=1.0, group="G"),
        ParameterSpec(name="mid", label="Mid", type="float", default=0.0),
        ParameterSpec(name="b", label="B", type="float", default=2.0, group="G"),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)

    layout = form.layout()
    assert layout.rowCount() == 2
    section = layout.itemAt(0, QFormLayout.ItemRole.SpanningRole).widget()
    assert isinstance(section, _CollapsibleSection)
    assert section.content_layout.rowCount() == 2


def test_generator_parameter_form_values_same_shape_with_and_without_grouping(
    qtbot: QtBot,
) -> None:
    parameters = (
        ParameterSpec(name="a", label="A", type="float", default=1.0, group="G"),
        ParameterSpec(name="b", label="B", type="int", default=3),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)

    assert form.values() == {"a": pytest.approx(1.0), "b": 3}


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


# --- feltételes mezőláthatóság (`visible_when`, ADR-0017 kiegészítés, 2026-08-24) ---


def _make_visible_when_form(qtbot: QtBot) -> _GeneratorParameterForm:
    """Kétszintű `visible_when`-lánc: `leaf` a `mid`-től, `mid` a
    `top`-tól függ."""
    parameters = (
        ParameterSpec(
            name="top", label="Top", type="enum", default="A", choices=("A", "B")
        ),
        ParameterSpec(
            name="mid",
            label="Mid",
            type="enum",
            default="X",
            choices=("X", "Y"),
            visible_when=("top", "B"),
        ),
        ParameterSpec(
            name="leaf",
            label="Leaf",
            type="float",
            default=1.0,
            visible_when=("mid", "X"),
        ),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)
    # `isVisible()` a teljes ős-láncot figyeli — a láthatósági asszerciókhoz
    # a formot ténylegesen meg kell jeleníteni (a `_make_panel` mintáját
    # követve).
    form.show()
    return form


def test_visible_when_field_initially_hidden_when_controller_mismatches(
    qtbot: QtBot,
) -> None:
    form = _make_visible_when_form(qtbot)

    assert not form._row_widgets["mid"][0].isVisible()


def test_visible_when_field_toggles_with_controller_value_change(
    qtbot: QtBot,
) -> None:
    form = _make_visible_when_form(qtbot)

    assert not form._row_widgets["mid"][0].isVisible()

    form._enum_widgets["top"].setCurrentIndex(form._enum_widgets["top"].findData("B"))
    assert form._row_widgets["mid"][0].isVisible()

    form._enum_widgets["top"].setCurrentIndex(form._enum_widgets["top"].findData("A"))
    assert not form._row_widgets["mid"][0].isVisible()


def test_visible_when_two_level_chain_stays_hidden_if_top_level_mismatches(
    qtbot: QtBot,
) -> None:
    """`leaf` saját feltétele (`mid == "X"`) a kezdeti állapotban teljesül,
    de mivel `mid` maga rejtve van (`top != "B"`), `leaf`-nek is rejtve kell
    maradnia — ez igazolja a rekurzív kaszkádolást."""
    form = _make_visible_when_form(qtbot)

    assert form._enum_widgets["mid"].currentData() == "X"
    assert not form._row_widgets["leaf"][0].isVisible()

    form._enum_widgets["top"].setCurrentIndex(form._enum_widgets["top"].findData("B"))
    assert form._row_widgets["leaf"][0].isVisible()


def test_visible_when_values_includes_hidden_field_values(qtbot: QtBot) -> None:
    form = _make_visible_when_form(qtbot)

    assert not form._row_widgets["mid"][0].isVisible()
    assert form.values() == {
        "top": "A",
        "mid": "X",
        "leaf": pytest.approx(1.0),
    }


# --- üres csoportok elrejtése (`visible_when` + `group`, 2026-08-29-i kiegészítés) ---


def _make_visible_when_group_form(qtbot: QtBot) -> _GeneratorParameterForm:
    """Egy `group`-hoz tartozó egyetlen mező, `visible_when`-nel — a
    szakasz láthatóságának a mező effektív láthatóságát kell követnie."""
    parameters = (
        ParameterSpec(
            name="top", label="Top", type="enum", default="A", choices=("A", "B")
        ),
        ParameterSpec(
            name="member",
            label="Member",
            type="float",
            default=1.0,
            group="G",
            visible_when=("top", "B"),
        ),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)
    form.show()
    return form


def test_group_section_hidden_when_all_members_effectively_invisible(
    qtbot: QtBot,
) -> None:
    form = _make_visible_when_group_form(qtbot)

    assert not form._sections["G"].isVisible()


def test_group_section_becomes_visible_when_a_member_becomes_visible(
    qtbot: QtBot,
) -> None:
    form = _make_visible_when_group_form(qtbot)

    form._enum_widgets["top"].setCurrentIndex(form._enum_widgets["top"].findData("B"))
    assert form._sections["G"].isVisible()

    form._enum_widgets["top"].setCurrentIndex(form._enum_widgets["top"].findData("A"))
    assert not form._sections["G"].isVisible()


def test_generator_parameter_form_without_groups_does_not_break_on_empty_group_members(
    qtbot: QtBot,
) -> None:
    parameters = (
        ParameterSpec(name="a", label="A", type="float", default=1.0),
        ParameterSpec(name="b", label="B", type="int", default=3),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)

    assert form._group_members == {}
    assert form._sections == {}
    assert form.values() == {"a": pytest.approx(1.0), "b": 3}


# --- "Generálás" gomb STL forrásnál (2026-08-29-i kiegészítés) ---


def test_generate_mesh_button_initially_hidden_with_stl_as_default_source(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    panel, _ = _make_panel_with_stub_descriptor(qtbot, monkeypatch)

    assert panel.generate_mesh_button is not None
    assert not panel.generate_mesh_button.isVisible()


def test_generate_mesh_button_toggles_with_source_selection(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    panel, _ = _make_panel_with_stub_descriptor(qtbot, monkeypatch)
    combo = panel.mesh_source_combo
    assert combo is not None
    assert panel.generate_mesh_button is not None

    combo.setCurrentIndex(1)
    assert panel.generate_mesh_button.isVisible()

    combo.setCurrentIndex(0)
    assert not panel.generate_mesh_button.isVisible()


# --- `"file"` típus (ADR-0017 kiegészítés, 2026-09-03, ROADMAP Phase 13.8) ---


def test_generator_parameter_form_builds_widget_for_file_type(qtbot: QtBot) -> None:
    parameters = (
        ParameterSpec(name="image_path", label="Kép fájl", type="file", default=""),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)

    assert "image_path" in form._file_widgets


def test_file_type_values_is_empty_string_initially(qtbot: QtBot) -> None:
    parameters = (
        ParameterSpec(name="image_path", label="Kép fájl", type="file", default=""),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)

    assert form.values() == {"image_path": ""}


def test_file_type_values_reflects_simulated_selection(qtbot: QtBot) -> None:
    parameters = (
        ParameterSpec(name="image_path", label="Kép fájl", type="file", default=""),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)

    # A `QFileDialog`-ot közvetlenül nem hívjuk — a sikeres fájlválasztás
    # eredményét a belső `path_label` szövegének beállításával szimuláljuk.
    form._file_widgets["image_path"].setText("C:/tmp/image.png")

    assert form.values() == {"image_path": "C:/tmp/image.png"}


# --- `ParameterSpec.editor` — "Szerkesztés..." gomb (ADR-0022, 2026-09-04) ---


def test_file_type_with_editor_gets_edit_button(qtbot: QtBot) -> None:
    parameters = (
        ParameterSpec(
            name="assignment_path",
            label="Hozzárendelési fájl (JSON)",
            type="file",
            default="",
            editor=lambda values: "C:/tmp/edited.json",
        ),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)

    file_picker = form._file_widgets["assignment_path"].parentWidget()
    edit_buttons = [
        button
        for button in file_picker.findChildren(QPushButton)
        if button.text() == "Szerkesztés..."
    ]
    assert len(edit_buttons) == 1


def test_file_type_without_editor_has_no_edit_button(qtbot: QtBot) -> None:
    parameters = (
        ParameterSpec(name="image_path", label="Kép fájl", type="file", default=""),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)

    file_picker = form._file_widgets["image_path"].parentWidget()
    edit_buttons = [
        button
        for button in file_picker.findChildren(QPushButton)
        if button.text() == "Szerkesztés..."
    ]
    assert len(edit_buttons) == 0


def test_edit_button_click_calls_editor_with_values_and_updates_label(
    qtbot: QtBot,
) -> None:
    received_values: list[dict[str, Any]] = []

    def _editor(values: dict[str, Any]) -> str | None:
        received_values.append(values)
        return "C:/tmp/edited.json"

    parameters = (
        ParameterSpec(
            name="assignment_path",
            label="Hozzárendelési fájl (JSON)",
            type="file",
            default="",
            editor=_editor,
        ),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)

    file_picker = form._file_widgets["assignment_path"].parentWidget()
    edit_button = next(
        button
        for button in file_picker.findChildren(QPushButton)
        if button.text() == "Szerkesztés..."
    )
    edit_button.click()

    assert received_values == [{"assignment_path": ""}]
    assert form._file_widgets["assignment_path"].text() == "C:/tmp/edited.json"


def test_edit_button_click_with_none_result_does_not_change_label(
    qtbot: QtBot,
) -> None:
    parameters = (
        ParameterSpec(
            name="assignment_path",
            label="Hozzárendelési fájl (JSON)",
            type="file",
            default="",
            editor=lambda values: None,
        ),
    )
    form = _GeneratorParameterForm(parameters)
    qtbot.addWidget(form)

    file_picker = form._file_widgets["assignment_path"].parentWidget()
    edit_button = next(
        button
        for button in file_picker.findChildren(QPushButton)
        if button.text() == "Szerkesztés..."
    )
    edit_button.click()

    assert form._file_widgets["assignment_path"].text() == "(nincs kiválasztva)"
