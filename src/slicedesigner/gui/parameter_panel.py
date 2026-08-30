"""Bal oldali paraméter-panel: a nyolc funkciócsoport (7 engine-paraméter
dataclass + DXF Export) fenti fülsávos (tab), lapozható kártyás beviteli
felülete (prompt 7.4 GUI-átalakítás, ROADMAP Phase 7 7.4 tétele).

Kizárólag elrendezés és widget-választás — a widgetek jelenlegi
állapotban nincsenek `PipelineConfig`-ba gyűjtve, ez a "teljes workflow"
feladat része (ROADMAP Phase 5, lásd `slicedesigner.project.pipeline`).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from enum import Enum
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from slicedesigner.engines.backplate_engine import BackplateNormalAxis
from slicedesigner.engines.mesh_import import Mesh
from slicedesigner.engines.nesting_engine import NestingRotationMode
from slicedesigner.engines.numbering_engine import NumberingDirectionSign
from slicedesigner.engines.slice_engine import SliceAxis
from slicedesigner.project.mesh_source_registry import (
    MeshSourceDescriptor,
    ParameterSpec,
    discover_mesh_sources,
)

logger = logging.getLogger(__name__)

_SPINBOX_MAX_MM = 100_000.0


class _OptionalDoubleSpinBox(QWidget):
    """`float | None` mezőhöz: `QDoubleSpinBox` egy "Automatikus" jelölőnégyzettel.

    Bejelölt "Automatikus" állapotban a mező `None`-nak felel meg (a
    beviteli mező inaktív) — ez tisztán widget-viselkedés, a `None`↔widget
    leképezést a "teljes workflow" feladat köti majd `PipelineConfig`-hoz.
    """

    def __init__(
        self,
        *,
        decimals: int = 3,
        maximum: float = _SPINBOX_MAX_MM,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.spin_box = QDoubleSpinBox(self)
        self.spin_box.setDecimals(decimals)
        self.spin_box.setMaximum(maximum)
        self.spin_box.setSuffix(" mm")
        self.spin_box.setEnabled(False)

        self.auto_checkbox = QCheckBox("Automatikus", self)
        self.auto_checkbox.setChecked(True)
        self.auto_checkbox.toggled.connect(
            lambda checked: self.spin_box.setEnabled(not checked)
        )

        layout.addWidget(self.spin_box)
        layout.addWidget(self.auto_checkbox)


class _CollapsibleSection(QWidget):
    """Összecsukható "Speciális beállítások" alrész alapértékkel rendelkező
    paramétereknek (prompt 2.2 szakasz)."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._toggle_button = QToolButton(self)
        self._toggle_button.setText(title)
        self._toggle_button.setCheckable(True)
        self._toggle_button.setChecked(False)
        self._toggle_button.setArrowType(Qt.ArrowType.RightArrow)
        self._toggle_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self._toggle_button.toggled.connect(self._on_toggled)

        self.content = QWidget(self)
        self.content.setVisible(False)
        self.content_layout = QFormLayout(self.content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._toggle_button)
        layout.addWidget(self.content)

    def _on_toggled(self, checked: bool) -> None:
        self.content.setVisible(checked)
        self._toggle_button.setArrowType(
            Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
        )


class _GeneratorParameterForm(QWidget):
    """Egy `MeshSourceDescriptor.parameters` listájából generikusan épített
    beviteli form (ADR-0017) — a `ParameterPanel` sosem szembesül
    plugin-specifikus (pl. relief-specifikus) fogalommal, kizárólag
    `ParameterSpec`-ekkel dolgozik.

    Az azonos `ParameterSpec.group`-ú mezők egy közös, összecsukható
    `_CollapsibleSection`-be kerülnek, a csoport első előfordulásának
    helyén — nem szükséges, hogy a `parameters` tuple-ben szomszédosak
    legyenek (ADR-0017 kiegészítés, 2026-08-23, ROADMAP Phase 10.1).

    A `ParameterSpec.visible_when`-nel rendelkező mezők sora (a Qt
    `QFormLayout`-sorban a felirat ÉS a beviteli widget együtt) rejtve
    marad, amíg a vezérlő mező értéke nem egyezik az elvárt értékkel — a
    vezérlő mező értékváltozására a forma minden érintett sor
    láthatóságát újraszámolja, rekurzívan, láncolt függőségekre is
    (ADR-0017 kiegészítés, 2026-08-24, ROADMAP Phase 11.0). A rejtett
    mezők értéke továbbra is szerepel a `values()` visszatérési
    dict-jében — ugyanaz az elv, mint az összecsukott `_CollapsibleSection`
    mezőinél.
    """

    def __init__(
        self,
        parameters: tuple[ParameterSpec, ...],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._float_widgets: dict[str, QDoubleSpinBox] = {}
        self._int_widgets: dict[str, QSpinBox] = {}
        self._str_widgets: dict[str, QLineEdit] = {}
        self._enum_widgets: dict[str, QComboBox] = {}
        self._list_widgets: dict[str, _ListParameterWidget] = {}

        self._spec_by_name: dict[str, ParameterSpec] = {
            spec.name: spec for spec in parameters
        }
        self._row_widgets: dict[str, tuple[QWidget, QFormLayout]] = {}

        self._sections: dict[str, _CollapsibleSection] = {}
        self._group_members: dict[str, list[str]] = {}
        for spec in parameters:
            widget = self._build_widget(spec)
            if spec.group is None:
                layout.addRow(f"{spec.label}:", widget)
                self._row_widgets[spec.name] = (widget, layout)
                continue
            section = self._sections.get(spec.group)
            if section is None:
                section = _CollapsibleSection(spec.group)
                self._sections[spec.group] = section
                layout.addRow(section)
            section.content_layout.addRow(f"{spec.label}:", widget)
            self._row_widgets[spec.name] = (widget, section.content_layout)
            self._group_members.setdefault(spec.group, []).append(spec.name)

        for combo in self._enum_widgets.values():
            combo.currentIndexChanged.connect(self._update_conditional_visibility)
        self._update_conditional_visibility()

    def _build_widget(self, spec: ParameterSpec) -> QWidget:
        if spec.type == "float":
            spin_box = QDoubleSpinBox()
            spin_box.setDecimals(4)
            spin_box.setMinimum(
                spec.minimum if spec.minimum is not None else -_SPINBOX_MAX_MM
            )
            spin_box.setMaximum(
                spec.maximum if spec.maximum is not None else _SPINBOX_MAX_MM
            )
            if spec.unit:
                spin_box.setSuffix(f" {spec.unit}")
            spin_box.setValue(spec.default)
            self._float_widgets[spec.name] = spin_box
            return spin_box
        if spec.type == "int":
            int_spin_box = QSpinBox()
            int_spin_box.setMinimum(
                int(spec.minimum) if spec.minimum is not None else 0
            )
            int_spin_box.setMaximum(
                int(spec.maximum) if spec.maximum is not None else 1_000_000
            )
            int_spin_box.setValue(spec.default)
            self._int_widgets[spec.name] = int_spin_box
            return int_spin_box
        if spec.type == "str":
            line_edit = QLineEdit(str(spec.default))
            self._str_widgets[spec.name] = line_edit
            return line_edit
        if spec.type == "list":
            list_widget = _ListParameterWidget(spec.item_schema)
            self._list_widgets[spec.name] = list_widget
            return list_widget
        combo = QComboBox()
        for choice in spec.choices:
            combo.addItem(choice, choice)
        found_index = combo.findData(spec.default)
        combo.setCurrentIndex(found_index if found_index >= 0 else 0)
        self._enum_widgets[spec.name] = combo
        return combo

    def values(self) -> dict[str, Any]:
        """A form jelenlegi állapota, a `MeshSourceDescriptor.build()`
        által elvárt `values` dict alakjában."""
        result: dict[str, Any] = {}
        for name, float_widget in self._float_widgets.items():
            result[name] = float_widget.value()
        for name, int_widget in self._int_widgets.items():
            result[name] = int_widget.value()
        for name, str_widget in self._str_widgets.items():
            result[name] = str_widget.text()
        for name, combo_widget in self._enum_widgets.items():
            result[name] = combo_widget.currentData()
        for name, list_widget in self._list_widgets.items():
            result[name] = list_widget.values()
        return result

    def _effective_visible(self, name: str) -> bool:
        """Egy mező tényleges (rekurzív) láthatósága.

        `spec.visible_when is None` esetén mindig `True` — ez a
        meglévő, Phase 10-ig egyetlen viselkedés. Egyébként a
        vezérlő mező jelenlegi értékét és a vezérlő mező SAJÁT
        effektív láthatóságát is figyelembe veszi, hogy a láncolt
        függőségek (pl. A a B-től, B a C-től függ) helyesen
        kaszkádoljanak.
        """
        spec = self._spec_by_name.get(name)
        if spec is None or spec.visible_when is None:
            return True
        controller_name, expected_value = spec.visible_when
        controller_combo = self._enum_widgets.get(controller_name)
        if controller_combo is None:
            return True
        if controller_combo.currentData() != expected_value:
            return False
        return self._effective_visible(controller_name)

    def _update_conditional_visibility(self) -> None:
        """Minden `visible_when`-nel rendelkező mező sorának (felirat +
        beviteli widget) láthatóságát frissíti, a jelenlegi vezérlő-
        értékek alapján, majd minden `_CollapsibleSection`-t elrejt,
        ha egyetlen benne lévő mező sem effektíven látható — enélkül
        egy aktuálisan nem releváns generátor (pl. Dune) csoportjai
        üresen, összecsukva, de láthatóan maradnának a formban, még
        akkor is, ha egyik mezőjük sem érhető el (2026-08-29-i
        kiegészítés, a projektgazda élő tesztelés közben jelzett
        visszajelzése alapján).

        Vezérlő-widget értékváltozásra (`currentIndexChanged`)
        hívódik, és egyszer, a form felépítésekor is, a kezdeti állapot
        beállításához."""
        for name, (widget, owning_layout) in self._row_widgets.items():
            visible = self._effective_visible(name)
            widget.setVisible(visible)
            label = owning_layout.labelForField(widget)
            if label is not None:
                label.setVisible(visible)
        for group, members in self._group_members.items():
            section = self._sections[group]
            section.setVisible(any(self._effective_visible(m) for m in members))


class _ListParameterWidget(QWidget):
    """`type="list"` `ParameterSpec`-hez: soronként egy, az `item_schema`
    alapján generikusan épített mini-form, "Hozzáadás"/"Eltávolítás"
    gombokkal (ADR-0017 kiegészítés, 2026-08-21).

    Minden sor önmagában egy `_GeneratorParameterForm`, az `item_schema`-t
    kapva `parameters`-ként — a beágyazott lista (`item_schema`-n belüli
    `type="list"`) nem támogatott.
    """

    def __init__(
        self,
        item_schema: tuple[ParameterSpec, ...],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._item_schema = item_schema
        self._rows: list[_GeneratorParameterForm] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._rows_layout = QVBoxLayout()
        layout.addLayout(self._rows_layout)

        add_button = QPushButton("Hozzáadás")
        add_button.clicked.connect(self._on_add_clicked)
        layout.addWidget(add_button)

    def _on_add_clicked(self) -> None:
        self._add_row()

    def _add_row(self) -> None:
        row_container = QWidget()
        row_layout = QHBoxLayout(row_container)
        row_layout.setContentsMargins(0, 0, 0, 0)

        row_form = _GeneratorParameterForm(self._item_schema)
        row_layout.addWidget(row_form)

        remove_button = QPushButton("Eltávolítás")
        row_layout.addWidget(remove_button)

        self._rows_layout.addWidget(row_container)
        self._rows.append(row_form)

        def _on_remove_clicked() -> None:
            self._rows_layout.removeWidget(row_container)
            row_container.deleteLater()
            self._rows.remove(row_form)

        remove_button.clicked.connect(_on_remove_clicked)

    def values(self) -> list[dict[str, Any]]:
        """Az egyes sorok `item_schema`-kulcsú `values()`-einek listája,
        a sorok hozzáadási sorrendjében."""
        return [row.values() for row in self._rows]


def _make_mm_spinbox(
    *, default: float = 0.0, decimals: int = 3, maximum: float = _SPINBOX_MAX_MM
) -> QDoubleSpinBox:
    """Előre beállított `QDoubleSpinBox` mm-értékű paraméterekhez."""
    spin_box = QDoubleSpinBox()
    spin_box.setDecimals(decimals)
    spin_box.setMaximum(maximum)
    spin_box.setValue(default)
    spin_box.setSuffix(" mm")
    return spin_box


def _make_int_spinbox(*, default: int = 0, maximum: int = 1000) -> QSpinBox:
    """Előre beállított `QSpinBox` egész-értékű paraméterekhez."""
    spin_box = QSpinBox()
    spin_box.setMaximum(maximum)
    spin_box.setValue(default)
    return spin_box


def _make_enum_combo(enum_cls: type[Enum]) -> QComboBox:
    """`QComboBox` feltöltése egy engine-enum tagjaival (érték = `userData`)."""
    combo = QComboBox()
    for member in enum_cls:
        combo.addItem(str(member.value), member)
    return combo


def _build_file_picker(
    dialog_caption: str, *, on_selected: Callable[[str], None] | None = None
) -> tuple[QWidget, QPushButton, QLabel]:
    """Fájlválasztó gomb + útvonal-felirat (kötelező fájl-paraméterekhez).

    `on_selected`, ha meg van adva, kizárólag sikeres fájlválasztás esetén
    (nem "Mégse") hívódik meg, a kiválasztott útvonallal.
    """
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)

    path_label = QLabel("(nincs kiválasztva)")
    path_label.setWordWrap(True)
    browse_button = QPushButton("Tallózás...")

    def _on_browse_clicked() -> None:
        file_path, _ = QFileDialog.getOpenFileName(container, dialog_caption)
        if file_path:
            path_label.setText(file_path)
            if on_selected is not None:
                on_selected(file_path)

    browse_button.clicked.connect(_on_browse_clicked)
    layout.addWidget(browse_button)
    layout.addWidget(path_label)
    return container, browse_button, path_label


def _build_placeholder_table(columns: list[str]) -> tuple[QWidget, QTableWidget]:
    """Üres lista-jellegű felülbírálási mezőkhöz (pl. `manual_dowel_positions`,
    `material_definitions`) — tartalmi validáció nélkül (prompt 2.2 szakasz).

    Új sor hozzáadásakor minden cellába üres, szerkeszthető
    `QTableWidgetItem` kerül, enélkül Qt-ben a cella nem válik azonnal
    szerkeszthetővé — ez a tényleges tartalom-kiolvasás előfeltétele (lásd
    `config_builder._read_material_definitions()` a materials-táblához;
    a másik négy tábla tartalma egyelőre nem jut el a `PipelineConfig`-ba,
    csak szerkeszthető marad).
    """
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)

    table = QTableWidget(0, len(columns), container)
    table.setHorizontalHeaderLabels(columns)

    def _insert_editable_row() -> None:
        row = table.rowCount()
        table.insertRow(row)
        for column in range(len(columns)):
            table.setItem(row, column, QTableWidgetItem(""))

    button_row = QHBoxLayout()
    add_button = QPushButton("Hozzáadás")
    remove_button = QPushButton("Törlés")
    add_button.clicked.connect(_insert_editable_row)

    def _remove_current_row() -> None:
        current_row = table.currentRow()
        if current_row >= 0:
            table.removeRow(current_row)

    remove_button.clicked.connect(_remove_current_row)
    button_row.addWidget(add_button)
    button_row.addWidget(remove_button)
    button_row.addStretch()

    layout.addWidget(table)
    layout.addLayout(button_row)
    return container, table


class ParameterPanel(QTabWidget):
    """A nyolc funkciócsoport (7 engine-paraméter dataclass + DXF Export)
    fenti fülsávos (tab), lapozható kártyás bal panelje.

    Minden fül saját `QScrollArea`-ba csomagolva (nem egy közös, teljes
    panelt átfogó görgető), hogy a hosszabb kártyák (pl. Backplate) kis
    ablakméretnél is önállóan görgethetők legyenek.

    A három kapcsoló (`use_dowels_checkbox`, `use_spacers_checkbox`,
    `use_backplate_checkbox`) a hozzájuk tartozó (Dowel/Gap/Backplate)
    `QGroupBox` show/hide állapotát vezérli, a saját fülükön belül —
    tisztán UI-viselkedés, nem pipeline-logika.

    Az Export fül kezdetben üres — a `RunPanel` DXF Export widgetjeit
    (`export_settings_widget`) a `MainWindow` illeszti be
    `set_export_tab_content()`-tel, mert a `RunPanel`-nek a
    `ParameterPanel` előtt kell létrejönnie (l. `main_window.py`).

    A `mesh_file_selected` signal kizárólag sikeres mesh-fájl-választás
    esetén (nem "Mégse") emittálódik, a kiválasztott útvonallal — a
    `MainWindow` ezt köti az automatikus 3D-előnézet betöltéséhez.
    """

    mesh_file_selected = Signal(str)
    generate_mesh_requested = Signal(object, dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        mesh_import_content = self._build_mesh_import_group()
        self._add_tab(
            "Mesh Import", mesh_import_content, footer=self.generate_mesh_button
        )
        self._add_tab("Slicing", self._build_slicing_group())

        self.use_dowels_checkbox = QCheckBox("Dowel rendszer használata")
        self.dowel_group = self._build_dowel_group()
        self.dowel_group.setVisible(False)
        self.use_dowels_checkbox.toggled.connect(self.dowel_group.setVisible)
        self._add_tab(
            "Dowel", self._build_toggle_tab(self.use_dowels_checkbox, self.dowel_group)
        )

        self.use_spacers_checkbox = QCheckBox("Gap / Spacer rendszer használata")
        self.gap_group = self._build_gap_group()
        self.gap_group.setVisible(False)
        self.use_spacers_checkbox.toggled.connect(self.gap_group.setVisible)
        self._add_tab(
            "Gap", self._build_toggle_tab(self.use_spacers_checkbox, self.gap_group)
        )

        self.use_backplate_checkbox = QCheckBox("Backplate használata")
        self.backplate_group = self._build_backplate_group()
        self.backplate_group.setVisible(False)
        self.use_backplate_checkbox.toggled.connect(self.backplate_group.setVisible)
        self._add_tab(
            "Backplate",
            self._build_toggle_tab(self.use_backplate_checkbox, self.backplate_group),
        )

        self._add_tab("Numbering", self._build_numbering_group())
        self._add_tab("Nesting", self._build_nesting_group())

        self._export_tab_layout = QVBoxLayout()
        self._export_tab_layout.addStretch()
        export_content = QWidget()
        export_content.setLayout(self._export_tab_layout)
        self._add_tab("Export", export_content)

        logger.debug("ParameterPanel felépítve.")

    def _add_tab(
        self, title: str, content: QWidget, *, footer: QWidget | None = None
    ) -> None:
        """Egy fül hozzáadása, saját `QScrollArea`-ba csomagolt tartalommal.

        Ha `footer` meg van adva, a `QScrollArea` ALÁ kerül egy közös
        függőleges layoutban — a görgetéstől függetlenül, fixen látható
        marad (ROADMAP Phase 10.1). `footer=None` esetén a viselkedés
        szó szerint megegyezik a korábbival (a `scroll_area` közvetlenül
        fül-tartalom).
        """
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content)
        if footer is None:
            self.addTab(scroll_area, title)
            return
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll_area)
        container_layout.addWidget(footer)
        self.addTab(container, title)

    @staticmethod
    def _build_toggle_tab(checkbox: QCheckBox, group: QGroupBox) -> QWidget:
        """Dowel/Gap/Backplate fül tartalma: kapcsoló + a hozzá tartozó,
        show/hide-olt `QGroupBox` — a korábbi, közös oszlopbeli mintázat
        VÁLTOZATLAN belső logikával, csak egy önálló fül tartalmaként."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(checkbox)
        layout.addWidget(group)
        layout.addStretch()
        return container

    def set_export_tab_content(self, widget: QWidget) -> None:
        """A `RunPanel` export-beállítás konténerének beillesztése az
        Export fülbe — a `MainWindow` hívja, miután mindkét panel
        létrejött (l. `main_window.py`, 2.4 szakasz)."""
        self._export_tab_layout.insertWidget(0, widget)

    def _build_mesh_import_group(self) -> QGroupBox:
        group = QGroupBox("Mesh Import")
        layout = QFormLayout(group)

        self.mesh_source_descriptors: tuple[MeshSourceDescriptor, ...] = (
            discover_mesh_sources()
        )
        self.generated_mesh: Mesh | None = None
        self.mesh_source_combo: QComboBox | None = None
        self.generate_mesh_button: QPushButton | None = None
        self._generator_source_container: QWidget | None = None
        self._generator_forms_stack: QStackedWidget | None = None

        if self.mesh_source_descriptors:
            self.mesh_source_combo = QComboBox()
            self.mesh_source_combo.addItem("STL fájl", None)
            for descriptor in self.mesh_source_descriptors:
                self.mesh_source_combo.addItem(descriptor.display_name, descriptor)
            self.mesh_source_combo.currentIndexChanged.connect(
                self._on_mesh_source_changed
            )
            layout.addRow("Forrás:", self.mesh_source_combo)

        self._stl_source_container = QWidget()
        stl_layout = QFormLayout(self._stl_source_container)
        stl_layout.setContentsMargins(0, 0, 0, 0)

        file_picker, self.mesh_browse_button, self.mesh_file_path_label = (
            _build_file_picker(
                "Mesh fájl kiválasztása", on_selected=self.mesh_file_selected.emit
            )
        )
        stl_layout.addRow("Fájl útvonal:", file_picker)

        advanced = _CollapsibleSection("Speciális beállítások")

        self.origin_alignment_combo = QComboBox()
        self.origin_alignment_combo.addItem("none", "none")
        self.origin_alignment_combo.addItem("min_corner", "min_corner")
        advanced.content_layout.addRow("Origó igazítás:", self.origin_alignment_combo)

        self.min_plausible_size_spin = _make_mm_spinbox(default=1.0)
        advanced.content_layout.addRow(
            "Min. valószerű méret:", self.min_plausible_size_spin
        )

        self.max_plausible_size_spin = _make_mm_spinbox(default=3000.0)
        advanced.content_layout.addRow(
            "Max. valószerű méret:", self.max_plausible_size_spin
        )

        stl_layout.addRow(advanced)
        layout.addRow(self._stl_source_container)

        if self.mesh_source_descriptors:
            self._generator_source_container = QWidget()
            generator_layout = QVBoxLayout(self._generator_source_container)
            generator_layout.setContentsMargins(0, 0, 0, 0)

            self._generator_forms_stack = QStackedWidget()
            for descriptor in self.mesh_source_descriptors:
                self._generator_forms_stack.addWidget(
                    _GeneratorParameterForm(descriptor.parameters)
                )
            generator_layout.addWidget(self._generator_forms_stack)

            self.generate_mesh_button = QPushButton("Generálás")
            self.generate_mesh_button.clicked.connect(self._on_generate_mesh_clicked)
            self.generate_mesh_button.setVisible(False)

            self._generator_source_container.setVisible(False)
            layout.addRow(self._generator_source_container)

        return group

    def _on_mesh_source_changed(self, index: int) -> None:
        """A "Forrás" legördülő váltásának kezelése: STL fájl vs. egy
        felfedezett MeshSource plugin (ADR-0017) — a megfelelő konténer
        láthatóságát és a generátor-form-stack aktív lapját állítja be.
        A "Generálás" gomb is ide tartozik (2026-08-29-i kiegészítés) —
        STL fájl forrásnál nincs funkciója."""
        if self.mesh_source_combo is None:
            return
        is_stl = self.mesh_source_combo.itemData(index) is None
        self._stl_source_container.setVisible(is_stl)
        if self._generator_source_container is not None:
            self._generator_source_container.setVisible(not is_stl)
        if self.generate_mesh_button is not None:
            self.generate_mesh_button.setVisible(not is_stl)
        if not is_stl and self._generator_forms_stack is not None:
            self._generator_forms_stack.setCurrentIndex(index - 1)

    def _on_generate_mesh_clicked(self) -> None:
        """A "Generálás" gomb kattintás-eseménye: a kiválasztott generátor
        leírója + a generikus form aktuális értékei alapján kéri a
        `MainWindow`-tól a tényleges generálást — a `ParameterPanel` maga
        sosem hívja a `MeshSource` contractot (ADR-0017,
        ARCHITECTURE.md 4. szakasz)."""
        if self.mesh_source_combo is None or self._generator_forms_stack is None:
            return
        descriptor = self.mesh_source_combo.currentData()
        if descriptor is None:
            return
        form = self._generator_forms_stack.currentWidget()
        if not isinstance(form, _GeneratorParameterForm):
            return
        self.generate_mesh_requested.emit(descriptor, form.values())

    def _build_slicing_group(self) -> QGroupBox:
        group = QGroupBox("Slicing")
        layout = QFormLayout(group)

        self.slice_thickness_spin = _make_mm_spinbox(default=1.0)
        layout.addRow("Szelet-vastagság:", self.slice_thickness_spin)

        advanced = _CollapsibleSection("Speciális beállítások")

        self.slice_axis_combo = _make_enum_combo(SliceAxis)
        self.slice_axis_combo.setCurrentText(SliceAxis.Z.value)
        advanced.content_layout.addRow("Szelet-tengely:", self.slice_axis_combo)

        self.slice_gap_spin = _make_mm_spinbox(default=0.0)
        advanced.content_layout.addRow("Gap (szeletek közt):", self.slice_gap_spin)

        self.max_scale_tolerance_spin = QDoubleSpinBox()
        self.max_scale_tolerance_spin.setDecimals(4)
        self.max_scale_tolerance_spin.setMaximum(1.0)
        self.max_scale_tolerance_spin.setValue(0.02)
        advanced.content_layout.addRow(
            "Max. skálázási tűrés:", self.max_scale_tolerance_spin
        )

        layout.addRow(advanced)
        return group

    def _build_dowel_group(self) -> QGroupBox:
        group = QGroupBox("Dowel")
        layout = QFormLayout(group)

        self.dowel_diameter_spin = _make_mm_spinbox(default=6.0)
        layout.addRow("Dowel átmérő:", self.dowel_diameter_spin)

        advanced = _CollapsibleSection("Speciális beállítások")

        self.dowel_spacer_diameter_spin = _make_mm_spinbox(default=0.0)
        advanced.content_layout.addRow(
            "Spacer átmérő:", self.dowel_spacer_diameter_spin
        )

        self.min_edge_clearance_optional = _OptionalDoubleSpinBox()
        advanced.content_layout.addRow(
            "Min. szegély-távolság:", self.min_edge_clearance_optional
        )

        self.dowel_count_per_region_spin = _make_int_spinbox(default=3, maximum=100)
        advanced.content_layout.addRow(
            "Dowel-szám régiónként:", self.dowel_count_per_region_spin
        )

        self.min_dowels_per_region_spin = _make_int_spinbox(default=1, maximum=100)
        advanced.content_layout.addRow(
            "Min. Dowel-szám régiónként:", self.min_dowels_per_region_spin
        )

        self.blind_hole_cap_optional = _OptionalDoubleSpinBox()
        advanced.content_layout.addRow(
            "Vak furat mélység-korlát:", self.blind_hole_cap_optional
        )

        layout.addRow(advanced)

        manual_positions_widget, self.manual_dowel_positions_table = (
            _build_placeholder_table(["x_mm", "y_mm", "start_slice", "end_slice"])
        )
        layout.addRow("Kézi Dowel-pozíciók:", manual_positions_widget)

        return group

    def _build_gap_group(self) -> QGroupBox:
        group = QGroupBox("Gap")
        layout = QFormLayout(group)

        self.gap_spacer_diameter_spin = _make_mm_spinbox(default=6.0)
        layout.addRow("Spacer átmérő:", self.gap_spacer_diameter_spin)

        advanced = _CollapsibleSection("Speciális beállítások")

        self.spacer_count_per_gap_spin = _make_int_spinbox(default=3, maximum=100)
        advanced.content_layout.addRow(
            "Spacer-szám résenként:", self.spacer_count_per_gap_spin
        )

        self.min_spacers_per_region_spin = _make_int_spinbox(default=1, maximum=100)
        advanced.content_layout.addRow(
            "Min. Spacer-szám régiónként:", self.min_spacers_per_region_spin
        )

        layout.addRow(advanced)
        return group

    def _build_backplate_group(self) -> QGroupBox:
        group = QGroupBox("Backplate")
        layout = QFormLayout(group)

        self.backplate_normal_axis_combo = _make_enum_combo(BackplateNormalAxis)
        layout.addRow("Backplate normál-tengely:", self.backplate_normal_axis_combo)

        self.backplate_thickness_spin = _make_mm_spinbox(default=3.0)
        layout.addRow("Backplate vastagság:", self.backplate_thickness_spin)

        self.tab_length_spin = _make_mm_spinbox(default=10.0)
        layout.addRow("Tab hossz:", self.tab_length_spin)

        advanced = _CollapsibleSection("Speciális beállítások")

        self.backplate_plane_tolerance_spin = _make_mm_spinbox(default=0.1)
        advanced.content_layout.addRow(
            "Backplate sík-tűrés:", self.backplate_plane_tolerance_spin
        )

        self.backplate_margin_spin = _make_mm_spinbox(default=0.0)
        advanced.content_layout.addRow("Backplate margó:", self.backplate_margin_spin)

        self.tab_spacing_spin = _make_mm_spinbox(default=700.0)
        advanced.content_layout.addRow("Tab-távolság:", self.tab_spacing_spin)

        self.tab_edge_margin_optional = _OptionalDoubleSpinBox()
        advanced.content_layout.addRow(
            "Tab szegély-margó:", self.tab_edge_margin_optional
        )

        self.material_reference_edit = QLineEdit()
        self.material_reference_edit.setPlaceholderText("(nincs megadva)")
        advanced.content_layout.addRow(
            "Anyag-referencia:", self.material_reference_edit
        )

        layout.addRow(advanced)

        tab_overrides_widget, self.slice_tab_overrides_table = _build_placeholder_table(
            [
                "slice_index",
                "island_index",
                "tab_length_mm",
                "tab_spacing_mm",
                "tab_edge_margin_mm",
            ]
        )
        layout.addRow("Szelet-Tab felülbírálások:", tab_overrides_widget)

        non_backplate_widget, self.non_backplate_islands_table = (
            _build_placeholder_table(["slice_index", "island_index"])
        )
        layout.addRow("Backplate-mentes szigetek:", non_backplate_widget)

        return group

    def _build_numbering_group(self) -> QGroupBox:
        group = QGroupBox("Numbering")
        layout = QFormLayout(group)

        self.numbering_normal_axis_combo = _make_enum_combo(BackplateNormalAxis)
        layout.addRow("Jelölés normál-tengely:", self.numbering_normal_axis_combo)

        self.numbering_direction_sign_combo = _make_enum_combo(NumberingDirectionSign)
        layout.addRow("Jelölés irány-előjel:", self.numbering_direction_sign_combo)

        self.numbering_height_spin = _make_mm_spinbox(default=5.0)
        layout.addRow("Jelölés magasság:", self.numbering_height_spin)

        advanced = _CollapsibleSection("Speciális beállítások")

        self.numbering_min_height_optional = _OptionalDoubleSpinBox()
        advanced.content_layout.addRow(
            "Min. jelölés magasság:", self.numbering_min_height_optional
        )

        self.numbering_margin_optional = _OptionalDoubleSpinBox()
        advanced.content_layout.addRow("Jelölés margó:", self.numbering_margin_optional)

        layout.addRow(advanced)

        overrides_widget, self.slice_numbering_overrides_table = (
            _build_placeholder_table(
                [
                    "slice_index",
                    "island_index",
                    "numbering_height_mm",
                    "numbering_min_height_mm",
                    "numbering_margin_mm",
                ]
            )
        )
        layout.addRow("Szelet-jelölés felülbírálások:", overrides_widget)

        return group

    def _build_nesting_group(self) -> QGroupBox:
        group = QGroupBox("Nesting")
        layout = QFormLayout(group)

        materials_widget, self.material_definitions_table = _build_placeholder_table(
            [
                "material_id",
                "thickness_mm",
                "sheet_width_mm",
                "sheet_height_mm",
                "kerf_mm",
            ]
        )
        layout.addRow("Anyagok:", materials_widget)

        self.slice_material_id_edit = QLineEdit()
        layout.addRow("Szelet anyag-azonosító:", self.slice_material_id_edit)

        self.seam_marking_height_spin = _make_mm_spinbox(default=1.0)
        layout.addRow("Varrat-jelölés magasság:", self.seam_marking_height_spin)

        advanced = _CollapsibleSection("Speciális beállítások")

        self.backplate_material_id_edit = QLineEdit()
        self.backplate_material_id_edit.setPlaceholderText("(nincs megadva)")
        advanced.content_layout.addRow(
            "Backplate anyag-azonosító:", self.backplate_material_id_edit
        )

        self.spacer_material_id_edit = QLineEdit()
        self.spacer_material_id_edit.setPlaceholderText("(nincs megadva)")
        advanced.content_layout.addRow(
            "Spacer anyag-azonosító:", self.spacer_material_id_edit
        )

        self.nesting_rotation_mode_combo = _make_enum_combo(NestingRotationMode)
        self.nesting_rotation_mode_combo.setCurrentText(
            NestingRotationMode.ORTHOGONAL.value
        )
        advanced.content_layout.addRow(
            "Forgatási mód:", self.nesting_rotation_mode_combo
        )

        self.seam_marking_min_height_optional = _OptionalDoubleSpinBox()
        advanced.content_layout.addRow(
            "Min. varrat-jelölés magasság:", self.seam_marking_min_height_optional
        )

        self.seam_marking_margin_optional = _OptionalDoubleSpinBox()
        advanced.content_layout.addRow(
            "Varrat-jelölés margó:", self.seam_marking_margin_optional
        )

        layout.addRow(advanced)
        return group
